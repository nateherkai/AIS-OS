# GravityClaw Live HUD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a live "theater mode" HUD at `/live` in mission-control that visualizes GravityClaw's thinking, tool calls, memory writes, and cost in real time via Supabase Realtime.

**Architecture:** Two repos. (1) `gravity-claw/mission-control/` gets a new `/live` route with 3-panel theater layout, a reducer routing events by `metadata.event_type`, and panel components animated with framer-motion. (2) `gravity-claw/src/` (bot) gets a typed `emitEvent` helper wrapping the existing `SupabaseService.logActivity`, plus instrumentation at LLM/tool/memory hook points. No DB migration — uses existing `activity_log` table with `metadata.event_type` field.

**Tech Stack:** Next.js 15, React 19, TypeScript, framer-motion (new), `@supabase/supabase-js` (existing), Vitest for unit tests, Playwright for one integration test.

**Source spec:** `docs/superpowers/specs/2026-05-18-gravityclaw-live-hud-design.md`

---

## File Structure

**New files (mission-control: `gravity-claw/mission-control/`):**
- `src/app/live/layout.tsx` — dark theme, no Sidebar, full-bleed
- `src/app/live/page.tsx` — /live route, theater grid, realtime sub, hydration
- `src/app/live/page.module.css` — CSS Grid theater layout
- `src/components/live/IntentBanner.tsx`
- `src/components/live/ThoughtStream.tsx`
- `src/components/live/ActionPanel.tsx`
- `src/components/live/MemoryPanel.tsx`
- `src/components/live/CostTicker.tsx`
- `src/components/live/EventGlow.tsx` — framer-motion wrapper
- `src/components/live/liveReducer.ts`
- `src/components/live/liveTypes.ts`
- `src/lib/realtime.ts` — `subscribeActivityLog(onRow)` wrapper
- `__tests__/liveReducer.test.ts`
- `__tests__/realtime.test.ts`
- `__tests__/IntentBanner.test.tsx`
- `__tests__/ThoughtStream.test.tsx`
- `__tests__/ActionPanel.test.tsx`
- `__tests__/MemoryPanel.test.tsx`
- `__tests__/CostTicker.test.tsx`
- `playwright/live.spec.ts`

**New files (bot: `gravity-claw/src/`):**
- `src/agent/emit-event.ts` — typed wrapper + privacy filter + token batcher
- `src/agent/__tests__/emit-event.test.ts`

**Modified files (bot):**
- `src/bot/chat.ts` — emit `task_start` + `task_end`
- `src/ai/claude.ts` — emit `thought` (batched), `tool_call`, `tool_result`, `cost`
- `src/agent/memory.ts` — emit `memory_write` after `saveMemory`

**Reused (read or wrap):**
- `mission-control/src/lib/supabase.ts` — existing client
- `gravity-claw/src/agent/supabase.ts` — `SupabaseService.logActivity` (wrapped, not modified)
- `lucide-react` icons — existing
- `ActivityLog` interface — extended via metadata.event_type (no breaking change)

---

## Task 1: Mission-control test scaffolding (Vitest)

**Files:**
- Modify: `gravity-claw/mission-control/package.json` — add Vitest + testing-library deps
- Create: `gravity-claw/mission-control/vitest.config.ts`
- Create: `gravity-claw/mission-control/__tests__/smoke.test.ts`

- [ ] **Step 1: Add Vitest dependencies**

Run from `gravity-claw/mission-control/`:
```bash
npm install --save-dev vitest @vitejs/plugin-react @testing-library/react @testing-library/jest-dom jsdom @types/react@^19
```

- [ ] **Step 2: Create `vitest.config.ts`**

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

- [ ] **Step 3: Create `vitest.setup.ts`**

```typescript
import '@testing-library/jest-dom';
```

- [ ] **Step 4: Create smoke test `__tests__/smoke.test.ts`**

```typescript
import { describe, it, expect } from 'vitest';

describe('vitest smoke', () => {
  it('arithmetic works', () => {
    expect(1 + 1).toBe(2);
  });
});
```

- [ ] **Step 5: Add test script to package.json**

Edit `gravity-claw/mission-control/package.json` `scripts`:
```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **Step 6: Run smoke test**

```bash
cd gravity-claw/mission-control && npm test
```
Expected: 1 passed.

- [ ] **Step 7: Commit**

```bash
git add gravity-claw/mission-control/package.json gravity-claw/mission-control/package-lock.json gravity-claw/mission-control/vitest.config.ts gravity-claw/mission-control/vitest.setup.ts gravity-claw/mission-control/__tests__/smoke.test.ts
git commit -m "feat(mission-control): add Vitest + RTL testing setup"
```

---

## Task 2: liveTypes — event payload types

**Files:**
- Create: `gravity-claw/mission-control/src/components/live/liveTypes.ts`

- [ ] **Step 1: Write types**

```typescript
// Event payload types for the Live HUD. Mirrors the spec at
// docs/superpowers/specs/2026-05-18-gravityclaw-live-hud-design.md

export type EventType =
  | 'task_start'
  | 'task_end'
  | 'thought'
  | 'tool_call'
  | 'tool_result'
  | 'memory_write'
  | 'cost';

export interface TaskStartPayload { task_id: string; intent: string; }
export interface TaskEndPayload   { task_id: string; tokens_in: number; tokens_out: number; duration_ms: number; }
export interface ThoughtPayload   { text: string; }
export interface ToolCallPayload  { call_id: string; name: string; args: Record<string, unknown>; }
export interface ToolResultPayload{ call_id: string; output_preview: string; duration_ms: number; error?: boolean; }
export interface MemoryWritePayload { store: 'pinecone' | 'vault' | 'supabase'; key: string; summary: string; }
export interface CostPayload      { cents: number; tokens: number; model: string; }

export type EventPayload =
  | { event_type: 'task_start';   payload: TaskStartPayload }
  | { event_type: 'task_end';     payload: TaskEndPayload }
  | { event_type: 'thought';      payload: ThoughtPayload }
  | { event_type: 'tool_call';    payload: ToolCallPayload }
  | { event_type: 'tool_result';  payload: ToolResultPayload }
  | { event_type: 'memory_write'; payload: MemoryWritePayload }
  | { event_type: 'cost';         payload: CostPayload };

// Raw row from activity_log table
export interface ActivityRow {
  id: string;
  action: string;
  details: string;
  metadata: { event_type?: EventType; payload?: Record<string, unknown> } | null;
  timestamp: string;
}

// Per-panel state slices (used by liveReducer)
export interface IntentState  { task_id: string; intent: string; started_at: string; done: boolean; }
export interface ThoughtItem  { id: string; text: string; ts: string; }
export interface ActionItem   { call_id: string; name: string; args: Record<string, unknown>; ts: string; result?: { output_preview: string; duration_ms: number; error: boolean }; }
export interface MemoryItem   { id: string; store: 'pinecone' | 'vault' | 'supabase'; key: string; summary: string; ts: string; }
export interface CostSample   { ts: string; cents: number; tokens: number; }

export interface LiveState {
  intent: IntentState | null;
  thoughts: ThoughtItem[];   // cap 50
  actions: ActionItem[];     // cap 10
  memory: MemoryItem[];      // cap 20
  cost: { cents_total: number; tokens_total: number; samples: CostSample[] }; // samples within 60s
  connection: 'connecting' | 'live' | 'reconnecting';
}
```

- [ ] **Step 2: Commit**

```bash
git add gravity-claw/mission-control/src/components/live/liveTypes.ts
git commit -m "feat(live): event payload types"
```

---

## Task 3: liveReducer — event routing state machine

**Files:**
- Create: `gravity-claw/mission-control/src/components/live/liveReducer.ts`
- Create: `gravity-claw/mission-control/__tests__/liveReducer.test.ts`

**Caps:** thoughts=50, actions=10, memory=20, cost samples=60s rolling.

- [ ] **Step 1: Write failing tests**

```typescript
import { describe, it, expect, vi } from 'vitest';
import { liveReducer, initialState } from '@/components/live/liveReducer';
import type { ActivityRow } from '@/components/live/liveTypes';

