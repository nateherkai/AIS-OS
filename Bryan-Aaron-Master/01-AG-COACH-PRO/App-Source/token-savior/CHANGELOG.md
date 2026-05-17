# Changelog

## v3.0.0 — PyPI catch-up release (2026-04-30)

First PyPI release since v2.6.0 (2026-04-20). Bundles every accumulated
change from v2.7.0 through today onto the index. PyPI users on
`pip install token-savior-recall` jumping from v2.6.0 will see:

### Highlights since v2.6.0

- **Bench-driven optimization passes (v2.7.0 / v2.7.1)** — 14
  description/manifest tweaks; mean −13 % active tokens.
- **Audit & telemetry (v2.8.0)** — `audit_file`, watcher, telemetry
  groundwork.
- **Stability (v2.8.1 → v2.8.4)** — USE WHEN / NOT WHEN tool
  descriptions, root-level `_matches_include_patterns` fix,
  fail-loud memory hooks.
- **Defer-loading via `ts_search` + tiny / tiny_plus profiles
  (v2.9.0)** — embedding-based tool routing for thin manifests
  (~1.6 KT for `tiny_plus`, ~85 % manifest cost cut vs `lean`).
- **`get_feature_files` + v3 ergonomics groundwork.**

### New in v3.0.0 itself

- **Issue #26 — Java indexing resilience.** `_annotate_file` and
  `reindex_file` now wrap the dispatcher's `annotate(...)` call in
  an explicit `Exception` handler so a single bad file (parse glitch,
  encoding edge case, missing tree-sitter binding) is logged and
  skipped instead of poisoning the whole index. Adds `TestJavaProject`
  (default `include_patterns` end-to-end) and `TestAnnotatorResilience`
  regression coverage.
- **Issue #27 — MCP request lifecycle logging.** Opt-in
  `TOKEN_SAVIOR_TRACE=1` emits `-> call <name>` /
  `<- ok / err <name> (Nms)` on every `call_tool` invocation, plus
  three startup checkpoints (migrations, stdio open, server.run loop
  entered). Default behaviour unchanged. Helps localise the Windows
  `AbortError` class of issues by giving operators concrete request
  boundaries in stderr.
- **Test-suite bookkeeping.** `test_tool_count` and
  `test_nav_profile_is_subset_of_core` updated for the v2.9 `ts_search`
  addition (66 → 67 tools, `ts_search` legitimately exposed under
  `nav`).

### Compatibility

No deprecations or removals. Drop-in upgrade from any v2.x — including
the v2.6.0 snapshot still on PyPI before this release.

---

## v2.9.0 — Defer-loading via ts_search + capture/hints gating (2026-04-26)

Three additive optimizations targeting agent-side token cost. All changes
are opt-in via env var or new profile; default behavior is unchanged.

### `ts_search` defer-loading router (new tool)

Embedding-based tool routing for thin manifests. The agent passes a
natural-language query and gets the top-K Token Savior tools back —
including each one's full `inputSchema`, ready for the next turn.

```python
ts_search(query="find dependents of update_user", top_k=5)
# → {"matched_tools": [{"name": "get_dependents", "score": 0.68, ...}, ...]}
```

Implementation: cosine similarity over Nomic 768d embeddings of every
TOOL_SCHEMAS entry, computed once and cached in process memory (~200 KB).
Falls back to substring overlap if `VECTOR_SEARCH_AVAILABLE=False`. The
candidate pool is restricted to currently-visible tools, so a `tiny`
session can reach back into the ~60 hidden tools without breaking
profile/env-var gating.

