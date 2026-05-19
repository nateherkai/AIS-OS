# Hermes Claw ↔ AIS-OS Integration — Design

## Context

Bryan built **Hermes Claw** — a Python-based agent on Railway with its own tools registry, skills, SQLite Kanban, and Gmail integration. It runs alongside the existing TypeScript **GravityClaw** Telegram bot. He wants both bots to plug into the AIS-OS stack already shipped this session:

- **Live HUD** (`mission-control/src/app/live/`) — reads Supabase `activity_log` realtime
- **Eval harness** (`gravity-claw/src/scripts/eval-run.ts`) — accuracy regression suite
- **Pinecone vault** — shared semantic memory
- **Bryan-Aaron-Master wiki** — domain knowledge

Hermes is currently live on Railway but still being debugged (acp_* tools not registering, no persistent volume, Kanban DB lock on startup, config.toml dead, Gmail SA missing). This spec defines integration **without disturbing the Hermes build** — Bryan can drop the artifacts in when his other session stabilizes.

Four connection modes locked (from brainstorm):
1. Pipe events to Live HUD
2. Add to eval harness
3. Share Supabase `activity_log`
4. Share vault + Pinecone

---

## Architecture

**Identity model:** Hermes and GravityClaw are different personas on the same operator brain.

| Bot | Persona | Surface | Language |
|---|---|---|---|
| GravityClaw | Telegram operator | grammy bot | TypeScript |
| Hermes Claw | Desktop / email / Kanban | gateway HTTP | Python |

Both write to **the same `activity_log` table** keyed by a new `bot_id` column (`gravity_claw` / `hermes_claw`). Live HUD filters by bot or shows both. Eval harness targets either via `--target` flag.

**Why same table not separate tables:** single dashboard view, shared schema, dream/lint already understand it. Adds one column, no migration of existing rows.

**Why same Pinecone namespace:** Bryan-Aaron-Master vault is one source of truth. Both bots see the same memory. If a fact is recorded by Hermes (e.g., from Gmail), GravityClaw can recall it next time Bryan asks via Telegram.

---

## Connection 1: Events to Live HUD

**Mechanism:** Hermes writes rows to `activity_log` with the same `metadata.event_type` schema GravityClaw uses. Live HUD's reducer already routes by event_type; just add `bot_id` to the route key for filtering.

**Python emit_event helper:** sits at `hermes-claw/src/lib/emit_event.py` (Bryan drops in when ready). Mirrors the TS `emitEvent` in `gravity-claw/src/agent/emit-event.ts`:
- Typed `EventType` (task_start, task_end, thought, tool_call, tool_result, memory_write, cost)
- Privacy filter (sk-, Bearer, password, api_key, eyJ JWT) — same regex set
- Fire-and-forget (never raises)
- Token batcher for thoughts (50 tokens or 250ms idle)
- Inserts via `supabase-py`

Helper file shipped alongside this spec at:
`docs/superpowers/artifacts/hermes_emit_event.py`

**Hermes call sites (Bryan wires when stable):**

| Hermes module | Hook | Event |
|---|---|---|
| gateway entry (request handler) | first line | `task_start` |
| LLM call wrapper | streaming chunks | `thought` (batched) |
| LLM call wrapper | response end | `task_end` + `cost` |
| `tools/registry.py` | before tool exec | `tool_call` |
| `tools/registry.py` | after tool exec | `tool_result` |
| `tools/vault_query_tool.py` | after write | `memory_write` (store=vault) |
| `tools/aios_query_tool.py` | after write | `memory_write` (store=supabase) |
| Pinecone upsert (wherever) | after upsert | `memory_write` (store=pinecone) |

**HUD reducer change (mission-control):** add optional `bot_id` field to `ActivityRow` type. Default visualization shows both bots; filter dropdown lets Bryan pick. Reducer change is small — `liveTypes.ts` adds `bot_id?: 'gravity_claw' | 'hermes_claw'`, reducer threads it into each panel item.

---

## Connection 2: Eval harness adds Hermes

**Mechanism:** extend `gravity-claw/src/scripts/eval-run.ts` with `--target` flag. Three values:
- `--target gravity` (default) — calls `askClaude` directly
- `--target hermes` — POSTs to Hermes gateway HTTP endpoint
- `--target both` — runs each Q against both, side-by-side scoring

**Hermes gateway contract (assumed; confirm when stable):**
- HTTP POST `http://localhost:PORT/chat` (or Railway URL)
- Body: `{ "message": "<question>", "session_id": "eval-<run_id>" }`
- Response: `{ "reply": "<text>", "tokens": {...}, "model": "..." }`

If contract differs, edit the `runOneHermes` adapter — that's the only change.

**Eval JSON output adds `target` field** so dashboard can distinguish runs. `dashboard/data/eval-runs/2026-05-18-gravity.json` and `dashboard/data/eval-runs/2026-05-18-hermes.json` (separate files, same schema). `/eval` page reads both, shows two trend lines.

**Same 30-question eval set serves both bots.** Some questions (factuality red lines) will score differently — Hermes might have different guardrails. That's the point: visible delta = where the personas diverge.

---

## Connection 3: Shared `activity_log` table

**Schema change (one-time migration):**

```sql
ALTER TABLE activity_log
  ADD COLUMN IF NOT EXISTS bot_id TEXT DEFAULT 'gravity_claw';

CREATE INDEX IF NOT EXISTS idx_activity_log_bot_ts
  ON activity_log (bot_id, timestamp DESC);
```

