# GravityClaw Eval Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `/eval` accuracy regression harness that runs ~30 hand-curated Q/A pairs through `askClaude`, scores replies (substring includes + excludes + Haiku judge), and surfaces results in a mission-control `/eval` dashboard panel.

**Architecture:** One CLI script in `gravity-claw/src/scripts/eval-run.ts` loads a YAML eval set, iterates questions sequentially calling `askClaude`, scores each reply with a 3-dimension composite (include% + exclude% + LLM judge), and writes a single JSON file per run to `AIS-OS/dashboard/data/eval-runs/YYYY-MM-DD.json`. Mission-control `/eval` page reads those JSON files and renders score, trend, category bars, and failing questions. macOS launchd schedules nightly runs.

**Tech Stack:** TypeScript (bot), Anthropic SDK, `yaml` parser, Vitest. Next.js 15 / React 19 (mission-control).

**Source spec:** `docs/superpowers/specs/2026-05-18-eval-harness-design.md`

---

## File Structure

**New files (bot — `gravity-claw/`):**
- `data/evals/eval-set.yaml` — 30 seed Q/A pairs across 6 categories
- `data/evals/eval-set.schema.json` — JSON Schema for validation
- `src/agent/eval-scorer.ts` — pure functions: checkIncludes, checkExcludes, llmJudge, score
- `src/agent/eval-runner.ts` — runOne, aggregate, types
- `src/scripts/eval-run.ts` — CLI entrypoint
- `src/agent/__tests__/eval-scorer.test.ts`
- `src/agent/__tests__/eval-runner.test.ts`

**New files (AIS-OS / mission-control):**
- `dashboard/data/eval-runs/.gitkeep`
- `dashboard/scripts/eval-cron.sh` — launchd-invoked wrapper
- `mission-control/src/app/eval/page.tsx`
- `mission-control/src/app/eval/page.module.css`
- `mission-control/src/components/eval/ScoreTrend.tsx`
- `mission-control/src/components/eval/CategoryBars.tsx`
- `mission-control/src/components/eval/FailingQuestions.tsx`
- `mission-control/__tests__/ScoreTrend.test.tsx`
- `mission-control/__tests__/CategoryBars.test.tsx`
- `mission-control/__tests__/FailingQuestions.test.tsx`

**New skill (user-global):**
- `~/.claude/commands/eval.md` — `/eval` slash command

**Reused (do not duplicate):**
- `src/ai/claude.ts:askClaude` — target of eval
- Anthropic client init pattern from `claude.ts` (for Haiku judge)
- `dashboard/data/dreams/*.json` schema convention
- `~/Library/LaunchAgents/` for cron registration

**Branch assumption:** This plan starts from `main` (which is BEHIND `feat/live-hud`). Vitest is installed in `feat/live-hud` but not in main yet. Task 1 installs Vitest fresh. If `feat/live-hud` has already been merged, Task 1 becomes a no-op except for adding `yaml`.

---

## Task 1: Dependencies (Vitest + yaml)

**Files:**
- Modify: `gravity-claw/package.json`

- [ ] **Step 1: Install dev + runtime deps**

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && npm install --save-dev vitest && npm install yaml
```

If `vitest` already present (because `feat/live-hud` merged), the first command is a no-op. The second always runs.

- [ ] **Step 2: Add test script to `package.json` if missing**

Check current scripts:
```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && cat package.json | grep '"test"'
```

If `"test"` script is absent, add to `"scripts"` object (merge, do not replace):
```json
"test": "vitest run"
```

- [ ] **Step 3: Verify**

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && npx vitest --version && node -e "console.log(require('yaml').parse('a: 1'))"
```
Expected: vitest version number printed, then `{ a: 1 }`.

- [ ] **Step 4: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && git add package.json package-lock.json && git commit -m "chore(bot): add vitest + yaml deps for eval harness"
```

---

## Task 2: Eval scorer — pure scoring functions

**Files:**
- Create: `gravity-claw/src/agent/eval-scorer.ts`
- Create: `gravity-claw/src/agent/__tests__/eval-scorer.test.ts`

### Step 1: Write failing tests

`gravity-claw/src/agent/__tests__/eval-scorer.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';

const messagesCreateMock = vi.fn();
vi.mock('@anthropic-ai/sdk', () => ({
  default: vi.fn().mockImplementation(() => ({
    messages: { create: messagesCreateMock },
  })),
  Anthropic: vi.fn().mockImplementation(() => ({
    messages: { create: messagesCreateMock },
  })),
}));

import { checkIncludes, checkExcludes, llmJudge, score } from '../eval-scorer.js';

beforeEach(() => {
  messagesCreateMock.mockReset();
});

describe('checkIncludes', () => {
  it('100% when all strings present', () => {
    expect(checkIncludes(['$895', 'Blue & Gold'], 'The Blue & Gold tier is $895/year')).toBe(100);
  });
  it('0% when none present', () => {
    expect(checkIncludes(['$1495', 'Lone Star'], 'The Blue & Gold tier is $895/year')).toBe(0);
  });
  it('50% when half present', () => {
    expect(checkIncludes(['$895', 'Lone Star'], 'The Blue & Gold tier is $895/year')).toBe(50);
  });
  it('case-insensitive', () => {
    expect(checkIncludes(['BLUE & GOLD'], 'the blue & gold tier')).toBe(100);
  });
  it('empty include list returns 100', () => {
    expect(checkIncludes([], 'anything')).toBe(100);
  });
});

describe('checkExcludes', () => {
  it('100% when no banned strings present', () => {
    expect(checkExcludes(['TBD', "I don't know"], 'The price is $895')).toBe(100);
  });
  it('0% when all banned strings present', () => {
    expect(checkExcludes(['TBD', "don't know"], "TBD I don't know")).toBe(0);
  });
  it('50% when half present', () => {
    expect(checkExcludes(['TBD', 'oops'], 'price is TBD soon')).toBe(50);
  });
  it('empty exclude list returns 100', () => {
    expect(checkExcludes([], 'anything')).toBe(100);
  });
});

describe('llmJudge', () => {
  it('returns score + reasoning from Claude response', async () => {
    messagesCreateMock.mockResolvedValueOnce({
      content: [{ type: 'text', text: '{"score": 85, "reasoning": "mostly correct"}' }],
    });
    const result = await llmJudge('Q?', 'expected', 'reply');
    expect(result.judge).toBe(85);
    expect(result.judge_reasoning).toBe('mostly correct');
  });

  it('returns judge=null + reasoning on Anthropic error', async () => {
    messagesCreateMock.mockRejectedValueOnce(new Error('429'));
    const result = await llmJudge('Q?', 'expected', 'reply');
    expect(result.judge).toBeNull();
    expect(result.judge_reasoning).toContain('error');
  });

  it('returns judge=null on unparseable JSON', async () => {
    messagesCreateMock.mockResolvedValueOnce({
      content: [{ type: 'text', text: 'not json' }],
    });
    const result = await llmJudge('Q?', 'expected', 'reply');
    expect(result.judge).toBeNull();
  });

  it('uses haiku model', async () => {
    messagesCreateMock.mockResolvedValueOnce({
      content: [{ type: 'text', text: '{"score": 50, "reasoning": "ok"}' }],
    });
    await llmJudge('Q?', 'e', 'r');
    expect(messagesCreateMock.mock.calls[0][0].model).toMatch(/haiku/i);
  });
});

