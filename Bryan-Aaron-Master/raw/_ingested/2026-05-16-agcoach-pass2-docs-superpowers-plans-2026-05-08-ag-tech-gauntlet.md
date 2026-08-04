# AG Tech Formula Gauntlet — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the static math-drill screen in the Ag Tech module with a 10-question adaptive Formula Gauntlet mixing formula problems and RAG-backed written questions, with per-question Gemini coaching and a chapter leaderboard.

**Architecture:** A new `lib/ag-tech-gauntlet.ts` module owns question assembly, adaptive tier logic, score calculation, Gemini coaching calls, and Supabase persistence. `app/practice/ag-tech/gauntlet.tsx` is a single-screen component that toggles between question view and results view. The existing `ag-tech-formulas.ts` is extended with difficulty tags; RAG questions are fetched upfront via `generateRAGBatch`.

**Tech Stack:** Expo Router 4, React Native, TypeScript, Supabase (PostgreSQL + RLS), Gemini 2.0 Flash via `getModel()` / `retryOperation`, `parseAIJson` from `lib/ai/parser.ts`, `useHistoryStore` from `lib/store/history.ts`

---

## File Map

| File | Action |
|------|--------|
| `lib/ai/rag-quiz.ts` | Modify — add `ag-tech-written` to `TOPIC_QUERIES` |
| `lib/data/ag-tech-formulas.ts` | Modify — add `difficulty` field to `FormulaTemplate`, tag all existing formulas |
| `lib/store/history.ts` | Modify — add `'ag-tech-gauntlet'` to `PracticeType` union |
| `supabase/migrations/20260508120000_ag_tech_gauntlet_scores.sql` | Create — new leaderboard table |
| `lib/prompts/ag-tech-prompts.ts` | Create — all Gemini prompt strings |
| `lib/ag-tech-gauntlet.ts` | Create — engine: question assembly, tier logic, AI calls, DB persistence |
| `app/practice/ag-tech/gauntlet.tsx` | Create — full gauntlet screen (question + results) |
| `app/practice/ag-tech/math-drill.tsx` | Delete |
| `app/practice/ag-tech/index.tsx` | Modify — route math-drill → gauntlet |

---

## ⚠️ RAG Prerequisite (before Task 1)

The RAG knowledge base must have ag-tech content before the gauntlet can generate written questions. Run the `rag-knowledge-ingest` skill on these PDFs from `Texas_FFA_Resources/CDE_Events/Ag_Technology/`:
- `2018_TX_FFA_State_ATMS_CDE_Written_Exam.pdf`
- `2017_ATMS_State_CDE_Exam.pdf`
- `2016_State_ATMS_CDE_Exam.pdf`
- `ATMS_Rules_2022-2026__Updated_9.11.24_.pdf`

Use `contest_category = 'ag-tech'` when ingesting. Verify with `rag-coverage-report` skill before continuing.

---

## Task 1: Add RAG topic entry

**Files:**
- Modify: `lib/ai/rag-quiz.ts` (TOPIC_QUERIES map, ~line 46)

- [ ] **Step 1: Add ag-tech-written to TOPIC_QUERIES**

Open `lib/ai/rag-quiz.ts` and add this entry inside the `TOPIC_QUERIES` object (after the last existing entry before the closing `}`):

```ts
  // ── Ag Technology & Mechanical Systems CDE ──────────────────────────────
  'ag-tech-written':
    'agricultural technology mechanical systems equipment power hydraulics electrical wiring engine small engine tractor implements GPS precision agriculture welding concrete fabrication',
```

- [ ] **Step 2: Commit**

```bash
git add lib/ai/rag-quiz.ts
git commit -m "feat(ag-tech): add ag-tech-written RAG topic query"
```

---

## Task 2: Add difficulty field to FormulaTemplate

**Files:**
- Modify: `lib/data/ag-tech-formulas.ts`

- [ ] **Step 1: Extend FormulaTemplate interface**

In `lib/data/ag-tech-formulas.ts`, add `difficulty` to the `FormulaTemplate` interface (after the `description` field):

```ts
export interface FormulaTemplate {
  id: string;
  title: string;
  category: string;
  difficulty: 'easy' | 'medium' | 'hard';
  description: string;
  variables: FormulaVariable[];
  scenarioTemplate: string;
  calculateAnswer: (vars: Record<string, number>) => number;
  getStepByStep: (vars: Record<string, number>, answer: number) => string;
}
```

- [ ] **Step 2: Tag each formula in AG_TECH_FORMULAS**

Find each formula object in `AG_TECH_FORMULAS` and add `difficulty` after `category`. Use this mapping:

- `aph-theoretical` → `difficulty: 'easy'`
- `aph-effective` → `difficulty: 'medium'`
- Any displacement / electrical formulas already in the file → `difficulty: 'hard'`

If there are fewer than 9 formulas total (the file is ~126 lines with ~3 entries), add these 6 additional formulas below the existing ones so all 3 difficulty tiers have at least 3 entries each:

