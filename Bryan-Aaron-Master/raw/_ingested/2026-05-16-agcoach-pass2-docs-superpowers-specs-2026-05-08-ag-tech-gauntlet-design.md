# AG Tech Formula Gauntlet — Design Spec
**Date:** 2026-05-08  
**Module:** Ag Technology & Mechanical Systems CDE  
**Scope:** Replace `app/practice/ag-tech/math-drill.tsx` with adaptive Formula Gauntlet

---

## Overview

Replace the static math drill with a 10-question adaptive gauntlet mixing formula/math problems and RAG-backed written questions from Texas state ATMS CDE exams. Wrong answers trigger inline Gemini coaching. Results screen shows score, personal best, AI pattern summary, and chapter leaderboard.

---

## Architecture

### Files Changed / Created

| File | Action |
|------|--------|
| `app/practice/ag-tech/gauntlet.tsx` | New — replaces math-drill.tsx |
| `app/practice/ag-tech/math-drill.tsx` | Delete |
| `app/practice/ag-tech/index.tsx` | Update route: math-drill → gauntlet |
| `lib/prompts/ag-tech-prompts.ts` | New — all Gemini prompt strings for this module |
| `lib/data/ag-tech-formulas.ts` | Extend with difficulty tier tags per formula |
| `lib/ai/rag-quiz.ts` | Add `ag-tech-written` entry to `TOPIC_QUERIES` |
| `lib/store/history.ts` | Add `'ag-tech-gauntlet'` to PracticeType union |
| `supabase/migrations/<timestamp>_ag_tech_gauntlet_scores.sql` | New table migration |

### Question Types

```ts
type GauntletQuestion =
  | { type: 'formula'; template: FormulaTemplate; instance: ProblemInstance }
  | { type: 'rag'; question: QuizQuestion }
```

Session = 10 questions, ~60% formula / 40% RAG. Ratio maintained by interleaving: positions 1,2,4,5,7,8,10 = formula; 3,6,9 = RAG.

### Adaptive Difficulty

Three tiers mapping to contest levels:

| Tier | Label | Formula Filter | RAG Difficulty |
|------|-------|---------------|----------------|
| 1 | Area | `difficulty: 'easy'` | `easy` |
| 2 | Invitational | `difficulty: 'medium'` | `medium` |
| 3 | State | `difficulty: 'hard'` | `hard` |

Rules:
- Start at Tier 1
- 2 consecutive correct → advance one tier (cap at 3)
- Wrong answer → hold current tier (no regression)
- Tier badge displayed on question card

---

## Screen Flow

```
Hub (index.tsx)
  └─ "Formula Gauntlet" button → gauntlet.tsx

gauntlet.tsx (question view)
  ├─ Question card (formula scenario or MCQ)
  ├─ Tier badge + streak counter
  ├─ Answer input / option selector
  ├─ Submit → reveal correct answer
  │     └─ Wrong → Gemini coaching card (collapsible, must dismiss)
  └─ Next → repeat until Q10

gauntlet.tsx (results view — same screen, swap state)
  ├─ Score card (score / tier reached / PB delta)
  ├─ AI pattern summary card
  └─ Chapter leaderboard (top 10, current student highlighted)
```

---

## AI Coaching Layer

### Per-Question Coaching

Triggered on wrong answer. Single Gemini call.

**Payload:** formula name, student's randomized variable values, their submitted answer, correct answer, step-by-step solution string.

**Response:** 2-3 sentence explanation using student's actual numbers. Rendered as collapsible card below answer reveal. Student must dismiss before advancing.

### Session Summary

Single Gemini call after Q10. Only fires if ≥1 miss.

**Payload:** array of missed questions with `{ category, studentAnswer, correctAnswer, questionType }`.

**Response schema:**
```ts
{
  weakCategory: string,       // e.g. "Hydraulics"
  pattern: string,            // e.g. "Forgetting unit conversion before calculating"
  drillRecommendation: string // e.g. "Review hydraulic pressure formulas, focus on PSI↔Pa conversion"
}
```

Both calls use `parseAIJson` from `lib/ai/parser.ts`. Summary cached in component state — no re-fetch on scroll.

All prompt strings live in `lib/prompts/ag-tech-prompts.ts`.

---

## Scoring

```
score = (correct / 10) × 100 + tier_bonus
tier_bonus: Tier 1 = 0, Tier 2 = +10, Tier 3 = +20
max score: 120
```

Personal best: compare current score to student's all-time best from `ag_tech_gauntlet_scores`. Show delta on results screen ("New PB! +12 pts").

---

## Database

### New Table: `ag_tech_gauntlet_scores`

```sql
create table ag_tech_gauntlet_scores (
  id uuid primary key default gen_random_uuid(),
  student_id uuid references auth.users(id) on delete cascade,
  classroom_id uuid references classrooms(id) on delete set null,
  score integer not null,
  tier_reached integer not null check (tier_reached between 1 and 3),
  correct_count integer not null,
  missed_categories text[] default '{}',
  created_at timestamptz default now()
);

create index on ag_tech_gauntlet_scores (student_id, score desc);
create index on ag_tech_gauntlet_scores (classroom_id, score desc);
```

Migration file: `supabase/migrations/<timestamp>_ag_tech_gauntlet_scores.sql`

### Leaderboard Query

`ag_tech_gauntlet_scores` joined to `classroom_students` filtered by `classroom_id`. Top 10 by best score per student. No real-time subscription — query on results screen mount.

---

## RAG Prerequisite

Before build: run `rag-knowledge-ingest` skill on state exam PDFs from `Texas_FFA_Resources/CDE_Events/Ag_Technology/` (prioritize `2017_ATMS_State_CDE_Exam.pdf`, `2018_TX_FFA_State_ATMS_CDE_Written_Exam.pdf`, `2016_State_ATMS_CDE_Exam.pdf`).

Add to `TOPIC_QUERIES` in `lib/ai/rag-quiz.ts`:
```ts
'ag-tech-written': 'agricultural technology mechanical systems equipment power hydraulics electrical wiring engine'
```

---

## Out of Scope (Phase 2)

- Skill Area Simulation Stations (welding, concrete, DC wiring, GPS)
- State-wide leaderboard
- Teacher dashboard visibility into gauntlet scores