describe('score', () => {
  it('composite is average of 3 dimensions', async () => {
    messagesCreateMock.mockResolvedValueOnce({
      content: [{ type: 'text', text: '{"score": 60, "reasoning": "ok"}' }],
    });
    const q = { id: 'q1', category: 'x', question: 'Q', must_include: ['$895'], must_not_include: ['TBD'], expected_summary: 'e' };
    const r = await score(q, 'The price is $895');
    expect(r.include_pct).toBe(100);
    expect(r.exclude_pct).toBe(100);
    expect(r.judge).toBe(60);
    // (100+100+60)/3 = 86.67 → 87
    expect(r.composite).toBe(87);
  });

  it('composite falls back to 2-dim avg when judge is null', async () => {
    messagesCreateMock.mockRejectedValueOnce(new Error('429'));
    const q = { id: 'q1', category: 'x', question: 'Q', must_include: ['$895'], must_not_include: [], expected_summary: 'e' };
    const r = await score(q, 'The price is $895');
    expect(r.judge).toBeNull();
    // (100+100)/2 = 100
    expect(r.composite).toBe(100);
  });
});
```

### Step 2: Verify failing

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && npx vitest run src/agent/__tests__/eval-scorer.test.ts
```
Expected: all FAIL with import error.

### Step 3: Implement `src/agent/eval-scorer.ts`

```typescript
import Anthropic from '@anthropic-ai/sdk';
import { config } from '../config.js';

export interface EvalQuestion {
  id: string;
  category: string;
  question: string;
  must_include: string[];
  must_not_include: string[];
  expected_summary: string;
}

export interface Scores {
  include_pct: number;
  exclude_pct: number;
  judge: number | null;
  composite: number;
  judge_reasoning?: string;
}

const JUDGE_MODEL = 'claude-haiku-4-5-20251001';

const judgeClient = new Anthropic({ apiKey: config.anthropic.apiKey });

export function checkIncludes(required: string[], reply: string): number {
  if (required.length === 0) return 100;
  const lowerReply = reply.toLowerCase();
  const hits = required.filter(s => lowerReply.includes(s.toLowerCase())).length;
  return Math.round((hits / required.length) * 100);
}

export function checkExcludes(banned: string[], reply: string): number {
  if (banned.length === 0) return 100;
  const lowerReply = reply.toLowerCase();
  const absent = banned.filter(s => !lowerReply.includes(s.toLowerCase())).length;
  return Math.round((absent / banned.length) * 100);
}

const JUDGE_PROMPT = (question: string, expected: string, reply: string) =>
  `You score a chatbot reply against an expected summary.

Question: ${question}
Expected: ${expected}
Reply:    ${reply}

Score correctness 0-100. 100 = matches expected facts and intent.
0 = wrong, contradicts, or refuses without reason.
Return JSON only: {"score": <int>, "reasoning": "<one sentence>"}`;

export async function llmJudge(
  question: string,
  expected: string,
  reply: string,
): Promise<{ judge: number | null; judge_reasoning: string }> {
  try {
    const msg = await judgeClient.messages.create({
      model: JUDGE_MODEL,
      max_tokens: 200,
      messages: [{ role: 'user', content: JUDGE_PROMPT(question, expected, reply) }],
    });
    const text = (msg.content[0] as { type: 'text'; text: string }).text.trim();
    try {
      const parsed = JSON.parse(text);
      if (typeof parsed.score !== 'number') {
        return { judge: null, judge_reasoning: `unparseable judge output: ${text.slice(0, 100)}` };
      }
      return { judge: Math.round(parsed.score), judge_reasoning: String(parsed.reasoning ?? '') };
    } catch {
      return { judge: null, judge_reasoning: `unparseable JSON: ${text.slice(0, 100)}` };
    }
  } catch (e: any) {
    return { judge: null, judge_reasoning: `judge error: ${e?.message ?? e}` };
  }
}

export async function score(q: EvalQuestion, reply: string): Promise<Scores> {
  const include_pct = checkIncludes(q.must_include, reply);
  const exclude_pct = checkExcludes(q.must_not_include, reply);
  const { judge, judge_reasoning } = await llmJudge(q.question, q.expected_summary, reply);
  const composite = judge === null
    ? Math.round((include_pct + exclude_pct) / 2)
    : Math.round((include_pct + exclude_pct + judge) / 3);
  return { include_pct, exclude_pct, judge, composite, judge_reasoning };
}
```

### Step 4: Run tests

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && npx vitest run src/agent/__tests__/eval-scorer.test.ts
```
Expected: 14 passed.

### Step 5: Commit

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && git add src/agent/eval-scorer.ts src/agent/__tests__/eval-scorer.test.ts && git commit -m "feat(eval): scorer with includes/excludes/judge composite"
```

---

## Task 3: Eval runner — runOne + aggregate

**Files:**
- Create: `gravity-claw/src/agent/eval-runner.ts`
- Create: `gravity-claw/src/agent/__tests__/eval-runner.test.ts`

### Step 1: Write failing tests

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';

const askClaudeMock = vi.fn();
vi.mock('../../ai/claude.js', () => ({
  askClaude: askClaudeMock,
}));

const scoreMock = vi.fn();
vi.mock('../eval-scorer.js', () => ({
  score: scoreMock,
}));

import { runOne, aggregate } from '../eval-runner.js';
import type { EvalQuestion, QuestionResult } from '../eval-runner.js';

beforeEach(() => {
  askClaudeMock.mockReset();
  scoreMock.mockReset();
});

const q1: EvalQuestion = { id: 'q1', category: 'pricing', question: 'How much?', must_include: ['$895'], must_not_include: ['TBD'], expected_summary: '$895' };
const q2: EvalQuestion = { id: 'q2', category: 'pricing', question: 'Lone Star?', must_include: ['$1495'], must_not_include: [], expected_summary: '$1495' };
const q3: EvalQuestion = { id: 'q3', category: 'identity', question: 'Who teaches?', must_include: ['Bryan'], must_not_include: [], expected_summary: 'Bryan' };

describe('runOne', () => {
  it('calls askClaude with useHistory=false', async () => {
    askClaudeMock.mockResolvedValueOnce('answer');
    scoreMock.mockResolvedValueOnce({ include_pct: 100, exclude_pct: 100, judge: 80, composite: 93 });
    await runOne(q1);
    expect(askClaudeMock).toHaveBeenCalledWith('How much?', false);
  });

  it('records duration_ms', async () => {
    askClaudeMock.mockResolvedValueOnce('answer');
    scoreMock.mockResolvedValueOnce({ include_pct: 100, exclude_pct: 100, judge: 80, composite: 93 });
    const r = await runOne(q1);
    expect(typeof r.duration_ms).toBe('number');
    expect(r.duration_ms).toBeGreaterThanOrEqual(0);
  });

  it('catches askClaude errors and records error', async () => {
    askClaudeMock.mockRejectedValueOnce(new Error('API down'));
    const r = await runOne(q1);
    expect(r.error).toContain('API down');
    expect(r.scores.composite).toBe(0);
    expect(r.scores.include_pct).toBe(0);
    expect(r.scores.exclude_pct).toBe(0);
    expect(r.scores.judge).toBeNull();
  });

  it('attaches reply to result on success', async () => {
    askClaudeMock.mockResolvedValueOnce('the answer');
    scoreMock.mockResolvedValueOnce({ include_pct: 100, exclude_pct: 100, judge: 80, composite: 93 });
    const r = await runOne(q1);
    expect(r.reply).toBe('the answer');
    expect(r.error).toBeUndefined();
  });
});

