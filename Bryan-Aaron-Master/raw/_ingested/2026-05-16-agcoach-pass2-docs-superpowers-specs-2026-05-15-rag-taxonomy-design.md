# RAG Taxonomy + Ingest Enforcement

**Date:** 2026-05-15
**Status:** Design (pending implementation)
**Owner:** Bryan

## Problem

Brain v2 retrieval returns weak/mixed-topic chunks, so the model defaults to "ask one clarifying question if ambiguous." Manual QA confirmed: asking *"how do I score slaughter cattle?"* triggers two consecutive clarifying questions before any rulebook answer.

Root cause is data, not prompt:

| Symptom | Cause |
|---|---|
| 4,193 `rulebook` chunks have `contest_category = NULL` | No classification step at ingest |
| `knowledge_documents` has no `subcategory` column | DB schema does not mirror `TOPIC_QUERIES` granularity in `lib/ai/rag-quiz.ts` |
| Livestock = 574 chunks, all flat | "Slaughter Cattle Grading" mixed with "Female Selection" mixed with "Phenotype-Cattle" |
| `source_path` NULL on rulebook chunks | Cannot trace chunk → PDF for verification |
| 174 Obsidian chunks all NULL `contest_category` | Same loophole as rulebook |

Net effect: when retrieval ANN search returns chunks across many sub-domains within Livestock, the top-K is noisy, similarity scores compress, and the model lacks signal to answer confidently.

## Scope

In scope:

1. Add `subcategory`, `classified_by`, `classified_at` columns to `knowledge_documents`.
2. Build `scripts/classify_chunk.py` — heuristic rules with Gemini Flash fallback. Labels drawn from existing `TOPIC_QUERIES` keys.
3. Build `scripts/backfill_taxonomy.py` — idempotent, resumable backfill for ~16k existing chunks.
4. Rewrite `ingest_knowledge.py` to require `(contest_category, subcategory, source_path)` at insert; failures land in new `classification_failures` table.
5. Update `match_knowledge_v2` RPC — accept optional `p_subcategory`, apply additive similarity boost (no filter, no zero-result cliff).
6. New `lib/ai/brain/queryRouter.ts` — keyword map deriving subcategory hint from user query. Plumbed into `brain-v2.ts`.
7. Post-backfill enforcement migration: `contest_category NOT NULL` + `source_path NOT NULL` for `source_type IN ('rulebook','obsidian')`.

Out of scope (each its own future spec):

- NotebookLM ingest (AI Brain + Wool notebooks into `knowledge_documents`).
- Pinecone index for personal/session memory (separate from knowledge).
- Retrieval algorithm tuning beyond the subcategory boost (query rewrite, hybrid lex+vec, weight optimization).
- User/teacher memory architecture (chat history, preferences, progress signals).
- Superadmin UI for reviewing `classification_failures` rows.

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Taxonomy depth | 3 levels: `source_type` / `contest_category` / `subcategory` | Matches how CDEs subdivide. Mirrors existing `TOPIC_QUERIES` keys in code. |
| Subcategory enum source | Existing `TOPIC_QUERIES` keys in `lib/ai/rag-quiz.ts` | Already the de-facto source of truth; one place to maintain. |
| DB integrity | `text` column, no FK to enum table | `TOPIC_QUERIES` evolves often; FK adds friction with no real safety win. |
| Classification approach | Heuristic + Gemini Flash fallback | Heuristic covers ~70% of chunks cheaply; LLM cleans up the rest. ~$0.50 total for full backfill. |
| Ingest enforcement | Hard block on NULL contest/subcategory; row goes to `classification_failures` instead of `knowledge_documents` | Permanent fix for the loophole that created the 4193 NULL rows. |
| RPC integration | Additive boost, not filter | Wrong subcategory hint cannot zero out results; degrades to current behavior. |
| Client query hint | Keyword map (regex), not LLM | Cheap, deterministic, covers top ~50 queries. LLM query-rewrite belongs to retrieval-tuning spec. |
| Backfill scope | All `source_type` values including `obsidian` and `app_meta` | Same loophole; uniform fix. |

## Design

### 1. Schema migration A — additive

`supabase/migrations/YYYYMMDDHHMMSS_rag_taxonomy.sql`:

```sql
alter table knowledge_documents
  add column if not exists subcategory text,
  add column if not exists classified_by text
    check (classified_by in ('heuristic','llm','manual')),
  add column if not exists classified_at timestamptz;

create index if not exists knowledge_documents_subcat_idx
  on knowledge_documents (contest_category, subcategory)
  where contest_category is not null;

create table if not exists classification_failures (
  id uuid primary key default gen_random_uuid(),
  chunk_text_preview text not null,
  source_type text not null,
  source_path text,
  reason text not null,
  attempted_label jsonb,
  created_at timestamptz default now()
);

alter table classification_failures enable row level security;
create policy "admin read" on classification_failures
  for select using (
    auth.uid() in (select user_id from public.users where role = 'superadmin')
  );
```

