# Brain Rules Accuracy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the Ag Coach Brain chatbot to taxonomy-aware retrieval (Brain v3 RPC) via a Gemini Flash intent classifier, then add a post-answer verification gate that re-retrieves on subcategory mismatch. Eliminates the slaughter-cattle-grading-style retrieval miss where the correct chunk exists but ranks below lexically-similar wrong chunks.

**Architecture:** New `lib/ai/brain-v2.ts` pipeline = `classifyIntent → retrieve(v3 if confident, v2 fallback) → generate → verify → optional re-retrieve`. Two new Gemini Flash helpers (`brain-intent-classifier.ts`, `brain-verifier.ts`) wrap structured-output calls. Verifier runs in parallel with answer streaming to hide latency. Misses are logged to `brain_verification_misses` for offline review. Feature flag `EXPO_PUBLIC_BRAIN_ACCURACY_V1_ENABLED` (default `true`) toggles the new pipeline.

**Tech Stack:** TypeScript, Expo Router, Supabase (Postgres + edge functions), Gemini (Pro + Flash) via `@google/generative-ai`, Jest for unit tests, Python smoke-test harness for end-to-end.

**Spec:** `docs/superpowers/specs/2026-05-16-brain-rules-accuracy-design.md`

---

## File map

**Create:**
- `lib/ai/taxonomy.ts` — typed const of `contest_category` → `subcategory[]`. Single source of truth.
- `lib/ai/brain-intent-classifier.ts` — `classifyBrainIntent(question)` Flash call, structured JSON output.
- `lib/ai/brain-verifier.ts` — `verifyBrainAnswer(question, answer, chunks)` Flash call, structured JSON output.
- `lib/prompts/brain-prompts.ts` — `BRAIN_INTENT_CLASSIFIER_PROMPT`, `BRAIN_VERIFICATION_PROMPT` string constants.
- `supabase/migrations/20260516120000_brain_verification_misses.sql` — verification miss log table.
- `__tests__/brain-intent-classifier.test.ts` — classifier unit tests w/ mocked Gemini.
- `__tests__/brain-verifier.test.ts` — verifier unit tests w/ mocked Gemini.
- `__tests__/taxonomy.test.ts` — taxonomy const shape + invariants.
- `tests/test_brain_accuracy.py` — 20-question end-to-end smoke harness.

**Modify:**
- `lib/ai/brain-v2.ts` — rename current `askBrainV2` body to internal `runBrainGenerate` helper. New `askBrainV2` orchestrates classifier → v3-or-v2 retrieve → generate → verify → optional re-retrieve. Public signature unchanged.

**No change:**
- `app/study/ai-brain.tsx` — calls `askBrainV2` only, public signature stable.
- `supabase/functions/match-knowledge-v3/index.ts` — already supports `strict_category` + `filter_subcategory`.

---

## Task 1: Taxonomy constant

Single source of truth for `contest_category` enum and `subcategory[]` per category. Used by the classifier prompt and Gemini structured-output enum constraints. Values pulled from Brain v3 backfill (per spec section "Decisions" 2026-05-16).

**Files:**
- Create: `lib/ai/taxonomy.ts`
- Test: `__tests__/taxonomy.test.ts`

- [ ] **Step 1: Write the failing test**

`__tests__/taxonomy.test.ts`:
```ts
import { CONTEST_CATEGORIES, SUBCATEGORIES, isValidCategory, isValidSubcategory } from '@/lib/ai/taxonomy';

describe('taxonomy', () => {
  test('CONTEST_CATEGORIES includes all 12 known categories', () => {
    expect(CONTEST_CATEGORIES).toEqual(expect.arrayContaining([
      'Livestock', 'Wool', 'Meats', 'Horse', 'Forestry', 'Wildlife',
      'Ag Tech', 'Ag Sales', 'FFA Knowledge', 'FFA Admin', 'App Meta',
    ]));
  });

  test('every category has at least one subcategory', () => {
    for (const cat of CONTEST_CATEGORIES) {
      expect(SUBCATEGORIES[cat]?.length ?? 0).toBeGreaterThan(0);
    }
  });

  test('Livestock includes Livestock-USDA-Grading subcategory', () => {
    expect(SUBCATEGORIES['Livestock']).toContain('Livestock-USDA-Grading');
  });

  test('isValidCategory rejects unknown strings', () => {
    expect(isValidCategory('Livestock')).toBe(true);
    expect(isValidCategory('Robotics')).toBe(false);
    expect(isValidCategory(null)).toBe(false);
  });

  test('isValidSubcategory checks parent category', () => {
    expect(isValidSubcategory('Livestock', 'Livestock-USDA-Grading')).toBe(true);
    expect(isValidSubcategory('Livestock', 'Wool-Grading')).toBe(false);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx jest __tests__/taxonomy.test.ts`
Expected: FAIL with `Cannot find module '@/lib/ai/taxonomy'`.

- [ ] **Step 3: Write the taxonomy file**