```ts
  {
    id: 'engine-displacement',
    title: 'Engine Displacement',
    category: 'Power Systems',
    difficulty: 'medium',
    description: 'Calculate total engine displacement from bore, stroke, and cylinders.',
    variables: [
      { id: 'bore', name: 'Bore Diameter', unit: 'inches', min: 2.5, max: 4.5, decimals: 2 },
      { id: 'stroke', name: 'Stroke Length', unit: 'inches', min: 2.5, max: 4.0, decimals: 2 },
      { id: 'cylinders', name: 'Number of Cylinders', unit: 'cylinders', min: 1, max: 8, decimals: 0 },
    ],
    scenarioTemplate:
      'A small engine has a bore of {{bore}} inches, a stroke of {{stroke}} inches, and {{cylinders}} cylinders. Calculate the total engine displacement in cubic inches. Round to two decimal places.',
    calculateAnswer: (vars) =>
      Number(((Math.PI / 4) * vars.bore ** 2 * vars.stroke * vars.cylinders).toFixed(2)),
    getStepByStep: (vars, answer) =>
      `Displacement = (π/4) × Bore² × Stroke × Cylinders\n= (π/4) × ${vars.bore}² × ${vars.stroke} × ${vars.cylinders}\n= ${answer} cubic inches`,
  },
  {
    id: 'ohms-law-current',
    title: "Ohm's Law — Current",
    category: 'Electrical Systems',
    difficulty: 'easy',
    description: 'Calculate current given voltage and resistance.',
    variables: [
      { id: 'voltage', name: 'Voltage', unit: 'volts', min: 6, max: 120, decimals: 1 },
      { id: 'resistance', name: 'Resistance', unit: 'ohms', min: 1, max: 50, decimals: 1 },
    ],
    scenarioTemplate:
      'A DC circuit has a voltage of {{voltage}} volts and a resistance of {{resistance}} ohms. What is the current (in amps)? Round to two decimal places.',
    calculateAnswer: (vars) => Number((vars.voltage / vars.resistance).toFixed(2)),
    getStepByStep: (vars, answer) =>
      `I = V ÷ R\nI = ${vars.voltage} ÷ ${vars.resistance}\nI = ${answer} amps`,
  },
  {
    id: 'hydraulic-pressure',
    title: 'Hydraulic Cylinder Force',
    category: 'Hydraulics',
    difficulty: 'hard',
    description: 'Calculate force exerted by a hydraulic cylinder.',
    variables: [
      { id: 'pressure', name: 'System Pressure', unit: 'PSI', min: 1000, max: 3000, decimals: 0 },
      { id: 'diameter', name: 'Cylinder Bore Diameter', unit: 'inches', min: 2, max: 6, decimals: 1 },
    ],
    scenarioTemplate:
      'A hydraulic cylinder with a bore diameter of {{diameter}} inches is operating at {{pressure}} PSI. Calculate the extend force (in pounds). Round to the nearest whole number.',
    calculateAnswer: (vars) =>
      Math.round((Math.PI / 4) * vars.diameter ** 2 * vars.pressure),
    getStepByStep: (vars, answer) =>
      `Force = (π/4) × Diameter² × Pressure\n= (π/4) × ${vars.diameter}² × ${vars.pressure}\n= ${answer} lbs`,
  },
  {
    id: 'field-efficiency',
    title: 'Field Efficiency',
    category: 'Tractor & Machinery',
    difficulty: 'medium',
    description: 'Calculate actual field capacity given theoretical capacity and efficiency.',
    variables: [
      { id: 'width', name: 'Implement Width', unit: 'feet', min: 10, max: 40, decimals: 1 },
      { id: 'speed', name: 'Operating Speed', unit: 'mph', min: 3, max: 8, decimals: 1 },
      { id: 'efficiency', name: 'Field Efficiency', unit: '%', min: 65, max: 90, decimals: 0 },
    ],
    scenarioTemplate:
      'A tractor operates a {{width}}-foot implement at {{speed}} mph with a field efficiency of {{efficiency}}%. What is the effective acres per hour? Round to two decimal places.',
    calculateAnswer: (vars) =>
      Number(((vars.width * vars.speed * (vars.efficiency / 100)) / 8.25).toFixed(2)),
    getStepByStep: (vars, answer) =>
      `Effective APH = (Width × Speed × Efficiency%) ÷ 8.25\n= (${vars.width} × ${vars.speed} × ${vars.efficiency / 100}) ÷ 8.25\n= ${answer} acres/hour`,
  },
  {
    id: 'electrical-power',
    title: 'Electrical Power',
    category: 'Electrical Systems',
    difficulty: 'medium',
    description: 'Calculate wattage given voltage and current.',
    variables: [
      { id: 'voltage', name: 'Voltage', unit: 'volts', min: 12, max: 120, decimals: 0 },
      { id: 'current', name: 'Current', unit: 'amps', min: 1, max: 20, decimals: 1 },
    ],
    scenarioTemplate:
      'An electrical circuit operates at {{voltage}} volts and draws {{current}} amps. What is the power consumption in watts?',
    calculateAnswer: (vars) => Number((vars.voltage * vars.current).toFixed(1)),
    getStepByStep: (vars, answer) =>
      `P = V × I\nP = ${vars.voltage} × ${vars.current}\nP = ${answer} watts`,
  },
  {
    id: 'concrete-volume',
    title: 'Concrete Volume',
    category: 'Fabrication',
    difficulty: 'hard',
    description: 'Calculate cubic yards of concrete needed for a slab.',
    variables: [
      { id: 'length', name: 'Slab Length', unit: 'feet', min: 8, max: 24, decimals: 0 },
      { id: 'width', name: 'Slab Width', unit: 'feet', min: 4, max: 12, decimals: 0 },
      { id: 'thickness', name: 'Slab Thickness', unit: 'inches', min: 3, max: 6, decimals: 0 },
    ],
    scenarioTemplate:
      'You need to pour a concrete slab {{length}} feet long, {{width}} feet wide, and {{thickness}} inches thick. How many cubic yards of concrete are required? Round to two decimal places.',
    calculateAnswer: (vars) =>
      Number(((vars.length * vars.width * (vars.thickness / 12)) / 27).toFixed(2)),
    getStepByStep: (vars, answer) =>
      `Volume (ft³) = Length × Width × (Thickness ÷ 12)\n= ${vars.length} × ${vars.width} × ${vars.thickness / 12}\n= ${vars.length * vars.width * (vars.thickness / 12)} ft³\n\nConvert to cubic yards (÷ 27):\n= ${answer} cubic yards`,
  },
```

- [ ] **Step 3: Type-check**

```bash
npx tsc --noEmit -p .
```

Expected: no errors related to `difficulty`.

- [ ] **Step 4: Commit**

```bash
git add lib/data/ag-tech-formulas.ts
git commit -m "feat(ag-tech): add difficulty tiers to formula templates"
```

---

## Task 3: PracticeType + database migration