function mkRow(event_type: string, payload: any, id = String(Math.random())): ActivityRow {
  return {
    id,
    action: 'test',
    details: 'd',
    metadata: { event_type: event_type as any, payload },
    timestamp: new Date().toISOString(),
  };
}

describe('liveReducer', () => {
  it('task_start sets intent', () => {
    const s = liveReducer(initialState, { type: 'event', row: mkRow('task_start', { task_id: 't1', intent: 'reply to user' }) });
    expect(s.intent?.intent).toBe('reply to user');
    expect(s.intent?.task_id).toBe('t1');
    expect(s.intent?.done).toBe(false);
  });

  it('task_end marks intent done when task_id matches', () => {
    const s1 = liveReducer(initialState, { type: 'event', row: mkRow('task_start', { task_id: 't1', intent: 'x' }) });
    const s2 = liveReducer(s1, { type: 'event', row: mkRow('task_end', { task_id: 't1', tokens_in: 100, tokens_out: 50, duration_ms: 2000 }) });
    expect(s2.intent?.done).toBe(true);
  });

  it('task_end with mismatched task_id is ignored', () => {
    const s1 = liveReducer(initialState, { type: 'event', row: mkRow('task_start', { task_id: 't1', intent: 'x' }) });
    const s2 = liveReducer(s1, { type: 'event', row: mkRow('task_end', { task_id: 'other', tokens_in: 0, tokens_out: 0, duration_ms: 0 }) });
    expect(s2.intent?.done).toBe(false);
  });

  it('thought pushes to thoughts', () => {
    const s = liveReducer(initialState, { type: 'event', row: mkRow('thought', { text: 'hello' }) });
    expect(s.thoughts).toHaveLength(1);
    expect(s.thoughts[0].text).toBe('hello');
  });

  it('thoughts cap at 50 (oldest dropped)', () => {
    let s = initialState;
    for (let i = 0; i < 60; i++) {
      s = liveReducer(s, { type: 'event', row: mkRow('thought', { text: `t${i}` }, `r${i}`) });
    }
    expect(s.thoughts).toHaveLength(50);
    expect(s.thoughts[0].text).toBe('t10'); // 10..59 kept
    expect(s.thoughts[49].text).toBe('t59');
  });

  it('tool_call pushes to actions', () => {
    const s = liveReducer(initialState, { type: 'event', row: mkRow('tool_call', { call_id: 'c1', name: 'pinecone', args: { q: 'x' } }) });
    expect(s.actions).toHaveLength(1);
    expect(s.actions[0].call_id).toBe('c1');
    expect(s.actions[0].result).toBeUndefined();
  });

  it('tool_result patches matching action by call_id', () => {
    const s1 = liveReducer(initialState, { type: 'event', row: mkRow('tool_call', { call_id: 'c1', name: 'p', args: {} }) });
    const s2 = liveReducer(s1, { type: 'event', row: mkRow('tool_result', { call_id: 'c1', output_preview: 'ok', duration_ms: 500, error: false }) });
    expect(s2.actions[0].result?.output_preview).toBe('ok');
    expect(s2.actions[0].result?.error).toBe(false);
  });

  it('tool_result without matching call_id is appended as orphan', () => {
    const s = liveReducer(initialState, { type: 'event', row: mkRow('tool_result', { call_id: 'unknown', output_preview: 'orphan', duration_ms: 100, error: false }) });
    expect(s.actions).toHaveLength(1);
    expect(s.actions[0].name).toBe('(orphan result)');
    expect(s.actions[0].result?.output_preview).toBe('orphan');
  });

  it('memory_write pushes to memory', () => {
    const s = liveReducer(initialState, { type: 'event', row: mkRow('memory_write', { store: 'pinecone', key: 'k', summary: 's' }) });
    expect(s.memory).toHaveLength(1);
    expect(s.memory[0].store).toBe('pinecone');
  });

  it('cost tallies totals and prunes samples older than 60s', () => {
    const oldTs = new Date(Date.now() - 90_000).toISOString();
    const s1: any = { ...initialState, cost: { cents_total: 0, tokens_total: 0, samples: [{ ts: oldTs, cents: 5, tokens: 100 }] } };
    const s2 = liveReducer(s1, { type: 'event', row: mkRow('cost', { cents: 3, tokens: 50, model: 'haiku' }) });
    expect(s2.cost.cents_total).toBe(3);
    expect(s2.cost.tokens_total).toBe(50);
    expect(s2.cost.samples).toHaveLength(1); // old sample pruned, new added
    expect(s2.cost.samples[0].cents).toBe(3);
  });

  it('unknown event_type falls back to thought + warns', () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const s = liveReducer(initialState, { type: 'event', row: mkRow('bogus', { text: 'x' }) });
    expect(s.thoughts).toHaveLength(1);
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
  });

  it('connection action sets connection state', () => {
    const s = liveReducer(initialState, { type: 'connection', status: 'reconnecting' });
    expect(s.connection).toBe('reconnecting');
  });
});
```

- [ ] **Step 2: Run tests to verify failure**

```bash
cd gravity-claw/mission-control && npm test -- liveReducer
```
Expected: all FAIL with import error.

- [ ] **Step 3: Implement `liveReducer.ts`**

```typescript
import type {
  ActivityRow, EventType, LiveState,
  ThoughtItem, ActionItem, MemoryItem, CostSample,
} from './liveTypes';

const CAP_THOUGHTS = 50;
const CAP_ACTIONS = 10;
const CAP_MEMORY = 20;
const COST_WINDOW_MS = 60_000;

export const initialState: LiveState = {
  intent: null,
  thoughts: [],
  actions: [],
  memory: [],
  cost: { cents_total: 0, tokens_total: 0, samples: [] },
  connection: 'connecting',
};

export type LiveAction =
  | { type: 'event'; row: ActivityRow }
  | { type: 'connection'; status: 'connecting' | 'live' | 'reconnecting' }
  | { type: 'hydrate'; rows: ActivityRow[] };

function trimEnd<T>(arr: T[], cap: number): T[] {
  return arr.length > cap ? arr.slice(arr.length - cap) : arr;
}

