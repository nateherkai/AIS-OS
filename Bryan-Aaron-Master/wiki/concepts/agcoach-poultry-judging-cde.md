---
name: agcoach-poultry-judging-cde
type: concept
tags: [ag-coach-pro, cde, poultry, judging, rag, notebooklm]
source_files: [raw/_ingested/2026-05-16-agcoach-poultry-judging-feature.md, raw/_ingested/2026-05-16-agcoach-CLAUDE.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Poultry Judging CDE

Texas FFA Poultry Evaluation CDE. Six categories: Live Broiler Placing · RTC Carcass Placing · Egg Grading · Processed Product Evaluation · Poultry Parts ID (27+ parts) · Written Exam. Module ID `cde-poultry`; route `/practice/poultry-eval`.

## Contest exam shape

30 MC questions in fixed breakdown (defined in [[../sources/agcoach-poultry-judging-feature|feature spec]]):

| Topic | Count |
|---|---:|
| Poultry-Production | 7 |
| Poultry-Anatomy | 6 |
| Poultry-Grading | 6 |
| Poultry-Nutrition | 6 |
| Poultry-Health | 5 |

All generated via `generateRAGBatch(topic, 'multiple_choice', count, 'senior')` from [[agcoach-rag-architecture|RAG]]. Topics must each have a `TOPIC_QUERIES` entry in `lib/ai/rag-quiz.ts`.

## Knowledge sources

Five NotebookLM projects → Study Guide + Q&A export → `python3 ingest_knowledge.py --category Poultry --subcategory <topic>` → embeddings in `knowledge_documents`:

| Project | Primary sources |
|---|---|
| USDA Poultry Grading | USDA Standards & Grades handbook, CFR Title 7 Part 56 |
| Live Bird Evaluation | FFA Poultry CDE Rules, state contest archives, judging cards |
| Poultry Anatomy & Parts | USDA carcass breakdown, butchering guides |
| Egg Standards & Quality | USDA AMS standards, candling guides |
| Poultry Nutrition & Health | USDA poultry production handbook, feed formulation |

## File map (target)

```
app/practice/poultry-eval/
  index.tsx              hub (7 sections)
  basics.tsx             5 annotated slide decks
  live-placing.tsx       scenario-based placing
  carcass-placing.tsx    pair/trio judging with reasoning
  eggs.tsx               candling grades + defect spotting (see Egg Eval CDE)
  processed.tsx          multi-image QA-line defect picker
  parts.tsx              interactive 27-part labeling
  exam.tsx               30-MC contest

lib/poultry-eval-quiz.ts
lib/prompts/poultry-prompts.ts        (must be created)
lib/data/poultry-id.ts                grades / parts / defects
lib/data/poultry-questions.ts         static fallback
lib/data/slide-decks/poultry/
lib/data/poultry-scenarios.ts         (must be created)
```

## Wiring checklist (from feature spec)

1. `lib/ai/rag-quiz.ts` — add 5 `TOPIC_QUERIES` entries.
2. `lib/store/history.ts` — add `'poultry-eval'` to `PracticeType` union.
3. `lib/tier.ts` — add `'poultry-eval': 'free'` to `FEATURE_TIERS`.
4. `app/contest/[id].tsx` → `startPractice()` — route `cde-poultry` → `/practice/poultry-eval`.
5. Create `lib/prompts/poultry-prompts.ts` (system + MC + T/F builders).

## Engagement design highlights

- **Concept Unlock Path** — `prerequisites: ['basics-guide', 'carcass-placing']` gates live-placing (capstone).
- **Scenario placing** — "Judger's Dilemma — Fast & Thin vs Slow & Fat", "Split Decision — The Pair Talk"; 60s justification.
- **Comparative judging** — pair/trio with explanation of judging logic, not binary right/wrong.
- **Defect QA line** — pick which nuggets fail on a simulated production line.

## Build status (2026-05-16)

- Done: hub UI, RAG infra, poultry data types, contest routing registered.
- Skeleton: every practice screen.
- Missing: prompts file, NotebookLM ingest, TOPIC_QUERIES, PracticeType, tier mapping, 50+ images, scenarios JSON.

## Related

- [[../sources/agcoach-poultry-judging-feature|Poultry Judging Feature spec]]
- [[agcoach-egg-evaluation-cde|Egg Evaluation CDE]]
- [[agcoach-rag-architecture|RAG Architecture]]
- [[agcoach-contest-modules|Contest Modules]]
- [[agcoach-vet-science-cde|Vet Science CDE]]
- [[agcoach-livestock-judging-cde|Livestock Judging CDE]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