**Files:**
- Modify: `lib/store/history.ts`
- Create: `supabase/migrations/20260508120000_ag_tech_gauntlet_scores.sql`

- [ ] **Step 1: Add PracticeType**

In `lib/store/history.ts`, add `'ag-tech-gauntlet'` to the `PracticeType` union. Insert after `'ag-eng-quiz'`:

```ts
  | 'ag-eng-quiz'
  | 'ag-tech-gauntlet'
```

- [ ] **Step 2: Write migration**

Create `supabase/migrations/20260508120000_ag_tech_gauntlet_scores.sql`:

```sql
create table if not exists ag_tech_gauntlet_scores (
  id             uuid primary key default gen_random_uuid(),
  student_id     uuid not null references auth.users(id) on delete cascade,
  classroom_id   uuid references classrooms(id) on delete set null,
  score          integer not null check (score >= 0 and score <= 120),
  tier_reached   integer not null check (tier_reached between 1 and 3),
  correct_count  integer not null check (correct_count between 0 and 10),
  missed_categories text[] not null default '{}',
  created_at     timestamptz not null default now()
);

-- Per-student leaderboard lookup
create index ag_tech_gauntlet_scores_student_idx
  on ag_tech_gauntlet_scores (student_id, score desc);

-- Per-classroom leaderboard lookup
create index ag_tech_gauntlet_scores_classroom_idx
  on ag_tech_gauntlet_scores (classroom_id, score desc);

-- RLS: students can insert their own scores, read classroom scores
alter table ag_tech_gauntlet_scores enable row level security;

create policy "students insert own scores"
  on ag_tech_gauntlet_scores for insert
  with check (auth.uid() = student_id);

create policy "students read classroom scores"
  on ag_tech_gauntlet_scores for select
  using (
    classroom_id in (
      select classroom_id from classroom_members
      where student_id = auth.uid() and status = 'active'
    )
    or student_id = auth.uid()
  );
```

- [ ] **Step 3: Apply migration**

Use the Supabase MCP tool `apply_migration` with the SQL above, or run:
```bash
npx supabase db push
```

- [ ] **Step 4: Commit**

```bash
git add lib/store/history.ts supabase/migrations/20260508120000_ag_tech_gauntlet_scores.sql
git commit -m "feat(ag-tech): add ag-tech-gauntlet PracticeType + scores table migration"
```

---

## Task 4: Create ag-tech-prompts.ts

**Files:**
- Create: `lib/prompts/ag-tech-prompts.ts`

- [ ] **Step 1: Create the prompts file**

Create `lib/prompts/ag-tech-prompts.ts`:

```ts
/**
 * Prompts for the AG Tech Formula Gauntlet — per-question coaching and session summary.
 */

export interface CoachingContext {
  questionTitle: string;
  category: string;
  studentAnswer: string;
  correctAnswer: string;
  stepByStep: string; // for formula questions; empty string for RAG questions
  questionText: string;
}

export interface SessionMiss {
  category: string;
  questionType: 'formula' | 'rag';
  studentAnswer: string;
  correctAnswer: string;
  questionTitle: string;
}

export interface SessionSummaryResponse {
  weakCategory: string;
  pattern: string;
  drillRecommendation: string;
}

export function buildCoachingPrompt(ctx: CoachingContext): string {
  const stepSection = ctx.stepByStep
    ? `\nCorrect step-by-step solution:\n${ctx.stepByStep}`
    : '';
  return `You are a Texas FFA Agricultural Technology & Mechanical Systems CDE coach.

A student just answered a practice question incorrectly.

Question: "${ctx.questionText}"
Topic: ${ctx.questionTitle} (${ctx.category})
Student answered: ${ctx.studentAnswer}
Correct answer: ${ctx.correctAnswer}${stepSection}

In 2-3 sentences, explain exactly why the student's answer was wrong and how to get the right answer. Use their specific numbers if this was a math problem. Be direct and educational — no filler.`;
}

export function buildSessionSummaryPrompt(misses: SessionMiss[]): string {
  const missLines = misses
    .map(
      (m, i) =>
        `${i + 1}. [${m.category}] ${m.questionTitle} — Student: "${m.studentAnswer}", Correct: "${m.correctAnswer}"`
    )
    .join('\n');

  return `You are a Texas FFA Agricultural Technology & Mechanical Systems CDE coach analyzing a student's practice session.

The student missed these questions:
${missLines}

Respond with a JSON object in this exact shape:
{
  "weakCategory": "the single most problematic category name",
  "pattern": "one sentence describing the recurring mistake pattern",
  "drillRecommendation": "one specific, actionable drill or study recommendation"
}`;
}
```

- [ ] **Step 2: Type-check**

```bash
npx tsc --noEmit -p .
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add lib/prompts/ag-tech-prompts.ts
git commit -m "feat(ag-tech): add gauntlet coaching prompts"
```

---

## Task 5: Build gauntlet engine

**Files:**
- Create: `lib/ag-tech-gauntlet.ts`

- [ ] **Step 1: Create the engine file**

Create `lib/ag-tech-gauntlet.ts`:

```ts
import { supabase } from '@/lib/supabase';
import { getModel, retryOperation } from '@/lib/ai/gemini';
import { parseAIJson } from '@/lib/ai/parser';
import { AG_TECH_FORMULAS, generateProblem } from '@/lib/data/ag-tech-formulas';
import { generateRAGBatch } from '@/lib/ai/rag-quiz';
import {
  buildCoachingPrompt,
  buildSessionSummaryPrompt,
  type SessionMiss,
  type SessionSummaryResponse,
} from '@/lib/prompts/ag-tech-prompts';
import type { QuizQuestion } from '@/lib/senior-quiz';

// ── Types ────────────────────────────────────────────────────────────────────

export type GauntletTier = 1 | 2 | 3;

export const TIER_LABELS: Record<GauntletTier, string> = {
  1: 'Area',
  2: 'Invitational',
  3: 'State',
};