function applyRow(state: LiveState, row: ActivityRow): LiveState {
  const meta = row.metadata ?? {};
  const eventType = (meta.event_type ?? 'thought') as EventType;
  const payload = (meta.payload ?? {}) as Record<string, unknown>;

  if (!meta.event_type) {
    console.warn(`liveReducer: row ${row.id} missing event_type, treating as thought`);
  } else if (!['task_start','task_end','thought','tool_call','tool_result','memory_write','cost'].includes(meta.event_type)) {
    console.warn(`liveReducer: unknown event_type ${meta.event_type} on row ${row.id}, treating as thought`);
  }

  switch (eventType) {
    case 'task_start': {
      const intent = String(payload.intent ?? row.details ?? '');
      const task_id = String(payload.task_id ?? row.id);
      return { ...state, intent: { task_id, intent, started_at: row.timestamp, done: false } };
    }
    case 'task_end': {
      const task_id = String(payload.task_id ?? '');
      if (state.intent && state.intent.task_id === task_id) {
        return { ...state, intent: { ...state.intent, done: true } };
      }
      return state;
    }
    case 'thought': {
      const text = String(payload.text ?? row.details ?? '');
      const item: ThoughtItem = { id: row.id, text, ts: row.timestamp };
      return { ...state, thoughts: trimEnd([...state.thoughts, item], CAP_THOUGHTS) };
    }
    case 'tool_call': {
      const call_id = String(payload.call_id ?? row.id);
      const name = String(payload.name ?? 'tool');
      const args = (payload.args ?? {}) as Record<string, unknown>;
      const item: ActionItem = { call_id, name, args, ts: row.timestamp };
      return { ...state, actions: trimEnd([...state.actions, item], CAP_ACTIONS) };
    }
    case 'tool_result': {
      const call_id = String(payload.call_id ?? '');
      const output_preview = String(payload.output_preview ?? '');
      const duration_ms = Number(payload.duration_ms ?? 0);
      const error = Boolean(payload.error);
      const idx = state.actions.findIndex(a => a.call_id === call_id);
      if (idx >= 0) {
        const updated = [...state.actions];
        updated[idx] = { ...updated[idx], result: { output_preview, duration_ms, error } };
        return { ...state, actions: updated };
      }
      const orphan: ActionItem = {
        call_id, name: '(orphan result)', args: {},
        ts: row.timestamp, result: { output_preview, duration_ms, error },
      };
      console.warn(`liveReducer: tool_result with no matching call_id ${call_id}`);
      return { ...state, actions: trimEnd([...state.actions, orphan], CAP_ACTIONS) };
    }
    case 'memory_write': {
      const item: MemoryItem = {
        id: row.id,
        store: (payload.store as 'pinecone'|'vault'|'supabase') ?? 'supabase',
        key: String(payload.key ?? ''),
        summary: String(payload.summary ?? ''),
        ts: row.timestamp,
      };
      return { ...state, memory: trimEnd([...state.memory, item], CAP_MEMORY) };
    }
    case 'cost': {
      const cents = Number(payload.cents ?? 0);
      const tokens = Number(payload.tokens ?? 0);
      const sample: CostSample = { ts: row.timestamp, cents, tokens };
      const cutoff = Date.now() - COST_WINDOW_MS;
      const samples = [...state.cost.samples, sample].filter(s => new Date(s.ts).getTime() >= cutoff);
      return {
        ...state,
        cost: {
          cents_total: state.cost.cents_total + cents,
          tokens_total: state.cost.tokens_total + tokens,
          samples,
        },
      };
    }
    default: {
      // Unknown — already warned above. Fallback to thought.
      const item: ThoughtItem = { id: row.id, text: String(payload.text ?? row.details ?? ''), ts: row.timestamp };
      return { ...state, thoughts: trimEnd([...state.thoughts, item], CAP_THOUGHTS) };
    }
  }
}

export function liveReducer(state: LiveState, action: LiveAction): LiveState {
  switch (action.type) {
    case 'event':
      return applyRow(state, action.row);
    case 'connection':
      return { ...state, connection: action.status };
    case 'hydrate': {
      let s = state;
      for (const row of action.rows) s = applyRow(s, row);
      return s;
    }
  }
}
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd gravity-claw/mission-control && npm test -- liveReducer
```
Expected: 12 passed.

- [ ] **Step 5: Commit**

```bash
git add gravity-claw/mission-control/src/components/live/liveReducer.ts gravity-claw/mission-control/__tests__/liveReducer.test.ts
git commit -m "feat(live): reducer with per-event routing and caps"
```

---

## Task 4: Realtime subscription wrapper

**Files:**
- Create: `gravity-claw/mission-control/src/lib/realtime.ts`
- Create: `gravity-claw/mission-control/__tests__/realtime.test.ts`

Contract: `subscribeActivityLog(onRow, onStatus)` returns `{ unsubscribe(): void }`. Also exports `hydrateRecent(minutes): Promise<ActivityRow[]>`.

- [ ] **Step 1: Write failing tests**

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { subscribeActivityLog, hydrateRecent } from '@/lib/realtime';

vi.mock('@/lib/supabase', () => {
  const channelObj: any = {
    on: vi.fn().mockReturnThis(),
    subscribe: vi.fn((cb: any) => { channelObj._statusCb = cb; return channelObj; }),
    unsubscribe: vi.fn(),
  };
  return {
    supabase: {
      channel: vi.fn(() => channelObj),
      from: vi.fn(() => ({
        select: vi.fn().mockReturnThis(),
        gte: vi.fn().mockReturnThis(),
        order: vi.fn().mockReturnThis(),
        then: (resolve: any) => resolve({ data: [{ id: '1', action: 'a', details: 'd', metadata: null, timestamp: new Date().toISOString() }], error: null }),
      })),
    },
    __channel: channelObj,
  };
});

describe('realtime', () => {
  beforeEach(() => vi.clearAllMocks());

  it('subscribeActivityLog wires postgres_changes listener', async () => {
    const onRow = vi.fn();
    const onStatus = vi.fn();
    subscribeActivityLog(onRow, onStatus);
    const mod = await import('@/lib/supabase') as any;
    expect(mod.__channel.on).toHaveBeenCalled();
    const args = mod.__channel.on.mock.calls[0];
    expect(args[0]).toBe('postgres_changes');
    expect(args[1]).toMatchObject({ event: 'INSERT', schema: 'public', table: 'activity_log' });
  });

  it('subscribeActivityLog calls onStatus with live when subscribed', async () => {
    const onStatus = vi.fn();
    subscribeActivityLog(() => {}, onStatus);
    const mod = await import('@/lib/supabase') as any;
    mod.__channel._statusCb('SUBSCRIBED');
    expect(onStatus).toHaveBeenCalledWith('live');
  });

  it('subscribeActivityLog calls onStatus with reconnecting on CHANNEL_ERROR or CLOSED', async () => {
    const onStatus = vi.fn();
    subscribeActivityLog(() => {}, onStatus);
    const mod = await import('@/lib/supabase') as any;
    mod.__channel._statusCb('CHANNEL_ERROR');
    expect(onStatus).toHaveBeenCalledWith('reconnecting');
    mod.__channel._statusCb('CLOSED');
    expect(onStatus).toHaveBeenCalledWith('reconnecting');
  });

  it('hydrateRecent returns rows', async () => {
    const rows = await hydrateRecent(5);
    expect(rows).toHaveLength(1);
    expect(rows[0].id).toBe('1');
  });
});
```

- [ ] **Step 2: Verify failing**

```bash
cd gravity-claw/mission-control && npm test -- realtime
```
Expected: 4 FAIL with import error.

- [ ] **Step 3: Implement `realtime.ts`**

```typescript
import { supabase } from './supabase';
import type { ActivityRow } from '@/components/live/liveTypes';

export type ConnectionStatus = 'connecting' | 'live' | 'reconnecting';

export function subscribeActivityLog(
  onRow: (row: ActivityRow) => void,
  onStatus: (status: ConnectionStatus) => void,
): { unsubscribe: () => void } {
  if (!supabase) {
    onStatus('reconnecting');
    return { unsubscribe: () => {} };
  }
  const channel = supabase
    .channel('hud')
    .on(
      'postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'activity_log' },
      (msg: any) => onRow(msg.new as ActivityRow),
    )
    .subscribe((status: string) => {
      if (status === 'SUBSCRIBED') onStatus('live');
      else if (status === 'CHANNEL_ERROR' || status === 'CLOSED' || status === 'TIMED_OUT') onStatus('reconnecting');
      else onStatus('connecting');
    });
  return {
    unsubscribe: () => { channel.unsubscribe(); },
  };
}

export async function hydrateRecent(minutes: number): Promise<ActivityRow[]> {
  if (!supabase) return [];
  const since = new Date(Date.now() - minutes * 60_000).toISOString();
  const { data, error } = await supabase
    .from('activity_log')
    .select('*')
    .gte('timestamp', since)
    .order('timestamp', { ascending: true });
  if (error) {
    console.warn('hydrateRecent failed', error);
    return [];
  }
  return (data ?? []) as ActivityRow[];
}
```

- [ ] **Step 4: Run tests**

```bash
cd gravity-claw/mission-control && npm test -- realtime
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add gravity-claw/mission-control/src/lib/realtime.ts gravity-claw/mission-control/__tests__/realtime.test.ts
git commit -m "feat(live): realtime subscription wrapper + hydration"
```

---

## Task 5: framer-motion + EventGlow wrapper

**Files:**
- Modify: `gravity-claw/mission-control/package.json` — add framer-motion
- Create: `gravity-claw/mission-control/src/components/live/EventGlow.tsx`