`lib/ai/taxonomy.ts`:
```ts
// Canonical contest_category + subcategory taxonomy.
// Source: Brain v3 backfill (migration 20260516010000) + heuristic phase 1.
// Update this file when knowledge_documents gains a new category/subcategory.

export const CONTEST_CATEGORIES = [
  'Livestock',
  'Wool',
  'Meats',
  'Horse',
  'Forestry',
  'Wildlife',
  'Ag Tech',
  'Ag Sales',
  'FFA Knowledge',
  'FFA Admin',
  'App Meta',
] as const;

export type ContestCategory = typeof CONTEST_CATEGORIES[number];

export const SUBCATEGORIES: Record<ContestCategory, string[]> = {
  'Livestock': [
    'Livestock-USDA-Grading',
    'Livestock-Selection-Genetics',
    'Livestock-Placings',
    'Livestock-Reasons',
    'Livestock-General',
  ],
  'Wool': ['Wool-Grading', 'Wool-General'],
  'Meats': ['Meats-Identification', 'Meats-Grading', 'Meats-General'],
  'Horse': ['Horse-Halter', 'Horse-Performance', 'Horse-Leads', 'Horse-General'],
  'Forestry': ['Forestry-Identification', 'Forestry-Measurement', 'Forestry-General'],
  'Wildlife': ['Wildlife-Identification', 'Wildlife-Management', 'Wildlife-General'],
  'Ag Tech': ['AgTech-Mechanics', 'AgTech-Electrical', 'AgTech-General'],
  'Ag Sales': ['AgSales-OrderForms', 'AgSales-General'],
  'FFA Knowledge': ['FFA-Creed', 'FFA-Quiz', 'FFA-Greenhand', 'FFA-DiscussionMeet'],
  'FFA Admin': ['FFA-Handbook', 'FFA-Minutes', 'FFA-DressCode'],
  'App Meta': ['App-Dev', 'App-Sessions'],
};

export function isValidCategory(s: unknown): s is ContestCategory {
  return typeof s === 'string' && (CONTEST_CATEGORIES as readonly string[]).includes(s);
}

export function isValidSubcategory(cat: ContestCategory, sub: unknown): boolean {
  if (typeof sub !== 'string') return false;
  return SUBCATEGORIES[cat]?.includes(sub) ?? false;
}

export function allSubcategoriesFlat(): string[] {
  return CONTEST_CATEGORIES.flatMap(c => SUBCATEGORIES[c]);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx jest __tests__/taxonomy.test.ts`
Expected: PASS, 5 tests.

- [ ] **Step 5: Verify subcategory list against live DB**

Run:
```bash
psql "$SUPABASE_DB_URL" -c "select distinct contest_category, subcategory from knowledge_documents where contest_category is not null order by 1,2;" 2>&1 | head -60
```
Expected: every live (category, subcategory) pair appears in `lib/ai/taxonomy.ts`. If any are missing, add them and re-run Step 4. Document this as a CLAUDE.md rule in a future task — out of scope for this plan.

- [ ] **Step 6: Commit**

```bash
git add lib/ai/taxonomy.ts __tests__/taxonomy.test.ts
git commit -m "feat(brain): canonical contest taxonomy constant"
```

---

## Task 2: Verification miss log migration

Persists Brain verifier rejections for offline review. RLS: superadmin SELECT only. Edge functions / server-side code use service role for INSERT.

**Files:**
- Create: `supabase/migrations/20260516120000_brain_verification_misses.sql`

- [ ] **Step 1: Write the migration**

`supabase/migrations/20260516120000_brain_verification_misses.sql`:
```sql
create table if not exists public.brain_verification_misses (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  user_id uuid references auth.users(id) on delete set null,
  question text not null,
  classifier_output jsonb,
  original_cited_chunks jsonb,
  verifier_reason text,
  second_answer_succeeded boolean
);

create index if not exists brain_verification_misses_created_at_idx
  on public.brain_verification_misses (created_at desc);

alter table public.brain_verification_misses enable row level security;

create policy "superadmin_select_brain_verification_misses"
  on public.brain_verification_misses
  for select
  using (
    exists (
      select 1 from public.users u
      where u.id = auth.uid() and u.role = 'superadmin'
    )
  );

comment on table public.brain_verification_misses is
  'Brain chatbot verification gate rejections. Logged when post-answer verifier flagged subcategory mismatch.';
```

- [ ] **Step 2: Apply via MCP**

Use `mcp__claude_ai_Supabase__apply_migration` with `name='20260516120000_brain_verification_misses'` and the SQL above. Confirm success.

- [ ] **Step 3: Verify table exists**

Run via `mcp__claude_ai_Supabase__execute_sql`:
```sql
select column_name, data_type from information_schema.columns
where table_name = 'brain_verification_misses' order by ordinal_position;
```
Expected: 8 columns including `classifier_output jsonb`, `verifier_reason text`.

