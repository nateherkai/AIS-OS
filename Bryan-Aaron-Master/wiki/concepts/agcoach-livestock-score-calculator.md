---
name: agcoach-livestock-score-calculator
type: concept
tags: [ag-coach-pro, livestock, scoring, contest, blueprint]
source_files: [raw/_ingested/2026-05-16-agcoach-task_plan.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Livestock Contest Score Calculator

Active blueprint module. Replaces the manual coach spreadsheet for the Livestock CDE: students enter post-contest card data → instant per-component scores → coach sees every student in a single table with top-3 team totals.

## Scoring math (725 / 2,175)

| Component | Classes | Pts/Class | Total |
|---|---:|---:|---:|
| Placing (Hormel) | 7 | 50 | 350 |
| Questions | 3 of 7 | 25 | 75 |
| Keep/Cull Female | 3 | 50 | 150 |
| Slaughter Grading | 1 | 50 | 50 |
| Feeder Grading | 1 | 50 | 50 |
| Written Exam | 1 | 50 | 50 |
| **Individual** | | | **725** |
| **Team (top 3)** | | | **2,175** |

## Surfaces

- `app/practice/livestock-judging/contest-entry.tsx` — 7-step dark-glass wizard.
- `app/practice/livestock-judging/contest-results.tsx` — color-coded scorecard (green ≥80% / gold ≥60% / red <60%), per-class collapsible.
- `app/practice/livestock-judging/contest-history.tsx` — per-student timeline; tap row → reuse results screen.
- `app/(admin)/livestock-scores.tsx` — teacher table (top-3 per team in gold, CSV export, sort/filter by contest).
- Growth tab inside history → line chart of individual total + per-component sparklines.

## Pure scoring engine (`lib/livestock-scoring.ts`)

- `calculateHormelScore(official, cuts, contestant) → 0..50`
- `validateCuts(cuts) → boolean`
- `calculateKeepCullScore(pointValues[8], selections[4]) → 0..50`
- `calculateSlaughterAnimalScore(offQ, offY, stuQ, stuY) → 0..10` (×5 animals = 50)
- `calculateFeederAnimalScore(offF, offM, stuF, stuM) → 0..10` (×5 animals = 50)
- `calculateContestTotal(session) → all component totals + individual_total`

Grade scales handled: **Quality** Standard/Select/Choice/Prime × (-, mid, +) = 12 steps. **Yield** 1–5 in 0.5 steps. **Frame** Small/Medium/Large. **Muscle** 1 Thick / 2 Moderate / 3 Thin.

## Persistence schema

`livestock_contest_sessions`:

- `placing_classes` JSONB[7] — official, cuts, contestant, score, has_questions, question_scores, questions_total.
- `keep_cull_classes` JSONB[3] — point_values{1..8}, selections[4], score.
- `slaughter_animals` JSONB[5] — official_quality, official_yield, student_quality, student_yield, quality_score, yield_score.
- `feeder_animals` JSONB[5] — official_frame, official_muscle, student_frame, student_muscle, frame_score, muscle_score.
- `written_exam_score` int 0..50.
- `placing_total`, `questions_total`, `keep_cull_total`, `slaughter_total`, `feeder_total`, `individual_total`.
- `contest_name`, `contest_date`, `user_id`, `team_id`.

## Verification fixtures

- Hormel: Official `[3,1,2,4]`, Cuts `[3,6,2]`, Contestant `[4,1,2,3]` → 17.
- Keep/Cull: Student `[6,8,4,2]` with values `11,18,7,3` → 39.
- Slaughter quality: 4 correct / 3 ½off / 2 1off / 0 >1off; same for yield.
- Feeder: 5 correct / 3 1off / 1 2off / 0 3+off (both frame and muscle).
- Team total = top 3 individual scores summed, max 2,175.

## Status

Phase 3 (Architect) work. Migration file + scoring engine + entry wizard not yet shipped on `main`. Blueprint locked; build queued behind brain-v2/v3 + onboarding-v2 stabilization.

## Related

- [[../sources/agcoach-task-plan-livestock-calc|Task Plan: Livestock Score Calculator]]
- [[agcoach-livestock-judging-cde|Livestock Judging CDE]]
- [[../sources/agcoach-agent-master-prompt|B.L.A.S.T. Master Prompt]]
- [[agcoach-contest-modules|Contest Modules]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
