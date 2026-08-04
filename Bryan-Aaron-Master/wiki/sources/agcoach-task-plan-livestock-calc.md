---
name: agcoach-task-plan-livestock-calc
type: source
tags: [ag-coach-pro, livestock, scoring, contest, blueprint]
source_files: [raw/_ingested/2026-05-16-agcoach-task_plan.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Task Plan: Livestock Contest Score Calculator

Active blueprint for replacing the manual coach spreadsheet with an in-app calculator. Targets Phase 3 (Architect) of the B.L.A.S.T. master prompt.

## Goal

Students enter post-contest card data → instant accurate scores by component. Coaches see every student in a table with team totals (top 3) — replacing manual spreadsheet math.

## Contest Math (725 pts individual / 2,175 pts team)

| Component | Classes | Pts/Class | Total |
|---|---|---|---|
| Placing (Hormel) | 7 | 50 | 350 |
| Questions | 3 of 7 | 25 | 75 |
| Keep/Cull Female | 3 | 50 | 150 |
| Slaughter Grading | 1 | 50 | 50 |
| Feeder Grading | 1 | 50 | 50 |
| Written Exam | 1 | 50 | 50 |
| **TOTAL** | | | **725** |

Team total = top 3 individuals, max 2,175.

## 7-step plan

1. Migration → `livestock_contest_sessions` (JSONB per component + per-component totals + individual_total).
2. Scoring engine `lib/livestock-scoring.ts` (pure functions: `calculateHormelScore`, `validateCuts`, `calculateKeepCullScore`, `calculateSlaughterAnimalScore`, `calculateFeederAnimalScore`, `calculateContestTotal`).
3. Student entry wizard `app/practice/livestock-judging/contest-entry.tsx` (7-step dark-glass form).
4. Results screen `contest-results.tsx` (color-coded table, per-class collapsible).
5. Teacher table `app/(admin)/livestock-scores.tsx` (top-3-per-team gold, CSV export).
6. Student history `contest-history.tsx`.
7. Growth view (tab inside history): line chart + per-component sparklines.

## Grade scales

- Quality: Standard / Select / Choice / Prime × (-, mid, +) = 12 steps.
- Yield: 1–5 in 0.5 steps.
- Frame: Small / Medium / Large.
- Muscle: 1 (Thick) / 2 (Moderate) / 3 (Thin).

## Verification fixtures

- Hormel: Official `[3,1,2,4]`, Cuts `[3,6,2]`, Contestant `[4,1,2,3]` → 17.
- Keep/Cull: Student A `[6,8,4,2]` with values `11,18,7,3` → 39.
- Slaughter quality: 4 / 3 / 2 / 0 for correct, ½off, 1off, >1off.
- Feeder: 5 / 3 / 1 / 0 for correct, 1off, 2off, 3+off (both frame & muscle).

## Status snapshot

Phase 1 Blueprint: discovery questions + blueprint approval still open. Phase 2 Link: complete. Phase 3 Architect: SOPs + tools partially complete (Creed SOP done, Job Interview SOP in progress; `rubric_calculator.py` + `whisper_transcription_validator.py` done).

## Related

- [[../concepts/agcoach-livestock-score-calculator|Livestock Contest Score Calculator]]
- [[../concepts/agcoach-livestock-judging-cde|Livestock Judging CDE]]
- [[agcoach-agent-master-prompt|B.L.A.S.T. Master Prompt]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