export const TIER_BONUS: Record<GauntletTier, number> = {
  1: 0,
  2: 10,
  3: 20,
};

interface FormulaQuestion {
  type: 'formula';
  id: string;
  title: string;
  category: string;
  scenarioText: string;
  correctAnswer: number;
  stepByStep: string;
  tolerance: number; // ±tolerance for numeric comparison
}

interface RAGQuestion {
  type: 'rag';
  id: string;
  title: string;
  category: string;
  questionText: string;
  options: string[];
  correctAnswer: string;
}

export type GauntletQuestion = FormulaQuestion | RAGQuestion;

export interface GauntletSession {
  questions: GauntletQuestion[];
}

export interface LeaderboardEntry {
  student_id: string;
  display_name: string;
  best_score: number;
  tier_reached: number;
}

// ── Question assembly ────────────────────────────────────────────────────────

// Positions 0,1,3,4,6,7,9 = formula (7 questions); 2,5,8 = RAG (3 questions)
const FORMULA_POSITIONS = new Set([0, 1, 3, 4, 6, 7, 9]);

function pickFormulas(tier: GauntletTier): FormulaQuestion[] {
  const difficultyMap: Record<GauntletTier, Array<'easy' | 'medium' | 'hard'>> = {
    1: ['easy'],
    2: ['easy', 'medium'],
    3: ['easy', 'medium', 'hard'],
  };
  const allowed = difficultyMap[tier];
  const pool = AG_TECH_FORMULAS.filter((f) => allowed.includes(f.difficulty));
  const shuffled = [...pool].sort(() => Math.random() - 0.5);
  const selected = shuffled.slice(0, 7);

  return selected.map((template) => {
    const instance = generateProblem(template);
    return {
      type: 'formula' as const,
      id: template.id,
      title: template.title,
      category: template.category,
      scenarioText: instance.scenarioText,
      correctAnswer: instance.correctAnswer,
      stepByStep: instance.stepByStep,
      tolerance: 0.05,
    };
  });
}

async function fetchRAGQuestions(tier: GauntletTier): Promise<RAGQuestion[]> {
  const ragDifficulty = tier === 1 ? 'greenhand' : 'senior';
  const raw: QuizQuestion[] = await generateRAGBatch(
    'ag-tech-written',
    'multiple_choice',
    3,
    ragDifficulty
  );
  return raw.map((q) => ({
    type: 'rag' as const,
    id: q.id ?? Math.random().toString(36).slice(2),
    title: q.topic ?? 'Ag Technology',
    category: 'Written Exam',
    questionText: q.question,
    options: q.options ?? [],
    correctAnswer: q.correctAnswer,
  }));
}

export async function buildGauntletSession(
  initialTier: GauntletTier = 1
): Promise<GauntletSession> {
  const [formulaQs, ragQs] = await Promise.all([
    Promise.resolve(pickFormulas(initialTier)),
    fetchRAGQuestions(initialTier),
  ]);

  const questions: GauntletQuestion[] = Array.from({ length: 10 }, (_, i) => {
    if (FORMULA_POSITIONS.has(i)) {
      return formulaQs.shift()!;
    }
    return ragQs.shift()!;
  });

  return { questions };
}

// ── Scoring ──────────────────────────────────────────────────────────────────

export function calculateScore(correctCount: number, tierReached: GauntletTier): number {
  return Math.round((correctCount / 10) * 100) + TIER_BONUS[tierReached];
}

export function checkFormulaAnswer(
  studentRaw: string,
  correctAnswer: number,
  tolerance: number
): boolean {
  const parsed = parseFloat(studentRaw.replace(/,/g, ''));
  if (isNaN(parsed)) return false;
  return Math.abs(parsed - correctAnswer) <= tolerance;
}

// ── Adaptive tier ────────────────────────────────────────────────────────────

export function nextTier(current: GauntletTier, consecutiveCorrect: number): GauntletTier {
  if (consecutiveCorrect >= 2 && current < 3) return (current + 1) as GauntletTier;
  return current;
}

// ── AI coaching ──────────────────────────────────────────────────────────────

export async function getCoachingExplanation(params: {
  questionTitle: string;
  category: string;
  questionText: string;
  studentAnswer: string;
  correctAnswer: string;
  stepByStep: string;
}): Promise<string> {
  const model = getModel({ model: 'gemini-2.0-flash' });
  const prompt = buildCoachingPrompt(params);
  const result = await retryOperation(
    () => model.generateContent(prompt),
    'ag-tech-gauntlet:coaching'
  );
  return result.response.text().trim();
}

export async function getSessionSummary(
  misses: SessionMiss[]
): Promise<SessionSummaryResponse | null> {
  if (misses.length === 0) return null;
  const model = getModel({ model: 'gemini-2.0-flash' });
  const prompt = buildSessionSummaryPrompt(misses);
  const result = await retryOperation(
    () => model.generateContent(prompt),
    'ag-tech-gauntlet:summary'
  );
  return parseAIJson<SessionSummaryResponse>(result.response.text(), {
    weakCategory: '',
    pattern: '',
    drillRecommendation: '',
  });
}

// ── Persistence ──────────────────────────────────────────────────────────────

export async function saveGauntletScore(params: {
  studentId: string;
  score: number;
  tierReached: GauntletTier;
  correctCount: number;
  missedCategories: string[];
}): Promise<void> {
  // Resolve classroom from classroom_members
  const { data: membership } = await supabase
    .from('classroom_members')
    .select('classroom_id')
    .eq('student_id', params.studentId)
    .eq('status', 'active')
    .limit(1)
    .single();

  await supabase.from('ag_tech_gauntlet_scores').insert({
    student_id: params.studentId,
    classroom_id: membership?.classroom_id ?? null,
    score: params.score,
    tier_reached: params.tierReached,
    correct_count: params.correctCount,
    missed_categories: params.missedCategories,
  });
}