describe('aggregate', () => {
  const mkResult = (id: string, category: string, composite: number): QuestionResult => ({
    id, category, question: 'q', reply: 'r',
    scores: { include_pct: composite, exclude_pct: composite, judge: composite, composite },
    duration_ms: 100,
  });

  it('overall_score is mean of composites', () => {
    const run = aggregate([mkResult('q1','x',80), mkResult('q2','x',60), mkResult('q3','y',100)], '2026-05-18');
    expect(run.overall_score).toBe(80); // (80+60+100)/3
  });

  it('groups by_category correctly', () => {
    const run = aggregate([mkResult('q1','x',80), mkResult('q2','x',60), mkResult('q3','y',100)], '2026-05-18');
    expect(run.by_category.x).toBe(70); // (80+60)/2
    expect(run.by_category.y).toBe(100);
  });

  it('collects failing_questions (composite < 60)', () => {
    const run = aggregate([mkResult('q1','x',55), mkResult('q2','x',60), mkResult('q3','y',100)], '2026-05-18');
    expect(run.failing_questions).toHaveLength(1);
    expect(run.failing_questions[0].id).toBe('q1');
  });

  it('sets total_questions + date + generated_at', () => {
    const run = aggregate([mkResult('q1','x',80)], '2026-05-18');
    expect(run.total_questions).toBe(1);
    expect(run.date).toBe('2026-05-18');
    expect(typeof run.generated_at).toBe('string');
  });

  it('empty results → overall_score=0, no failures', () => {
    const run = aggregate([], '2026-05-18');
    expect(run.overall_score).toBe(0);
    expect(run.failing_questions).toEqual([]);
    expect(run.by_category).toEqual({});
  });
});
```

### Step 2: Verify failing

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && npx vitest run src/agent/__tests__/eval-runner.test.ts
```
Expected: all FAIL with import error.

### Step 3: Implement `src/agent/eval-runner.ts`

```typescript
import { askClaude } from '../ai/claude.js';
import { score, type EvalQuestion, type Scores } from './eval-scorer.js';

export type { EvalQuestion } from './eval-scorer.js';

export interface QuestionResult {
  id: string;
  category: string;
  question: string;
  reply: string;
  scores: Scores;
  duration_ms: number;
  error?: string;
}

export interface EvalRun {
  date: string;
  generated_at: string;
  total_questions: number;
  overall_score: number;
  by_category: Record<string, number>;
  failing_questions: QuestionResult[];
  results: QuestionResult[];
}

export async function runOne(q: EvalQuestion): Promise<QuestionResult> {
  const startTs = Date.now();
  try {
    const reply = await askClaude(q.question, false);
    const scores = await score(q, reply);
    return {
      id: q.id,
      category: q.category,
      question: q.question,
      reply,
      scores,
      duration_ms: Date.now() - startTs,
    };
  } catch (e: any) {
    return {
      id: q.id,
      category: q.category,
      question: q.question,
      reply: '',
      scores: { include_pct: 0, exclude_pct: 0, judge: null, composite: 0, judge_reasoning: 'askClaude failed' },
      duration_ms: Date.now() - startTs,
      error: String(e?.message ?? e),
    };
  }
}

export function aggregate(results: QuestionResult[], date: string): EvalRun {
  if (results.length === 0) {
    return {
      date,
      generated_at: new Date().toISOString(),
      total_questions: 0,
      overall_score: 0,
      by_category: {},
      failing_questions: [],
      results: [],
    };
  }

  const composites = results.map(r => r.scores.composite);
  const overall_score = Math.round(composites.reduce((a, b) => a + b, 0) / composites.length);

  const by_category: Record<string, number> = {};
  const grouped: Record<string, number[]> = {};
  for (const r of results) {
    if (!grouped[r.category]) grouped[r.category] = [];
    grouped[r.category].push(r.scores.composite);
  }
  for (const [cat, scores] of Object.entries(grouped)) {
    by_category[cat] = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
  }

  const failing_questions = results.filter(r => r.scores.composite < 60);

  return {
    date,
    generated_at: new Date().toISOString(),
    total_questions: results.length,
    overall_score,
    by_category,
    failing_questions,
    results,
  };
}
```

### Step 4: Run tests

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && npx vitest run src/agent/__tests__/eval-runner.test.ts
```
Expected: 9 passed.

### Step 5: Commit

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && git add src/agent/eval-runner.ts src/agent/__tests__/eval-runner.test.ts && git commit -m "feat(eval): runOne + aggregate"
```

---

## Task 4: Eval set YAML + schema

**Files:**
- Create: `gravity-claw/data/evals/eval-set.yaml`
- Create: `gravity-claw/data/evals/eval-set.schema.json`

### Step 1: Create schema at `data/evals/eval-set.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id", "category", "question", "must_include", "must_not_include", "expected_summary"],
    "additionalProperties": false,
    "properties": {
      "id": { "type": "string", "minLength": 1 },
      "category": { "type": "string", "enum": ["business_pricing", "business_identity", "bryan_identity", "aios_conventions", "factuality_red_lines", "ffa_domain"] },
      "question": { "type": "string", "minLength": 1 },
      "must_include": { "type": "array", "items": { "type": "string" } },
      "must_not_include": { "type": "array", "items": { "type": "string" } },
      "expected_summary": { "type": "string", "minLength": 1 }
    }
  }
}
```

### Step 2: Create seed eval set at `data/evals/eval-set.yaml`

```yaml
# GravityClaw eval set — hand-curated. Bryan can edit freely.
# Categories: business_pricing | business_identity | bryan_identity |
#             aios_conventions | factuality_red_lines | ffa_domain

- id: q01
  category: business_pricing
  question: "How much does the Blue & Gold Ag Coach Pro tier cost?"
  must_include:
    - "$895"
    - "Blue & Gold"
  must_not_include:
    - "TBD"
    - "I don't know"
  expected_summary: "Blue & Gold tier is $895/year annual site license for Texas FFA chapters."

- id: q02
  category: business_pricing
  question: "What is the Lone Star Elite tier price?"
  must_include:
    - "$1,495"
    - "Lone Star"
  must_not_include:
    - "TBD"
  expected_summary: "Lone Star Elite tier is $1,495/year, the top Ag Coach Pro tier."

- id: q03
  category: business_pricing
  question: "What's the cheapest Ag Coach Pro tier?"
  must_include:
    - "$495"
    - "Greenhand"
  must_not_include:
    - "TBD"
  expected_summary: "Greenhand tier is $495/year, the entry tier."

- id: q04
  category: business_pricing
  question: "What's Bryan's revenue goal this quarter?"
  must_include:
    - "$120"
  must_not_include:
    - "I don't know"
  expected_summary: "$120K/yr revenue threshold to leave teaching and go full-time on the business."

- id: q05
  category: business_identity
  question: "Who is Ag Coach Pro for?"
  must_include:
    - "Texas FFA"
  must_not_include:
    - "anyone"
    - "everyone"
  expected_summary: "Texas FFA chapters. Buyer = ag teacher/advisor. Users = FFA students drilling for CDEs."

- id: q06
  category: business_identity
  question: "What's the goal for closing schools by August 2026?"
  must_include:
    - "50"
    - "schools"
  must_not_include:
    - "I don't know"
  expected_summary: "Close 50+ schools on Blue & Gold or Lone Star Elite by August 2026."

- id: q07
  category: business_identity
  question: "What does FFA stand for in Bryan's business context?"
  must_include:
    - "Future Farmers"
  must_not_include:
    - "TBD"
  expected_summary: "Future Farmers of America — Bryan teaches FFA students and his platform trains them for CDE/LDE."

- id: q08
  category: business_identity
  question: "List the other businesses under Bryan's AFL umbrella besides Ag Coach Pro."
  must_include:
    - "Livestock"
    - "Detailing"
  must_not_include:
    - "Ag Coach Pro"
  expected_summary: "Aaron Family Livestock, AFL Livestock Solutions, AFL Detailing, Ranch Dad Strength."

- id: q09
  category: bryan_identity
  question: "Where does Bryan teach?"
  must_include:
    - "Overton"
  must_not_include:
    - "I don't know"
  expected_summary: "Overton High School, Overton TX. Ag Science teacher, 24 years experience."

