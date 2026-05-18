# GravityClaw Live HUD — Design

## Context

Bryan wants a live "theater mode" visualization of his GravityClaw Telegram AI bot in action — showing what it's thinking, what tool it's calling, what it's writing to memory, and how much it's spending, all in real time. Goal: shareable screen-recordings that demonstrate the bot is real work, like the references at https://youtu.be/IiJLI0mJ2gk (his own earlier "OpenClaw MoltBot" demo) and https://youtu.be/7xuWZ-3lyQE ("Hermes Agent just got 10X Better (Agentic OS)").

Existing infrastructure already covers ~60% of this: `gravity-claw/mission-control/` is a Next.js 15 / React 19 dashboard hitting Supabase, with an `activity_log` table and `ActivityLog` type already feeding a `CommandCenter` page. This spec adds a new `/live` route on top, and instruments the bot to emit structured event types so the HUD can route them into distinct panels.

This is the second of three subprojects flagged during the earlier brainstorm (Dream→Skill pipeline shipped; AIS quality/accuracy audit deferred to a future spec).

---

## Decisions Locked (from brainstorm)

| # | Question | Choice |
|---|---|---|
| 1 | Scope | Extend `mission-control/` with new `/live` route (not standalone app) |
| 2 | Data stream | Supabase Realtime subscription on `activity_log` INSERT |
| 3 | Layout | Theater (3-panel: thoughts left, action center, memory right, cost bottom) |
| 4 | Event schema | Extend existing `ActivityLog` via `metadata.event_type` (no DB migration) |
| 5 | Polish | Cinematic — framer-motion animations, dark theme, typewriter thoughts, pulse-glow on new events |

---

## Architecture

**Two repos touched:**

1. `gravity-claw/mission-control/` — new `/live` route, panel components, realtime subscription, reducer
2. `gravity-claw/src/` (bot) — new `emitEvent` helper + call sites at LLM/tool/memory hooks

**No mission-control backend changes** — pure read from Supabase realtime.

**Event types** (string values in `metadata.event_type`):

| Type | Panel | Payload fields |
|---|---|---|
| `task_start` | intent banner | `intent` (string), `task_id` |
| `task_end` | intent banner | `task_id`, `tokens_in`, `tokens_out`, `duration_ms` |
| `thought` | left stream | `text` (string, ~50-token chunk) |
| `tool_call` | center action | `name`, `args` (jsonb), `call_id` |
| `tool_result` | center action | `call_id`, `output_preview`, `duration_ms`, `error` (bool) |
| `memory_write` | right panel | `store` (`pinecone` \| `vault` \| `supabase`), `key`, `summary` |
| `cost` | bottom ticker | `cents`, `tokens`, `model` |

**Theater layout (CSS Grid, fullscreen):**

```
┌──────────── intent banner (task_start text) ─ ● live ─┐
├─ thought stream ─┬─ current action ─┬─ memory writes ─┤
│ typewriter feed  │ big tool icon    │ slide-in list  │
│ auto-scroll      │ + pulsing ring   │ store + summary│
├──────────────────┴──────────────────┴────────────────┤
└─── cost ticker — cents/min sparkline | tokens | uptime ┘
```

**Color per event type:** thought=cyan, tool=amber, memory=violet, cost=green. Dark theme throughout.

**Realtime model:** one Supabase channel subscribed to `INSERT` on `activity_log`. Each row's `metadata.event_type` routes to the right panel via a React reducer. Last 50 events kept per panel; older fade out.

**Initial hydration:** on mount, REST query fetches last 5 minutes of activity, populates state, THEN opens realtime channel. No empty screen on cold load.

---

## Components

**Mission-control (`gravity-claw/mission-control/`):**

```
src/app/live/
  page.tsx                  # /live route, theater layout, realtime sub
  layout.tsx                # dark-theme override, no Sidebar, full-bleed

src/components/live/
  IntentBanner.tsx          # top — current task_start text, "● live" indicator
  ThoughtStream.tsx         # left — typewriter feed, auto-scroll, fade-in
  ActionPanel.tsx           # center — big tool icon + pulsing ring + JSON args
  MemoryPanel.tsx           # right — recent memory_write list, slide-in
  CostTicker.tsx            # bottom — cents/min sparkline + token counter
  EventGlow.tsx             # shared — framer-motion pulse animation wrapper
  liveReducer.ts            # state machine routing events → panels
  liveTypes.ts              # TS types per event_type payload

src/lib/realtime.ts         # supabase.channel('activity_log') wrapper

src/app/live/page.module.css   # CSS Grid theater layout
```

