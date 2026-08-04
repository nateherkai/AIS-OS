---
name: contest-builder
description: Builds complete FFA contest practice modules end-to-end including screens, data files, scoring logic, and navigation wiring. Use when the user asks to create a new CDE or LDE module, add a contest, build a practice flow, or implement scoring for a specific FFA event.
---

# Contest Builder Agent

## When to use this skill
- Building a new CDE or LDE practice module
- Adding questions or rubric data for a contest
- Creating or modifying scoring logic
- Wiring a new contest into navigation
- Fixing a broken practice flow

## Files Owned
```
app/contest/*
app/practice/**/*
lib/data/*
lib/scoring/*
lib/types/*
constants/contests.ts
```

## Contest Type Templates

### 1. Quiz-Based CDEs
**Reference**: `app/practice/greenhand-quiz/`
**Flow**: Instructions → Quiz (multiple choice) → Results
**Scoring**: Local — compare answers, no AI needed
**Examples**: Greenhand Quiz, Senior Quiz, Livestock Judging knowledge

Files to create:
```
app/practice/{slug}/index.tsx      → Instructions + start
app/practice/{slug}/quiz.tsx       → Question flow
app/practice/{slug}/results.tsx    → Score + review (or use shared results)
lib/data/{slug}.ts                 → Questions array
lib/scoring/{slug}.ts              → Local scoring function
```

Data format:
```typescript
export interface Question {
  id: string;
  question: string;
  options: string[];
  correctAnswer: number;  // index into options
  explanation?: string;
  category?: string;
  difficulty?: 'easy' | 'medium' | 'hard';
}
```

### 2. Speech/Presentation LDEs
**Reference**: `app/contest/creed-speaking.tsx`, `app/practice/ag-advocacy/`
**Flow**: Instructions → Audio Recording → Whisper STT → Gemini Scoring → Results
**Scoring**: AI-graded via Gemini against rubric
**Examples**: Creed Speaking, Extemporaneous Speaking, Prepared Speaking

Files to create:
```
app/practice/{slug}/index.tsx      → Instructions + rules
app/practice/{slug}/record.tsx     → Audio recording screen
app/practice/{slug}/result.tsx     → AI score + category feedback
lib/data/{slug}.ts                 → Rubric criteria, reference text
lib/scoring/{slug}.ts              → Prompt builder + response parser
```

Scoring pattern:
```typescript
import { generateAnalysis } from '@/lib/ai/gemini';

export async function scorePresentation(transcript: string): Promise<ScoreResult> {
  const prompt = buildRubricPrompt(transcript);  // contest-specific
  const response = await generateAnalysis(prompt);
  return parseScoreResponse(response);
}
```

### 3. Role-Play CDEs
**Reference**: `app/practice/job-interview/`
**Flow**: Instructions → Setup/Scenario → Interactive Practice → AI Evaluation
**Scoring**: AI-graded with scenario context
**Examples**: Job Interview, Ag Sales

Files to create:
```
app/practice/{slug}/index.tsx      → Instructions
app/practice/{slug}/setup.tsx      → Scenario selection/setup
app/practice/{slug}/practice.tsx   → Interactive flow
app/practice/{slug}/result.tsx     → AI evaluation results
lib/data/{slug}.ts                 → Scenarios, evaluation criteria
lib/scoring/{slug}.ts              → AI scoring with scenario context
```

### 4. Document/Portfolio CDEs
**Reference**: `app/practice/ag-issues/`
**Flow**: Instructions → Document Upload/Creation → Presentation → Scoring
**Scoring**: AI-graded on content + presentation
**Examples**: Ag Issues Forum, Public Relations

Files to create:
```
app/practice/{slug}/index.tsx      → Instructions
app/practice/{slug}/portfolio.tsx  → Document upload/creation
app/practice/{slug}/record.tsx     → Presentation recording
app/practice/{slug}/result.tsx     → Combined score
lib/data/{slug}.ts                 → Portfolio criteria, topic bank
lib/scoring/{slug}.ts              → Multi-factor AI scoring
```

## Module Creation Checklist
1. [ ] Determine contest type (quiz / speech / role-play / document)
2. [ ] Create folder: `app/practice/{contest-slug}/`
3. [ ] Create `index.tsx` with instructions matching official FFA rules
4. [ ] Create practice screen(s) following the appropriate template above
5. [ ] Create `result.tsx` with score display + category breakdowns + feedback + retry
6. [ ] Add data file: `lib/data/{contest-slug}.ts`
7. [ ] Add scoring logic: `lib/scoring/{contest-slug}.ts`
8. [ ] Verify contest exists in `constants/contests.ts` — add if missing
9. [ ] Wire navigation from `app/contest/[id].tsx`
10. [ ] Add types to `lib/types/` if needed
11. [ ] Verify TypeScript compiles without errors

## Scoring Function Contract

Every scoring function must return this shape:
```typescript
interface ScoreResult {
  score: number;
  maxScore: number;
  feedback: string;          // Overall 2-3 sentence feedback
  details: {
    categories: Array<{
      name: string;
      score: number;
      maxScore: number;
      feedback: string;      // Category-specific feedback
    }>;
  };
  metadata?: Record<string, any>;  // Contest-specific extra data
}
```

## Remaining Contests

### CDEs Not Yet Implemented
Agricultural Communications, Agricultural Mechanics, Agronomy, Cotton Classing, Dairy Cattle Judging, Dairy Foods, Entomology, Farm Business Management, Floriculture, Food Science & Technology, Forestry, Horse Judging, Homesite Evaluation, Land Judging, Marketing Plan, Meat Evaluation, Milk Quality & Dairy Foods, Nursery/Landscape, Parliamentary Procedure, Poultry Judging, Range Evaluation, Tractor Technician, Veterinary Science, Wildlife

### LDEs Not Yet Implemented
Extemporaneous Speaking, Prepared Public Speaking, FFA Quiz, Opening & Closing Ceremonies, Parliamentary Procedure

## Batching Strategy
Build by contest type for maximum code reuse:
- **Batch 1** (Quiz): Agronomy, Entomology, Forestry, Wildlife, Vet Science, Food Science
- **Batch 2** (Judging): Dairy Cattle, Horse, Poultry, Meat Evaluation, Land
- **Batch 3** (Speech): Extemporaneous Speaking, Prepared Speaking
- **Batch 4** (Skills): Ag Mechanics, Tractor Tech, Floriculture, Nursery/Landscape
- **Batch 5** (Document): Marketing Plan, Ag Communications, Farm Business Mgmt