Default `gravity_claw` so existing rows keep working. New Hermes rows specify `bot_id: 'hermes_claw'`. GravityClaw's existing emit-event helper unchanged (default applies).

**Backward compat:** mission-control `ActivityRow` reads `bot_id` optionally. If absent, treat as `gravity_claw`.

**No data migration required** — existing rows get the default at SELECT time.

---

## Connection 4: Shared vault + Pinecone

**Already mostly true.** Hermes' `tools/vault_query_tool.py` already reads `Bryan-Aaron-Master/wiki/`. Both bots can read the same vault.

**What changes for writes:**
- Both bots' Pinecone upserts use the **same index** (`gravityclaw-vector`) and **same namespace** (`knowledge`)
- Both bots' embedding model = OpenAI `text-embedding-3-small` @ dim=1024 (already standardized — see `~/.claude/CLAUDE.md`)
- Both emit `memory_write` events when they upsert so the HUD shows who learned what

**Wiki writes:** Hermes should only write to `Bryan-Aaron-Master/raw/` (drop zone). The existing `ingest` skill (GravityClaw-side) processes `raw/` into `wiki/`. This keeps wiki authoring single-sourced and avoids merge conflicts.

**Vault skill convention enforced:**
- Hermes `tools/vault_query_tool.py` — read-only on `wiki/`
- Hermes can write to `raw/` (for ingestion)
- Ingest skill (runs from gravity-claw or AIS-OS) processes both bots' raw drops

---

## Data Flow (events end-to-end)

```
Hermes Claw (Python, Railway)
  │ user request hits gateway
  ▼
emit_event(type='task_start', payload={task_id, intent})
emit_event(type='thought', payload={text})     ←── batched
emit_event(type='tool_call', payload={call_id, name, args})
emit_event(type='tool_result', payload={call_id, output_preview, ms})
emit_event(type='memory_write', payload={store, key, summary})
emit_event(type='task_end', payload={task_id, tokens_in, tokens_out, ms})
emit_event(type='cost', payload={cents, tokens, model})
  │
  │ each emit = INSERT INTO activity_log (action, details, metadata, bot_id, ts)
  │                                                                 ^^^^^^^^^
  │                                                                 'hermes_claw'
  ▼
Supabase activity_log
  │ realtime push (postgres_changes INSERT)
  ▼
mission-control /live
  │ reducer routes by event_type
  │ panels render with bot_id badge (optional filter)
  ▼
Bryan sees both bots' actions side by side
```

---

## Implementation Phases

Phase 0: artifacts ready (no Hermes-side change yet)
- ✅ `docs/superpowers/artifacts/hermes_emit_event.py` — Python helper
- ✅ This spec

Phase 1: Supabase schema change (one Bryan can run any time)
- Apply migration adding `bot_id` column + index
- Verify GravityClaw still works (default applies to its INSERTs)

Phase 2: Hermes side (Bryan does in other session when stable)
- Drop `emit_event.py` into Hermes' `src/lib/`
- Wire it at the 8 call sites listed above
- Set `HERMES_BOT_ID=hermes_claw` env var

Phase 3: Mission-control update (small)
- Add `bot_id?` to `ActivityRow` and `LiveState` items
- Optional: filter dropdown in IntentBanner
- Optional: bot-id chip on each event item

Phase 4: Eval extension
- Add `--target {gravity,hermes,both}` flag to eval-run.ts
- Add `runOneHermes` adapter calling gateway HTTP
- Add `target` field to EvalRun JSON
- `/eval` page renders two trend lines

Each phase ships independently. Phase 1 unblocks Phase 2 but doesn't depend on it.

---

## Error Handling

| Failure | Response |
|---|---|
| Hermes can't reach Supabase | emit_event swallows error, log to stderr; Hermes keeps running |
| Schema migration fails | Rollback, GravityClaw unaffected (no new column needed) |
| Hermes emits invalid event_type | HUD reducer warns + falls back to thought (already implemented) |
| Eval `--target hermes` and gateway down | Per-question error recorded; run continues |
| Both bots emit simultaneously | Postgres handles concurrency; HUD reducer is append-only with caps |

---

## Testing

**Python helper (Phase 0, ready now):**
- `tests/test_emit_event.py` — mocks `supabase.table().insert()`
- Tests: typed event_type values, privacy filter, fire-and-forget, token batcher 50/250ms

**Mission-control (Phase 3):**
- Update `liveReducer.test.ts` — bot_id passes through to panel items
- New component test: bot-id chip renders correctly

**Eval (Phase 4):**
- `eval-run.test.ts` — `--target hermes` calls Hermes adapter, not askClaude
- Integration: synthetic gateway server returning fixed replies; assert eval scores

**Manual verification (Phase 2 final step):**
1. Hermes processes a real request
2. `/live` shows Hermes events in real time
3. Memory writes from Hermes show up in MemoryPanel with `vault` or `pinecone` store
4. Cost ticker tallies both bots
5. SQL: `SELECT bot_id, count(*) FROM activity_log WHERE timestamp > now()-interval '1 hour' GROUP BY bot_id` → both rows

---

## Out of Scope

- Hermes-internal bugs (acp_* registry, Kanban lock, config.toml port) — Bryan's other session
- Cross-bot task handoff (Hermes asks GravityClaw to do X) — separate spec
- Bot-to-bot message bus — same
- Unified persona / merging the two brains — explicitly out (they're different personas on purpose)
- Email gateway wiring (Hermes Phase 3 — Bryan's session)
- Multi-tenant `bot_id` beyond two bots — schema supports it but no specific need yet
- Hermes targeting other LLM providers — separate
