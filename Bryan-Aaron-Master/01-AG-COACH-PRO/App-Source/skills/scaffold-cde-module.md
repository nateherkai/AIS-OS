# Skill: Scaffold CDE Practice Module

## Purpose

Scaffold a **complete CDE practice module** — all 4 screens, the quiz lib file, and all 6 integration points — from the canonical forages template. Runs the full 10-step checklist from CLAUDE.md in one shot.

Use this whenever you need to build a new module from scratch or finish a stub that is missing builder/quiz/flashcards.

---

## Inputs Required from User

Collect these before writing any files:

| Field | Example | Notes |
|---|---|---|
| `MODULE_NAME` | `dairy-cattle` | Route folder name under `app/practice/` and key in `FEATURE_TIERS` |
| `DISPLAY_TITLE` | `Dairy Cattle Evaluation CDE` | Shown in page headers and Stack.Screen titles |
| `LEGACY_ID` | `cde-dairy` | The `legacyId` used in `app/contest/[id].tsx` routing checks |
| `TIER` | `The Blue & Gold` | Must be one of: `The Greenhand`, `The Blue & Gold`, `The Lone Star Elite` |
| `PRACTICE_TYPE` | `dairy-cattle` | Added to `PracticeType` union in `lib/store/history.ts` |
| `ACCENT_COLOR` | `#00f2ff` | Hex — the neon highlight color for this module's UI |
| `ICON` | `medical-outline` | Any valid Ionicons name |
| `TOPICS` | `['Breeds & Type', 'Dairy Character', ...]` | Array of topic strings used as QUIZ_SOURCES |
| `TOPIC_QUERIES` | `{ 'Breeds & Type': 'holstein guernsey jersey ayrshire breed identification dairy...' }` | Semantic retrieval query per topic |
| `CONTEST_FORMAT` | `[{ name: 'Breeds & Type', count: 10 }, ...]` | Topic name + MC question count — must sum to the official total |
| `CONTEST_TOTAL` | `40` | Official total MC questions for the contest exam |
| `RESOURCE_NOTE` | `2026 Dairy Cattle CDE Resource` | Source PDF description shown in loading screen |

---

## Step 1 — Create `lib/[MODULE_NAME]-quiz.ts`

Copy the forages pattern exactly. Substitute module-specific values.

```typescript
/**
 * [MODULE_NAME]-quiz.ts
 *
 * RAG-powered quiz generation for the Texas FFA [DISPLAY_TITLE].
 * PREREQUISITE: Ingest source PDF via ingest_knowledge.py with
 * contest_category = "[DISPLAY_TITLE]" before use.
 */

import { generateRAGBatch } from './ai/rag-quiz';
import type { QuizQuestion } from '@/lib/senior-quiz';

export type { QuizQuestion };

export const QUIZ_SOURCES = [
  /* paste TOPICS array here */
] as const;

export type QuizSource = typeof QUIZ_SOURCES[number];

export interface QuizSettings {
  topics: QuizSource[];
  questionCount: number;
  type: 'mixed' | 'multiple_choice' | 'true_false';
  isMock: boolean;
}

const CONTEST_SOURCES: Array<{ name: QuizSource; count: number }> = [
  /* paste CONTEST_FORMAT here */
];

export async function generate[PascalCase]Quiz(settings: QuizSettings): Promise<QuizQuestion[]> {
  if (settings.isMock) return generateContestExam();
  return generateCustomQuiz(settings);
}

async function generateContestExam(): Promise<QuizQuestion[]> {
  const allQuestions: QuizQuestion[] = [];
  const CHUNK = 2;
  for (let i = 0; i < CONTEST_SOURCES.length; i += CHUNK) {
    const chunk = CONTEST_SOURCES.slice(i, i + CHUNK);
    const results = await Promise.all(
      chunk.map(src => generateRAGBatch(src.name, 'multiple_choice', src.count, 'senior'))
    );
    results.forEach(r => allQuestions.push(...r));
    if (i + CHUNK < CONTEST_SOURCES.length) await new Promise(r => setTimeout(r, 800));
  }
  return allQuestions.map((q, i) => ({ ...q, id: `q-[MODULE_NAME]-mock-${Date.now()}-${i}` }));
}

async function generateCustomQuiz(settings: QuizSettings): Promise<QuizQuestion[]> {
  const perTopic = Math.ceil(settings.questionCount / settings.topics.length);
  const allQuestions: QuizQuestion[] = [];
  for (const topic of settings.topics) {
    if (settings.type === 'mixed') {
      const tfCount = Math.floor(perTopic / 2);
      const mcCount = perTopic - tfCount;
      const [tf, mc] = await Promise.all([
        generateRAGBatch(topic, 'true_false', tfCount, 'senior'),
        generateRAGBatch(topic, 'multiple_choice', mcCount, 'senior'),
      ]);
      allQuestions.push(...tf, ...mc);
    } else {
      allQuestions.push(...await generateRAGBatch(topic, settings.type, perTopic, 'senior'));
    }
    if (settings.topics.indexOf(topic) < settings.topics.length - 1)
      await new Promise(r => setTimeout(r, 400));
  }
  return allQuestions.map((q, i) => ({ ...q, id: `q-[MODULE_NAME]-${Date.now()}-${i}` }));
}

export async function generate[PascalCase]Flashcards(
  topic: QuizSource,
  count: number = 15,
): Promise<QuizQuestion[]> {
  const qs = await generateRAGBatch(topic, 'multiple_choice', count, 'senior');
  return qs.map((q, i) => ({ ...q, id: `q-[MODULE_NAME]-fc-${Date.now()}-${i}` }));
}
```