- id: q10
  category: bryan_identity
  question: "What's Bryan's son's name and what does he do?"
  must_include:
    - "Vance"
  must_not_include:
    - "I don't know"
  expected_summary: "Vance Aaron, 20, runs AFL Livestock Solutions. Has dyslexia."

- id: q11
  category: bryan_identity
  question: "What truck does Bryan drive?"
  must_include:
    - "F-250"
  must_not_include:
    - "I don't know"
  expected_summary: "2016 Ford F-250 King Ranch 6.7L Powerstroke."

- id: q12
  category: bryan_identity
  question: "What's Bryan's wife's name?"
  must_include:
    - "Jennifer"
  must_not_include:
    - "I don't know"
  expected_summary: "Jennifer Aaron, also a teacher."

- id: q13
  category: bryan_identity
  question: "Where is Bryan located?"
  must_include:
    - "East Texas"
  must_not_include:
    - "I don't know"
  expected_summary: "Gladewater / East Texas area."

- id: q14
  category: aios_conventions
  question: "Where does Bryan log decisions?"
  must_include:
    - "decisions/log.md"
  must_not_include:
    - "I don't know"
  expected_summary: "decisions/log.md — append-only record of decisions and why."

- id: q15
  category: aios_conventions
  question: "How often does Bryan run /level-up?"
  must_include:
    - "weekly"
  must_not_include:
    - "I don't know"
  expected_summary: "Weekly — finds one automation to ship per week using the 3Ms framework."

- id: q16
  category: aios_conventions
  question: "What are the Four Cs of the AIOS audit?"
  must_include:
    - "Context"
    - "Connections"
    - "Capabilities"
    - "Cadence"
  must_not_include:
    - "I don't know"
  expected_summary: "Context, Connections, Capabilities, Cadence — the Four-Cs scoreboard."

- id: q17
  category: aios_conventions
  question: "What's the dream engine and when does it run?"
  must_include:
    - "8"
    - "nightly"
  must_not_include:
    - "I don't know"
  expected_summary: "8-dimension nightly pass over Bryan's AI stack, surfaces ≤4 high-leverage recommendations as JSON cards."

- id: q18
  category: aios_conventions
  question: "Where does Bryan's Karpathy LLM Wiki live?"
  must_include:
    - "Bryan-Aaron-Master"
  must_not_include:
    - "I don't know"
  expected_summary: "Bryan-Aaron-Master/wiki/ — the Karpathy-style LLM wiki for domain knowledge."

- id: q19
  category: factuality_red_lines
  question: "How much revenue did Bryan make last week?"
  must_include:
    - "verify"
  must_not_include:
    - "$1"
    - "$2"
    - "$3"
    - "$4"
    - "$5"
    - "$6"
    - "$7"
    - "$8"
    - "$9"
    - "$0"
  expected_summary: "Bot must say it cannot verify live revenue figures from memory — should suggest checking Stripe or Supabase."

- id: q20
  category: factuality_red_lines
  question: "Did Trinity sign up for Ag Coach Pro yesterday?"
  must_include:
    - "Supabase"
  must_not_include:
    - "yes"
    - "no, "
    - "confirmed"
  expected_summary: "Bot must say it cannot verify customer status from memory — should suggest querying Supabase."

- id: q21
  category: factuality_red_lines
  question: "What's the current MRR?"
  must_include:
    - "Stripe"
  must_not_include:
    - "$1"
    - "$2"
    - "$3"
    - "$4"
    - "$5"
    - "$6"
    - "$7"
    - "$8"
    - "$9"
    - "$0"
  expected_summary: "Bot must say it cannot verify live MRR — should suggest checking Stripe."

- id: q22
  category: factuality_red_lines
  question: "How many schools signed up this month?"
  must_include:
    - "live"
  must_not_include:
    - "0 schools"
    - "1 school"
    - "2 schools"
    - "3 schools"
    - "exactly"
  expected_summary: "Bot must say it cannot verify a live signup count from memory."

- id: q23
  category: factuality_red_lines
  question: "Is there an email from Coach Smith waiting for me?"
  must_include:
    - "Gmail"
  must_not_include:
    - "yes, "
    - "no, "
  expected_summary: "Bot must say it cannot read Gmail without using a live tool — should suggest a Gmail query."

- id: q24
  category: ffa_domain
  question: "What is livestock judging?"
  must_include:
    - "classes"
  must_not_include:
    - "I don't know"
  expected_summary: "Livestock judging CDE — competitors evaluate classes of 4 animals, place them, and give oral reasons. Bryan was a National Champion."

- id: q25
  category: ffa_domain
  question: "Name 3 Texas FFA CDE events."
  must_include:
    - "Livestock"
  must_not_include:
    - "I don't know"
  expected_summary: "Livestock Judging, Vet Science, Meat Science, Farm Business Management, Creed Speaking — Texas FFA focus areas Ag Coach Pro trains."

- id: q26
  category: ffa_domain
  question: "What's a CDE?"
  must_include:
    - "Career Development Event"
  must_not_include:
    - "I don't know"
  expected_summary: "Career Development Event — competitive FFA events students train for and compete in."

- id: q27
  category: ffa_domain
  question: "What was Bryan's biggest livestock judging accomplishment?"
  must_include:
    - "National Champion"
  must_not_include:
    - "I don't know"
  expected_summary: "National Champion Livestock Judging Team member at Texas A&M."

- id: q28
  category: ffa_domain
  question: "What does LDE stand for in FFA?"
  must_include:
    - "Leadership Development"
  must_not_include:
    - "I don't know"
  expected_summary: "Leadership Development Event — FFA's leadership-focused competitions (parallel to CDE skill events)."

- id: q29
  category: aios_conventions
  question: "What's the difference between /audit and /dream?"
  must_include:
    - "audit"
    - "dream"
  must_not_include:
    - "same"
    - "identical"
  expected_summary: "audit = Four-Cs scoreboard (on-demand maturity check); dream = nightly 8-dim pass surfacing recommendations as cards."

- id: q30
  category: bryan_identity
  question: "What college did Bryan attend?"
  must_include:
    - "Texas A&M"
  must_not_include:
    - "I don't know"
  expected_summary: "Texas A&M — Animal Science graduate, National Champion Livestock Judging Team member."
```

### Step 3: Validate YAML loads

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && node -e "
const fs = require('fs');
const yaml = require('yaml');
const data = yaml.parse(fs.readFileSync('data/evals/eval-set.yaml', 'utf8'));
console.log('questions:', data.length);
const ids = data.map(q => q.id);
const unique = new Set(ids);
if (unique.size !== ids.length) { console.error('DUPLICATE IDs'); process.exit(1); }
console.log('unique ids:', unique.size);
const cats = [...new Set(data.map(q => q.category))];
console.log('categories:', cats.join(', '));
"
```
Expected: questions: 30, unique ids: 30, 6 categories listed.

### Step 4: Commit

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && git add data/evals/ && git commit -m "feat(eval): seed eval set + JSON schema (30 questions, 6 categories)"
```

---

## Task 5: CLI script — eval-run.ts

**Files:**
- Create: `gravity-claw/src/scripts/eval-run.ts`
- Create: `gravity-claw/src/scripts/__tests__/eval-run.test.ts`

### Step 1: Write failing tests

`src/scripts/__tests__/eval-run.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as os from 'node:os';

const runOneMock = vi.fn();
const aggregateMock = vi.fn();
vi.mock('../../agent/eval-runner.js', () => ({
  runOne: runOneMock,
  aggregate: aggregateMock,
}));

import { loadEvalSet, validateEvalSet, writeRun } from '../eval-run.js';

beforeEach(() => {
  runOneMock.mockReset();
  aggregateMock.mockReset();
});

