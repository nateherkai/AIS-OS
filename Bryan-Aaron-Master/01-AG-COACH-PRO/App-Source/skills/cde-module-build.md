# Skill: CDE Module Build

## Purpose

Consolidation of `scaffold-cde-module` + `complete-stub-module`. One skill, two modes:

- `--scaffold` → directory absent, build all 4 screens + lib + 6 integrations from forages template
- `--complete` → `index.tsx` exists but routes to generic stub, replace with RAG-backed screens

---

## When to Use

Run `module-readiness` skill first. Use its decision column:

- State **missing** → mode `--scaffold`
- State **stub** → mode `--complete`

---

## Inputs

- `<module-slug>` (kebab, matches directory name)
- `<contest-category>` (matches `FOLDER_TO_CATEGORY` in ingest)
- `<display-name>` (UI label)
- `<tier>` (greenhand | blue-and-gold | lone-star-elite)

---

## Mode: --scaffold

Reference template: `app/practice/forages/` + `lib/forages-quiz.ts` + `lib/prompts/` (if domain prompts exist).

### Files to create

```
app/practice/<slug>/
  index.tsx       ← Hub: Contest Hub + Study + Flashcards
  builder.tsx     ← Topic/count/format pickers
  quiz.tsx        ← Quiz engine (RAG-backed)
  flashcards.tsx  ← Flip cards

lib/<slug>-quiz.ts             ← generateXxxQuiz, generateXxxFlashcards wrapping generateRAGBatch
lib/prompts/<slug>-prompts.ts  ← optional, if module has specialized prompts
```

### Procedure

1. Copy `app/practice/forages/` → `app/practice/<slug>/`
2. Copy `lib/forages-quiz.ts` → `lib/<slug>-quiz.ts`
3. Rename symbols: `generateForagesQuiz` → `generate<Slug>Quiz`, same for flashcards
4. Replace `contest_category` filter literal
5. Update `QUIZ_SOURCES`, `QuizSettings` for module's topic list
6. Add entries to `TOPIC_QUERIES` in `lib/ai/rag-quiz.ts`
7. Run `tier-feature-register` skill → handles the 4-file integration checklist
8. Type check: `npx tsc --noEmit -p .`

### RAG prerequisite

Before scaffolding, run `rag-coverage-report` (or `module-readiness`) — confirm category has chunks. If 0 → `pdf-to-rag` first.

---

## Mode: --complete

`index.tsx` exists. Currently routes to `/practice/study` or `/practice/test` (generic placeholder).

### Procedure

1. Read existing `app/practice/<slug>/index.tsx` — identify the topic list / sources it knows about
2. Create `builder.tsx`, `quiz.tsx`, `flashcards.tsx` from forages template (same as scaffold)
3. Create `lib/<slug>-quiz.ts`
4. Replace stub routing in `index.tsx`:
   ```diff
   -onPress={() => router.push('/practice/study')}
   +onPress={() => router.push('/practice/<slug>/builder')}
   ```
5. Add entries to `TOPIC_QUERIES`
6. Run `tier-feature-register` skill
7. Type check

---

## File Templates

### `lib/<slug>-quiz.ts`

```ts
import { generateRAGBatch } from './ai/rag-quiz';
import type { QuizQuestion } from './types';

export type WidgetTopic = 'anatomy' | 'judging' | 'breeds';

export const QUIZ_SOURCES: Record<WidgetTopic, string> = {
  anatomy: 'Texas FFA Widget Anatomy Guide',
  judging: 'Texas FFA Widget Judging Manual',
  breeds: 'Texas FFA Widget Breed Standards',
};

export interface QuizSettings {
  topic: WidgetTopic;
  count: number;
  difficulty: 'easy' | 'medium' | 'hard';
}

export async function generateWidgetQuiz(s: QuizSettings): Promise<QuizQuestion[]> {
  return generateRAGBatch(`widget-${s.topic}`, 'mcq', s.count, s.difficulty);
}

export async function generateWidgetFlashcards(topic: WidgetTopic, count = 20) {
  return generateRAGBatch(`widget-${topic}`, 'flashcard', count, 'medium');
}
```

### `lib/ai/rag-quiz.ts` additions

```ts
const TOPIC_QUERIES: Record<string, string> = {
  // ... existing ...
  'widget-anatomy': 'widget anatomy parts structure identification',
  'widget-judging': 'widget judging scorecard criteria placing',
  'widget-breeds': 'widget breed standards characteristics traits',
};
```

---

## Verification Checklist

After build:

- [ ] `app/practice/<slug>/{index,builder,quiz,flashcards}.tsx` all exist
- [ ] `lib/<slug>-quiz.ts` exists
- [ ] `TOPIC_QUERIES` has entries for all module topics
- [ ] `constants/contests.ts` → `is_active: true`
- [ ] `app/contest/[id].tsx` → `if (legacyId === 'cde-<slug>')` block added
- [ ] `lib/tier.ts` → `FEATURE_TIERS['cde-<slug>'] = '<tier>'`
- [ ] `lib/store/history.ts` → `PracticeType` includes `'<slug>'`
- [ ] `npx tsc --noEmit -p .` clean
- [ ] Smoke run: open module, generate 5-Q quiz, verify questions appear
- [ ] Citations point to chunks from correct category (use Brain v2 if module surfaces them)

---

## Related

- `module-readiness` — pick mode
- `tier-feature-register` — handles 4-file integration
- `pdf-to-rag` — prerequisite if no chunks
- `rag-quiz-generate` — reference for `generateRAGBatch`
- `brand-voice-lint` — run on new UI strings