export async function fetchPersonalBest(studentId: string): Promise<number> {
  const { data } = await supabase
    .from('ag_tech_gauntlet_scores')
    .select('score')
    .eq('student_id', studentId)
    .order('score', { ascending: false })
    .limit(1)
    .single();
  return data?.score ?? 0;
}

export async function fetchLeaderboard(
  classroomId: string | null
): Promise<LeaderboardEntry[]> {
  if (!classroomId) return [];
  // Best score per student in classroom
  const { data } = await supabase
    .from('ag_tech_gauntlet_scores')
    .select('student_id, score, tier_reached')
    .eq('classroom_id', classroomId)
    .order('score', { ascending: false })
    .limit(50);

  if (!data) return [];

  // Deduplicate to best score per student
  const seen = new Set<string>();
  const best: LeaderboardEntry[] = [];
  for (const row of data) {
    if (!seen.has(row.student_id)) {
      seen.add(row.student_id);
      best.push({
        student_id: row.student_id,
        display_name: row.student_id.slice(0, 8), // replaced by profile fetch below
        best_score: row.score,
        tier_reached: row.tier_reached,
      });
    }
    if (best.length >= 10) break;
  }

  // Resolve display names from profiles table
  const ids = best.map((e) => e.student_id);
  const { data: profiles } = await supabase
    .from('profiles')
    .select('id, full_name')
    .in('id', ids);

  const nameMap = new Map((profiles ?? []).map((p: any) => [p.id, p.full_name]));
  return best.map((e) => ({
    ...e,
    display_name: nameMap.get(e.student_id) ?? 'Student',
  }));
}
```

> **Note:** If `profiles` table does not have a `full_name` column, substitute with whatever the user display name column is in your schema. Check `SCHEMA.md` profiles section.

- [ ] **Step 2: Type-check**

```bash
npx tsc --noEmit -p .
```

Expected: no errors. If `QuizQuestion` is missing `id` or `topic`, adjust the mapping in `fetchRAGQuestions` to use `q.question` as the id fallback.

- [ ] **Step 3: Commit**

```bash
git add lib/ag-tech-gauntlet.ts
git commit -m "feat(ag-tech): gauntlet engine — assembly, scoring, AI, persistence"
```

---

## Task 6: Build gauntlet.tsx screen

**Files:**
- Create: `app/practice/ag-tech/gauntlet.tsx`

- [ ] **Step 1: Create the screen**

Create `app/practice/ag-tech/gauntlet.tsx`:

```tsx
import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { AnimatedButton as TouchableOpacity } from '@/components/common/AnimatedButton';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Theme, GlassEffect } from '@/constants/theme';
import { safeBack } from '@/lib/navigation';
import { useAuthStore } from '@/lib/store/auth';
import { useHistoryStore } from '@/lib/store/history';
import {
  buildGauntletSession,
  calculateScore,
  checkFormulaAnswer,
  nextTier,
  getCoachingExplanation,
  getSessionSummary,
  saveGauntletScore,
  fetchPersonalBest,
  fetchLeaderboard,
  TIER_LABELS,
  TIER_BONUS,
  type GauntletQuestion,
  type GauntletTier,
  type GauntletSession,
  type LeaderboardEntry,
} from '@/lib/ag-tech-gauntlet';
import type { SessionMiss, SessionSummaryResponse } from '@/lib/prompts/ag-tech-prompts';

type ScreenState = 'loading' | 'question' | 'results';
type AnswerState = 'unanswered' | 'correct' | 'wrong';

const TIER_COLORS: Record<GauntletTier, string> = {
  1: '#4CAF50',
  2: '#FF9800',
  3: '#F44336',
};