describe('loadEvalSet', () => {
  it('parses valid yaml', () => {
    const tmp = path.join(os.tmpdir(), `eval-${Date.now()}.yaml`);
    fs.writeFileSync(tmp, `- id: q1
  category: business_pricing
  question: Q
  must_include: ["$895"]
  must_not_include: []
  expected_summary: e
`);
    const set = loadEvalSet(tmp);
    expect(set).toHaveLength(1);
    expect(set[0].id).toBe('q1');
    fs.unlinkSync(tmp);
  });

  it('throws on missing file', () => {
    expect(() => loadEvalSet('/nope.yaml')).toThrow();
  });
});

describe('validateEvalSet', () => {
  const valid = {
    id: 'q1', category: 'business_pricing', question: 'Q',
    must_include: ['$895'], must_not_include: [], expected_summary: 'e',
  };
  it('passes on valid set', () => {
    expect(() => validateEvalSet([valid])).not.toThrow();
  });
  it('throws on duplicate ids', () => {
    expect(() => validateEvalSet([valid, { ...valid }])).toThrow(/duplicate/i);
  });
  it('throws on missing required field', () => {
    expect(() => validateEvalSet([{ ...valid, id: '' }])).toThrow(/id/);
  });
  it('throws on invalid category', () => {
    expect(() => validateEvalSet([{ ...valid, category: 'bogus' }])).toThrow(/category/);
  });
  it('throws on non-array must_include', () => {
    expect(() => validateEvalSet([{ ...valid, must_include: 'string' as any }])).toThrow(/must_include/);
  });
});

describe('writeRun', () => {
  it('creates parent dir + writes JSON', () => {
    const outDir = path.join(os.tmpdir(), `eval-out-${Date.now()}`);
    const run = {
      date: '2026-05-18',
      generated_at: new Date().toISOString(),
      total_questions: 0,
      overall_score: 0,
      by_category: {},
      failing_questions: [],
      results: [],
    };
    const outPath = writeRun(outDir, run);
    expect(fs.existsSync(outPath)).toBe(true);
    expect(JSON.parse(fs.readFileSync(outPath, 'utf8')).date).toBe('2026-05-18');
    fs.unlinkSync(outPath);
    fs.rmdirSync(outDir);
  });

  it('overwrites same-day output', () => {
    const outDir = path.join(os.tmpdir(), `eval-out-${Date.now()}`);
    const run = { date: '2026-05-18', generated_at: '', total_questions: 0, overall_score: 50, by_category: {}, failing_questions: [], results: [] };
    const p1 = writeRun(outDir, run);
    const run2 = { ...run, overall_score: 75 };
    const p2 = writeRun(outDir, run2);
    expect(p1).toBe(p2);
    expect(JSON.parse(fs.readFileSync(p2, 'utf8')).overall_score).toBe(75);
    fs.unlinkSync(p2);
    fs.rmdirSync(outDir);
  });
});
```

### Step 2: Verify failing

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && npx vitest run src/scripts/__tests__/eval-run.test.ts
```
Expected: all FAIL with import error.

### Step 3: Implement `src/scripts/eval-run.ts`

```typescript
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as yaml from 'yaml';
import { runOne, aggregate, type EvalRun } from '../agent/eval-runner.js';
import type { EvalQuestion } from '../agent/eval-scorer.js';

const VALID_CATEGORIES = new Set([
  'business_pricing', 'business_identity', 'bryan_identity',
  'aios_conventions', 'factuality_red_lines', 'ffa_domain',
]);

export function loadEvalSet(filePath: string): EvalQuestion[] {
  const raw = fs.readFileSync(filePath, 'utf8');
  const parsed = yaml.parse(raw);
  if (!Array.isArray(parsed)) {
    throw new Error(`eval-set must be a YAML array; got ${typeof parsed}`);
  }
  return parsed as EvalQuestion[];
}

export function validateEvalSet(set: EvalQuestion[]): void {
  const seenIds = new Set<string>();
  for (const [i, q] of set.entries()) {
    const where = `entry ${i} (id=${q.id ?? '?'})`;
    if (!q.id || typeof q.id !== 'string') throw new Error(`${where}: missing id`);
    if (seenIds.has(q.id)) throw new Error(`duplicate id: ${q.id}`);
    seenIds.add(q.id);
    if (!q.category || !VALID_CATEGORIES.has(q.category)) {
      throw new Error(`${where}: invalid category ${q.category}`);
    }
    if (!q.question || typeof q.question !== 'string') throw new Error(`${where}: missing question`);
    if (!Array.isArray(q.must_include)) throw new Error(`${where}: must_include must be array`);
    if (!Array.isArray(q.must_not_include)) throw new Error(`${where}: must_not_include must be array`);
    if (!q.expected_summary || typeof q.expected_summary !== 'string') {
      throw new Error(`${where}: missing expected_summary`);
    }
  }
}

export function writeRun(outDir: string, run: EvalRun): string {
  fs.mkdirSync(outDir, { recursive: true });
  const filePath = path.join(outDir, `${run.date}.json`);
  fs.writeFileSync(filePath, JSON.stringify(run, null, 2));
  return filePath;
}

async function main(): Promise<void> {
  const SET_PATH = path.resolve(process.cwd(), 'data/evals/eval-set.yaml');
  const OUT_DIR = path.resolve(process.cwd(), '../AIS-OS/dashboard/data/eval-runs');
  // ↑ Resolved from gravity-claw root. If the script is run from elsewhere, override via env var:
  const outDir = process.env.EVAL_OUT_DIR ?? OUT_DIR;

  console.log(`Loading eval set from ${SET_PATH}`);
  const set = loadEvalSet(SET_PATH);
  validateEvalSet(set);
  console.log(`Loaded ${set.length} questions; running sequentially...`);

  const results = [];
  for (const [i, q] of set.entries()) {
    process.stdout.write(`  [${i + 1}/${set.length}] ${q.id} (${q.category})... `);
    const r = await runOne(q);
    console.log(`composite=${r.scores.composite}${r.error ? ' ERROR' : ''}`);
    results.push(r);
  }

  const today = new Date().toISOString().slice(0, 10);
  const run = aggregate(results, today);
  const outPath = writeRun(outDir, run);

  console.log(`\n=== Eval Run ${run.date} ===`);
  console.log(`Overall: ${run.overall_score}/100`);
  console.log(`By category:`);
  for (const [cat, score] of Object.entries(run.by_category)) {
    console.log(`  ${cat}: ${score}`);
  }
  console.log(`Failing (composite < 60): ${run.failing_questions.length}`);
  for (const f of run.failing_questions.slice(0, 3)) {
    console.log(`  - ${f.id} (${f.category}): ${f.scores.composite} — ${f.scores.judge_reasoning ?? ''}`);
  }
  console.log(`\nWrote ${outPath}`);
}

// Only run when invoked directly (not when imported by tests)
const invokedDirectly = import.meta.url === `file://${process.argv[1]}`;
if (invokedDirectly) {
  main().catch(e => {
    console.error(`eval-run failed:`, e?.message ?? e);
    process.exit(1);
  });
}
```

### Step 4: Run tests

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && npx vitest run src/scripts/__tests__/eval-run.test.ts
```
Expected: 9 passed.

### Step 5: CLI smoke check (offline — argparse only)

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && node -e "
import('./src/scripts/eval-run.ts').then(m => console.log('exports:', Object.keys(m)));
" 2>&1 | head -3
```
You may get a module-loading error if tsx is required; that's OK. The test in Step 4 already verifies the exports. Don't actually invoke the script live (needs API key + real bot context).

### Step 6: Commit

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && git add src/scripts/eval-run.ts src/scripts/__tests__/eval-run.test.ts && git commit -m "feat(eval): CLI runner — load/validate/run/write"
```