- [ ] **Step 1: Install framer-motion**

```bash
cd gravity-claw/mission-control && npm install framer-motion
```

- [ ] **Step 2: Create `EventGlow.tsx`**

```tsx
"use client";
import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface Props {
  children: ReactNode;
  color: 'cyan' | 'amber' | 'violet' | 'green';
  className?: string;
}

const COLOR_MAP: Record<Props['color'], string> = {
  cyan:   'rgba(34, 211, 238, 0.6)',
  amber:  'rgba(245, 158, 11, 0.6)',
  violet: 'rgba(167, 139, 250, 0.6)',
  green:  'rgba(74, 222, 128, 0.6)',
};

export function EventGlow({ children, color, className }: Props) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 10, boxShadow: `0 0 0px ${COLOR_MAP[color]}` }}
      animate={{ opacity: 1, y: 0, boxShadow: `0 0 12px ${COLOR_MAP[color]}` }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add gravity-claw/mission-control/package.json gravity-claw/mission-control/package-lock.json gravity-claw/mission-control/src/components/live/EventGlow.tsx
git commit -m "feat(live): framer-motion + EventGlow shared wrapper"
```

---

## Task 6: IntentBanner component

**Files:**
- Create: `gravity-claw/mission-control/src/components/live/IntentBanner.tsx`
- Create: `gravity-claw/mission-control/__tests__/IntentBanner.test.tsx`

- [ ] **Step 1: Write failing tests**

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IntentBanner } from '@/components/live/IntentBanner';

describe('IntentBanner', () => {
  it('shows "idle" when intent is null', () => {
    render(<IntentBanner intent={null} connection="live" />);
    expect(screen.getByText(/idle/i)).toBeInTheDocument();
  });

  it('shows intent text when set', () => {
    render(<IntentBanner intent={{ task_id: 't1', intent: 'reply to user', started_at: new Date().toISOString(), done: false }} connection="live" />);
    expect(screen.getByText('reply to user')).toBeInTheDocument();
  });

  it('renders live connection indicator green', () => {
    render(<IntentBanner intent={null} connection="live" />);
    const indicator = screen.getByTestId('connection-indicator');
    expect(indicator).toHaveAttribute('data-status', 'live');
  });

  it('renders reconnecting indicator', () => {
    render(<IntentBanner intent={null} connection="reconnecting" />);
    const indicator = screen.getByTestId('connection-indicator');
    expect(indicator).toHaveAttribute('data-status', 'reconnecting');
  });

  it('marks intent done when done flag true', () => {
    render(<IntentBanner intent={{ task_id: 't1', intent: 'x', started_at: new Date().toISOString(), done: true }} connection="live" />);
    expect(screen.getByText('x')).toBeInTheDocument();
    expect(screen.getByTestId('intent-status')).toHaveAttribute('data-done', 'true');
  });
});
```

- [ ] **Step 2: Verify failing**

```bash
cd gravity-claw/mission-control && npm test -- IntentBanner
```
Expected: 5 FAIL.

- [ ] **Step 3: Implement `IntentBanner.tsx`**

```tsx
"use client";
import type { IntentState, LiveState } from './liveTypes';

interface Props {
  intent: IntentState | null;
  connection: LiveState['connection'];
}

const STATUS_COLOR: Record<LiveState['connection'], string> = {
  live: '#22c55e',
  reconnecting: '#f59e0b',
  connecting: '#64748b',
};

const STATUS_LABEL: Record<LiveState['connection'], string> = {
  live: 'live',
  reconnecting: 'reconnecting…',
  connecting: 'connecting…',
};

export function IntentBanner({ intent, connection }: Props) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '12px 24px', borderBottom: '1px solid #1f2937',
      background: '#0b1220', color: '#e5e7eb',
    }}>
      <div style={{ fontSize: 14, opacity: 0.7 }}>Current intent</div>
      <div data-testid="intent-status" data-done={intent?.done ?? false} style={{
        flex: 1, textAlign: 'center', fontSize: 18, fontWeight: 600,
        opacity: intent?.done ? 0.5 : 1, transition: 'opacity 1s',
      }}>
        {intent ? intent.intent : <span style={{ opacity: 0.5 }}>idle</span>}
      </div>
      <div
        data-testid="connection-indicator"
        data-status={connection}
        style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}
      >
        <span style={{
          width: 8, height: 8, borderRadius: '50%',
          background: STATUS_COLOR[connection],
          boxShadow: `0 0 6px ${STATUS_COLOR[connection]}`,
        }}/>
        {STATUS_LABEL[connection]}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run tests**

```bash
cd gravity-claw/mission-control && npm test -- IntentBanner
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add gravity-claw/mission-control/src/components/live/IntentBanner.tsx gravity-claw/mission-control/__tests__/IntentBanner.test.tsx
git commit -m "feat(live): IntentBanner component"
```

---

## Task 7: ThoughtStream component (typewriter)

**Files:**
- Create: `gravity-claw/mission-control/src/components/live/ThoughtStream.tsx`
- Create: `gravity-claw/mission-control/__tests__/ThoughtStream.test.tsx`

- [ ] **Step 1: Write failing tests**

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ThoughtStream } from '@/components/live/ThoughtStream';