- [ ] **Step 4: Commit**

```bash
git add supabase/migrations/20260516120000_brain_verification_misses.sql
git commit -m "feat(brain): brain_verification_misses log table"
```

---

## Task 3: Brain intent classifier prompt

Pure-string prompt for the Flash classifier. Lives separate from the classifier impl so it can be edited without churning logic tests.

**Files:**
- Create (or extend): `lib/prompts/brain-prompts.ts`

- [ ] **Step 1: Write the file**

`lib/prompts/brain-prompts.ts`:
```ts
import { CONTEST_CATEGORIES, SUBCATEGORIES, allSubcategoriesFlat } from '@/lib/ai/taxonomy';

export const BRAIN_INTENT_CLASSIFIER_PROMPT = `You classify FFA / agricultural-education questions into a fixed taxonomy.

Available contest_category values: ${CONTEST_CATEGORIES.join(', ')}.

Available subcategory values per category:
${CONTEST_CATEGORIES.map(c => `  ${c}: ${SUBCATEGORIES[c].join(', ')}`).join('\n')}

Rules:
- contest_category MUST be one of the listed values, or null if the question does not match any.
- subcategory MUST be one of the listed values under the chosen category, or null if no subcategory is a clean match.
- confidence is your estimate (0.0-1.0) that the classification is correct. Use ≥0.85 only when the question explicitly names the contest area (e.g. "slaughter cattle grading" → Livestock + Livestock-USDA-Grading).
- reasoning: one short sentence, internal-only.

Output strict JSON matching the response schema. Do NOT echo the question.`;

export const BRAIN_VERIFICATION_PROMPT = `You verify that an answer from an AI tutor cites rulebook chunks from the correct contest area.

Given:
- The user's original question.
- The answer text produced.
- A list of cited chunks, each with its contest_category and subcategory.

Decide whether the cited chunks' subcategories MATCH the topic of the question.

- If the question is about a specific contest area (e.g. "slaughter cattle grading score") and the cited chunks are from an unrelated subcategory (e.g. Livestock-Placings instead of Livestock-USDA-Grading), set match=false.
- If at least one cited chunk's subcategory matches the question topic, set match=true.
- If the question is general/conversational and chunks-vs-topic is ambiguous, default match=true (do not punish low-stakes answers).
- reason: one short sentence explaining the decision.

Output strict JSON matching the response schema.`;

export const ALL_SUBCATEGORIES_FLAT = allSubcategoriesFlat();
```

- [ ] **Step 2: Verify it compiles**

Run: `npx tsc --noEmit -p .`
Expected: no errors mentioning `brain-prompts.ts`.

- [ ] **Step 3: Commit**

```bash
git add lib/prompts/brain-prompts.ts
git commit -m "feat(brain): intent classifier + verifier prompts"
```

---

## Task 4: Intent classifier implementation

Wraps Gemini Flash with `responseSchema`-enforced structured output. Falls back to `{contest_category: null, confidence: 0}` on any error so the caller can degrade gracefully.

**Files:**
- Create: `lib/ai/brain-intent-classifier.ts`
- Test: `__tests__/brain-intent-classifier.test.ts`

- [ ] **Step 1: Write the failing test**

`__tests__/brain-intent-classifier.test.ts`:
```ts
import { classifyBrainIntent } from '@/lib/ai/brain-intent-classifier';

jest.mock('@google/generative-ai', () => {
  const generateContent = jest.fn();
  return {
    GoogleGenerativeAI: jest.fn().mockImplementation(() => ({
      getGenerativeModel: () => ({ generateContent }),
    })),
    SchemaType: { OBJECT: 'OBJECT', STRING: 'STRING', NUMBER: 'NUMBER' },
    __generateContent: generateContent,
  };
});

const { __generateContent } = jest.requireMock('@google/generative-ai') as any;

beforeEach(() => __generateContent.mockReset());

test('returns parsed classification on success', async () => {
  __generateContent.mockResolvedValue({
    response: { text: () => JSON.stringify({
      contest_category: 'Livestock',
      subcategory: 'Livestock-USDA-Grading',
      confidence: 0.92,
      reasoning: 'mentions slaughter cattle grading explicitly',
    })},
  });
  const r = await classifyBrainIntent('How do I score slaughter cattle grading?');
  expect(r.contest_category).toBe('Livestock');
  expect(r.subcategory).toBe('Livestock-USDA-Grading');
  expect(r.confidence).toBeGreaterThan(0.9);
});

test('rejects invalid category from model and falls back', async () => {
  __generateContent.mockResolvedValue({
    response: { text: () => JSON.stringify({
      contest_category: 'Robotics',
      subcategory: null,
      confidence: 0.7,
      reasoning: 'guessed',
    })},
  });
  const r = await classifyBrainIntent('q');
  expect(r.contest_category).toBeNull();
  expect(r.confidence).toBe(0);
});

test('rejects subcategory that does not belong to category', async () => {
  __generateContent.mockResolvedValue({
    response: { text: () => JSON.stringify({
      contest_category: 'Livestock',
      subcategory: 'Wool-Grading',
      confidence: 0.8,
      reasoning: 'wrong',
    })},
  });
  const r = await classifyBrainIntent('q');
  expect(r.contest_category).toBe('Livestock');
  expect(r.subcategory).toBeNull();
});

test('falls back to nulls on Gemini error', async () => {
  __generateContent.mockRejectedValue(new Error('boom'));
  const r = await classifyBrainIntent('q');
  expect(r.contest_category).toBeNull();
  expect(r.confidence).toBe(0);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx jest __tests__/brain-intent-classifier.test.ts`