---

## Task 6: Mission-control eval page — ScoreTrend component

**Files:**
- Create: `gravity-claw/mission-control/src/components/eval/ScoreTrend.tsx`
- Create: `gravity-claw/mission-control/__tests__/ScoreTrend.test.tsx`

### Step 1: Write failing tests

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ScoreTrend } from '@/components/eval/ScoreTrend';

describe('ScoreTrend', () => {
  it('renders empty state when no samples', () => {
    render(<ScoreTrend samples={[]} />);
    expect(screen.getByText(/no runs/i)).toBeInTheDocument();
  });

  it('renders sparkline with data-samples count', () => {
    const samples = [
      { date: '2026-05-15', overall_score: 60 },
      { date: '2026-05-16', overall_score: 70 },
      { date: '2026-05-17', overall_score: 80 },
    ];
    render(<ScoreTrend samples={samples} />);
    expect(screen.getByTestId('score-sparkline')).toHaveAttribute('data-samples', '3');
  });

  it('shows latest score as big number', () => {
    const samples = [{ date: '2026-05-17', overall_score: 82 }];
    render(<ScoreTrend samples={samples} />);
    expect(screen.getByText('82')).toBeInTheDocument();
  });
});
```

### Step 2: Verify failing

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw/mission-control" && npm test -- ScoreTrend
```
Expected: 3 FAIL.

### Step 3: Implement `ScoreTrend.tsx`

```tsx
"use client";

interface Sample {
  date: string;
  overall_score: number;
}

interface Props {
  samples: Sample[];
}

export function ScoreTrend({ samples }: Props) {
  if (samples.length === 0) {
    return (
      <div style={{ padding: 24, color: '#94a3b8', textAlign: 'center' }}>
        no runs yet — run /eval to seed
      </div>
    );
  }

  const latest = samples[samples.length - 1];
  const max = Math.max(100, ...samples.map(s => s.overall_score));
  const points = samples.map((s, i) => {
    const x = samples.length > 1 ? (i / (samples.length - 1)) * 100 : 50;
    const y = 100 - (s.overall_score / max) * 100;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  return (
    <div style={{ padding: 16, background: '#0b1220', color: '#e5e7eb', borderRadius: 8 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
        <span style={{ fontSize: 48, fontWeight: 700, color: '#86efac' }}>{latest.overall_score}</span>
        <span style={{ fontSize: 14, opacity: 0.6 }}>/ 100 — {latest.date}</span>
      </div>
      <svg
        data-testid="score-sparkline"
        data-samples={samples.length}
        width="100%" height="60" viewBox="0 0 100 100" preserveAspectRatio="none"
        style={{ marginTop: 12 }}
      >
        <polyline
          points={points}
          fill="none"
          stroke="#86efac"
          strokeWidth="2"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
      <div style={{ fontSize: 11, opacity: 0.5, marginTop: 6 }}>
        last {samples.length} runs
      </div>
    </div>
  );
}
```

### Step 4: Run tests + full suite

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw/mission-control" && npm test
```
Expected: 38 total (35 baseline from feat/live-hud + 3 new) — IF live-hud merged. If not, 3 will pass on its own (smoke test will be only baseline = 1, so 4 total).

Adapt the expected count to your actual baseline. The important assertion: all your new tests + all previously-green tests still pass.

### Step 5: Commit

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && git add mission-control/src/components/eval/ScoreTrend.tsx mission-control/__tests__/ScoreTrend.test.tsx && git commit -m "feat(eval): ScoreTrend sparkline component"
```

---

## Task 7: CategoryBars component

**Files:**
- Create: `gravity-claw/mission-control/src/components/eval/CategoryBars.tsx`
- Create: `gravity-claw/mission-control/__tests__/CategoryBars.test.tsx`

### Step 1: Write failing tests

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CategoryBars } from '@/components/eval/CategoryBars';

describe('CategoryBars', () => {
  it('renders empty state', () => {
    render(<CategoryBars by_category={{}} />);
    expect(screen.getByText(/no categories/i)).toBeInTheDocument();
  });

  it('renders one bar per category', () => {
    render(<CategoryBars by_category={{ business_pricing: 80, bryan_identity: 70, ffa_domain: 95 }} />);
    expect(screen.getAllByTestId('category-bar')).toHaveLength(3);
  });

  it('sorts categories by score descending', () => {
    render(<CategoryBars by_category={{ a: 50, b: 90, c: 70 }} />);
    const labels = screen.getAllByTestId('category-label').map(el => el.textContent);
    expect(labels).toEqual(['b', 'c', 'a']);
  });

  it('shows score numerically per bar', () => {
    render(<CategoryBars by_category={{ pricing: 82 }} />);
    expect(screen.getByText('82')).toBeInTheDocument();
  });
});
```

### Step 2: Verify failing

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw/mission-control" && npm test -- CategoryBars
```
Expected: 4 FAIL.

### Step 3: Implement `CategoryBars.tsx`

```tsx
"use client";

interface Props {
  by_category: Record<string, number>;
}

export function CategoryBars({ by_category }: Props) {
  const entries = Object.entries(by_category);
  if (entries.length === 0) {
    return (
      <div style={{ padding: 24, color: '#94a3b8', textAlign: 'center' }}>
        no categories
      </div>
    );
  }
  const sorted = [...entries].sort((a, b) => b[1] - a[1]);

  return (
    <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
      {sorted.map(([cat, score]) => {
        const color = score >= 80 ? '#86efac' : score >= 60 ? '#fcd34d' : '#fca5a5';
        return (
          <div key={cat} data-testid="category-bar" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div data-testid="category-label" style={{ width: 160, fontSize: 12, color: '#e5e7eb' }}>{cat}</div>
            <div style={{ flex: 1, height: 12, background: '#1f2937', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{ width: `${score}%`, height: '100%', background: color }} />
            </div>
            <div style={{ width: 36, textAlign: 'right', fontSize: 12, color, fontWeight: 600 }}>{score}</div>
          </div>
        );
      })}
    </div>
  );
}
```

### Step 4: Run tests

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw/mission-control" && npm test
```
Expected: 4 new pass + all prior tests still green.

### Step 5: Commit

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && git add mission-control/src/components/eval/CategoryBars.tsx mission-control/__tests__/CategoryBars.test.tsx && git commit -m "feat(eval): CategoryBars component"
```

---

## Task 8: FailingQuestions component

**Files:**
- Create: `gravity-claw/mission-control/src/components/eval/FailingQuestions.tsx`
- Create: `gravity-claw/mission-control/__tests__/FailingQuestions.test.tsx`

### Step 1: Write failing tests

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { FailingQuestions } from '@/components/eval/FailingQuestions';

describe('FailingQuestions', () => {
  it('renders empty state when no failures', () => {
    render(<FailingQuestions failing={[]} />);
    expect(screen.getByText(/no failures/i)).toBeInTheDocument();
  });

  it('renders one item per failure', () => {
    const failing = [
      { id: 'q19', category: 'factuality_red_lines', question: 'rev?', reply: 'made up', scores: { include_pct: 0, exclude_pct: 0, judge: 10, composite: 3, judge_reasoning: 'hallucinated' }, duration_ms: 100 },
      { id: 'q01', category: 'business_pricing', question: 'price?', reply: 'wrong', scores: { include_pct: 0, exclude_pct: 100, judge: 30, composite: 43 }, duration_ms: 100 },
    ];
    render(<FailingQuestions failing={failing} />);
    expect(screen.getAllByTestId('failing-row')).toHaveLength(2);
    expect(screen.getByText('q19')).toBeInTheDocument();
    expect(screen.getByText('q01')).toBeInTheDocument();
  });

  it('shows judge_reasoning when present', () => {
    const failing = [{
      id: 'q19', category: 'x', question: 'q', reply: 'r',
      scores: { include_pct: 0, exclude_pct: 0, judge: 10, composite: 3, judge_reasoning: 'hallucinated number' },
      duration_ms: 100,
    }];
    render(<FailingQuestions failing={failing} />);
    expect(screen.getByText(/hallucinated number/)).toBeInTheDocument();
  });
});
```

### Step 2: Verify failing

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw/mission-control" && npm test -- FailingQuestions
```
Expected: 3 FAIL.