---

## Step 2 — Create `app/practice/[MODULE_NAME]/index.tsx`

Hub screen. Three sections: Contest Hub, Study & Practice, (optional) Specimen ID.

**Key substitutions from the forages template:**
- Replace all `forages` / `Forages` with `[MODULE_NAME]` / `[DISPLAY_TITLE]`
- Replace `CHAPTERS` array with the module's CONTEST_FORMAT (name, mcCount, color)
- Replace `Ionicons name="leaf-outline"` with the module's `ICON`
- Replace NEON_GREEN page header color with `ACCENT_COLOR`
- Replace `contestCTA` backgroundColor with `ACCENT_COLOR` or `GOLD`
- Replace quiz `pathname` with `/practice/[MODULE_NAME]/quiz`
- Replace builder `pathname` with `/practice/[MODULE_NAME]/builder`
- If no Specimen ID sub-module, omit that section
- Update `useFeatureEngagement('[DISPLAY_TITLE]')`
- Update `Stack.Screen title` to `'[DISPLAY_TITLE]'`

Copy the full styles block from forages — they are generic and need no changes.

---

## Step 3 — Create `app/practice/[MODULE_NAME]/builder.tsx`

Topic/count/format pickers. Launches quiz with settings.

**Key substitutions from the forages template:**
- Import from `@/lib/[MODULE_NAME]-quiz` instead of `@/lib/forages-quiz`
- Replace `CHAPTER_COLORS` record with `Record<QuizSource, string>` using TOPICS and their colors
- Replace default `selectedTopics` state to reflect all TOPICS as `true`
- Replace `router.push` pathname with `/practice/[MODULE_NAME]/quiz`
- Replace `headerBackTitle` with `'[DISPLAY_TITLE]'`
- Replace `startBtn` color with `ACCENT_COLOR`

---

## Step 4 — Create `app/practice/[MODULE_NAME]/quiz.tsx`

Live quiz engine. Scores + records to history.

**Key substitutions from the forages template:**
- Import from `@/lib/[MODULE_NAME]-quiz`
- Replace `generateForagesQuiz` with `generate[PascalCase]Quiz`
- Replace `CHAPTER_COLORS` record with module-specific topic→color map
- In `finishQuiz()`: change `type: 'forages-quiz'` to `type: '[PRACTICE_TYPE]'`
- Replace loading icon: `Ionicons name="leaf-outline"` → module's `ICON`
- Replace loading `color={NEON_GREEN}` → `color={ACCENT_COLOR}`
- Replace `safeBack(router, '/practice/forages')` → `safeBack(router, '/practice/[MODULE_NAME]')`
- Replace PDF note in `subLoadingText` with `RESOURCE_NOTE`
- Replace `Stack.Screen title` with `'[DISPLAY_TITLE] Quiz'`

---

## Step 5 — Create `app/practice/[MODULE_NAME]/flashcards.tsx`

Flashcard mode with flip animation, Got It / Study More tracking.

**Key substitutions from the forages template:**
- Import from `@/lib/[MODULE_NAME]-quiz`
- Replace `generateForagesFlashcards` with `generate[PascalCase]Flashcards`
- Replace `QUIZ_SOURCES` with the module's sources
- Replace `CHAPTER_INFO` array with topic name, color, icon, and desc for each TOPIC
- Replace `headerBackTitle` with `'[DISPLAY_TITLE]'`
- Replace `safeBack(router, '/practice/forages')` → `safeBack(router, '/practice/[MODULE_NAME]')`
- Replace PDF note in Alert with RESOURCE_NOTE