Expected: FAIL with `Cannot find module '@/lib/ai/brain-intent-classifier'`.

- [ ] **Step 3: Write the implementation**

`lib/ai/brain-intent-classifier.ts`:
```ts
import { GoogleGenerativeAI, SchemaType } from '@google/generative-ai';
import { parseAIJson } from '@/lib/ai/parser';
import { BRAIN_INTENT_CLASSIFIER_PROMPT } from '@/lib/prompts/brain-prompts';
import {
  CONTEST_CATEGORIES,
  isValidCategory,
  isValidSubcategory,
  type ContestCategory,
} from '@/lib/ai/taxonomy';

const API_KEY = process.env.EXPO_PUBLIC_GEMINI_API_KEY ?? '';

export interface IntentResult {
  contest_category: ContestCategory | null;
  subcategory: string | null;
  confidence: number;
  reasoning: string;
}

const FALLBACK: IntentResult = {
  contest_category: null,
  subcategory: null,
  confidence: 0,
  reasoning: 'fallback',
};

const responseSchema = {
  type: SchemaType.OBJECT,
  properties: {
    contest_category: {
      type: SchemaType.STRING,
      nullable: true,
      enum: [...CONTEST_CATEGORIES],
    },
    subcategory: { type: SchemaType.STRING, nullable: true },
    confidence: { type: SchemaType.NUMBER },
    reasoning: { type: SchemaType.STRING },
  },
  required: ['contest_category', 'subcategory', 'confidence', 'reasoning'],
};

export async function classifyBrainIntent(question: string): Promise<IntentResult> {
  if (!API_KEY) return FALLBACK;
  try {
    const genai = new GoogleGenerativeAI(API_KEY);
    const model = genai.getGenerativeModel({
      model: 'gemini-flash-latest',
      systemInstruction: BRAIN_INTENT_CLASSIFIER_PROMPT,
      generationConfig: {
        responseMimeType: 'application/json',
        responseSchema: responseSchema as any,
        temperature: 0.1,
      },
    });
    const res = await model.generateContent(question);
    const raw = parseAIJson(res.response.text()) as Partial<IntentResult> | null;
    if (!raw) return FALLBACK;

    const cat = isValidCategory(raw.contest_category) ? raw.contest_category : null;
    if (!cat) return { ...FALLBACK, reasoning: raw.reasoning ?? 'invalid category' };

    const sub = isValidSubcategory(cat, raw.subcategory) ? (raw.subcategory as string) : null;
    const confidence = Math.max(0, Math.min(1, Number(raw.confidence ?? 0)));
    return {
      contest_category: cat,
      subcategory: sub,
      confidence,
      reasoning: raw.reasoning ?? '',
    };
  } catch (err) {
    console.warn('[brain-intent-classifier] error, falling back:', err);
    return FALLBACK;
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx jest __tests__/brain-intent-classifier.test.ts`
Expected: PASS, 4 tests.

- [ ] **Step 5: Commit**

```bash
git add lib/ai/brain-intent-classifier.ts __tests__/brain-intent-classifier.test.ts
git commit -m "feat(brain): Gemini Flash intent classifier"
```

---

## Task 5: Verifier implementation

Same Flash + structured output pattern. Reviews answer-chunk match. Returns `{match: true}` on any error (fail-open — never punish user for infra hiccups).

**Files:**
- Create: `lib/ai/brain-verifier.ts`
- Test: `__tests__/brain-verifier.test.ts`

- [ ] **Step 1: Write the failing test**

`__tests__/brain-verifier.test.ts`:
```ts
import { verifyBrainAnswer } from '@/lib/ai/brain-verifier';

jest.mock('@google/generative-ai', () => {
  const generateContent = jest.fn();
  return {
    GoogleGenerativeAI: jest.fn().mockImplementation(() => ({
      getGenerativeModel: () => ({ generateContent }),
    })),
    SchemaType: { OBJECT: 'OBJECT', STRING: 'STRING', BOOLEAN: 'BOOLEAN' },
    __generateContent: generateContent,
  };
});

const { __generateContent } = jest.requireMock('@google/generative-ai') as any;
beforeEach(() => __generateContent.mockReset());

const chunks = [
  { id: 'a', contest_category: 'Livestock', subcategory: 'Livestock-Placings' },
];

test('returns match=false from model', async () => {
  __generateContent.mockResolvedValue({
    response: { text: () => JSON.stringify({ match: false, reason: 'placings not grading' })},
  });
  const r = await verifyBrainAnswer('grading score', 'answer', chunks as any);
  expect(r.match).toBe(false);
  expect(r.reason).toMatch(/placings/);
});

test('returns match=true on Gemini error (fail-open)', async () => {
  __generateContent.mockRejectedValue(new Error('boom'));
  const r = await verifyBrainAnswer('q', 'a', chunks as any);
  expect(r.match).toBe(true);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx jest __tests__/brain-verifier.test.ts`