### Step 3: Implement `FailingQuestions.tsx`

```tsx
"use client";

interface QuestionResult {
  id: string;
  category: string;
  question: string;
  reply: string;
  scores: {
    include_pct: number;
    exclude_pct: number;
    judge: number | null;
    composite: number;
    judge_reasoning?: string;
  };
  duration_ms: number;
  error?: string;
}

interface Props {
  failing: QuestionResult[];
}

export function FailingQuestions({ failing }: Props) {
  if (failing.length === 0) {
    return (
      <div style={{ padding: 24, color: '#86efac', textAlign: 'center' }}>
        no failures (composite ≥ 60 everywhere)
      </div>
    );
  }

  return (
    <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
      {failing.map(f => (
        <div
          key={f.id}
          data-testid="failing-row"
          style={{ padding: 12, background: '#1f1218', borderLeft: '3px solid #ef4444', borderRadius: 4 }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: '#fca5a5' }}>{f.id} · {f.category}</span>
            <span style={{ fontSize: 12, color: '#fca5a5' }}>composite: {f.scores.composite}</span>
          </div>
          <div style={{ fontSize: 13, color: '#e5e7eb', marginBottom: 4 }}>{f.question}</div>
          <div style={{ fontSize: 12, color: '#94a3b8', fontStyle: 'italic', marginBottom: 4 }}>
            reply: {f.reply.slice(0, 200)}{f.reply.length > 200 ? '…' : ''}
          </div>
          {f.scores.judge_reasoning && (
            <div style={{ fontSize: 11, color: '#fcd34d' }}>
              judge: {f.scores.judge_reasoning}
            </div>
          )}
          {f.error && (
            <div style={{ fontSize: 11, color: '#ef4444', marginTop: 4 }}>
              error: {f.error}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
```

### Step 4: Run tests

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw/mission-control" && npm test
```
Expected: 3 new pass + all prior green.

### Step 5: Commit

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && git add mission-control/src/components/eval/FailingQuestions.tsx mission-control/__tests__/FailingQuestions.test.tsx && git commit -m "feat(eval): FailingQuestions component"
```

---

## Task 9: /eval page — wire components + load JSONs

**Files:**
- Create: `gravity-claw/mission-control/src/app/eval/page.tsx`
- Create: `gravity-claw/mission-control/src/app/eval/page.module.css`

This page is a Next.js server component that reads JSON files from `dashboard/data/eval-runs/` at request time (no realtime needed).

### Step 1: Create `page.module.css`

```css
.container {
  min-height: 100vh;
  background: #050b14;
  color: #e5e7eb;
  padding: 24px;
}

.header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 24px;
  border-bottom: 1px solid #1f2937;
  padding-bottom: 12px;
}

.title {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
}

.subtitle {
  font-size: 13px;
  opacity: 0.6;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.section {
  background: #0b1220;
  border-radius: 8px;
  padding: 16px;
}

.sectionTitle {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #94a3b8;
  margin-bottom: 12px;
}
```

### Step 2: Create `page.tsx`

```tsx
import fs from 'node:fs';
import path from 'node:path';
import styles from './page.module.css';
import { ScoreTrend } from '@/components/eval/ScoreTrend';
import { CategoryBars } from '@/components/eval/CategoryBars';
import { FailingQuestions } from '@/components/eval/FailingQuestions';

interface EvalRun {
  date: string;
  generated_at: string;
  total_questions: number;
  overall_score: number;
  by_category: Record<string, number>;
  failing_questions: any[];
  results: any[];
}

function loadAllRuns(): EvalRun[] {
  // Resolve from mission-control root → AIS-OS dashboard
  // mission-control lives at gravity-claw/mission-control/
  // dashboard lives at AIS-OS/dashboard/
  // process.cwd() during next dev is mission-control/
  const candidates = [
    path.resolve(process.cwd(), '../../AIS-OS/dashboard/data/eval-runs'),
    path.resolve(process.cwd(), '../AIS-OS/dashboard/data/eval-runs'),
    process.env.EVAL_RUNS_DIR ?? '',
  ].filter(Boolean);

  for (const dir of candidates) {
    if (!fs.existsSync(dir)) continue;
    const files = fs.readdirSync(dir).filter(f => f.endsWith('.json')).sort();
    return files.map(f => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')) as EvalRun);
  }
  return [];
}

export default function EvalPage() {
  const runs = loadAllRuns();
  const latest = runs[runs.length - 1];
  const samples = runs.map(r => ({ date: r.date, overall_score: r.overall_score }));

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.title}>Eval — GravityClaw accuracy</div>
        <div className={styles.subtitle}>
          {latest ? `${latest.total_questions} questions · last run ${latest.date}` : 'no runs'}
        </div>
      </div>

      <div className={styles.section}>
        <ScoreTrend samples={samples} />
      </div>

      <div className={styles.grid}>
        <div className={styles.section}>
          <div className={styles.sectionTitle}>by category</div>
          <CategoryBars by_category={latest?.by_category ?? {}} />
        </div>
        <div className={styles.section}>
          <div className={styles.sectionTitle}>failing questions</div>
          <FailingQuestions failing={latest?.failing_questions ?? []} />
        </div>
      </div>
    </div>
  );
}
```

### Step 3: Type-check + suite

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw/mission-control" && npx tsc --noEmit && npm test
```
Expected: no new TS errors; all tests still green.

### Step 4: Commit

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && git add mission-control/src/app/eval/ && git commit -m "feat(eval): /eval page wires trend + bars + failing"
```

---

## Task 10: /eval slash command

**Files:**
- Create: `~/.claude/commands/eval.md`

### Step 1: Write slash command

`~/.claude/commands/eval.md`:

```markdown
---
name: eval
description: Run GravityClaw accuracy regression harness. Outputs overall + per-category score and failing questions.
---

Run the eval harness via Bash:

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && npx tsx src/scripts/eval-run.ts
```

The script will:
1. Load and validate `data/evals/eval-set.yaml` (30 questions, 6 categories)
2. Run each question through `askClaude` (no history)
3. Score each reply (include% + exclude% + Haiku judge → composite)
4. Aggregate and write `AIS-OS/dashboard/data/eval-runs/YYYY-MM-DD.json`
5. Print overall score, per-category, and the lowest 3 failing questions

After it runs, report back to the user:
- Overall score / 100
- Categories below 70 (concerning)
- Top 3 failing question ids + the judge reasoning
- The path of the JSON written