describe('ThoughtStream', () => {
  it('renders empty state', () => {
    render(<ThoughtStream items={[]} />);
    expect(screen.getByTestId('thought-stream')).toBeInTheDocument();
    expect(screen.queryByTestId('thought-item')).toBeNull();
  });

  it('renders each item', () => {
    const items = [
      { id: '1', text: 'thinking about it', ts: new Date().toISOString() },
      { id: '2', text: 'next thought', ts: new Date().toISOString() },
    ];
    render(<ThoughtStream items={items} />);
    expect(screen.getAllByTestId('thought-item')).toHaveLength(2);
    expect(screen.getByText('thinking about it')).toBeInTheDocument();
    expect(screen.getByText('next thought')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Verify failing**

```bash
cd gravity-claw/mission-control && npm test -- ThoughtStream
```
Expected: 2 FAIL.

- [ ] **Step 3: Implement `ThoughtStream.tsx`**

```tsx
"use client";
import { useEffect, useRef } from 'react';
import { EventGlow } from './EventGlow';
import type { ThoughtItem } from './liveTypes';

interface Props {
  items: ThoughtItem[];
}

export function ThoughtStream({ items }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [items.length]);

  return (
    <div
      data-testid="thought-stream"
      ref={ref}
      style={{
        height: '100%', overflowY: 'auto', padding: 16,
        background: '#0b1220', color: '#a5f3fc', fontFamily: 'ui-monospace, SFMono-Regular, monospace',
        fontSize: 13, lineHeight: 1.6,
      }}
    >
      {items.map(item => (
        <EventGlow key={item.id} color="cyan" className="">
          <div data-testid="thought-item" style={{ padding: '4px 0', borderBottom: '1px dashed #1e3a5f' }}>
            {item.text}
          </div>
        </EventGlow>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Run tests**

```bash
cd gravity-claw/mission-control && npm test -- ThoughtStream
```
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add gravity-claw/mission-control/src/components/live/ThoughtStream.tsx gravity-claw/mission-control/__tests__/ThoughtStream.test.tsx
git commit -m "feat(live): ThoughtStream component with auto-scroll"
```

---

## Task 8: ActionPanel component

**Files:**
- Create: `gravity-claw/mission-control/src/components/live/ActionPanel.tsx`
- Create: `gravity-claw/mission-control/__tests__/ActionPanel.test.tsx`

- [ ] **Step 1: Write failing tests**

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ActionPanel } from '@/components/live/ActionPanel';

describe('ActionPanel', () => {
  it('renders idle when no actions', () => {
    render(<ActionPanel actions={[]} />);
    expect(screen.getByText(/no active tool/i)).toBeInTheDocument();
  });

  it('shows spinner when newest action has no result', () => {
    const actions = [{ call_id: 'c1', name: 'pinecone', args: { q: 'x' }, ts: new Date().toISOString() }];
    render(<ActionPanel actions={actions} />);
    expect(screen.getByTestId('action-spinner')).toBeInTheDocument();
  });

  it('shows done state when newest action has result.error=false', () => {
    const actions = [{ call_id: 'c1', name: 'pinecone', args: {}, ts: new Date().toISOString(), result: { output_preview: 'ok', duration_ms: 100, error: false } }];
    render(<ActionPanel actions={actions} />);
    expect(screen.getByTestId('action-status')).toHaveAttribute('data-state', 'done');
  });

  it('shows error state when newest action has result.error=true', () => {
    const actions = [{ call_id: 'c1', name: 'pinecone', args: {}, ts: new Date().toISOString(), result: { output_preview: 'fail', duration_ms: 100, error: true } }];
    render(<ActionPanel actions={actions} />);
    expect(screen.getByTestId('action-status')).toHaveAttribute('data-state', 'error');
  });

  it('renders tool name and args preview', () => {
    const actions = [{ call_id: 'c1', name: 'pinecone_query', args: { q: 'hello' }, ts: new Date().toISOString() }];
    render(<ActionPanel actions={actions} />);
    expect(screen.getByText('pinecone_query')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Verify failing**

```bash
cd gravity-claw/mission-control && npm test -- ActionPanel
```
Expected: 5 FAIL.

- [ ] **Step 3: Implement `ActionPanel.tsx`**

```tsx
"use client";
import { Wrench } from 'lucide-react';
import { EventGlow } from './EventGlow';
import type { ActionItem } from './liveTypes';

interface Props {
  actions: ActionItem[];
}

export function ActionPanel({ actions }: Props) {
  const current = actions[actions.length - 1];

  if (!current) {
    return (
      <div style={{
        height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: '#0a0f1d', color: '#fcd34d', opacity: 0.5, fontSize: 14,
      }}>
        no active tool
      </div>
    );
  }

  const state: 'running' | 'done' | 'error' = !current.result
    ? 'running'
    : current.result.error ? 'error' : 'done';

  const borderColor = state === 'error' ? '#ef4444' : state === 'done' ? '#22c55e' : '#f59e0b';

  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      background: '#0a0f1d', color: '#fcd34d', padding: 24, gap: 16,
    }}>
      <EventGlow color="amber">
        <div
          data-testid="action-status"
          data-state={state}
          style={{
            width: 96, height: 96, borderRadius: '50%',
            border: `3px solid ${borderColor}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            animation: state === 'running' ? 'pulse 1.5s ease-in-out infinite' : 'none',
          }}
        >
          <Wrench size={36} />
          {state === 'running' && <span data-testid="action-spinner" style={{ display: 'none' }} />}
        </div>
      </EventGlow>
      <div style={{ fontSize: 20, fontWeight: 600 }}>{current.name}</div>
      <pre style={{
        fontSize: 12, maxWidth: '90%', maxHeight: 120, overflow: 'auto',
        background: '#1f2937', padding: 12, borderRadius: 6, color: '#e5e7eb',
      }}>
        {JSON.stringify(current.args, null, 2)}
      </pre>
      {current.result && (
        <div style={{ fontSize: 13, opacity: 0.8 }}>
          {current.result.error ? '✗ ' : '✓ '}
          {current.result.duration_ms}ms — {current.result.output_preview.slice(0, 80)}
        </div>
      )}
      <style>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); box-shadow: 0 0 24px ${borderColor}; }
        }
      `}</style>
    </div>
  );
}
```

- [ ] **Step 4: Run tests**

```bash
cd gravity-claw/mission-control && npm test -- ActionPanel
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add gravity-claw/mission-control/src/components/live/ActionPanel.tsx gravity-claw/mission-control/__tests__/ActionPanel.test.tsx
git commit -m "feat(live): ActionPanel with running/done/error states"
```

---

## Task 9: MemoryPanel component

**Files:**
- Create: `gravity-claw/mission-control/src/components/live/MemoryPanel.tsx`
- Create: `gravity-claw/mission-control/__tests__/MemoryPanel.test.tsx`

- [ ] **Step 1: Write failing tests**

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryPanel } from '@/components/live/MemoryPanel';

describe('MemoryPanel', () => {
  it('renders empty state', () => {
    render(<MemoryPanel items={[]} />);
    expect(screen.getByText(/no recent writes/i)).toBeInTheDocument();
  });

  it('renders memory item summary', () => {
    const items = [{ id: 'm1', store: 'pinecone' as const, key: 'k', summary: 'remembered X', ts: new Date().toISOString() }];
    render(<MemoryPanel items={items} />);
    expect(screen.getByText('remembered X')).toBeInTheDocument();
  });

  it('shows store badge', () => {
    const items = [{ id: 'm1', store: 'vault' as const, key: 'k', summary: 's', ts: new Date().toISOString() }];
    render(<MemoryPanel items={items} />);
    expect(screen.getByText('vault')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Verify failing**

```bash
cd gravity-claw/mission-control && npm test -- MemoryPanel
```
Expected: 3 FAIL.

- [ ] **Step 3: Implement `MemoryPanel.tsx`**

```tsx
"use client";
import { EventGlow } from './EventGlow';
import type { MemoryItem } from './liveTypes';

interface Props {
  items: MemoryItem[];
}

const STORE_COLOR: Record<MemoryItem['store'], string> = {
  pinecone: '#a78bfa',
  vault: '#c4b5fd',
  supabase: '#8b5cf6',
};

export function MemoryPanel({ items }: Props) {
  if (items.length === 0) {
    return (
      <div style={{
        height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: '#1a1033', color: '#a78bfa', opacity: 0.5, fontSize: 14,
      }}>
        no recent writes
      </div>
    );
  }
  // Show newest first
  const sorted = [...items].slice().reverse();
  return (
    <div style={{
      height: '100%', overflowY: 'auto', padding: 16,
      background: '#1a1033', color: '#e5e7eb', fontSize: 13,
    }}>
      {sorted.map(item => (
        <EventGlow key={item.id} color="violet" className="">
          <div style={{ padding: 8, marginBottom: 8, background: '#2b1255', borderRadius: 6 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{
                fontSize: 10, textTransform: 'uppercase', letterSpacing: 1,
                color: STORE_COLOR[item.store], fontWeight: 600,
              }}>{item.store}</span>
              <span style={{ fontSize: 10, opacity: 0.5 }}>{new Date(item.ts).toLocaleTimeString()}</span>
            </div>
            <div style={{ fontWeight: 500, color: '#fff' }}>{item.summary}</div>
            {item.key && <div style={{ fontSize: 11, opacity: 0.6, marginTop: 2 }}>key: {item.key}</div>}
          </div>
        </EventGlow>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Run tests**

```bash
cd gravity-claw/mission-control && npm test -- MemoryPanel
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add gravity-claw/mission-control/src/components/live/MemoryPanel.tsx gravity-claw/mission-control/__tests__/MemoryPanel.test.tsx
git commit -m "feat(live): MemoryPanel component"
```

---

## Task 10: CostTicker component

**Files:**
- Create: `gravity-claw/mission-control/src/components/live/CostTicker.tsx`
- Create: `gravity-claw/mission-control/__tests__/CostTicker.test.tsx`

- [ ] **Step 1: Write failing tests**

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CostTicker } from '@/components/live/CostTicker';

describe('CostTicker', () => {
  it('shows zero totals on empty', () => {
    render(<CostTicker cost={{ cents_total: 0, tokens_total: 0, samples: [] }} />);
    expect(screen.getByText(/\$0\.00/)).toBeInTheDocument();
    expect(screen.getByText(/0 tokens/i)).toBeInTheDocument();
  });

  it('formats cents as dollars with 2 decimals', () => {
    render(<CostTicker cost={{ cents_total: 123, tokens_total: 45000, samples: [] }} />);
    expect(screen.getByText(/\$1\.23/)).toBeInTheDocument();
    expect(screen.getByText(/45,000 tokens/i)).toBeInTheDocument();
  });

  it('renders sparkline with sample count', () => {
    const now = new Date().toISOString();
    render(<CostTicker cost={{ cents_total: 10, tokens_total: 100, samples: [
      { ts: now, cents: 5, tokens: 50 },
      { ts: now, cents: 5, tokens: 50 },
    ]}} />);
    expect(screen.getByTestId('sparkline')).toHaveAttribute('data-samples', '2');
  });
});
```

- [ ] **Step 2: Verify failing**

```bash
cd gravity-claw/mission-control && npm test -- CostTicker
```
Expected: 3 FAIL.

- [ ] **Step 3: Implement `CostTicker.tsx`**

```tsx
"use client";
import type { LiveState } from './liveTypes';

interface Props {
  cost: LiveState['cost'];
}

function formatDollars(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}

function formatTokens(n: number): string {
  return `${n.toLocaleString()} tokens`;
}

export function CostTicker({ cost }: Props) {
  // Simple inline SVG sparkline
  const samples = cost.samples;
  const max = Math.max(1, ...samples.map(s => s.cents));
  const points = samples.map((s, i) => {
    const x = samples.length > 1 ? (i / (samples.length - 1)) * 100 : 50;
    const y = 100 - (s.cents / max) * 100;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 24,
      padding: '8px 24px', borderTop: '1px solid #1f2937',
      background: '#0b1220', color: '#86efac', fontSize: 13, fontFamily: 'ui-monospace, monospace',
    }}>
      <div><strong>{formatDollars(cost.cents_total)}</strong></div>
      <div>{formatTokens(cost.tokens_total)}</div>
      <svg
        data-testid="sparkline"
        data-samples={samples.length}
        width="200" height="32" viewBox="0 0 100 100" preserveAspectRatio="none"
        style={{ flexShrink: 0 }}
      >
        {samples.length > 0 && (
          <polyline
            points={points}
            fill="none"
            stroke="#86efac"
            strokeWidth="2"
            vectorEffect="non-scaling-stroke"
          />
        )}
      </svg>
      <div style={{ marginLeft: 'auto', opacity: 0.5 }}>last 60s</div>
    </div>
  );
}
```

- [ ] **Step 4: Run tests**

```bash
cd gravity-claw/mission-control && npm test -- CostTicker
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add gravity-claw/mission-control/src/components/live/CostTicker.tsx gravity-claw/mission-control/__tests__/CostTicker.test.tsx
git commit -m "feat(live): CostTicker with sparkline"
```

---

## Task 11: `/live` page + layout — wire panels with realtime

**Files:**
- Create: `gravity-claw/mission-control/src/app/live/layout.tsx`
- Create: `gravity-claw/mission-control/src/app/live/page.tsx`
- Create: `gravity-claw/mission-control/src/app/live/page.module.css`

No new tests — this is the integration shell, manually verified.

- [ ] **Step 1: Create `layout.tsx`**

```tsx
import type { ReactNode } from 'react';

export default function LiveLayout({ children }: { children: ReactNode }) {
  return (
    <div style={{
      minHeight: '100vh', background: '#000', color: '#e5e7eb',
      margin: 0, padding: 0,
    }}>
      {children}
    </div>
  );
}
```

- [ ] **Step 2: Create `page.module.css`**

```css
.theater {
  display: grid;
  grid-template-rows: auto 1fr auto;
  grid-template-columns: 1fr 1.4fr 1fr;
  grid-template-areas:
    "banner banner banner"
    "thoughts action memory"
    "cost cost cost";
  height: 100vh;
  width: 100vw;
  gap: 1px;
  background: #1f2937;
}

.banner   { grid-area: banner;   background: #0b1220; }
.thoughts { grid-area: thoughts; background: #0b1220; overflow: hidden; }
.action   { grid-area: action;   background: #0a0f1d; overflow: hidden; }
.memory   { grid-area: memory;   background: #1a1033; overflow: hidden; }
.cost     { grid-area: cost;     background: #0b1220; }
```

- [ ] **Step 3: Create `page.tsx`**

```tsx
"use client";
import { useEffect, useReducer } from 'react';
import styles from './page.module.css';
import { IntentBanner } from '@/components/live/IntentBanner';
import { ThoughtStream } from '@/components/live/ThoughtStream';
import { ActionPanel } from '@/components/live/ActionPanel';
import { MemoryPanel } from '@/components/live/MemoryPanel';
import { CostTicker } from '@/components/live/CostTicker';
import { liveReducer, initialState } from '@/components/live/liveReducer';
import { subscribeActivityLog, hydrateRecent } from '@/lib/realtime';

export default function LivePage() {
  const [state, dispatch] = useReducer(liveReducer, initialState);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const rows = await hydrateRecent(5);
      if (!cancelled && rows.length > 0) {
        dispatch({ type: 'hydrate', rows });
      }
    })();

    const sub = subscribeActivityLog(
      row => dispatch({ type: 'event', row }),
      status => dispatch({ type: 'connection', status }),
    );

    return () => {
      cancelled = true;
      sub.unsubscribe();
    };
  }, []);

  return (
    <div className={styles.theater}>
      <div className={styles.banner}>
        <IntentBanner intent={state.intent} connection={state.connection} />
      </div>
      <div className={styles.thoughts}><ThoughtStream items={state.thoughts} /></div>
      <div className={styles.action}><ActionPanel actions={state.actions} /></div>
      <div className={styles.memory}><MemoryPanel items={state.memory} /></div>
      <div className={styles.cost}><CostTicker cost={state.cost} /></div>
    </div>
  );
}
```

- [ ] **Step 4: Sanity check — run dev server**

```bash
cd gravity-claw/mission-control && npm run dev
```
Open `http://localhost:3000/live` in browser. Expected: 3-panel theater, dark, "● connecting" then "● live" once Supabase subscribes. No console errors.

Kill dev server with Ctrl-C.

- [ ] **Step 5: Run full test suite**

```bash
cd gravity-claw/mission-control && npm test
```
Expected: all previous tests still pass.

- [ ] **Step 6: Commit**

```bash
git add gravity-claw/mission-control/src/app/live/
git commit -m "feat(live): /live page wires panels + realtime + hydration"
```

---

## Task 12: Bot — `emit-event` helper + tests

**Files:**
- Create: `gravity-claw/src/agent/emit-event.ts`
- Create: `gravity-claw/src/agent/__tests__/emit-event.test.ts`
- Modify: `gravity-claw/package.json` — confirm `vitest` already a dev dep, add if missing

- [ ] **Step 1: Verify Vitest available in bot repo**

```bash
cd gravity-claw && cat package.json | grep -i vitest
```
If not present:
```bash
cd gravity-claw && npm install --save-dev vitest
```

- [ ] **Step 2: Write failing tests**

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock SupabaseService BEFORE importing emit-event
const logActivityMock = vi.fn(async () => {});
vi.mock('../supabase.js', () => ({
  SupabaseService: { logActivity: logActivityMock },
}));

import { emitEvent, _testing } from '../emit-event';

beforeEach(() => {
  logActivityMock.mockClear();
  logActivityMock.mockResolvedValue(undefined);
});

describe('emit-event', () => {
  it('writes activity_log row with event_type in metadata', async () => {
    await emitEvent({ type: 'task_start', action: 'reply', payload: { task_id: 't1', intent: 'hi' } });
    expect(logActivityMock).toHaveBeenCalledTimes(1);
    const arg = logActivityMock.mock.calls[0][0];
    expect(arg.action).toBe('reply');
    expect(arg.metadata.event_type).toBe('task_start');
    expect(arg.metadata.payload.task_id).toBe('t1');
  });

  it('swallows errors from logActivity (fire-and-forget)', async () => {
    logActivityMock.mockRejectedValueOnce(new Error('supabase down'));
    await expect(emitEvent({ type: 'thought', action: 't', payload: { text: 'x' } })).resolves.toBeUndefined();
  });

  it('privacy filter strips sk- API keys from payload', async () => {
    await emitEvent({ type: 'tool_call', action: 'call', payload: { args: { key: 'sk-abcdef123456789' } } });
    const arg = logActivityMock.mock.calls[0][0];
    expect(JSON.stringify(arg.metadata.payload)).not.toContain('sk-abcdef');
    expect(JSON.stringify(arg.metadata.payload)).toContain('***');
  });

  it('privacy filter strips Bearer tokens', async () => {
    await emitEvent({ type: 'tool_call', action: 'c', payload: { headers: 'Authorization: Bearer abc123xyz' } });
    expect(JSON.stringify(logActivityMock.mock.calls[0][0].metadata.payload)).not.toContain('abc123xyz');
  });

  it('privacy filter strips password= and api_key=', async () => {
    await emitEvent({ type: 'tool_call', action: 'c', payload: { url: 'http://x?password=secret123&api_key=k4b' } });
    const s = JSON.stringify(logActivityMock.mock.calls[0][0].metadata.payload);
    expect(s).not.toContain('secret123');
    expect(s).not.toContain('k4b');
  });

  it('token batcher flushes after 50 tokens', async () => {
    const batcher = _testing.makeThoughtBatcher();
    for (let i = 0; i < 49; i++) await batcher.push('a');
    expect(logActivityMock).not.toHaveBeenCalled();
    await batcher.push('a');
    expect(logActivityMock).toHaveBeenCalledTimes(1);
    expect(logActivityMock.mock.calls[0][0].metadata.event_type).toBe('thought');
  });

  it('token batcher flushes on idle 250ms', async () => {
    vi.useFakeTimers();
    const batcher = _testing.makeThoughtBatcher();
    await batcher.push('a');
    expect(logActivityMock).not.toHaveBeenCalled();
    vi.advanceTimersByTime(260);
    await vi.runAllTimersAsync();
    expect(logActivityMock).toHaveBeenCalledTimes(1);
    vi.useRealTimers();
  });
});
```

- [ ] **Step 3: Verify failing**

```bash
cd gravity-claw && npx vitest run src/agent/__tests__/emit-event.test.ts
```
Expected: 7 FAIL with import error.

- [ ] **Step 4: Implement `emit-event.ts`**

```typescript
import { SupabaseService } from './supabase.js';

export type EventType =
  | 'task_start' | 'task_end'
  | 'thought'
  | 'tool_call' | 'tool_result'
  | 'memory_write'
  | 'cost';

export interface EmitOpts {
  type: EventType;
  action: string;
  details?: string;
  payload?: Record<string, unknown>;
}

const SECRET_PATTERNS: Array<{ re: RegExp; replace: string }> = [
  { re: /sk-[A-Za-z0-9_-]{8,}/g,             replace: 'sk-***' },
  { re: /Bearer\s+[A-Za-z0-9._-]{8,}/gi,     replace: 'Bearer ***' },
  { re: /password\s*=\s*[^&\s"']+/gi,        replace: 'password=***' },
  { re: /api[_-]?key\s*=\s*[^&\s"']+/gi,     replace: 'api_key=***' },
];

function scrub(value: unknown): unknown {
  if (typeof value === 'string') {
    let out = value;
    for (const { re, replace } of SECRET_PATTERNS) out = out.replace(re, replace);
    return out;
  }
  if (Array.isArray(value)) return value.map(scrub);
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value)) out[k] = scrub(v);
    return out;
  }
  return value;
}

export async function emitEvent(opts: EmitOpts): Promise<void> {
  try {
    const cleanPayload = scrub(opts.payload ?? {}) as Record<string, unknown>;
    await SupabaseService.logActivity({
      action: opts.action,
      details: opts.details ?? '',
      metadata: { event_type: opts.type, payload: cleanPayload },
    });
  } catch (e: any) {
    console.error('[emitEvent] failed:', e?.message ?? e);
  }
}

interface ThoughtBatcher {
  push(token: string): Promise<void>;
  flush(): Promise<void>;
}

function makeThoughtBatcher(): ThoughtBatcher {
  const FLUSH_TOKENS = 50;
  const FLUSH_IDLE_MS = 250;
  let buffer = '';
  let count = 0;
  let timer: NodeJS.Timeout | null = null;

  async function flush() {
    if (count === 0) return;
    const text = buffer;
    buffer = '';
    count = 0;
    if (timer) { clearTimeout(timer); timer = null; }
    await emitEvent({ type: 'thought', action: 'reasoning', payload: { text } });
  }

  async function push(token: string) {
    buffer += token;
    count++;
    if (count >= FLUSH_TOKENS) {
      await flush();
      return;
    }
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => { void flush(); }, FLUSH_IDLE_MS);
  }

  return { push, flush };
}

export const _testing = { makeThoughtBatcher };
```

- [ ] **Step 5: Run tests**

```bash
cd gravity-claw && npx vitest run src/agent/__tests__/emit-event.test.ts
```
Expected: 7 passed.

- [ ] **Step 6: Commit**

```bash
git add gravity-claw/src/agent/emit-event.ts gravity-claw/src/agent/__tests__/emit-event.test.ts gravity-claw/package.json gravity-claw/package-lock.json
git commit -m "feat(bot): emit-event helper with privacy filter + thought batcher"
```

---

## Task 13: Instrument `bot/chat.ts` — task_start + task_end

**Files:**
- Modify: `gravity-claw/src/bot/chat.ts`

- [ ] **Step 1: Read current `chat.ts`**

Open `gravity-claw/src/bot/chat.ts`. Find the `bot.on('message:text', ...)` handler.

- [ ] **Step 2: Wrap handler with emit_event calls**

Edit `gravity-claw/src/bot/chat.ts` — apply this diff at the message handler:

```typescript
import type { Bot } from 'grammy';
import { randomUUID } from 'node:crypto';
import { askClaude } from '../ai/claude.js';
import { emitEvent } from '../agent/emit-event.js';

export function registerChat(bot: Bot): void {
  bot.on('message:text', async (ctx) => {
    const text = ctx.message.text.trim();
    if (text.startsWith('/')) return;

    const task_id = randomUUID();
    const startTs = Date.now();

    await emitEvent({
      type: 'task_start',
      action: 'reply to telegram',
      details: text.slice(0, 200),
      payload: { task_id, intent: text.slice(0, 200) },
    });

    try {
      await ctx.replyWithChatAction('typing');
      const reply = await askClaude(text, true);

      try {
        await ctx.reply(reply, { parse_mode: 'Markdown' });
      } catch {
        await ctx.reply(reply);
      }

      await emitEvent({
        type: 'task_end',
        action: 'reply complete',
        payload: { task_id, tokens_in: 0, tokens_out: 0, duration_ms: Date.now() - startTs },
      });
    } catch (err) {
      const errMsg = (err as Error).message;
      console.error('[chat] Claude error:', errMsg);
      await emitEvent({
        type: 'task_end',
        action: 'reply failed',
        details: errMsg,
        payload: { task_id, tokens_in: 0, tokens_out: 0, duration_ms: Date.now() - startTs },
      });
    }
  });
}
```

**Note:** `tokens_in/out` left at 0 here; `ai/claude.ts` will be updated in Task 14 to emit a `cost` event with real numbers, and Bryan can later thread token totals back to `chat.ts` if desired. Don't over-couple.

- [ ] **Step 3: Type-check**

```bash
cd gravity-claw && npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add gravity-claw/src/bot/chat.ts
git commit -m "feat(bot): emit task_start/task_end in chat handler"
```

---

## Task 14: Instrument `ai/claude.ts` — thought batching, tool_call/result, cost

**Files:**
- Modify: `gravity-claw/src/ai/claude.ts`

**Note:** This task touches a large existing file. Make surgical changes only — don't refactor unrelated logic. If the file is too tangled and unclear where hooks go, return DONE_WITH_CONCERNS describing what was wired and what was skipped.

- [ ] **Step 1: Read full `claude.ts`**

```bash
cd gravity-claw && wc -l src/ai/claude.ts
```
Then inspect the function `askClaude` and any streaming / tool dispatch logic.

- [ ] **Step 2: Add imports at top**

Add to imports:
```typescript
import { emitEvent, _testing } from '../agent/emit-event.js';
import { randomUUID } from 'node:crypto';
```

- [ ] **Step 3: Wire thought batcher and tool events**

Inside `askClaude` (or whichever function does the streaming call):

**At call start (no separate event — task_start is owned by `chat.ts`):**
```typescript
const thoughtBatcher = _testing.makeThoughtBatcher();
```

**On streaming text chunk:**
```typescript
// where you receive token deltas:
await thoughtBatcher.push(delta);
```

**On tool_use block detected:**
```typescript
const call_id = randomUUID();
await emitEvent({
  type: 'tool_call',
  action: `tool: ${toolName}`,
  payload: { call_id, name: toolName, args: toolInput },
});
const toolStart = Date.now();

// ...run the tool...

await emitEvent({
  type: 'tool_result',
  action: `tool done: ${toolName}`,
  payload: {
    call_id,
    output_preview: String(toolResult).slice(0, 300),
    duration_ms: Date.now() - toolStart,
    error: false,
  },
});
```

Wrap tool execution in try/catch — on throw, emit `tool_result` with `error: true`.

**At call end:**
```typescript
await thoughtBatcher.flush();

// If you have token/cost info available:
await emitEvent({
  type: 'cost',
  action: 'llm cost',
  payload: { cents: estimatedCents, tokens: totalTokens, model: modelName },
});
```

- [ ] **Step 4: Type-check**

```bash
cd gravity-claw && npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 5: Manual smoke**

```bash
cd gravity-claw && node --version  # confirms Node available
# Don't start the actual bot — just ensure no import-time errors:
node --experimental-vm-modules -e "import('./dist/ai/claude.js').then(() => console.log('ok')).catch(e => { console.error(e); process.exit(1); })"
```
(If you don't have a dist build, skip — type-check is sufficient.)

- [ ] **Step 6: Commit**

```bash
git add gravity-claw/src/ai/claude.ts
git commit -m "feat(bot): instrument askClaude — thought, tool_call/result, cost"
```

---

## Task 15: Instrument `agent/memory.ts` — memory_write

**Files:**
- Modify: `gravity-claw/src/agent/memory.ts`

- [ ] **Step 1: Find `saveMemory` function**

```bash
cd gravity-claw && grep -n "saveMemory\|export function save\|export async function save" src/agent/memory.ts | head -10
```

- [ ] **Step 2: Add import + emit at end of `saveMemory`**

Add to imports:
```typescript
import { emitEvent } from './emit-event.js';
```

Inside `saveMemory` (after the existing write succeeds, before returning), add the emit using the variables already in scope. Example for the common case where `saveMemory(content, opts)` writes a single supabase row keyed by something like `opts.key` or a generated id:

```typescript
const __summary = String(content ?? '').slice(0, 120);
const __key = (opts as any)?.key ?? (opts as any)?.id ?? '';
await emitEvent({
  type: 'memory_write',
  action: 'memory saved',
  payload: { store: 'supabase', key: __key, summary: __summary },
});
```

If `saveMemory` writes to a different store (pinecone via `vector.upsert`, or vault file write), use `store: 'pinecone'` or `store: 'vault'` accordingly. If `saveMemory` is a façade that fans out to multiple stores, emit one `memory_write` per real write inside each branch — not once at the façade level. If the function body is unclear, return DONE_WITH_CONCERNS describing what was wired and what was skipped.

- [ ] **Step 3: Type-check**

```bash
cd gravity-claw && npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add gravity-claw/src/agent/memory.ts
git commit -m "feat(bot): emit memory_write events from saveMemory"
```

---

## Task 16: Manual end-to-end verification

**Files:** none (verification only)

- [ ] **Step 1: Start mission-control dev**

```bash
cd gravity-claw/mission-control && npm run dev
```
Open `http://localhost:3000/live`. Expected: 3-panel theater, dark, "● connecting" then "● live".

- [ ] **Step 2: Insert test events via SQL**

Open the Supabase SQL editor (or psql) and run, one at a time, observing the HUD between each:

```sql
INSERT INTO activity_log (action, details, metadata, timestamp)
VALUES ('test', 'manual', '{"event_type":"task_start","payload":{"task_id":"manual-1","intent":"manual smoke test"}}', now());

INSERT INTO activity_log (action, details, metadata, timestamp)
VALUES ('test', 'manual', '{"event_type":"thought","payload":{"text":"I am thinking about the smoke test"}}', now());

INSERT INTO activity_log (action, details, metadata, timestamp)
VALUES ('test', 'manual', '{"event_type":"tool_call","payload":{"call_id":"c1","name":"test_tool","args":{"x":1}}}', now());

INSERT INTO activity_log (action, details, metadata, timestamp)
VALUES ('test', 'manual', '{"event_type":"tool_result","payload":{"call_id":"c1","output_preview":"ok","duration_ms":250,"error":false}}', now());

INSERT INTO activity_log (action, details, metadata, timestamp)
VALUES ('test', 'manual', '{"event_type":"memory_write","payload":{"store":"pinecone","key":"k","summary":"remembered smoke test"}}', now());

INSERT INTO activity_log (action, details, metadata, timestamp)
VALUES ('test', 'manual', '{"event_type":"cost","payload":{"cents":2,"tokens":42,"model":"haiku"}}', now());

INSERT INTO activity_log (action, details, metadata, timestamp)
VALUES ('test', 'manual', '{"event_type":"task_end","payload":{"task_id":"manual-1","tokens_in":42,"tokens_out":0,"duration_ms":1000}}', now());
```

- [ ] **Step 3: Visual checks**

After step 2, confirm:
- Intent banner showed "manual smoke test" then faded
- Thought stream shows "I am thinking about the smoke test"
- Action panel showed test_tool spinning, then green done
- Memory panel shows pinecone entry "remembered smoke test"
- Cost ticker shows $0.02 / 42 tokens
- Sparkline has at least 1 sample

- [ ] **Step 4: Live bot test**

In a separate terminal:
```bash
cd gravity-claw && npm start  # or whatever the bot start command is — check package.json
```

Send a Telegram message to the bot. Watch `/live` panel populate in real time: task_start → thoughts streaming → tool_calls (if Bryan's bot uses tools for that query) → task_end → cost.

- [ ] **Step 5: Disconnect test**

While `/live` is open, kill internet (or Wi-Fi) for ~10s. Banner should flip to "● reconnecting" amber within 5s. Restore network — banner returns "● live" green within ~30s (Supabase client default retry).

- [ ] **Step 6: Final commit (only if anything tweaked)**

If you adjusted any code during manual verification, commit. Otherwise leave a note in the PR body: "Manual verification passed: SQL inserts, live bot, disconnect/reconnect."

---

## Self-Review Checklist (engineer should run before merge)

- All mission-control tests pass: `cd gravity-claw/mission-control && npm test`
- Bot tests pass: `cd gravity-claw && npx vitest run src/agent/__tests__/emit-event.test.ts`
- Bot type-checks: `cd gravity-claw && npx tsc --noEmit`
- `/live` renders without console errors
- Manual SQL inserts (Task 16 step 2) correctly route to each panel
- Disconnect/reconnect cycles work
- No new `console.log` debug statements left
- `decisions/log.md` may get a new entry if Bryan wants to record the ship

---

## Out of Scope (deferred to future plans)

- Multi-bot view (Hermes + GravityClaw side by side)
- Replay/scrub mode (rewind to 5 minutes ago)
- Recording / one-click GIF export
- Per-event drill-down modal
- Authentication on `/live` (inherits mission-control's auth posture)
- Mobile responsive layout (desktop-only for v1)
- Public-facing demo URL
- Real token threading from claude.ts back to chat.ts (chat.ts emits 0 for tokens_in/out at task_end; cost event from claude.ts is authoritative)