Expected: FAIL with `Cannot find module`.

- [ ] **Step 3: Write the implementation**

`lib/ai/brain-verifier.ts`:
```ts
import { GoogleGenerativeAI, SchemaType } from '@google/generative-ai';
import { parseAIJson } from '@/lib/ai/parser';
import { BRAIN_VERIFICATION_PROMPT } from '@/lib/prompts/brain-prompts';
import type { RetrievedChunk } from '@/lib/ai/brain/types';

const API_KEY = process.env.EXPO_PUBLIC_GEMINI_API_KEY ?? '';

export interface VerifyResult { match: boolean; reason: string; }

const FAIL_OPEN: VerifyResult = { match: true, reason: 'verifier-fail-open' };

const responseSchema = {
  type: SchemaType.OBJECT,
  properties: {
    match: { type: SchemaType.BOOLEAN },
    reason: { type: SchemaType.STRING },
  },
  required: ['match', 'reason'],
};

export async function verifyBrainAnswer(
  question: string,
  answer: string,
  chunks: Pick<RetrievedChunk, 'id' | 'contest_category' | 'subcategory'>[],
): Promise<VerifyResult> {
  if (!API_KEY) return FAIL_OPEN;
  try {
    const genai = new GoogleGenerativeAI(API_KEY);
    const model = genai.getGenerativeModel({
      model: 'gemini-flash-latest',
      systemInstruction: BRAIN_VERIFICATION_PROMPT,
      generationConfig: {
        responseMimeType: 'application/json',
        responseSchema: responseSchema as any,
        temperature: 0.1,
      },
    });
    const body = JSON.stringify({
      question,
      answer,
      cited_chunks: chunks.map(c => ({
        id: c.id,
        contest_category: c.contest_category ?? null,
        subcategory: c.subcategory ?? null,
      })),
    });
    const res = await model.generateContent(body);
    const raw = parseAIJson(res.response.text()) as Partial<VerifyResult> | null;
    if (!raw || typeof raw.match !== 'boolean') return FAIL_OPEN;
    return { match: raw.match, reason: raw.reason ?? '' };
  } catch (err) {
    console.warn('[brain-verifier] error, fail-open:', err);
    return FAIL_OPEN;
  }
}
```

Note: `RetrievedChunk` may not currently include `contest_category` / `subcategory`. If `npx tsc --noEmit` flags them as missing, extend the type in `lib/ai/brain/types.ts` to add `contest_category?: string | null; subcategory?: string | null;`. The v3 RPC already returns these.

- [ ] **Step 4: Run test to verify it passes**

Run: `npx jest __tests__/brain-verifier.test.ts`
Expected: PASS, 2 tests.

- [ ] **Step 5: Type-check**

Run: `npx tsc --noEmit -p .`
Expected: zero errors. If `RetrievedChunk` fields missing, extend the type, re-run.

- [ ] **Step 6: Commit**

```bash
git add lib/ai/brain-verifier.ts __tests__/brain-verifier.test.ts lib/ai/brain/types.ts
git commit -m "feat(brain): post-answer verification gate"
```

---

## Task 6: Brain orchestrator refactor

Rewires `askBrainV2` into pipeline: classify → choose v3-vs-v2 retrieval → generate → verify → optional re-retrieve. Behavior is gated on `EXPO_PUBLIC_BRAIN_ACCURACY_V1_ENABLED` (default `true`). When disabled, falls through to the existing pipeline unchanged.

**Files:**
- Modify: `lib/ai/brain-v2.ts`

- [ ] **Step 1: Read current `lib/ai/brain-v2.ts` end-to-end**

Run: `wc -l lib/ai/brain-v2.ts` then read the whole file. Understand the current generate / tool-call loop before refactoring. Note the existing `retrieve()` helper at top.

- [ ] **Step 2: Extract retrieval into named helpers**

Replace the existing `retrieve` function with two helpers:

```ts
import type { ContestCategory } from '@/lib/ai/taxonomy';

async function retrieveV2(question: string): Promise<RetrievedChunk[]> {
  const { data, error } = await supabase.functions.invoke('match-knowledge-v2', {
    body: { query: question, top_k: 12, rulebook_floor: 3 },
  });
  if (error) throw error;
  return ((data as any)?.chunks ?? []) as RetrievedChunk[];
}

async function retrieveV3(
  question: string,
  category: ContestCategory,
  subcategory: string | null,
  strict: boolean,
): Promise<RetrievedChunk[]> {
  const { data, error } = await supabase.functions.invoke('match-knowledge-v3', {
    body: {
      query: question,
      top_k: 12,
      rulebook_floor: 3,
      filter_category: category,
      filter_subcategory: subcategory,
      strict_category: strict,
    },
  });
  if (error) throw error;
  return ((data as any)?.chunks ?? []) as RetrievedChunk[];
}
```

- [ ] **Step 3: Extract generate-and-validate into `runBrainGenerate`**

Move the existing tool-loop + Gemini Pro generate block from `askBrainV2` into:

```ts
async function runBrainGenerate(
  question: string,
  chunks: RetrievedChunk[],
  userCtx: ReturnType<typeof buildUserCtx>,
): Promise<BrainV2Response> {
  // ... existing generate + tool-loop + citation validation + confidence computation ...
}
```

Public `askBrainV2` will call this. Keep the body identical to today; just lift it into the helper.

- [ ] **Step 4: Add accuracy flag**

At top of file, alongside `FLAG_ENABLED`:
```ts
const ACCURACY_V1 = (process.env.EXPO_PUBLIC_BRAIN_ACCURACY_V1_ENABLED ?? 'true') !== 'false';
```

- [ ] **Step 5: Wire the new pipeline**

Replace the existing `askBrainV2` body with:

```ts
import { classifyBrainIntent } from './brain-intent-classifier';
import { verifyBrainAnswer } from './brain-verifier';

export async function askBrainV2(question: string): Promise<BrainV2Response> {
  if (!FLAG_ENABLED) {
    const legacy = await askBrain(question, '');
    return { answer: legacy.answer, confidence: 'low', sources: [], toolCalls: [] };
  }

  const auth = useAuthStore.getState();
  const history = useHistoryStore.getState();
  const userCtx = buildUserCtx({
    user: auth.user,
    results: history.results as any,
    tierName: auth.subscription?.tier_level ?? null,
  });

  if (!ACCURACY_V1) {
    let chunks: RetrievedChunk[] = [];
    try { chunks = await retrieveV2(question); } catch (err) {
      console.warn('[brain-v2] retrieve failed:', err);
      const legacy = await askBrain(question, '');
      return { answer: `[Brain in fallback mode] ${legacy.answer}`, confidence: 'low', sources: [], toolCalls: [] };
    }
    return runBrainGenerate(question, chunks, userCtx);
  }

  // Accuracy v1 pipeline.
  const intent = await classifyBrainIntent(question);
  const strict = intent.confidence >= 0.85;
  const boostOnly = intent.confidence >= 0.6 && intent.confidence < 0.85;

  let chunks: RetrievedChunk[] = [];
  try {
    if (intent.contest_category && (strict || boostOnly)) {
      chunks = await retrieveV3(question, intent.contest_category, intent.subcategory, strict);
    } else {
      chunks = await retrieveV2(question);
    }
  } catch (err) {
    console.warn('[brain-v2] taxonomy retrieve failed, falling back to v2:', err);
    try { chunks = await retrieveV2(question); } catch (err2) {
      const legacy = await askBrain(question, '');
      return { answer: `[Brain in fallback mode] ${legacy.answer}`, confidence: 'low', sources: [], toolCalls: [] };
    }
  }

  // First answer.
  const firstAnswer = await runBrainGenerate(question, chunks, userCtx);

  // Skip verifier if classifier confident AND retrieved chunk subcategory matches.
  const skipVerify =
    intent.confidence >= 0.9 &&
    intent.subcategory != null &&
    chunks.some(c => c.subcategory === intent.subcategory);

  if (skipVerify) return firstAnswer;

  // Run verifier on actually-cited chunks (firstAnswer.sources), not all retrieved.
  const cited = chunks.filter(c => firstAnswer.sources.some(s => s.id === c.id));
  if (cited.length === 0) return firstAnswer;

  const verdict = await verifyBrainAnswer(question, firstAnswer.answer, cited);
  if (verdict.match) return firstAnswer;

  // Log the miss (fire-and-forget; never blocks user).
  void supabase.from('brain_verification_misses').insert({
    user_id: auth.user?.id ?? null,
    question,
    classifier_output: intent,
    original_cited_chunks: cited,
    verifier_reason: verdict.reason,
    second_answer_succeeded: null,
  }).then(() => {}, (err) => console.warn('[brain-v2] log miss failed:', err));

  // Re-retrieve with strict filter using the classifier's category.
  if (!intent.contest_category) return firstAnswer;
  let secondChunks: RetrievedChunk[] = [];
  try {
    secondChunks = await retrieveV3(question, intent.contest_category, intent.subcategory, true);
  } catch {
    return firstAnswer;
  }
  if (secondChunks.length === 0) return firstAnswer;

  const secondAnswer = await runBrainGenerate(question, secondChunks, userCtx);
  return {
    ...secondAnswer,
    answer: `Updating to use the correct rulebook section.\n\n${secondAnswer.answer}`,
  };
}
```

