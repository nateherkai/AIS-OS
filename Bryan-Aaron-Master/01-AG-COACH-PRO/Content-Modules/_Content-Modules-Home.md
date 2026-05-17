# Content Modules — Ag Coach Pro

> Human-curated CDE/LDE module inventory.
> Generated 2026-05-16 from ag-coach-app/BUSINESS_BRAIN.md + ag-coach-app/CLAUDE.md
> Full wiki layer → [[../../wiki/concepts/agcoach-contest-modules|Contest Modules Wiki Page]]

---

## Module Counts

- **Total contest modules:** 40 (29 CDEs + 11 LDEs)
- **Active CDEs:** 28 of 29 (Milk Quality is `is_active: false`)
- **Active LDEs:** 11 of 11

---

## CDE Modules (Active — 28)

Agronomy, Ag Communications, Ag Technology & Mechanical Systems, Ag Sales, Applied Ag Engineering, Cotton, Dairy Cattle, Entomology, Environmental & Natural Resources, **Farm & Agribusiness Management**, Floriculture, Food Science, Forage, Forestry, Homesite Evaluation, Horse, Land, **Livestock Judging**, Marketing Plan, **Meats (Meats Evaluation & Technology)**, Nursery/Landscape, Poultry, Plant Identification, Range, Tractor Technician, **Veterinary Science**, Wildlife, Wool

**Bryan's specialty:** Livestock Judging — National Champion background. This module is the core differentiator.

**Inactive:** Milk Quality (planned future activation)

## LDE Modules (11)

Agricultural Issues Forum, Agricultural Skill Demonstration, Senior FFA Quiz, Greenhand FFA Quiz, Chapter Conducting, **Creed Speaking**, Spanish Creed Speaking, FFA Broadcasting, Public Relations, **Job Interview**, Ag Advocacy

---

## Priority CDE Build Status (Initial 5)

| CDE | Content Pack | Build Status | Notes |
|---|---|---|---|
| Farm Business Management | ✅ Built | Needs: interactive calculator, case study scenarios | Only CDE with pre-built content pack |
| Livestock Judging | ⚠️ Rules found | Active — Bryan's specialty | Phenotype Analyzer live; Score Calculator in progress |
| Veterinary Science | ⚠️ Rules found | Active | Highest-volume CDE in Texas FFA |
| Meat Science | ⚠️ Rules found | Active | USDA grading, marbling, yield grades |
| Creed Speaking | ⚠️ Rules found | Active | 1,000-pt AI video scoring rubric |

---

## 4-Screen Module Pattern

Every CDE module follows this file structure:
```
app/practice/[name]/
  index.tsx      — Hub: Contest Hub + Study + Flashcards
  builder.tsx    — Topic/count/format pickers
  quiz.tsx       — Quiz engine with scoring + results
  flashcards.tsx — Flip-card mode
lib/[name]-quiz.ts        — generateXxxQuiz() + generateXxxFlashcards()
lib/prompts/[name]-prompts.ts  — AI prompts for the domain
```

## 9-Step Checklist to Add a New Module

1. `lib/[name]-quiz.ts` — wrap `generateRAGBatch`, define `TOPIC_QUERIES` entry
2. `app/practice/[name]/index.tsx` — Hub screen
3. `app/practice/[name]/builder.tsx` — pickers
4. `app/practice/[name]/quiz.tsx` — quiz engine
5. `app/practice/[name]/flashcards.tsx` — flashcard mode
6. `lib/store/history.ts` — add new `PracticeType`
7. `app/contest/[id].tsx` — add `if (legacyId === …)` block
8. `lib/tier.ts` — add feature → tier mapping
9. `constants/contests.ts` — set `is_active: true` when ready
+ RAG prerequisite: ingest PDF via `rag-knowledge-ingest` skill first

---

## Recent Module Additions

- **Poultry Judging** — Full design spec complete; NotebookLM pipeline planned
- **Egg Evaluation** — Image-based air-cell measurement; 5 open questions before build
- **Wool & Mohair** — Study guide complete; module spec approved 2026-05-06

---

## Related Wiki

- [[../../wiki/concepts/agcoach-contest-modules|Contest Modules (full 40-module list)]]
- [[../../wiki/concepts/agcoach-livestock-judging-cde|Livestock Judging CDE]]
- [[../../wiki/concepts/agcoach-vet-science-cde|Veterinary Science CDE]]
- [[../../wiki/concepts/agcoach-meat-science-cde|Meat Science CDE]]
- [[../../wiki/concepts/agcoach-creed-speaking-lde|Creed Speaking LDE]]
- [[../../wiki/concepts/agcoach-farm-business-management-cde|Farm Business Management CDE]]
- [[../../wiki/concepts/agcoach-poultry-judging-cde|Poultry Judging CDE]]
- [[../../wiki/concepts/agcoach-egg-evaluation-cde|Egg Evaluation CDE]]
- [[../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
