---
name: agcoach-poultry-judging-feature
type: source
tags: [ag-coach-pro, poultry, rag, notebooklm, module-design]
source_files: [raw/_ingested/2026-05-16-agcoach-poultry-judging-feature.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Poultry Judging Feature

`docs/POULTRY_JUDGING_FEATURE.md`. Full module-design + NotebookLM-integration plan for the Poultry Evaluation CDE. Tactical subset `POULTRY_IMPLEMENTATION_QUICK_START.md` not separately ingested.

## Six judging categories

Live Broiler Placing · RTC Carcass Placing · Egg Grading · Processed Product Evaluation · Poultry Parts ID (27+ parts) · Written Exam.

## Current module structure

```
app/practice/poultry-eval/
  index.tsx         hub (7 sections)
  basics.tsx        curriculum + slide decks
  live-placing.tsx  live bird judging
  carcass-placing.tsx
  eggs.tsx          interior/exterior grading
  processed.tsx     defect evaluation
  parts.tsx         27+ parts ID
  exam.tsx          30 MC questions

lib/poultry-eval-quiz.ts          RAG wrapper
lib/prompts/poultry-prompts.ts    MISSING — must be created
lib/data/poultry-id.ts            egg grades, parts, defects
lib/data/poultry-questions.ts     static fallback
lib/data/slide-decks/poultry/     curriculum slide decks
```

## Quiz integration

`generateRAGBatch('Poultry-Production', 'multiple_choice', 6, 'senior')` per topic. Contest mode auto-generates 30 MC questions across `Poultry-Production` (7), `Poultry-Anatomy` (6), `Poultry-Grading` (6), `Poultry-Nutrition` (6), `Poultry-Health` (5).

## NotebookLM knowledge plan

5 NotebookLM projects → export Study Guide (md) + Q&A (json) → `python3 ingest_knowledge.py --source ... --category Poultry --subcategory <topic>` → embeddings in `knowledge_documents`:

| Project | Sources |
|---|---|
| USDA Poultry Grading | USDA Standards, CFR Title 7 Part 56 |
| Live Bird Evaluation | FFA Poultry CDE Rules, state contest archives, judging cards |
| Poultry Anatomy & Parts | USDA carcass breakdown, butchering guides |
| Egg Standards & Quality | USDA AMS egg standards, candling guides |
| Poultry Nutrition & Health | USDA poultry production handbook, feed formulation |

## Engagement features

- **Concept Unlock Path** — `prerequisites: ['basics-guide', 'carcass-placing']` gates live-placing (capstone).
- **Annotated slide decks** in basics.tsx (live structure, carcass grades, egg candling, processed defects, parts anatomy).
- **Scenario-based placing** — "Judger's Dilemma — Fast & Thin vs Slow & Fat", "Split Decision — The Pair Talk", justify in 60s.
- **Defect pattern recognition** — multi-image QA-line "which fail" picker.
- **Comparative judging** — pair/trio placing with explanation of judging logic.

## Build status

- Complete: hub UI, RAG infra, poultry data types, contest routing (`cde-poultry`).
- Partial: every screen is skeleton (basics, live-placing, carcass-placing, eggs, processed, parts, exam).
- Missing: `lib/prompts/poultry-prompts.ts`, NotebookLM ingest, `TOPIC_QUERIES` entries, `PracticeType` 'poultry-eval', `FEATURE_TIERS` mapping, 50+ images, scenarios JSON.

## 3-phase roadmap

1. Foundation (W1–2) — prompts file, TOPIC_QUERIES, history union, tier mapping, 30-MC exam working end-to-end.
2. Image-based practice (W3–4) — slide decks, interactive labeling, candling grades, defect spotting, NotebookLM ingest.
3. Scenario + comparative (W5+) — placing scenarios, pair/trio decisions, feedback-with-reasoning, gated progression.

## Required file edits

1. `lib/ai/rag-quiz.ts` — add 5 entries to `TOPIC_QUERIES`.
2. `lib/store/history.ts` — add `'poultry-eval'` to `PracticeType` union.
3. `lib/tier.ts` — add `'poultry-eval': 'free'` to `FEATURE_TIERS`.
4. `app/contest/[id].tsx → startPractice()` — `if (legacyId === 'cde-poultry') router.push('/practice/poultry-eval')`.
5. Create `lib/prompts/poultry-prompts.ts` with system + MC + T/F prompt builders.

## Known issues

- Image management (50+ high-res); consider Cloudinary.
- `live-placing.tsx` needs realistic scenarios with decision trees — manual curation.
- Feedback system is binary right/wrong; poultry needs comparative reasoning.
- Prerequisite gating not yet implemented in router.

## Related

- [[../concepts/agcoach-poultry-judging-cde|Poultry Judging CDE]]
- [[agcoach-egg-evaluation-feature|Egg Evaluation Feature]]
- [[../concepts/agcoach-egg-evaluation-cde|Egg Evaluation CDE]]
- [[../concepts/agcoach-rag-architecture|RAG Architecture]]
- [[../concepts/agcoach-contest-modules|Contest Modules]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