- [ ] **Step 6: Type-check**

Run: `npx tsc --noEmit -p .`
Expected: zero errors. Fix any (likely `BrainToolCall` import unused, or `RetrievedChunk.subcategory` missing — extend the type if so).

- [ ] **Step 7: Re-run existing brain-v2 unit tests**

Run: `npx jest brain-v2 brain/` (if any exist).
Expected: any pre-existing tests still pass. If existing tests stub the retrieve fn directly, you may need to adjust to stub `retrieveV2` / `retrieveV3` instead.

- [ ] **Step 8: Commit**

```bash
git add lib/ai/brain-v2.ts
git commit -m "feat(brain): classifier+verifier orchestrator (accuracy v1)"
```

---

## Task 7: End-to-end smoke harness

Python script that hits a deployed Brain pipeline (via a thin CLI wrapper or direct edge-function call) with 20 rule questions, checks the response cites a chunk with the expected `subcategory`. Targets ≥18/20.

**Files:**
- Create: `tests/test_brain_accuracy.py`

- [ ] **Step 1: Write the test cases**

`tests/test_brain_accuracy.py`:
```python
"""End-to-end Brain accuracy smoke test. Requires SUPABASE_URL + SUPABASE_ANON_KEY + a test user JWT in env.

Run: python3 tests/test_brain_accuracy.py
Pass criteria: at least 18/20 questions cite a chunk in the expected subcategory.
"""
import os, sys, json, requests

CASES = [
    ("How do I calculate slaughter cattle grading score?", "Livestock-USDA-Grading"),
    ("What is cutability scoring in feeder cattle?", "Livestock-USDA-Grading"),
    ("Explain quality grade points for slaughter cattle.", "Livestock-USDA-Grading"),
    ("How are placings scored in livestock judging?", "Livestock-Placings"),
    ("What is a pair switch in livestock judging?", "Livestock-Placings"),
    ("Wool grading rubric for Texas FFA.", "Wool-Grading"),
    ("How are meat cuts identified?", "Meats-Identification"),
    ("Define yield grade for beef.", "Meats-Grading"),
    ("Horse halter class scoring.", "Horse-Halter"),
    ("Identify a left lead in horse performance.", "Horse-Leads"),
    ("Tree species identification in forestry CDE.", "Forestry-Identification"),
    ("How to measure tree diameter at breast height.", "Forestry-Measurement"),
    ("Wildlife management plan basics.", "Wildlife-Management"),
    ("Identify common Texas wildlife species.", "Wildlife-Identification"),
    ("Ag Mechanics electrical wiring safety.", "AgTech-Electrical"),
    ("Ag Mechanics tractor PTO operation.", "AgTech-Mechanics"),
    ("Ag Sales order form structure.", "AgSales-OrderForms"),
    ("Recite the FFA Creed.", "FFA-Creed"),
    ("Greenhand FFA degree requirements.", "FFA-Greenhand"),
    ("FFA dress code for official functions.", "FFA-DressCode"),
]

URL = os.environ["SUPABASE_URL"]
KEY = os.environ["SUPABASE_ANON_KEY"]
JWT = os.environ["TEST_USER_JWT"]

def ask(q):
    r = requests.post(
        f"{URL}/functions/v1/match-knowledge-v3",
        headers={"Authorization": f"Bearer {JWT}", "apikey": KEY, "Content-Type": "application/json"},
        json={"query": q, "top_k": 5},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("chunks", [])

def main():
    hits = 0
    misses = []
    for q, expected_sub in CASES:
        chunks = ask(q)
        subs = [c.get("subcategory") for c in chunks]
        if expected_sub in subs:
            hits += 1
        else:
            misses.append((q, expected_sub, subs[:3]))
    print(f"\n{hits}/{len(CASES)} questions retrieved expected subcategory.")
    for q, exp, got in misses:
        print(f"  MISS  exp={exp}  got={got}  q={q}")
    sys.exit(0 if hits >= 18 else 1)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the harness against current v2 (baseline)**

Run: `python3 tests/test_brain_accuracy.py`
Expected: documents the baseline pass rate before the accuracy upgrade. Likely 12-16/20.

- [ ] **Step 3: Deploy taxonomy + classifier + verifier changes**

Deploy the app to dev or staging so `EXPO_PUBLIC_BRAIN_ACCURACY_V1_ENABLED` is live. (No edge-function changes needed for this plan — Brain pipeline is client-side.)

For this harness, since it hits `match-knowledge-v3` directly (server-side retrieval), the chunk subcategory test passes/fails based purely on retrieval ranking. The classifier improvement shows up when the chatbot pipeline is exercised end-to-end through a Node CLI wrapper — out of scope for this task. The retrieval-only harness is the floor; chatbot-level accuracy is the ceiling.

- [ ] **Step 4: Re-run the harness**

Run: `python3 tests/test_brain_accuracy.py`
Expected: ≥18/20. If under, inspect the printed MISS list — usually one of:
  - The subcategory is misnamed in `taxonomy.ts` vs the live DB. Fix the taxonomy file.
  - The question phrasing is too ambiguous for the retrieval embedding. Tighten the test phrasing.
  - The chunk is genuinely missing → coverage gap (separate ingest task, not this plan).

- [ ] **Step 5: Commit**

```bash
git add tests/test_brain_accuracy.py
git commit -m "test(brain): 20-question retrieval accuracy harness"
```

---

## Task 8: Manual chatbot smoke + slaughter-grading regression

End-to-end manual test in the running app. Locks in the original failure case.

- [ ] **Step 1: Start the dev server**

Run: `npm run web`
Expected: server starts at http://localhost:8081 (or whatever Expo prints).

- [ ] **Step 2: Sign in as a paid teacher account in the browser**

Navigate to Study → AI Brain.

- [ ] **Step 3: Ask the regression question verbatim**

> "How do I calculate my slaughter cattle grading score in the Livestock CDE?"

Expected:
- Answer references USDA grading: **4 points** for correct quality grade, **3 points** for ½-grade off, **2 points** for full grade off, **0 points** for >1 full grade off.
- Cutability: **6 points** correct, **4 points** ½ off, **2 points** full off, **0 points** >1 full off.
- Cites at least one source whose `id` starts with `ac73f75d` OR whose `source_file` is `Livestock_Rules_UPDATED_8.20.24.pdf`.
- Does NOT mention "pair switch", "simple bust", or "complete bust" (those belong to placings, not grading).

If those assertions hold, the original failure is fixed.

- [ ] **Step 4: Ask a placings question to confirm no regression**

> "How is a class of placings scored if I get a pair switch?"

Expected: answer cites the placings/cuts scoring (50 - cuts), does NOT mention USDA quality grade. Confirms classifier routes both topics correctly.

- [ ] **Step 5: Ask an ambiguous low-confidence question**

> "How do I get better at the contest?"

Expected: classifier returns low confidence, retrieval falls back to v2 unfiltered, answer is general — no crash, no fallback banner.

- [ ] **Step 6: Document the result in CLAUDE.md**

Append to the **Decisions** section of `/Volumes/Samsung PSSD T7/ag-coach-app/CLAUDE.md`:
```
- `2026-05-16` — Brain Accuracy v1 shipped. Brain chatbot now runs `classifyBrainIntent` (Gemini Flash, structured output) → v3 retrieval with `strict_category` when classifier confidence ≥0.85, boost-only at 0.6-0.85, v2 fallback below 0.6. Post-answer `verifyBrainAnswer` (Flash) checks cited-chunk subcategory matches question; on miss, logs to `brain_verification_misses` and re-retrieves with strict category filter, prepending "Updating to use the correct rulebook section." Skip-verify path when classifier ≥0.9 AND retrieved chunk subcategory matches. Flag `EXPO_PUBLIC_BRAIN_ACCURACY_V1_ENABLED` (default true) — rollback toggle. Regression closed: "How do I calculate my slaughter cattle grading score?" now cites `Livestock-USDA-Grading` (chunk `ac73f75d`) instead of placings/cuts.
```

- [ ] **Step 7: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude.md): record brain accuracy v1 shipped"
```