**Bot (`gravity-claw/src/`):**

```
src/lib/emitEvent.ts        # typed helper writing one activity_log row
src/lib/__tests__/emitEvent.test.ts
```

**Reuses (do not duplicate):**
- `@/lib/supabase` — existing client
- `lucide-react` — existing icon set, pick icons per tool name (Wrench, Database, Brain, Search, etc.)
- `ActivityLog` type — extend with optional `metadata.event_type` field (TS only)

**New deps:**
- `framer-motion` — mission-control only
- No new bot deps

---

## Data Flow

```
Bot (Railway)
  │ User msg arrives (Telegram webhook / iMessage)
  ▼
emitEvent({type:'task_start', payload:{intent}})
  │
  ▼
LLM streaming begins
  ├─► token batch (every ~50 tokens or 250ms) → emitEvent({type:'thought', payload:{text}})
  ├─► tool requested  → emitEvent({type:'tool_call', payload:{name,args,call_id}})
  ├─► tool returns    → emitEvent({type:'tool_result', payload:{call_id,output_preview,duration_ms,error?}})
  └─► memory written  → emitEvent({type:'memory_write', payload:{store,key,summary}})

LLM call ends
  ├─► emitEvent({type:'task_end', payload:{task_id,tokens_in,tokens_out,duration_ms}})
  └─► emitEvent({type:'cost',     payload:{cents,tokens,model}})

  │ Each emit = INSERT INTO activity_log (action, details, metadata, timestamp)
  ▼
Supabase Postgres + Realtime publication
  │ WebSocket push (postgres_changes on INSERT)
  ▼
mission-control /live (browser)
  │ realtime.ts on mount:
  │   supabase.channel('hud').on('postgres_changes', {event:'INSERT', schema:'public', table:'activity_log'},
  │     row => dispatch({kind: row.metadata.event_type, row}))
  │
  │ liveReducer state:
  │   { intent, thoughts[≤50], actions[≤10], memory[≤20], cost:{cents,tokens,samples[60s]} }
  │
  │ Routing:
  │   task_start  → set intent
  │   task_end    → mark done, banner fades 3s
  │   thought     → push to thoughts
  │   tool_call   → push to actions head, trigger pulse-glow
  │   tool_result → patch matching call_id in actions (status=done/error)
  │   memory_write→ push to memory
  │   cost        → tally + push sparkline sample
  │
  ▼
Panels read state via React context, render with framer-motion entrance (fade + slide-up)
```

**Backpressure:** if events arrive >30/s, reducer batches in 100ms windows; trim oldest beyond panel cap.

**Disconnect handling:** Supabase client auto-reconnects. Banner shows `● live` green / `● reconnecting…` amber based on channel `status`.

---

## Bot Instrumentation

**`emitEvent` contract:**

```ts
type EventType =
  | 'task_start' | 'task_end'
  | 'thought'
  | 'tool_call' | 'tool_result'
  | 'memory_write'
  | 'cost';

interface EmitOpts {
  type: EventType;
  action: string;       // short verb phrase ("query pinecone")
  details?: string;     // human-readable line
  payload?: Record<string, unknown>;
}

async function emitEvent(opts: EmitOpts): Promise<void>;
```

**Behavior:**
- Inserts one row into `activity_log` with `metadata = { event_type, ...payload }`
- Fire-and-forget: errors logged but never thrown (bot must not crash if Supabase is down)
- Timestamp: `now()` server-side
- Cheap: <5ms per call typical, async

**Call site map (exact files determined during plan; bot files may differ):**

| Bot module | Hook | Event |
|---|---|---|
| `handlers/telegram.ts` (or msg entrypoint) | first line | `task_start` (intent) |
| `llm/anthropic.ts` | streaming batch | `thought` (text chunk) |
| `llm/anthropic.ts` | call end | `task_end` + `cost` |
| `tools/dispatcher.ts` | before exec | `tool_call` (name, args, call_id) |
| `tools/dispatcher.ts` | after exec | `tool_result` (call_id, output, ms) |
| `memory/pinecone.ts` | after upsert | `memory_write` (store='pinecone') |
| `memory/vault.ts` | after file write | `memory_write` (store='vault') |
| `memory/supabase.ts` | after persistent write | `memory_write` (store='supabase') |