export default function GauntletScreen() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const addResult = useHistoryStore((s) => s.addResult);

  const [screen, setScreen] = useState<ScreenState>('loading');
  const [session, setSession] = useState<GauntletSession | null>(null);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [tier, setTier] = useState<GauntletTier>(1);
  const [consecutiveCorrect, setConsecutiveCorrect] = useState(0);
  const [answerState, setAnswerState] = useState<AnswerState>('unanswered');
  const [formulaInput, setFormulaInput] = useState('');
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [coachingText, setCoachingText] = useState<string | null>(null);
  const [coachingLoading, setCoachingLoading] = useState(false);
  const [correctCount, setCorrectCount] = useState(0);
  const [tierReached, setTierReached] = useState<GauntletTier>(1);
  const misses = useRef<SessionMiss[]>([]);

  // Results state
  const [finalScore, setFinalScore] = useState(0);
  const [personalBest, setPersonalBest] = useState(0);
  const [summary, setSummary] = useState<SessionSummaryResponse | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [classroomId, setClassroomId] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const s = await buildGauntletSession(1);
      setSession(s);
      setScreen('question');
    })();
  }, []);

  const currentQuestion: GauntletQuestion | undefined = session?.questions[questionIndex];

  function handleSubmitAnswer() {
    if (!currentQuestion || answerState !== 'unanswered') return;

    let isCorrect = false;
    let studentAnswerStr = '';

    if (currentQuestion.type === 'formula') {
      isCorrect = checkFormulaAnswer(formulaInput, currentQuestion.correctAnswer, currentQuestion.tolerance);
      studentAnswerStr = formulaInput;
    } else {
      isCorrect = selectedOption === currentQuestion.correctAnswer;
      studentAnswerStr = selectedOption ?? '';
    }

    const newConsecutive = isCorrect ? consecutiveCorrect + 1 : 0;
    const newTier = nextTier(tier, newConsecutive);

    setAnswerState(isCorrect ? 'correct' : 'wrong');
    setConsecutiveCorrect(newConsecutive);
    if (newTier > tier) setTier(newTier);
    if (newTier > tierReached) setTierReached(newTier);

    if (isCorrect) {
      setCorrectCount((c) => c + 1);
    } else {
      misses.current.push({
        category: currentQuestion.category,
        questionType: currentQuestion.type,
        questionTitle: currentQuestion.title,
        studentAnswer: studentAnswerStr,
        correctAnswer: currentQuestion.type === 'formula'
          ? currentQuestion.correctAnswer.toString()
          : currentQuestion.correctAnswer,
      });

      // Fetch coaching in background
      setCoachingLoading(true);
      getCoachingExplanation({
        questionTitle: currentQuestion.title,
        category: currentQuestion.category,
        questionText: currentQuestion.type === 'formula'
          ? currentQuestion.scenarioText
          : currentQuestion.questionText,
        studentAnswer: studentAnswerStr,
        correctAnswer: currentQuestion.type === 'formula'
          ? currentQuestion.correctAnswer.toString()
          : currentQuestion.correctAnswer,
        stepByStep: currentQuestion.type === 'formula' ? currentQuestion.stepByStep : '',
      }).then((text) => {
        setCoachingText(text);
        setCoachingLoading(false);
      }).catch(() => setCoachingLoading(false));
    }
  }

  async function handleNext() {
    const isLast = questionIndex === 9;

    if (isLast) {
      const score = calculateScore(correctCount + (answerState === 'correct' ? 0 : 0), tierReached);
      // correctCount already updated in state; use local calculation
      const finalCorrect = answerState === 'correct' ? correctCount : correctCount;
      const computedScore = calculateScore(finalCorrect, tierReached);
      setFinalScore(computedScore);

      addResult({ type: 'ag-tech-gauntlet', score: computedScore, maxScore: 120 });

      // Fire async tasks
      setSummaryLoading(true);
      setScreen('results');

      const [pb, summ] = await Promise.all([
        fetchPersonalBest(user?.id ?? ''),
        getSessionSummary(misses.current),
      ]);
      setPersonalBest(pb);
      setSummary(summ);
      setSummaryLoading(false);

      if (user?.id) {
        const missedCats = [...new Set(misses.current.map((m) => m.category))];
        await saveGauntletScore({
          studentId: user.id,
          score: computedScore,
          tierReached,
          correctCount: finalCorrect,
          missedCategories: missedCats,
        });
      }

      // Fetch leaderboard (need classroom_id from saved score)
      // Re-query classroom_members
      const { supabase } = await import('@/lib/supabase');
      const { data: mem } = await supabase
        .from('classroom_members')
        .select('classroom_id')
        .eq('student_id', user?.id ?? '')
        .eq('status', 'active')
        .limit(1)
        .single();
      if (mem?.classroom_id) {
        setClassroomId(mem.classroom_id);
        const lb = await fetchLeaderboard(mem.classroom_id);
        setLeaderboard(lb);
      }
    } else {
      setQuestionIndex((i) => i + 1);
      setAnswerState('unanswered');
      setFormulaInput('');
      setSelectedOption(null);
      setCoachingText(null);
    }
  }

  // ── Render: loading ────────────────────────────────────────────────────────
  if (screen === 'loading') {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={Theme.colors.accent} />
        <Text style={styles.loadingText}>Loading Gauntlet...</Text>
      </View>
    );
  }

  // ── Render: results ────────────────────────────────────────────────────────
  if (screen === 'results') {
    const pbDelta = finalScore - personalBest;
    return (
      <ScrollView style={styles.container} contentContainerStyle={styles.resultsContent}>
        <TouchableOpacity style={styles.backBtn} onPress={() => safeBack(router, '/practice/ag-tech')}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>

        {/* Score card */}
        <View style={[styles.card, GlassEffect]}>
          <Text style={styles.cardLabel}>GAUNTLET COMPLETE</Text>
          <Text style={styles.bigScore}>{finalScore}</Text>
          <Text style={styles.scoreSubLabel}>/ 120 pts</Text>
          <Text style={styles.tierLabel}>Tier Reached: {TIER_LABELS[tierReached]} (+{TIER_BONUS[tierReached]} pts)</Text>
          {pbDelta > 0 && (
            <View style={styles.pbBadge}>
              <Text style={styles.pbText}>New Personal Best! +{pbDelta} pts</Text>
            </View>
          )}
          {pbDelta <= 0 && personalBest > 0 && (
            <Text style={styles.pbSubtext}>Personal Best: {personalBest}</Text>
          )}
        </View>

        {/* AI summary */}
        <View style={[styles.card, GlassEffect]}>
          <Text style={styles.cardLabel}>SESSION ANALYSIS</Text>
          {summaryLoading && <ActivityIndicator color={Theme.colors.accent} />}
          {!summaryLoading && summary && misses.current.length > 0 && (
            <>
              <Text style={styles.summaryWeak}>Weak Area: {summary.weakCategory}</Text>
              <Text style={styles.summaryText}>{summary.pattern}</Text>
              <Text style={styles.summaryRec}>Drill: {summary.drillRecommendation}</Text>
            </>
          )}
          {!summaryLoading && misses.current.length === 0 && (
            <Text style={styles.summaryText}>Perfect score — no weak areas detected.</Text>
          )}
        </View>

        {/* Leaderboard */}
        {leaderboard.length > 0 && (
          <View style={[styles.card, GlassEffect]}>
            <Text style={styles.cardLabel}>CHAPTER LEADERBOARD</Text>
            {leaderboard.map((entry, i) => (
              <View
                key={entry.student_id}
                style={[
                  styles.lbRow,
                  entry.student_id === user?.id && styles.lbRowHighlight,
                ]}
              >
                <Text style={styles.lbRank}>#{i + 1}</Text>
                <Text style={styles.lbName}>{entry.display_name}</Text>
                <Text style={styles.lbScore}>{entry.best_score} pts</Text>
              </View>
            ))}
          </View>
        )}

        <TouchableOpacity
          style={styles.replayBtn}
          onPress={() => router.replace('/practice/ag-tech/gauntlet' as any)}
        >
          <Text style={styles.replayText}>Run Again</Text>
        </TouchableOpacity>
      </ScrollView>
    );
  }

  // ── Render: question ───────────────────────────────────────────────────────
  if (!currentQuestion) return null;

  const progress = questionIndex + 1;
  const tierColor = TIER_COLORS[tier];

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.questionContent}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => safeBack(router, '/practice/ag-tech')}>
            <Ionicons name="close" size={24} color="#aaa" />
          </TouchableOpacity>
          <Text style={styles.progress}>Q{progress} / 10</Text>
          <View style={[styles.tierBadge, { backgroundColor: tierColor + '33', borderColor: tierColor }]}>
            <Text style={[styles.tierBadgeText, { color: tierColor }]}>{TIER_LABELS[tier]}</Text>
          </View>
        </View>

        {/* Category */}
        <Text style={styles.categoryLabel}>{currentQuestion.category.toUpperCase()}</Text>

        {/* Question text */}
        <View style={[styles.card, GlassEffect]}>
          <Text style={styles.questionText}>
            {currentQuestion.type === 'formula'
              ? currentQuestion.scenarioText
              : currentQuestion.questionText}
          </Text>
        </View>

        {/* Answer input */}
        {currentQuestion.type === 'formula' ? (
          <TextInput
            style={[
              styles.formulaInput,
              answerState === 'correct' && styles.inputCorrect,
              answerState === 'wrong' && styles.inputWrong,
            ]}
            value={formulaInput}
            onChangeText={setFormulaInput}
            placeholder="Enter numeric answer"
            placeholderTextColor="#555"
            keyboardType="decimal-pad"
            editable={answerState === 'unanswered'}
          />
        ) : (
          <View style={styles.optionsContainer}>
            {currentQuestion.options.map((opt) => {
              const isSelected = selectedOption === opt;
              const isRevealCorrect = answerState !== 'unanswered' && opt === currentQuestion.correctAnswer;
              const isRevealWrong = answerState === 'wrong' && isSelected && !isRevealCorrect;
              return (
                <TouchableOpacity
                  key={opt}
                  style={[
                    styles.optionBtn,
                    isSelected && styles.optionSelected,
                    isRevealCorrect && styles.optionCorrect,
                    isRevealWrong && styles.optionWrong,
                  ]}
                  onPress={() => answerState === 'unanswered' && setSelectedOption(opt)}
                  disabled={answerState !== 'unanswered'}
                >
                  <Text style={styles.optionText}>{opt}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        )}

        {/* Submit / Next button */}
        {answerState === 'unanswered' ? (
          <TouchableOpacity
            style={[
              styles.submitBtn,
              !(formulaInput || selectedOption) && styles.submitDisabled,
            ]}
            onPress={handleSubmitAnswer}
            disabled={!(formulaInput || selectedOption)}
          >
            <Text style={styles.submitText}>Submit</Text>
          </TouchableOpacity>
        ) : (
          <>
            {/* Answer reveal */}
            <View style={[styles.revealCard, answerState === 'correct' ? styles.revealCorrect : styles.revealWrong]}>
              <Text style={styles.revealLabel}>
                {answerState === 'correct' ? '✓ Correct' : '✗ Incorrect'}
              </Text>
              {answerState === 'wrong' && currentQuestion.type === 'formula' && (
                <Text style={styles.revealAnswer}>
                  Correct answer: {currentQuestion.correctAnswer}
                </Text>
              )}
            </View>

            {/* Coaching card */}
            {answerState === 'wrong' && (
              <View style={[styles.card, GlassEffect, styles.coachingCard]}>
                <Text style={styles.coachingLabel}>COACH</Text>
                {coachingLoading ? (
                  <ActivityIndicator color={Theme.colors.accent} />
                ) : (
                  <Text style={styles.coachingText}>{coachingText ?? 'Review the step-by-step above.'}</Text>
                )}
              </View>
            )}

            <TouchableOpacity style={styles.nextBtn} onPress={handleNext}>
              <Text style={styles.nextText}>
                {questionIndex === 9 ? 'See Results' : 'Next Question'}
              </Text>
              <Ionicons name="arrow-forward" size={18} color="#fff" />
            </TouchableOpacity>
          </>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Theme.colors.background },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: Theme.colors.background },
  loadingText: { color: '#aaa', marginTop: 12, fontSize: 16 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingTop: 56, paddingBottom: 16 },
  progress: { color: '#aaa', fontSize: 14, fontWeight: '600' },
  tierBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12, borderWidth: 1 },
  tierBadgeText: { fontSize: 12, fontWeight: '700' },
  backBtn: { padding: 8 },
  questionContent: { padding: 16, paddingBottom: 60 },
  resultsContent: { padding: 16, paddingBottom: 80, paddingTop: 56 },
  categoryLabel: { color: Theme.colors.accent, fontSize: 11, fontWeight: '700', letterSpacing: 1.5, marginBottom: 8, marginLeft: 4 },
  card: { borderRadius: 16, padding: 20, marginBottom: 16, backgroundColor: 'rgba(255,255,255,0.05)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)' },
  questionText: { color: '#fff', fontSize: 16, lineHeight: 24 },
  formulaInput: { borderWidth: 1, borderColor: 'rgba(255,255,255,0.2)', borderRadius: 12, padding: 16, color: '#fff', fontSize: 18, backgroundColor: 'rgba(255,255,255,0.05)', marginBottom: 16 },
  inputCorrect: { borderColor: '#4CAF50' },
  inputWrong: { borderColor: '#F44336' },
  optionsContainer: { gap: 10, marginBottom: 16 },
  optionBtn: { padding: 16, borderRadius: 12, borderWidth: 1, borderColor: 'rgba(255,255,255,0.15)', backgroundColor: 'rgba(255,255,255,0.05)' },
  optionSelected: { borderColor: Theme.colors.accent, backgroundColor: 'rgba(212,165,116,0.1)' },
  optionCorrect: { borderColor: '#4CAF50', backgroundColor: 'rgba(76,175,80,0.15)' },
  optionWrong: { borderColor: '#F44336', backgroundColor: 'rgba(244,67,54,0.15)' },
  optionText: { color: '#fff', fontSize: 15 },
  submitBtn: { backgroundColor: Theme.colors.accent, padding: 16, borderRadius: 14, alignItems: 'center', marginBottom: 16 },
  submitDisabled: { opacity: 0.4 },
  submitText: { color: '#000', fontSize: 16, fontWeight: '700' },
  revealCard: { padding: 14, borderRadius: 12, marginBottom: 12, borderWidth: 1 },
  revealCorrect: { backgroundColor: 'rgba(76,175,80,0.15)', borderColor: '#4CAF50' },
  revealWrong: { backgroundColor: 'rgba(244,67,54,0.15)', borderColor: '#F44336' },
  revealLabel: { color: '#fff', fontWeight: '700', fontSize: 15 },
  revealAnswer: { color: '#aaa', fontSize: 14, marginTop: 4 },
  coachingCard: { borderColor: 'rgba(212,165,116,0.3)' },
  coachingLabel: { color: Theme.colors.accent, fontSize: 11, fontWeight: '700', letterSpacing: 1.5, marginBottom: 8 },
  coachingText: { color: '#ddd', fontSize: 15, lineHeight: 22 },
  nextBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, backgroundColor: 'rgba(255,255,255,0.1)', padding: 16, borderRadius: 14, borderWidth: 1, borderColor: 'rgba(255,255,255,0.2)' },
  nextText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  // Results
  bigScore: { color: Theme.colors.accent, fontSize: 64, fontWeight: '800', textAlign: 'center', marginTop: 8 },
  scoreSubLabel: { color: '#aaa', fontSize: 16, textAlign: 'center', marginBottom: 4 },
  cardLabel: { color: Theme.colors.accent, fontSize: 11, fontWeight: '700', letterSpacing: 1.5, marginBottom: 12 },
  tierLabel: { color: '#aaa', fontSize: 14, textAlign: 'center', marginTop: 4 },
  pbBadge: { backgroundColor: 'rgba(212,165,116,0.2)', borderRadius: 8, padding: 8, marginTop: 10, alignItems: 'center' },
  pbText: { color: Theme.colors.accent, fontWeight: '700', fontSize: 14 },
  pbSubtext: { color: '#666', fontSize: 13, textAlign: 'center', marginTop: 6 },
  summaryWeak: { color: '#fff', fontWeight: '700', fontSize: 16, marginBottom: 6 },
  summaryText: { color: '#bbb', fontSize: 14, lineHeight: 20, marginBottom: 8 },
  summaryRec: { color: Theme.colors.accent, fontSize: 14, fontStyle: 'italic' },
  lbRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: 'rgba(255,255,255,0.05)' },
  lbRowHighlight: { backgroundColor: 'rgba(212,165,116,0.08)', borderRadius: 8, paddingHorizontal: 6 },
  lbRank: { color: '#666', width: 32, fontSize: 13 },
  lbName: { color: '#fff', flex: 1, fontSize: 14 },
  lbScore: { color: Theme.colors.accent, fontWeight: '700', fontSize: 14 },
  replayBtn: { backgroundColor: Theme.colors.accent, padding: 18, borderRadius: 14, alignItems: 'center', marginTop: 8 },
  replayText: { color: '#000', fontSize: 16, fontWeight: '700' },
});
```

- [ ] **Step 2: Type-check**

```bash
npx tsc --noEmit -p .
```

Fix any type errors. Common issues:
- `GlassEffect` may be a style object — spread it as `style={[styles.card, GlassEffect]}` or check `constants/theme.ts` for its shape and adjust usage.
- If `useAuthStore` selector signature differs, check `lib/store/auth.ts` and adjust.

- [ ] **Step 3: Commit**

```bash
git add app/practice/ag-tech/gauntlet.tsx
git commit -m "feat(ag-tech): add Formula Gauntlet screen with adaptive difficulty + AI coaching"
```

---

## Task 7: Update hub + remove math-drill

**Files:**
- Modify: `app/practice/ag-tech/index.tsx`
- Delete: `app/practice/ag-tech/math-drill.tsx`

- [ ] **Step 1: Update hub route**

In `app/practice/ag-tech/index.tsx`, find the "Scenario Math Machine" card's `onPress`:

```tsx
onPress={() => router.push('/practice/ag-tech/math-drill' as any)}
```

Replace with:

```tsx
onPress={() => router.push('/practice/ag-tech/gauntlet' as any)}
```

Also update the card's title and description if they still say "Scenario Math Machine":

```tsx
<Text style={styles.modeTitle}>Formula Gauntlet</Text>
<Text style={styles.modeDesc}>
  Adaptive difficulty {'•'} Math + Written {'•'} AI coaching