### 2. Classifier module — `scripts/classify_chunk.py`

Single Python module callable from both ingest and backfill. Signature:

```python
def classify_chunk(
    chunk_text: str,
    source_type: Literal['rulebook','obsidian','app_meta'],
    source_path: str | None,
    frontmatter: dict | None = None,
) -> ClassificationResult:
    # ClassificationResult = {
    #   contest_category: str | None,
    #   subcategory: str | None,
    #   classified_by: 'heuristic' | 'llm',
    #   confidence: float,  # 0..1
    # }
```

#### Heuristic stage

Priority order:

1. **`source_type == 'app_meta'`** — already typed in code. Map `practice_module_id → (contest_category, subcategory)` from a static dict mirroring `app/contest/[id].tsx → startPractice()`.
2. **`source_type == 'obsidian'`** — frontmatter `contest:` and `subcategory:` fields first. Then vault path: split `source_path` on `/`, first segment matches a `contest_category` value → use it.
3. **`source_type == 'rulebook'`** — filename pattern (`livestock*.pdf` → Livestock, `horse*.pdf` → Horse, etc.). TOC heading regex matched against chunk text for subcategory (e.g. `r'Slaughter Cattle Grading Class'` → `Livestock-USDA-Grading`).

Heuristic returns `confidence = 1.0` when matched; otherwise falls through to LLM.

#### LLM stage

Gemini Flash, structured output. Schema:

```json
{
  "contest_category": "Livestock",
  "subcategory": "Livestock-USDA-Grading",
  "confidence": 0.87
}
```

Prompt receives: chunk text (first 1000 chars) + filtered candidate list (`TOPIC_QUERIES` keys whose prefix matches a known `contest_category` if heuristic narrowed contest, otherwise the full enum).

Confidence < 0.6 → return `contest_category=None, subcategory=None` and let caller insert a `classification_failures` row.

### 3. Backfill script — `scripts/backfill_taxonomy.py`

Idempotent, resumable. Behavior:

```
- args: --dry-run, --batch-size N (default 100), --source-type (filter)
- query: select id, content, source_type, source_path, frontmatter
         from knowledge_documents
         where contest_category is null or subcategory is null
         order by id
         limit batch
- for each row: call classify_chunk(...)
- accumulate updates; flush per batch
- on confidence<0.6: insert classification_failures row, skip update
- emit summary every batch: counts by classified_by + failure count
- exit code 0 on completion
```

Estimated workload:

| Bucket | Rows | Heuristic match | LLM fallback |
|---|---|---|---|
| Rulebook NULL contest | 4,193 | ~85% (filename strong) | ~620 |
| Rulebook NULL subcategory only | ~7,800 | ~60% (TOC regex partial) | ~3,120 |
| Obsidian | 174 | ~70% (frontmatter + path) | ~52 |
| app_meta | 41 | 100% | 0 |
| **Total LLM calls** | | | **~3,800** |

Gemini Flash priced ≈ $0.0001 per call. Total backfill cost ≈ **$0.40**.

### 4. Ingest pipeline rewrite — `ingest_knowledge.py`

Net change: every chunk passes through `classify_chunk` before insert. Pseudocode:

```python
for file in to_ingest:
    chunks = chunk_file(file)
    for chunk in chunks:
        result = classify_chunk(chunk.text, src_type, file.path, chunk.frontmatter)
        if result.contest_category is None or result.subcategory is None:
            insert_classification_failure(chunk, result, reason='low_confidence')
            continue
        insert_knowledge_chunk(
            content=chunk.text,
            source_type=src_type,
            source_path=file.path,
            contest_category=result.contest_category,
            subcategory=result.subcategory,
            classified_by=result.classified_by,
            classified_at=now(),
            embedding=embed(chunk.text),
        )
```

No chunk lands in `knowledge_documents` without taxonomy populated.

### 5. RPC update — `match_knowledge_v2` accepts `p_subcategory`

`supabase/migrations/YYYYMMDDHHMMSS_match_knowledge_v2_subcat.sql`:

```sql
create or replace function match_knowledge_v2(
  p_query_embedding halfvec(3072),
  p_contest_category text default null,
  p_subcategory text default null,    -- new
  p_event_type text default null,
  p_source_types text[] default null,
  p_match_count int default 12,
  p_uid uuid default null
)
returns table (...)
language sql stable as $$
  with ann as (
    select id, content, source_type, source_path, contest_category, subcategory,
           1 - (embedding <=> p_query_embedding) as similarity
    from knowledge_documents
    where (p_source_types is null or source_type = any(p_source_types))
    order by embedding <=> p_query_embedding
    limit p_match_count * 4
  )
  select id, content, source_type, source_path, contest_category, subcategory,
         similarity
         + case when p_contest_category is not null and contest_category = p_contest_category
                then 0.10 else 0 end
         + case when p_subcategory is not null and subcategory = p_subcategory
                then 0.15 else 0 end
         as boosted_similarity
  from ann
  order by boosted_similarity desc
  limit p_match_count;
$$;
```