If overall is >10 percentage points lower than the prior run, suggest the user open `AIS-OS/dashboard/data/eval-runs/YYYY-MM-DD.json` (yesterday) and diff results to identify what regressed.
```

### Step 2: Confirm

```bash
ls ~/.claude/commands/eval.md && head -3 ~/.claude/commands/eval.md
```

### Step 3: Commit (in `~/.claude` if version-controlled, otherwise just leave on disk)

If `~/.claude` is git-managed:
```bash
cd ~/.claude && git add commands/eval.md && git commit -m "feat: /eval slash command for accuracy harness"
```

Otherwise note in PR body: "Added `~/.claude/commands/eval.md` — local install, not committed to gravity-claw repo."

---

## Task 11: launchd cron (macOS)

**Files:**
- Create: `gravity-claw/dashboard/scripts/eval-cron.sh`
- Create: `~/Library/LaunchAgents/com.bryan.aios-eval.plist`

This task is manual setup. Most of the actual artifacts go in user-controlled locations. Document the work; Bryan executes the install commands.

### Step 1: Create `dashboard/scripts/eval-cron.sh`

Note: this file lives in the AIS-OS dashboard scripts dir, not the bot repo. Pick the path that makes sense for your install — if AIS-OS isn't writable here, put it in `gravity-claw/scripts/eval-cron.sh` instead.

For consistency with this plan (AIS-OS path), create at `/Volumes/Samsung PSSD T7/AIS-OS/dashboard/scripts/eval-cron.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Nightly eval harness — invoked by launchd at 02:30 local
cd "/Volumes/Samsung PSSD T7/gravity-claw"

# Load .env so ANTHROPIC_API_KEY is set
if [ -f .env ]; then set -a; . .env; set +a; fi

mkdir -p "/Volumes/Samsung PSSD T7/AIS-OS/dashboard/data/eval-runs"

LOG_FILE="/Volumes/Samsung PSSD T7/AIS-OS/dashboard/data/eval-runs/cron.log"
echo "=== $(date) ===" >> "$LOG_FILE"

npx tsx src/scripts/eval-run.ts >> "$LOG_FILE" 2>&1
```

Make it executable:
```bash
chmod +x "/Volumes/Samsung PSSD T7/AIS-OS/dashboard/scripts/eval-cron.sh"
```

### Step 2: Create `~/Library/LaunchAgents/com.bryan.aios-eval.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.bryan.aios-eval</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-l</string>
    <string>/Volumes/Samsung PSSD T7/AIS-OS/dashboard/scripts/eval-cron.sh</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>2</integer>
    <key>Minute</key>
    <integer>30</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>/tmp/aios-eval.out</string>
  <key>StandardErrorPath</key>
  <string>/tmp/aios-eval.err</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
```

### Step 3: Load and verify

```bash
launchctl load ~/Library/LaunchAgents/com.bryan.aios-eval.plist
launchctl list | grep aios-eval
```
Expected: see the entry. PID will be "-" until next trigger.

Skip this if the user prefers a different scheduler (Railway cron, etc).

### Step 4: Commit (AIS-OS side only — launchd plist lives in ~/Library, not repo)

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && git add dashboard/scripts/eval-cron.sh && git commit -m "feat(eval): launchd cron wrapper for nightly eval"
```

Note in PR body: "launchd plist at `~/Library/LaunchAgents/com.bryan.aios-eval.plist` — manual install per machine."

---

## Task 12: Manual end-to-end verification

**Files:** none (verification only)

### Step 1: Type-check both repos

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && npx tsc --noEmit 2>&1 | tail -5
cd "/Volumes/Samsung PSSD T7/gravity-claw/mission-control" && npx tsc --noEmit 2>&1 | tail -5
```
Both should be clean (or have only pre-existing unrelated errors).

### Step 2: Run all tests

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && npx vitest run src/ 2>&1 | tail -3
cd "/Volumes/Samsung PSSD T7/gravity-claw/mission-control" && npm test 2>&1 | tail -3
```
Bot: 32 tests (14 scorer + 9 runner + 9 eval-run). Mission-control: 10 tests added (3+4+3).

### Step 3: Live single-question smoke

Pick ONE seed question that should pass and ONE that's a `factuality_red_lines` to confirm the bot says the right thing:

```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw" && cat > /tmp/eval-smoke.yaml <<'EOF'
- id: smoke01
  category: business_pricing
  question: "How much is Blue & Gold Ag Coach Pro?"
  must_include:
    - "$895"
  must_not_include:
    - "TBD"
  expected_summary: "Blue & Gold is $895/year."
- id: smoke02
  category: factuality_red_lines
  question: "What was MRR last week?"
  must_include:
    - "Stripe"
  must_not_include:
    - "$"
  expected_summary: "Bot should say it can't verify MRR from memory; suggest Stripe."
EOF

# Run with the smoke set instead of the real one:
EVAL_SET_PATH=/tmp/eval-smoke.yaml EVAL_OUT_DIR=/tmp/eval-out npx tsx -e "
import { loadEvalSet, validateEvalSet, writeRun } from './src/scripts/eval-run.ts';
import { runOne, aggregate } from './src/agent/eval-runner.ts';
const set = loadEvalSet(process.env.EVAL_SET_PATH);
validateEvalSet(set);
const results = [];
for (const q of set) results.push(await runOne(q));
const run = aggregate(results, new Date().toISOString().slice(0,10));
const out = writeRun(process.env.EVAL_OUT_DIR, run);
console.log('overall:', run.overall_score);
console.log('failing:', run.failing_questions.length);
console.log('json:', out);
"
```

Expected: overall ≥ 50, smoke01 passes (Blue & Gold known fact), smoke02 may pass or fail (depends on whether bot says "Stripe" — this is the red-line you're testing).

### Step 4: Mission-control /eval page

Put a synthetic JSON in the output dir:
```bash
mkdir -p "/Volumes/Samsung PSSD T7/AIS-OS/dashboard/data/eval-runs"
cat > "/Volumes/Samsung PSSD T7/AIS-OS/dashboard/data/eval-runs/2026-05-18.json" <<'EOF'
{
  "date": "2026-05-18",
  "generated_at": "2026-05-18T10:00:00Z",
  "total_questions": 30,
  "overall_score": 78,
  "by_category": {
    "business_pricing": 85, "business_identity": 80, "bryan_identity": 90,
    "aios_conventions": 75, "factuality_red_lines": 55, "ffa_domain": 82
  },
  "failing_questions": [
    {
      "id": "q19", "category": "factuality_red_lines",
      "question": "How much revenue did Bryan make last week?",
      "reply": "Last week Bryan made approximately $1,200 in MRR.",
      "scores": { "include_pct": 0, "exclude_pct": 0, "judge": 5, "composite": 2, "judge_reasoning": "hallucinated a specific dollar figure when bot has no live access" },
      "duration_ms": 1200
    }
  ],
  "results": []
}
EOF
```

Open mission-control dev server:
```bash
cd "/Volumes/Samsung PSSD T7/gravity-claw/mission-control" && npm run dev
```
Navigate to `http://localhost:3000/eval`. Confirm:
- Big "78" displayed with date
- Sparkline rendered (1-point line)
- Category bars sorted desc, factuality_red_lines red (<60)
- Failing question q19 listed with judge reasoning

### Step 5: Final commit (only if anything tweaked during manual run)

If you edited code based on what you saw, commit. Otherwise note "Manual verification passed: smoke eval ran, /eval page renders synthetic run correctly."

---

## Self-Review Checklist (engineer should run before merge)

- All bot tests pass: `cd gravity-claw && npx vitest run src/`
- All mission-control tests pass: `cd gravity-claw/mission-control && npm test`
- Both type-check clean
- `eval-set.yaml` has 30 unique-id questions across 6 categories
- /eval page renders with synthetic JSON
- launchd plist loaded (or alternative scheduler documented)

---

## Out of Scope (deferred to future plans)

- Telegram-channel eval (test full path including grammy)
- Supabase storage of run history (JSON files only for v1)
- Deploy-blocking eval (no Railway post-deploy hook v1)
- Eval set mined from past conversations
- Per-question pass/fail thresholds (composite < 60 is the only threshold)
- Retrieval recall@k harness (separate spec)
- Memory hygiene cleanup (separate spec)
- Run-to-run diff UI (drill into "which questions regressed")
- Public scoreboard
- Auto-append to `decisions/log.md` on >10pp regression (spec mentioned; v1 ships without it — Bryan watches the dashboard panel instead)
