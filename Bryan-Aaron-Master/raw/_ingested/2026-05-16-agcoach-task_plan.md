# Task Plan — Livestock Contest Score Calculator

## Business Goal
Students enter post-contest card data → instant accurate scores by component. Coaches see every student's scores in a table with team totals (top 3) — replacing manual spreadsheet math.

## Contest Structure (725 pts individual / 2,175 pts team)
| Component | Classes | Pts/Class | Total |
|---|---|---|---|
| Placing (Hormel) | 7 | 50 | 350 |
| Questions | 3 (of 7) | 25 | 75 |
| Keep/Cull Female | 3 | 50 | 150 |
| Slaughter Grading | 1 | 50 | 50 |
| Feeder Grading | 1 | 50 | 50 |
| Written Exam | 1 | 50 | 50 |
| **TOTAL** | | | **725** |

---

## Step 1 — Supabase Migration
Create `livestock_contest_sessions` table.

Schema:
- `placing_classes` JSONB array (7 items): official, cuts, contestant, score, has_questions, question_scores, questions_total
- `keep_cull_classes` JSONB array (3 items): point_values {1–8}, selections [4], score
- `slaughter_animals` JSONB array (5 items): official_quality, official_yield, student_quality, student_yield, quality_score, yield_score
- `feeder_animals` JSONB array (5 items): official_frame, official_muscle, student_frame, student_muscle, frame_score, muscle_score
- `written_exam_score` int (0–50)
- `placing_total`, `questions_total`, `keep_cull_total`, `slaughter_total`, `feeder_total` ints
- `individual_total` int (0–725)
- `contest_name`, `contest_date`, `user_id`, `team_id`

## Step 2 — Scoring Engine (`lib/livestock-scoring.ts`)
Pure functions:
- `calculateHormelScore(official, cuts, contestant)` → 0–50
- `validateCuts(cuts)` → boolean
- `calculateKeepCullScore(pointValues, selections)` → 0–50
- `calculateSlaughterAnimalScore(offQ, offY, stuQ, stuY)` → 0–10
- `calculateFeederAnimalScore(offF, offM, stuF, stuM)` → 0–10
- `calculateContestTotal(session)` → all component totals

Grade scales:
- Quality: Standard, Select, Choice, Prime (each with -, mid, + subdivisions = 12 steps)
- Yield: 1–5 in 0.5 steps
- Frame: Small, Medium, Large
- Muscle: 1 (Thick), 2 (Moderate), 3 (Thin)

## Step 3 — Student Entry Wizard (`app/practice/livestock-judging/contest-entry.tsx`)
Multi-step form (dark glass). Steps:
1. Contest info (name, date)
2. Placing Classes 1–7 (official placing, cuts, contestant placing; + 5 question scores on flagged classes)
3. Keep/Cull Classes 1–3 (8 animal point values + 4 selections)
4. Slaughter Grading (5 animals: official + student quality/yield)
5. Feeder Grading (5 animals: official + student frame/muscle)
6. Written Exam (enter raw score 0–50)
7. Summary + save

## Step 4 — Results Screen (`app/practice/livestock-judging/contest-results.tsx`)
Scorecard table: each component, your score vs max, percentage.
Per-class collapsible breakdown. Color-coded (green ≥80%, gold ≥60%, red <60%).

## Step 5 — Teacher Score Table (`app/(admin)/livestock-scores.tsx`)
Columns: Student | Placing | Questions | Keep/Cull | Grading | Written | Individual Total | Team
- Top 3 per team highlighted gold
- Team total row
- Sort by any column, filter by contest/date
- CSV export

## Step 6 — Student Score History (`app/practice/livestock-judging/contest-history.tsx`)
List of all past contest sessions for the logged-in student:
- Contest name, date, individual total / 725, percentage
- Color-coded score badge
- Tap row → full results breakdown (reuses contest-results.tsx)

## Step 7 — Growth View (tab inside contest-history.tsx)
- Line chart of individual total over time (last N contests)
- Per-component sparklines: placing, questions, keep/cull, grading, written
- Highlights best score and most-improved section

## Verification Checklist
- [ ] Hormel: Official [3,1,2,4], Cuts [3,6,2], Contestant [4,1,2,3] → 17
- [ ] Keep/Cull: Student A [6,8,4,2] with values 11,18,7,3 → 39
- [ ] Slaughter: correct quality=4, ½off=3, 1off=2, >1=0; correct yield=6, ½off=4, 1off=2, >1=0
- [ ] Feeder: correct=5, 1off=3, 2off=1, 3+off=0 (both frame and muscle)
- [ ] Team total = top 3 individual scores summed, max 2,175

---

# Previous Phases

## Phase 1: Blueprint (Current)
- [x] Save Master Prompt to `.agent/MASTER_PROMPT.md`
- [x] Initialize Project Memory (`task_plan.md`, `findings.md`, `progress.md`)
- [x] Initialize Project Constitution (`claude.md`)
- [ ] Answer Discovery Questions
- [ ] Define Data Schema in `gemini.md`
- [ ] Approve Blueprint

## Phase 2: Link (Complete)
- [x] Verify API connectivity (Confirmed by user)
- [x] Build minimal handshake scripts (Skipped per confirmation)

## Phase 3: Architect (In Progress)
- [/] Define SOPs in `architecture/`
    - [x] Creed Speaking Simulation SOP
    - [/] Job Interview Simulation SOP
- [/] Build deterministic tools in `tools/`
    - [x] `rubric_calculator.py`
    - [x] `whisper_transcription_validator.py`

## Phase 4: Stylize
- [ ] Refine payload formats
- [ ] UI/UX polish

## Phase 5: Trigger
- [ ] Deployment
- [ ] Documentation finalize