---

## Step 6 — Register PracticeType in `lib/store/history.ts`

Add `'[PRACTICE_TYPE]'` to the `PracticeType` union (lines 5–35):

```typescript
export type PracticeType =
  | 'job-interview'
  // ... existing entries ...
  | '[PRACTICE_TYPE]';   // ← ADD THIS
```

---

## Step 7 — Add routing block in `app/contest/[id].tsx`

Add an `if`-block in `startPractice()` before the final fallback. Pattern:

```typescript
// [DISPLAY_TITLE]
if (legacyId === '[LEGACY_ID]' || nameLower.includes('[keyword]')) {
    router.push('/practice/[MODULE_NAME]' as any);
    return;
}
```

Place it in alphabetical/logical order with similar CDEs. Check what `legacyId` the contest has by looking at `constants/contests.ts` — the `id` field on the contest object.

---

## Step 8 — Add tier mapping in `lib/tier.ts`

In `FEATURE_TIERS`, add:

```typescript
'[MODULE_NAME]': '[TIER]',
```

Place it under the appropriate tier comment block.

---

## Step 9 — Verify `is_active` in `constants/contests.ts`

Find the contest with `legacyId === '[LEGACY_ID]'` and confirm `is_active: true`. If it is `false`, change it:

```typescript
{ ..., is_active: true }
```

---

## Step 10 — Add TOPIC_QUERIES in `lib/ai/rag-quiz.ts`

In the `TOPIC_QUERIES` record, add one entry per topic:

```typescript
// ── [DISPLAY_TITLE] ──────────────────────────────────────────────────────────
'[Topic 1]': '[semantic query string with key terms from the PDF]',
'[Topic 2]': '[semantic query string]',
// ...
```

Place it with related CDEs. The query string should use 10–20 keywords from the PDF that a vector search would reliably match.

---

## Execution Order

Always do steps in this order to avoid TypeScript errors during the build:

1. `lib/[MODULE_NAME]-quiz.ts` (defines types used by screens)
2. `lib/store/history.ts` (adds PracticeType)
3. `lib/tier.ts` (adds feature key)
4. `lib/ai/rag-quiz.ts` (adds TOPIC_QUERIES)
5. `app/practice/[MODULE_NAME]/index.tsx`
6. `app/practice/[MODULE_NAME]/builder.tsx`
7. `app/practice/[MODULE_NAME]/quiz.tsx`
8. `app/practice/[MODULE_NAME]/flashcards.tsx`
9. `app/contest/[id].tsx` (add routing block)
10. `constants/contests.ts` (confirm is_active)

---

## Verification Checklist

After scaffolding, verify end-to-end:

1. `npm run web` — confirm no TypeScript errors
2. Open CDE tab → find the contest → tap **Practice**
3. Confirm it routes to `/practice/[MODULE_NAME]` (not a fallback)
4. Tap **START OFFICIAL CONTEST EXAM** — confirm loading screen appears
5. Wait for questions — confirm quiz runs and scores
6. Finish quiz — confirm score recorded in history (check Profile → History)
7. Tap **Study Mode** → confirm builder screen loads
8. Build a custom quiz — confirm it generates
9. Tap **Flashcard Mode** → pick a topic → confirm cards generate and flip

---

## Reference Files

| File | Purpose |
|---|---|
| `app/practice/forages/index.tsx` | Hub screen template |
| `app/practice/forages/builder.tsx` | Builder template |
| `app/practice/forages/quiz.tsx` | Quiz engine template |
| `app/practice/forages/flashcards.tsx` | Flashcard template |
| `lib/forages-quiz.ts` | Quiz lib template |
| `lib/store/history.ts` | PracticeType union |
| `lib/tier.ts` | FEATURE_TIERS |
| `lib/ai/rag-quiz.ts` | TOPIC_QUERIES |
| `app/contest/[id].tsx` | Routing if-blocks |
| `constants/contests.ts` | Contest is_active flags |

---

## Common Mistakes to Avoid

- **Do not** use `router.back()` anywhere — always use `safeBack(router, '/practice/[MODULE_NAME]')`
- **Do not** import `Theme` or `GlassEffect` — the forages screens use inline `StyleSheet.create` with the dark glass constants
- **Do not** skip adding TOPIC_QUERIES — quiz generation silently returns empty arrays without it
- **Do not** forget `as any` on `router.push` for screens not in the typed route list
- **PracticeType must match exactly** what is passed to `addResult({ type: '...' })` in quiz.tsx