</Text>
```

- [ ] **Step 2: Remove math-drill.tsx**

```bash
rm "/Volumes/Samsung PSSD T7/ag-coach-app/app/practice/ag-tech/math-drill.tsx"
```

- [ ] **Step 3: Type-check**

```bash
npx tsc --noEmit -p .
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add app/practice/ag-tech/index.tsx
git rm app/practice/ag-tech/math-drill.tsx
git commit -m "feat(ag-tech): wire Formula Gauntlet into hub, remove math-drill screen"
```

---

## Smoke Test Checklist

After all tasks complete:

- [ ] App starts without TS errors (`npx tsc --noEmit -p .`)
- [ ] Ag Tech hub shows "Formula Gauntlet" card (not "Scenario Math Machine")
- [ ] Tapping card navigates to gauntlet screen
- [ ] Gauntlet loads (spinner → first question appears)
- [ ] Formula question: entering correct answer → green reveal → Next works
- [ ] Formula question: entering wrong answer → red reveal → coaching card appears
- [ ] RAG question appears at positions 3, 6, 9 (0-indexed 2, 5, 8)
- [ ] After Q10 → results screen shows score, personal best, AI summary
- [ ] Chapter leaderboard renders if student is in a classroom
- [ ] "Run Again" replays the gauntlet

Run `check-site` skill after deploying to verify no blank screen regressions.
