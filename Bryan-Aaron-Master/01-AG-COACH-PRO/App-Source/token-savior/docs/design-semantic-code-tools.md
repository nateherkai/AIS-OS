# Design — Semantic code tools (post-Nomic)

Status: DRAFT, pending empirical model choice from `compare_models.py`.

Three features unlock value from the new embedding stack for TS's non-memory
tools. They share one piece of infrastructure: **a vector index over code
symbols** (as opposed to `obs_vectors` which indexes memory observations).

## 1. `search_codebase(semantic=True)` — flagship

### Today

`search_codebase(pattern)` is regex-only. To find "the function that handles
dedup logic" you need to guess a keyword (`dedup|duplicate|unique...`) and
hope.

### Target

```python
q.search_codebase("function that removes duplicate memory entries", semantic=True)
# → [{"file": "memory/observations.py", "symbol": "dedup_observations",
#     "line": 142, "score": 0.87, "excerpt": "def dedup_observations(..."}]
```

### How

For each indexed symbol, build an "embedding document":

```
search_document: {kind} {name}
{signature}
{docstring or first 3 non-blank body lines}
```

Embed once at index time, store in a new `symbol_vectors` table:

```sql
CREATE VIRTUAL TABLE symbol_vectors USING vec0(
  symbol_key TEXT PRIMARY KEY,      -- "file::qualified_name"
  embedding FLOAT[N]                 -- N = dim of chosen model
);
```

At query time: `embed(query, as_query=True)` then k-NN. Return top-k with
symbol metadata pulled from the existing project index.

### Cost

Typical project: 500–3000 symbols. Indexing is O(N) one-time, ~0.1s per
symbol on CPU → 1–5 min initial. Incremental reindex on file change uses
the existing `reindex_file` hook — only re-embed touched symbols.

## 2. True `find_semantic_duplicates` (embedding-based)

### Today

`find_semantic_duplicates` returns groups where the AST-normalized hash
collides. Misses functions that do the same thing written differently
(different variable names, reordered branches, different control flow).

### Target

New mode `method="embedding"` (default stays `"ast"` for speed):

```python
q.find_semantic_duplicates(method="embedding", min_similarity=0.85)
```

### How

Reuse `symbol_vectors` from feature 1. For each pair in the same project:
cosine similarity. Cluster pairs above threshold. Filter trivial hits (getters,
one-liners) with existing `min_lines` logic.

Tradeoff: O(N²) pair comparison on CPU. On 3000 symbols that's 4.5M pairs
× cheap dot product → still a few seconds. Acceptable for a manual run.

### Why it's worth it

AST hash detects copy-paste (important for stale utilities). Embedding
detects conceptual duplication — two functions that grew independently and
converged. Different bug, different value.

## 3. `find_library_symbol_by_description`

### Today

`get_library_symbol(package, symbol_path)` needs the exact name. To find
`list_library_symbols(package, pattern=regex)` does regex filtering over
names. Neither helps when you don't know the name.

### Target

```python
q.find_library_symbol_by_description(
    package="fastembed",
    description="encode a list of strings into vectors",
)
# → [{"symbol": "TextEmbedding.embed", "score": 0.91, ...}]
```

### How — on-the-fly, no persistent index

Unlike code symbols (which you query repeatedly), library lookups are
one-shot. No need for a persistent index:

1. List exports via existing `list_library_symbols` (TS) or `_py_symbol`
2. For each, extract name + docstring (already accessible from typings/
   Python introspection)
3. Embed all at query time (~50 symbols × 10ms = 500ms)
4. Cosine-rank against `embed(description, as_query=True)`

500ms latency is fine for a one-shot lookup. No disk storage. No reindex
concerns.

## Shared infrastructure

- New module: `src/token_savior/memory/symbol_embeddings.py`
  - `build_symbol_doc(symbol) -> str` — produce the embedding input
  - `index_symbol(key, doc, conn) -> bool` — embed + insert into vec table
  - `reindex_project_symbols(project_root) -> dict` — bulk index
  - `search_symbols(query, project_root, limit=10) -> list[dict]` — k-NN

- SQL: new `symbol_vectors` vec0 table (ships with feat/1 migration)
- `search.py` and friends stay untouched — these tools use their own path

## Safety design (specific to semantic ≠ regex)

Regex search fails loudly — a non-matching pattern gives empty results. A
semantic search always returns the k closest vectors, so **near-misses are
plausible and can mislead** a consumer that trusts the top result blindly.
The POC surfaced exactly this: query "function that removes duplicate
memory observations" returned `_mh_memory_delete` as top-1 (score 0.682).
A consumer acting on that result without verification would invoke a
destructive wipe instead of a dedup.

The contract for `search_codebase(semantic=True)` must therefore enforce:

1. **Always return k ≥ 5 with scores visible**. Never top-1 only. The
   consumer (human or agent) must see that multiple candidates exist.
2. **Include disambiguating metadata per hit**: signature + first
   docstring line + `file:lineno`, so one round-trip is enough to verify.
3. **Read-only semantics documented in the MCP schema**. The tool
   description must state: "Never call, modify, or delete a symbol
   returned solely by a semantic match — resolve the exact name via
   `find_symbol` first and cross-check the body via `get_function_source`
   before any destructive operation." This becomes a hard rule in
   project_rules.md.
4. **Low-confidence warning**: when `top1_score < 0.75` or when
   `top1_score - top2_score < 0.02` (dense cluster, ambiguous), the
   response prepends a warning that the query is likely ambiguous and
   suggests refining it.
5. **No auto-edit path**: `replace_symbol_source` / `insert_near_symbol` /
   `move_symbol` accept symbol names, not scores. If a caller wants to
   edit something it found via semantic search, it must pass through a
   `find_symbol(exact_name)` call as a gate — same rule that applies
   today to regex `search_codebase` results anyway.

The combination of #3, #4, #5 turns semantic search into a
**discoverability tool**, not an execution path. The user POC miss
(delete vs dedup) becomes a non-issue because the consumer sees
`_mh_memory_delete` and `_mh_memory_restore` in the top-3, spots the
mismatch, refines the query, or uses regex fallback.

### Applies equally to feature 2 (embedding duplicates)

Similar risk: embedding-based duplicate detection can flag two functions
as "duplicates" when they differ in a subtle business rule. The output
must present pairs with score and invite the human to verify, never
auto-merge.

### Does not apply to feature 3 (library lookup)

Library symbol retrieval returns typing/stub references — reading them
is non-destructive and the consumer can't accidentally call the wrong
function because it's external. Same safety budget, lower blast radius.

## Execution order after bench

Assuming the bench picks a model (Nomic or another VPS-safe candidate):

1. Ship the chosen model if ≠ current Nomic (migration is one-line in
   `_MODEL_NAME`, drop/rebuild `obs_vectors` like we did before).
2. Build `symbol_embeddings.py` + `symbol_vectors` schema.
3. Wire feature 1 (`search_codebase` semantic).
4. Wire feature 2 (embedding duplicates) — reuses the same table.
5. Wire feature 3 (on-the-fly library retrieval) — no table needed.
6. tsbench-style validation: a mini "find-by-description" benchmark like
   `memory_retrieval` but over code symbols, to prove the qualitative
   win empirically.

Estimated effort: 2–3 days total for the three features post-model-choice.
Feature 1 alone is ~1 day (infra + tool + tests + reindex hook). Feature 2
is ~0.5 day on top. Feature 3 is ~0.5 day standalone.