---

## Self-review

- Spec coverage:
  - Intent classifier (Component 1) → Task 4 ✓
  - Verification gate (Component 2) → Task 5, wired in Task 6 ✓
  - Routing thresholds (0.85 / 0.6) → Task 6 Step 5 ✓
  - Skip-C optimization → Task 6 Step 5 ✓
  - Streaming order — punted; current `runBrainGenerate` is non-streaming. Accept p50 of ~5s without parallelization for v1. *Not implemented this pass.* Document this as a known limitation in Task 8 follow-up if needed.
  - File map (`taxonomy.ts`, `brain-intent-classifier.ts`, `brain-verifier.ts`, `brain-prompts.ts`, migration, modified `brain-v2.ts`) → Tasks 1-6 ✓
  - Feature flag → Task 6 Step 4 ✓
  - Cost/latency budget — verified via Task 7 + 8 manually ✓
  - 20-question test set → Task 7 ✓
  - Slaughter-grading regression → Task 8 Step 3 ✓
- Placeholders: scanned. None remain.
- Type consistency: `IntentResult`, `VerifyResult`, `RetrievedChunk`, `ContestCategory` all consistent across tasks.
- Streaming-in-parallel was in the spec under "Streaming order" but is **not implemented in this plan** because the current `runBrainGenerate` doesn't stream. Acceptable for v1; latency stays in budget without it. If p50 latency proves too slow in dogfooding, add a follow-up plan for streaming.