Mirrors the [Tool Attention paper](https://arxiv.org/html/2604.21816v1)
(47.3k → 2.4k tokens / turn at 120 tools, −95 % prefix).

### New profile: `tiny`

```
TOKEN_SAVIOR_PROFILE=tiny → 6 tools advertised, ~1 090 tokens manifest
```

Exposes only `switch_project`, `find_symbol`, `get_function_source`,
`get_full_context`, `search_codebase`, `ts_search`. Other 60+ tools are
reachable just-in-time via `ts_search`. Adds 1 round-trip per turn for
non-hot tool usage but cuts the manifest cost ~85 % vs `lean`.

### New profile: `tiny_plus`

```
TOKEN_SAVIOR_PROFILE=tiny_plus → 10 tools advertised, ~1 592 tokens manifest
```

`tiny` + 4 tools that the 26/04 bench showed agents abandon when missing
(`find_dead_code`, `get_call_chain`, `analyze_config`, `get_git_status`).
Closes the score gap of `tiny` (91.7 % → 97.2 % on tsbench-90) while
keeping the manifest under 2 K tokens.

Bench tsbench-90 with Opus 4.7 / Claude Code 2.1.119:

| Profile     | Tools | Manifest | Score   | Active mean | Δ vs lean  |
|-------------|------:|---------:|---------|------------:|-----------:|
| `tiny`      |     6 |   1.1 KT | 91.7 %  |       3 805 | -57 % active, -8.3 pp score |
| `tiny_plus` |    10 |   1.6 KT | 97.2 %  |       6 550 | -27 % active, -2.8 pp score |
| `ultra`     |    33 |   4.6 KT | 98.3 %  |      10 260 | +15 % active, -1.7 pp score |
| `lean`      |    52 |   7.1 KT | 99.4 %  |      11 302 |  baseline (current degraded) |

### `TS_CAPTURE_DISABLED=1` now gates the manifest too

Previously the env var only short-circuited the PostToolUse hook. The
agent still discovered `capture_get` / `capture_search` / `capture_*` in
the manifest and burned turns calling them on an empty sandbox table.

Now the server drops all 6 capture tools from `tools/list` when the env
var is set. Measured impact: the regression from 11 070 → 15 915 active
mean tokens observed on 2026-04-26 morning (TASK-039 alone went from
9 913 → 56 479) is fully recovered.

### `TS_NO_HINTS=1` suppresses `_hints` / `_suggestion` blocks

Six injection sites in `code_nav.py` (all empty-result fallbacks plus
the next-step routing hints attached to `find_symbol` / `get_functions`
/ `get_classes`) become no-ops. Saves 30–50 tokens per tool result.
On a 96-task tsbench run with avg 2.5 tool calls/task, that's ~7-12 KB
cumulative cache_creation.

### Empirical impact (tsbench, 90 tasks, Claude Opus 4.7)

| Configuration                                          | Active mean | Score  |
| ------------------------------------------------------ | ----------: | :----: |
| Plain agent (Read/Grep/Bash, baseline)                 |     17 221  | 78.3 % |
| `lean` profile (default since v2.9)                    |      8 928  | 100 %  |
| `lean` + `TS_*_DISABLE` + `TS_NO_HINTS`                |     ~5 500  | 100 %  |
| `tiny` + `TS_*_DISABLE` (defer-loading via ts_search)  |   *TBD*     | *TBD*  |

### Internal

- `src/token_savior/server_handlers/tool_search.py` (new, 140 lines)
- `src/token_savior/server.py`: `ts_search` dispatch, `_TINY_INCLUDES`,
  `_CAPTURE_GATED` filter
- `src/token_savior/server_handlers/code_nav.py`: `_HINTS_DISABLED`
  guard at 6 injection sites
- `src/token_savior/tool_schemas.py`: `ts_search` schema entry

## v2.8.4 — Fail-loud on memory-hook errors (closes #15) (2026-04-23)

Non-breaking. The 6 memory hooks (`hooks/memory-*.sh`) used to pipe
every Python and `claude -p` sub-shell stderr through `2>/dev/null`,
swallowing real failures (missing venv, broken migration, corrupt DB,
typo in payload parser). A user updating token-savior and forgetting
to run `memory_db.run_migrations()` would see memory injection silently
die for weeks.

Changes:

- All 6 hooks gain an `ERR_LOG` variable pointing at
  `${XDG_STATE_HOME:-$HOME/.local/state}/token-savior/hook-errors.log`.
  Directory auto-created. Log self-rotates at 2 MB (truncates to last
  1 MB) so it can't fill the disk.
- `2>/dev/null` replaced with `2>>"$ERR_LOG"` on **32 of 33**
  Python / `claude -p` sub-shell sites. Remaining site is a legitimate
  `cat "$FLAG" 2>/dev/null || echo 0` first-run-missing fallback — kept.
- Hooks still `exit 0` — a failing sub-shell cannot block Claude Code.

Triage tip: after updating, `tail -f ~/.local/state/token-savior/hook-errors.log`
surfaces import errors, missing migrations, or a broken interpreter
path within seconds of the first hook firing.

1381 tests pass.

Closes [#15](https://github.com/Mibayy/token-savior/issues/15).

## v2.8.3 — Migration docs aligned with empirical measurements (2026-04-23)

Non-breaking docs patch. `docs/migration/v3.md` was written before the
description rewrite of v2.8.1 shifted the manifest tokenization.
Updated with empirical numbers (`full` ~16 000 t, `lean` ~11 700 t,
`ultra` ~3 900 t) and the post-spike-1 `lean` tool count (61, not 58).

Also adds the "Quick rollback" block at the top of the migration guide
and clarifies why `memory_save` and the
`discover_project_actions` / `run_project_action` pair are kept in
`lean` despite being atypical relative to the pure call-volume cut.

No code changes; docs only.

## v2.8.2 — Fix `_matches_include_patterns` on root-level files (2026-04-23)

Non-breaking bug fix surfaced during v2.8.1 validation on hermes-agent
(1704 files). A file created at project root (e.g. `foo.py`) was being
silently filtered out of incremental updates because Python's
`fnmatch` treats `**` as a single `*` (no globstar), so the default
`**/*.py` include pattern doesn't match a bare `foo.py`. The watcher
(B3) fires the add event correctly, but `maybe_update` then drops it
before calling `reindex_file`.

Fix: `_matches_include_patterns` in `slot_manager.py` now also tries
each `**/`-prefixed pattern with the `**/` stripped. Root-level files
matching the bare form now pass through.

Bug pre-dates v2.8.0 — same filter was used by the git-detected
incremental update path since forever. Only became visible after B3
made "new file at root" a common scenario.

1381 tests pass.

## v2.8.1 — Tool descriptions rewritten in USE WHEN / NOT WHEN format (2026-04-23)

Non-breaking patch. All 94 tool descriptions rewritten with explicit
USE WHEN / NOT WHEN clauses citing the nearest alternative tool when
one exists. No API change, no behavioural change — purely a
manifest-quality improvement aimed at tool-selection accuracy.

Why: Anthropic's engineering notes that accuracy degrades past 30–50
visible tools (see AUDIT.md Phase 3.6). Explicit routing hints in each
description give the agent a denser signal than prose alone.

What changed:

- 94 descriptions re-written in a 2–4 line format:
  - Line 1: verb + object (what the tool does).
  - Line 2: `USE WHEN:` — intent-level trigger.
  - Line 3: `NOT WHEN:` — alternative tool cited by name when applicable.
  - Line 4 (optional): safety/behavior/pedagogy — NOT schema duplication.
- Sweep `line-4 = schema duplication` removed from 15 descriptions
  (params/enum/return shape that the JSON inputSchema already carries).
  Saves 238 tokens with zero info loss.
- Reciprocal citations verified: `get_dependencies` ↔ `get_dependents`
  ↔ `get_change_impact` (trio, 6/6), library trio
  `get_library_symbol` ↔ `list_library_symbols` ↔
  `find_library_symbol_by_description` (6/6), plus 4 pairs.
- Client-agnostic: no NOT WHEN cites a non-TS tool name (Read,
  edit_file, etc.). Only `your client's file-read tool` generic.
- Memory_* allégé: 28 of the 33 hors-lean tools use a 2-line
  `<title>. USE WHEN:` form since agents in `full` don't need intra-
  ecosystem disambiguation. 5 cite a lean alternative when confusion
  with the `lean` default is plausible.

Manifest measurements (empirical, tiktoken cl100k_base proxy):

| Profile | Pre-rewrite | Post-rewrite | Δ       |
|---------|-------------|--------------|---------|
| full    | 14 245 t    | 15 986 t     | +12.2 % |
| lean    | 10 507 t    | 11 663 t    | +11.0 % |
| ultra   |  3 540 t    |  3 852 t     |  +8.8 % |

In zone PR review (+5 – 15 %), within projection, well below the +15 %
stop threshold. Net cost of the format is the price of discriminating
tool selection — validated over tsbench + VPS telemetry data (Spike 1).

1381 tests pass; ruff clean.

## v2.8.0 — Audit, watcher, telemetry, v3 prep (2026-04-23)

Non-breaking release. Consolidates the strategic audit + B3 file watcher +
A5 persistent call counter + B1a `mcp_toolset.example.json` + A1/A2 docs
reconcile. Also announces the v3.0 default-profile flip via a one-line
stderr warning at boot so users notice the change before it ships.

Key content (full detail in the `v2.8.0-dev` working log below; this
release crystallises that set):

- **Semantic code tools** : `search_codebase(semantic=True)`, `find_semantic_duplicates(method="embedding")`, `find_library_symbol_by_description` shipped (Nomic-embed-text-v1.5-Q, 768 d, fastembed). Safety contract: per-cluster `sim=min..mean` tags on embedding duplicates; no low-confidence warning (bench showed 0–12 % precision — absolute score doesn't discriminate correct vs wrong on code).
- **Library tooling** : `get_library_symbol`, `list_library_symbols`, `get_db_schema`, per-project `.token-savior/hint.md` auto-injected at `switch_project`.
- **Benchmarks** : `tests/benchmarks/code_retrieval` (30 queries, semantic +87 % MRR vs keyword), `tests/benchmarks/library_retrieval` (15 queries stdlib, MRR 0.84, Recall@10 1.00). CI gate via `scripts/check_bench_gates.py`.
- **Perf** : LRU cache on library embed (P95 cold→warm : 2548 ms → 236 ms, 10×).
- **Docs reconcile** : tool count aligned to actual 94 across README, `server.json`, `server.py` comments. Test count bumped 1318 → 1360. Earlier docs drift (README said 90, comments said 106) resolved.
- **Listing caps** (A2) : `get_functions`, `get_classes`, `get_imports` default to 100-row limit with explicit truncation marker. Passing `max_results=0` restores unlimited behavior.
- **B3 file watcher** (`src/token_savior/watcher.py`) : watchfiles-backed added/modified/deleted stream with mtime fallback. Flag `TOKEN_SAVIOR_WATCHER=on|off|auto` (default `auto`). Closes the 30 s live-editing window and the 2.1 ms/query mtime stat.
- **A5 persistent telemetry** (`src/token_savior/telemetry.py`) : `$TOKEN_SAVIOR_STATS_DIR/tool-calls.json` counter scoped by `(tool_name, TOKEN_SAVIOR_CLIENT)`. Silent on failure, surfaced via `telemetry_health()`.
- **B1a `mcp_toolset.example.json`** + `docs/migration/v3.md` : recommended Anthropic API config with 17 non-deferred tools; migration guide with Quick-rollback in 3 lines.
- **v3 deprecation warning** : `[token-savior] default profile will change from 'full' to 'lean' in v3.0.0 — see docs/migration/v3.md` fires once at boot when `TOKEN_SAVIOR_PROFILE` is unset; silent otherwise.
- **`_LEAN_EXCLUDES` spike-1 update** : `memory_save` and the atomic `discover_project_actions` / `run_project_action` pair kept in `lean` after measuring that dropping them would break (respectively) the user-facing "nothing forgotten" contract and a paired workflow. `lean` now = 61 tools / 10 507 est. tokens (narrowly above Claude Code's 10k auto-defer).
- **AUDIT.md** at repo root — full strategic review (869 lines, Phases 0–4, sourced).
- **GitHub issue #15** open for the `2>/dev/null` hook swallow (fix scheduled post-v2.8).

Tests: 1360 → 1381 passing (+21 : watcher, telemetry, listing caps, bench gates).

## v2.7.1 — Description retightening after v2.7.0 regression signal (2026-04-21)

- Reduce 5 heaviest tool descriptions by 47 % (1 525 → 811 chars) while preserving keyword signal (`BATCH`, `USE THIS instead`, `TERMINAL`, `ignore_generated`). Mean active_tokens delta on bench rerun: unchanged gains on heavy tasks, small regressions on single-tool tasks halved.
- `search_symbols_semantic` / `find_library_symbol_by_description` thresholds tuned (0.75 → 0.60 floor, 0.02 → 0.01 gap) then warnings removed entirely after bench showed distributions overlap.
- Tests : 1318 → 1360 passing after safety rework.

## v2.7.0 — 14 bench-driven optimisations (2026-04-21)

Sample haiku-ts v2.7 (12 tasks) — mean Δ active_tokens = **−13.2 %**. Winners: heavy-read −44 %, navigation −19.5 %, edit −13.9 %.

**Navigation / lookup**
- `find_symbol` returns `complete: true` + `scanned_files: N` (no follow-up exploration needed).
- `_resolve_symbol_info` fallback normalised (snake/kebab/case-insensitive) via `normalized_symbol_index`.
- `search_codebase` skips generated/minified files by default (`.generated.`, `.min.`, `.pb.`, `dist/`, `build/`, `.next/`, `node_modules/`, `.proto`).
- New `search_in_symbols` : content search + enclosing function/class.
- New `audit_file` : mega-batch dead_code + hotspots + semantic duplicates scoped to one file.

**Context / edit**
- `get_full_context` : new `brief=False` default (cap 12 deps, 4 000 chars).
- `get_class_source` : auto-downgrade level 2 when > 300 lines.
- `get_function_source` : prefix `[scaffold: stub]` via AST detection (`pass` / `Ellipsis` / docstring-only / `return None` / `raise NotImplementedError`).
- `get_routes` : `stub: true` flag on empty handlers.

**Analyse**
- `get_backward_slice` : `max_symbol_lines=500` cap.
- `find_hotspots` : T0-T3 tiers (actionability-ranked).
- `detect_breaking_changes` : `BREAKING: [T0] (N)` format (substring-stable for regression tests).
- `_graph_based_test_candidates` : transitive BFS on `reverse_import_graph`.
- `get_community` : `max_members=50` cap.

**Session**
- `_hm_switch_project` : session stickiness (no re-index if slot already active).

**Stats**
- Tool count: 88 → 90 (+ `search_in_symbols`, `audit_file`).
- Description total: 12 371 → 11 657 chars (−6 %).

## v2.6.0 — Memory Engine Phase 1+2 + tsbench 100% (2026-04-20)

### tsbench (90 paired tasks, Opus 4.7) — 180/180 (100.0%) vs 141/180 (78.3%)

- Active tokens: 1,549,915 → 803,531 (−48.2%)
- Wall time: 165.9min → 35.1min (−78.9%)
- Context chars: 473,752 → 258,329 (−45.5%)
- Wins/Ties/Losses: 25 / 65 / 0 (zero losses)
- Also on Sonnet 4.6: ts 170/180 (94.4%) vs base 156/180 (86.7%)

### Bench-driven fixes

- `CLAUDE_PROJECT_ROOT` env auto-promotes active project at boot (no `switch_project` round trip)
- Explicit `project=` hint auto-promotes active project on first call
- `TS_WARM_START=1` pre-builds index at server start
- `get_full_context` defaults to compact mode: source head 80 lines + names-only deps
- Empty-result `_suggestion` on `search_codebase` and `get_dependents`
- Lower defaults on noisy analyses (`analyze_config`, `find_dead_code`, `find_semantic_duplicates`)
- `lean` profile (59 tools) confirmed as bench default
- App-factory detection in `get_entry_points` (`create_app`, `make_app`, `build_app`, factory in `main.py`/`app.py`/`__init__.py`)
- Infra-tech surfacing in `get_project_summary` — flags top-level `infra/` / `deploy/` / `k8s/` and detected techs (docker, terraform, k8s)

### Phase 1 — Gap closure
- P1: `<private>` tag stripper (UserPromptSubmit hook)
- P2: content_hash persisté, dedup O(1) + backfill
- P3: `ts://obs/{id}` citation URIs dans injection output
- P4: PreToolUse-Read hook — file-context injection
- P5: session-end rollup structuré (FTS5, 6 champs)

### Phase 2 — Feature parity + differentiation
- A4: Progressive disclosure formalisé (Layer 1/2/3, cost table)
- A5: narrative / facts / concepts fields sur observations
- A1: sqlite-vec hybrid search + RRF fusion (FTS fallback graceful)
- A2: Web viewer opt-in `127.0.0.1:$TS_VIEWER_PORT` (htmx + SSE)
- A3: LLM auto-extraction PostToolUse (opt-in `TS_AUTO_EXTRACT=1`)

### Stats
- Tools : 105
- Tests : 1318/1318
- Vector search : `sqlite-vec` + `sentence-transformers/all-MiniLM-L6-v2`

## v2.0.0 — Token Savior Recall (2026-04-13)

### Memory Engine (new)

- SQLite WAL + FTS5: cross-session persistent memory
- 21 memory tools: save, search, get, delete, index, timeline, status, why, top
- 8 Claude Code lifecycle hooks: SessionStart, Stop, SessionEnd, PreCompact,
  PreToolUse ×2, UserPromptSubmit, PostToolUse
- LRU scoring: `0.4 × recency + 0.3 × access + 0.3 × type_priority`
- Delta injection: only the diff since last session is re-injected at start
- Explicit TTL per observation type (command 60d, research 90d, note 60d)
- Semantic dedup: exact hash + Jaccard (~0.85 threshold)
- Auto-promotion: note × 5 accesses → convention, warning × 5 → guardrail
- Contradiction detection at save time
- Auto-linking between observations (symbol, context, tags)
- Telegram feed for critical observations (warning / guardrail / error_pattern)
- Mode system: `code`, `review`, `debug`, `infra`, `silent` with auto-detection
- Thematic corpus Q&A
- Versioned markdown export (git-tracked)
- CLI: `ts memory {status,list,search,get,save,delete,top,why,doctor,relink}`
- Dashboard Memory tab
- 12 observation types: `bugfix`, `decision`, `convention`, `warning`,
  `guardrail`, `error_pattern`, `note`, `command`, `research`, `infra`,
  `config`, `idea`

### Manifest optimizations

- 80 → 69 tools (−11)
- 42,251 → 36,153 chars manifest (−14%)
- ~1,524 tokens saved per session on MCP manifest alone

### Cleanup

- Removed DEPRECATED tools (`apply_symbol_change_validate_with_rollback`,
  `get_changed_symbols_since_ref`)
- Fused 10 memory tools → 5 (`memory_mode`, `memory_archive`,
  `memory_maintain`, `memory_set_global`, `memory_prompts`)

### Core Token Savior (unchanged)

- 69 MCP tools total (53 core + 16 memory)
- 97% token savings measured across 170 real sessions
- ~$609 estimated cost saved
- 17 indexed projects
- Annotators: Python, TypeScript/JS, Rust, Go, C/C++, C#, JSON, YAML,
  TOML, XML, INI, ENV, HCL, Dockerfile, Markdown

### Rename

- Project renamed: **Token Savior → Token Savior Recall**
- MCP server identifier: `token-savior` → `token-savior-recall`
- PyPI package: `token-savior` → `token-savior-recall`

---

## v1.0.0 (2026-04-11)

### Architecture

- **ProjectQueryEngine**: Refactored 705-line closure `create_project_query_functions` into a class with one method per query tool. `as_dict()` preserves backward compatibility.
- **CacheManager**: Extracted cache persistence logic from `server.py` into `src/token_savior/cache_ops.py`.
- **SlotManager**: Extracted project slot management from `server.py` into `src/token_savior/slot_manager.py`.
- **Tool schemas**: Extracted all 53 MCP tool schemas from `server.py` into `src/token_savior/tool_schemas.py`. Server reduced from 2,439 to 990 lines.
- **Brace matcher**: Factored `_find_brace_end` from 4 annotators into `src/token_savior/brace_matcher.py` with per-language variants.
- **Annotator refactoring**: Table-driven dispatch in `annotate_rust` and `annotate_csharp` to reduce complexity below 150.
- **AnnotatorProtocol**: Added `typing.Protocol` for annotator type safety in `models.py`.

### Performance

- **LazyLines**: File lines are lazy-loaded from disk on demand instead of stored in cache. Cache size reduced by ~57%, idle RAM reduced proportionally.
- **Manual serialization**: Replaced `dataclasses.asdict()` in cache persistence with zero-copy field-by-field serialization.
- **scandir batching**: `_check_mtime_changes` uses `os.scandir()` per directory instead of individual `os.path.getmtime()` calls.
- **Regex cache**: Module-level `_WORD_BOUNDARY_CACHE` avoids recompiling patterns on every call.
- **File limits**: `ProjectIndexer` gains `max_files` param (env: `TOKEN_SAVIOR_MAX_FILES`, default 10,000).

### Bug fixes

- **Path traversal**: `create_checkpoint` validates file paths with `os.path.commonpath` to prevent `../../../etc/passwd` attacks.
- **Triple save**: `_maybe_incremental_update` uses `_dirty` flag pattern to call `_save_cache` at most once per execution path.
- **Output truncation**: `get_dependents` and `get_change_impact` gained `max_total_chars` (default 50,000) to prevent oversized responses.

### Tool fusions

- **get_changed_symbols**: Unified with `get_changed_symbols_since_ref` via optional `ref` parameter.
- **apply_symbol_change_and_validate**: Unified with rollback variant via `rollback_on_failure` parameter.

### Deprecated (removal planned for v1.1.0)

- **get_changed_symbols_since_ref**: Use `get_changed_symbols(ref=...)` instead.
- **apply_symbol_change_validate_with_rollback**: Use `apply_symbol_change_and_validate(rollback_on_failure=true)` instead.

Both deprecated tools inject a `_deprecated` field in their response with migration instructions. Their schemas are marked with `"deprecated": true` in `tool_schemas.py`.

### Tests

- `tests/test_cache_ops.py` (12 tests)
- `tests/test_slot_manager.py` (13 tests)
- `tests/test_server_integration.py` (5 end-to-end tests)
- `tests/test_annotator_protocol.py` (4 tests)
- `tests/test_tool_schemas.py` (7 tests)

### Benchmarks

- `benchmarks/run_benchmarks.py`: Automated benchmarks on FastAPI + CPython measuring index time, RAM, query response time, and cache size.
- `.github/workflows/benchmark.yml`: GitHub Action for release benchmarks.
