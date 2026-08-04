---
name: csv-question-importer
description: Streamlines building FFA contest practice modules and question portions by processing a CSV file of questions. Use this skill when the user provides a CSV file of questions and wants to build a practice section, flashcards, and test module for a contest fast and easy without going out of the guardrails.
---

# CSV Question Importer Skill

## When to use this skill

- When you are given a CSV file containing questions and asked to build a practice section for a CDE or LDE contest.
- When you need to quickly wire up new questions into the existing generic practice flow (Study, Test, Flashcards) without wasting time building new UI screens.

## The "No New UI" Guardrail

**CRITICAL RULE:** Do NOT build custom `study.tsx`, `test.tsx`, or `flashcard.tsx` screens for new question-based contests. The app already uses dynamically routed, generic screens found at `app/practice/study.tsx`, `app/practice/test.tsx`, and `app/practice/flashcard.tsx`.

To build a new question section from a CSV, you **ONLY** need to do data plumbing.

## Implementation Steps

### Step 1: Write a Node.js Parsing Script

**File Location:** `scripts/parse-[contest].js` (e.g., `scripts/parse-agronomy.js`)

Analyze the provided CSV to determine the columns (e.g., Question Text, Option A, Option B, Correct Answer, Category). Write a Node.js script that reads the CSV and formats the output into the `Question` array type.

- The `options` array should contain all possible answers (correct and incorrect), ideally randomized or sorted.
- The `subcategory` field is essential—it automatically populates the category selection buttons in the Study and Flashcard UI.
- Use `fs` and `readline` for parsing the CSV robustly (handling quoted commas).
- For a clean example, look at `scripts/parse-dairy.js` or `scripts/parse-livestock.js`.

**Required Output Object Format:**

```typescript
{
  id: '[contest-prefix]-[index]',
  contest_id: '[exact-contest-id]', // e.g., 'cde-livestock'
  question_text: '...',
  question_type: 'multiple_choice',
  options: ['A', 'B', 'C', 'D'],
  correct_answer: 'A',
  explanation: '...',
  difficulty: 2,
  subcategory: 'Category Name',
  image_url: null,
  is_active: true
}
```

### Step 2: Execute the Script

Run the script (`node scripts/parse-[contest].js`) to generate a strongly-typed TypeScript array file at `lib/data/[contest].ts` (e.g., `lib/data/agronomy-questions.ts`). Verify the file was generated with the correct data.

### Step 3: Wire Data into `questions.ts`

**File Location:** `lib/data/questions.ts`

The app looks for all offline practice questions in the `SAMPLE_QUESTIONS` dictionary in `lib/data/questions.ts`. Update this file to register your new contest data.

1. **Import the new array:**

```typescript
import { AGRONOMY_QUESTIONS } from './agronomy-questions';
```

1. **Combine arrays (if appending) or declare the local array:**

```typescript
const agronomyQuestions: Question[] = [...AGRONOMY_QUESTIONS];
```

1. **Map to `SAMPLE_QUESTIONS` export:**

```typescript
export const SAMPLE_QUESTIONS: Record<string, Question[]> = {
  // existing items...
  'cde-agronomy': agronomyQuestions,
};
```

### Step 4: Verify Contest Exists

Ensure the exact `contest_id` is defined as a `Contest` object containing `{ has_quiz: true }` so that the UI buttons appear on the `app/contest/[id].tsx` landing screen. (If `has_quiz` is false, the generic practice buttons won't show).

### Final Review

Following these exact steps guarantees a fast and easy practice module implementation. The router at `/contest/[id]` will naturally route the "Study Mode", "Test Mode", and "Flashcards" buttons to the correct dynamic pages using your newly registered `contestId`.
