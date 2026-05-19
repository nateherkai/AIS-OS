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

**Hermes architectural constraint (v2 P7):** single isolated patch to upstream `toolsets.py` only. All instrumentation lives in `plugins/hermes_claw/` — no upstream Hermes patches. The plugin wraps `ctx.register_tool` and monkeypatches the LLM adapter; nothing else gets touched.

**Hermes call sites — light-touch via plugin wrapper:**

| Hermes module | Hook | Event | Phase |
|---|---|---|---|
| `plugins/hermes_claw/__init__.py:register(ctx)` | wrap `ctx.register_tool` (covers all 8 tools) | `tool_call` + `tool_result` (+ `tool_error`) | 2a |
| `plugins/hermes_claw/__init__.py:register(ctx)` | monkeypatch `agent/anthropic_adapter.py:send_message` | `thought` (batched) + `task_end` + `cost` | 2b |
| `plugins/hermes_claw/vault.py` handler tail | after Pinecone upsert | `memory_write` (store=pinecone or vault) | 2a |
| `plugins/hermes_claw/gmail.py` handler tail | after draft created | `memory_write` (store=supabase, key=draft_id) | 2a |
| Skill `session-summary-pusher` | after Pinecone push | `memory_write` (store=pinecone, summary=session) | 2a |

`task_start` is implicit at first `tool_call` of a new task (or, if model-router skill is used, emit at top of `model-router/SKILL.md` invocation). Gateway-entry hook is **skipped** — would require upstream patch.

**Phase 2a register-wrapper pattern (drop-in):**

```python
# plugins/hermes_claw/__init__.py
from src.lib.emit_event import emit_event
import asyncio, functools, time, uuid

def register(ctx):
    original = ctx.register_tool

    def wrapped_register(*, name, handler, **kwargs):
        @functools.wraps(handler)
        def instrumented(args, **hkw):
            call_id = str(uuid.uuid4())
            t0 = time.time()
            asyncio.create_task(emit_event(
                type="tool_call",
                action=f"tool: {name}",
                payload={"call_id": call_id, "name": name, "args": args},
            ))
            try:
                result = handler(args, **hkw)
                asyncio.create_task(emit_event(
                    type="tool_result",
                    action=f"tool done: {name}",
                    payload={"call_id": call_id, "duration_ms": int((time.time() - t0) * 1000),
                             "output_preview": str(result)[:300], "error": False},
                ))
                return result
            except Exception as e:
                asyncio.create_task(emit_event(
                    type="tool_result",
                    action=f"tool error: {name}",
                    payload={"call_id": call_id, "duration_ms": int((time.time() - t0) * 1000),
                             "output_preview": str(e)[:300], "error": True},
                ))
                raise
        original(name=name, handler=instrumented, **kwargs)

    ctx.register_tool = wrapped_register
    for name, schema, handler, check_fn, emoji in _TOOLS:
        ctx.register_tool(name=name, toolset="hermes-claw", schema=schema,
                          handler=handler, check_fn=check_fn, emoji=emoji)
```

One file change. Covers all 8 tools. No upstream patch.

**Phase 2b LLM monkeypatch pattern (single line in register(ctx) after Phase 2a tool wrapping):**

```python
def register(ctx):
    # ... Phase 2a tool wrapper above ...

    # Phase 2b: instrument LLM calls via monkeypatch
    try:
        from agent import anthropic_adapter
        from src.lib.emit_event import emit_event, make_thought_batcher
        original_send = anthropic_adapter.send_message

        async def instrumented_send(*args, **kwargs):
            task_id = str(uuid.uuid4())
            t0 = time.time()
            await emit_event(type="task_start", action="llm send",
                             payload={"task_id": task_id, "intent": str(kwargs.get('messages', [{}])[-1])[:200]})
            try:
                result = await original_send(*args, **kwargs)
                # If result has usage info:
                tokens = (getattr(result, 'usage', {}) or {}).get('total_tokens', 0)
                cents = round(tokens / 1_000_000 * 1500)  # rough Sonnet output rate
                await emit_event(type="thought", action="llm reply",
                                 payload={"text": str(getattr(result, 'content', result))[:500]})
                await emit_event(type="cost", action="llm cost",
                                 payload={"cents": cents, "tokens": tokens, "model": os.environ.get('HERMES_MODEL_DEFAULT', 'unknown')})
                await emit_event(type="task_end", action="llm done",
                                 payload={"task_id": task_id, "tokens_in": 0, "tokens_out": tokens,
                                          "duration_ms": int((time.time() - t0) * 1000)})
                return result
            except Exception as e:
                await emit_event(type="task_end", action="llm failed",
                                 payload={"task_id": task_id, "tokens_in": 0, "tokens_out": 0,
                                          "duration_ms": int((time.time() - t0) * 1000)})
                raise
        anthropic_adapter.send_message = instrumented_send
    except ImportError:
        pass  # adapter not present, skip LLM instrumentation
```

If adapter signature/internals differ, adjust the args extraction. Adapter import path may need tweaking (`agent.anthropic_adapter` vs `src.agent.anthropic_adapter`) — verify against actual Hermes layout.

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

Phase 1: Supabase schema change (in MC project, not Ag Coach Pro)

Target Supabase project: `beorbykrtoeocuqxlhrp.supabase.co` (this is where `activity_log` lives — same project mission-control + GravityClaw both write to).

```sql
ALTER TABLE activity_log
  ADD COLUMN IF NOT EXISTS bot_id TEXT DEFAULT 'gravity_claw';

CREATE INDEX IF NOT EXISTS idx_activity_log_bot_ts
  ON activity_log (bot_id, timestamp DESC);
```

Apply via Supabase Studio SQL editor or the MCP Supabase tool. GravityClaw keeps working (default applies to existing/new INSERTs).

Phase 2: Hermes side (Bryan, when ready)

Railway env vars to set on `hermes-claw` service:
```bash
railway variable set MC_SUPABASE_URL='https://beorbykrtoeocuqxlhrp.supabase.co'
railway variable set MC_SUPABASE_KEY='<service-role-key from MC Supabase>'
railway variable set HERMES_BOT_ID='hermes_claw'
```

Drop in helper:
```bash
cp /Volumes/Samsung\ PSSD\ T7/AIS-OS/docs/superpowers/artifacts/hermes_emit_event.py \
   /Volumes/Samsung\ PSSD\ T7/hermes-claw/src/lib/emit_event.py
```

Phase 2a: tool-wrapper instrumentation in `plugins/hermes_claw/__init__.py` (see code block above). 8 tools covered by one wrapper. Ship + deploy + verify in HUD.

Phase 2b (optional, after 2a stable): LLM monkeypatch in same `register(ctx)`. Adds thought/task_end/cost events. Verify adapter import path matches actual Hermes layout.

Phase 2c (skip): gateway-entry hook would require upstream patch. Phase 2a + 2b cover enough for HUD value.

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