Boost values are additive on a [0,1] cosine similarity. Subcategory hint > contest hint > base ANN.

### 6. Client query hint — `lib/ai/brain/queryRouter.ts`

```ts
type Hint = { contestCategory?: string; subcategory?: string };

const KEYWORD_TO_SUBCAT: Array<{ pattern: RegExp; contest: string; sub: string }> = [
  { pattern: /\b(slaughter|grading|carcass|usda choice|usda prime)\b/i,
    contest: 'Livestock', sub: 'Livestock-USDA-Grading' },
  { pattern: /\b(reining|maneuver|horsemanship)\b/i,
    contest: 'Horse', sub: 'Horse-Reining-Maneuvers' },
  // … 30-50 patterns seeded from TOPIC_QUERIES, extendable
];

export function routeQuery(text: string): Hint {
  for (const { pattern, contest, sub } of KEYWORD_TO_SUBCAT) {
    if (pattern.test(text)) return { contestCategory: contest, subcategory: sub };
  }
  return {};
}
```

`brain-v2.ts` calls `routeQuery(question)` before retrieval and forwards `subcategory` to the edge fn → RPC.

### 7. Schema migration B — enforcement (run only after backfill green)

`supabase/migrations/YYYYMMDDHHMMSS_rag_taxonomy_enforce.sql`:

```sql
-- assumes backfill complete and unresolved rows have been hand-fixed or accepted
alter table knowledge_documents
  alter column contest_category set not null,
  alter column source_path set not null;
```

If any rows still have NULL, this migration will FAIL — that is the gate.

### 8. Files

| File | Action |
|---|---|
| `supabase/migrations/YYYYMMDDHHMMSS_rag_taxonomy.sql` | Create — additive schema |
| `supabase/migrations/YYYYMMDDHHMMSS_match_knowledge_v2_subcat.sql` | Create — RPC accepts subcategory |
| `supabase/migrations/YYYYMMDDHHMMSS_rag_taxonomy_enforce.sql` | Create — runs after backfill |
| `scripts/classify_chunk.py` | Create |
| `scripts/backfill_taxonomy.py` | Create |
| `ingest_knowledge.py` | Modify — pass through classifier |
| `lib/ai/brain/queryRouter.ts` | Create |
| `lib/ai/brain-v2.ts` | Modify — call routeQuery + forward subcategory |
| `supabase/functions/match-knowledge-v2/index.ts` | Modify — accept + forward p_subcategory |
| `SCHEMA.md` | Update — document new columns + table |
| `CLAUDE.md` | Append decision log entry |

## Verification

1. **Backfill dry-run** — `python3 scripts/backfill_taxonomy.py --dry-run` produces a per-source summary. Eyeball 20 random classifications.
2. **Live backfill** — run with `--batch-size 100`. Confirm post-state via SQL:
   ```sql
   select source_type, classified_by, count(*) from knowledge_documents group by 1,2;
   select count(*) from knowledge_documents where contest_category is null;
   select count(*) from classification_failures;
   ```
3. **RPC unit test** — call `match_knowledge_v2` with and without `p_subcategory`. Confirm boosted ordering when matched, unchanged ordering otherwise.
4. **E2E QA** — ask `/study/ai-brain` "how do I score slaughter cattle?" — must:
   - Hit `Livestock-USDA-Grading` chunks in top-3 retrieval.
   - Answer with cited rulebook excerpts.
   - No clarifying-question loop.
5. **Regression** — confirm `rag-quiz.ts` quiz generation still works (`match-knowledge` legacy fn) — schema is additive, legacy untouched.
6. **Enforcement migration** — only run after step 4 passes. If it fails on NULL rows, inspect `classification_failures` and the surviving NULL chunks; decide per-row whether to fix or delete.

## Rollback

- Migration A (additive) — reversible with `alter table drop column`.
- Backfill — `update knowledge_documents set contest_category=null, subcategory=null where classified_by in ('heuristic','llm');`
- RPC change — additive arg with default NULL; existing callers unaffected. Revert by re-applying the previous RPC definition.
- Ingest rewrite — keep old version on a branch tag.
- Migration B (enforcement) — drop the NOT NULL constraints.

## Open Questions

None at design time. Subcategory enum is dynamic via `TOPIC_QUERIES`; classifier prompt regenerates the candidate list each run.