**ID generation:**
- Bot generates a UUIDv4 `task_id` at `task_start`, propagates to `task_end` (and to all `cost` events for the same call).
- Bot generates a UUIDv4 `call_id` at each `tool_call`, propagates to the matching `tool_result`.
- IDs let HUD reducer pair start/end and call/result reliably.

**Token batching for `thought`:**
- Accumulate streamed tokens in a buffer
- Flush every 50 tokens OR every 250ms (whichever first)
- Avoids 1000s of micro-events per LLM call

**Privacy filter:** strip secrets from `args` and `details` before emit. Regex pass on `sk-…`, `Bearer …`, `password=…`, `api[_-]?key=…`. Lives inside `emitEvent` so call sites can't forget.

**Backward compat:** existing bot code that already writes `activity_log` rows keeps working — `event_type` is optional in metadata; HUD reducer treats missing `event_type` as `thought` fallback.

---

## Error Handling

| Failure | Detection | Response |
|---|---|---|
| Supabase unreachable on bot | `emitEvent` catch | log to stderr, swallow; bot keeps running |
| Realtime channel disconnects | `channel.subscribe` callback `status==='CLOSED'` | banner flips amber, auto-reconnect |
| Unknown `event_type` | reducer default branch | render as `thought` fallback; console.warn |
| Event flood (>30/s) | reducer queue length | batch in 100ms windows; trim oldest beyond panel cap |
| Hydration query slow/fails | REST fetch timeout 3s | render empty panels + connecting banner; realtime takes over |
| Privacy filter misses a secret | manual review | document filter location; expand patterns |
| `task_end` without matching `task_start` | reducer | ignore silently; intent stays at previous value |
| `tool_result` without matching `call_id` | reducer | append as orphan card; console.warn |

**Logging:**
- Bot: `emitEvent` failures → existing logger
- HUD: reducer warns to browser console only (no telemetry — local-first)

---

## Testing

**Bot unit (`gravity-claw/src/lib/__tests__/emitEvent.test.ts`):**
- writes correct row shape (mocked supabase client)
- swallows errors silently (mock throws → no rejection)
- privacy filter strips `sk-…`, `Bearer …`, `password=…`, `api_key=…`
- token batching: 100 tokens → 2 thought events; idle 250ms → flushes partial buffer

**HUD reducer (`mission-control/__tests__/liveReducer.test.ts`):**
- each event type routes to correct panel slice
- unknown `event_type` → thoughts fallback + warn
- `tool_result` patches matching `tool_call` by `call_id`
- 50-item cap on thoughts (oldest dropped)
- cost sparkline: 60s rolling window (older pruned)
- backpressure: 100 events in <100ms → batched into single state update

**Component (React Testing Library):**
- `IntentBanner` shows "idle" when no intent
- `ActionPanel` shows spinner while `tool_call` active (no matching result)
- `ActionPanel` shows error state when `tool_result.error === true`
- `ThoughtStream` typewriter renders characters progressively

**Integration (Playwright):**
- spin up against staging Supabase project (or local supabase)
- insert 5 events via SQL
- render `/live` in headless browser
- assert each panel populated

**Manual verification:**
1. `npm run dev` in mission-control, open `/live` → 3-panel theater renders dark, "● live" green
2. SQL insert: `INSERT INTO activity_log (action, details, metadata) VALUES ('test', 'd', '{"event_type":"thought","payload":{"text":"hello"}}')` → "hello" appears with fade-in
3. Repeat for each `event_type` → correct panel
4. Send real Telegram msg → full pipeline lights up (task_start → thoughts → tool_call → tool_result → memory_write → task_end → cost)
5. Kill network → banner amber within 5s
6. Restore network → banner green, missed events appear via catch-up

**Performance budget:**
- Render <16ms per event (60fps)
- Initial hydration <500ms
- Memory cap ~150 events total (50 thoughts + 10 actions + 20 memory + 60 cost samples + 10 misc)

---

## Out of Scope (deferred to future specs)

- Multi-bot view (Hermes + GravityClaw side by side)
- Replay/scrub mode (rewind to 5 minutes ago)
- Recording / one-click GIF export
- Per-event drill-down modal (show full args/output)
- Authentication on `/live` (currently inherits mission-control's auth posture)
- Mobile responsive layout (theater is desktop-only for v1)
- Public-facing demo URL (v1 is local/private)
