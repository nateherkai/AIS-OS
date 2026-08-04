---
name: agcoach-contest-modules
type: concept
tags: [ag-coach-pro, cde, lde, ffa, contests, modules]
source_files: [raw/_ingested/2026-05-16-agcoach-BUSINESS_BRAIN.md, raw/_ingested/2026-05-16-agcoach-CLAUDE.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Contest Modules (40 Total)

## CDE (Career Development Events) — 29 Active, 1 Inactive

Active CDEs: Agronomy, Ag Communications, Ag Technology & Mechanical Systems, Ag Sales, Applied Ag Engineering, Cotton, Dairy Cattle, Entomology, Environmental & Natural Resources, Farm & Agribusiness Management, Floriculture, Food Science, Forage, Forestry, Homesite Evaluation, Horse, Land, Livestock Judging, Marketing Plan, Meats, Nursery/Landscape, Poultry, Plant Identification, Range, Tractor Technician, Veterinary Science, Wildlife, Wool

**Inactive**: Milk Quality (`is_active: false` in `constants/contests.ts`)

## LDE (Leadership Development Events) — 11 Active

Agricultural Issues Forum, Agricultural Skill Demonstration, Senior FFA Quiz, Greenhand FFA Quiz, Chapter Conducting, Creed Speaking, Spanish Creed Speaking, FFA Broadcasting, Public Relations, Job Interview, Ag Advocacy

## Practice Module Architecture

Each CDE has 4 screens under `app/practice/[module]/`:
- `index.tsx` — Hub: Contest Hub card + Study & Practice + Flashcards
- `builder.tsx` — Topic/count/format pickers → launches quiz
- `quiz.tsx` — Live quiz engine with scoring + results
- `flashcards.tsx` — Flip-card study mode

Supporting lib: `lib/[module]-quiz.ts` wraps `generateRAGBatch()`.

## Adding a New CDE Module (9-Step Checklist)

1. `lib/[name]-quiz.ts` — wrap `generateRAGBatch`, add to `TOPIC_QUERIES` in `lib/ai/rag-quiz.ts`
2. `app/practice/[name]/index.tsx` — Hub screen
3. `app/practice/[name]/builder.tsx` — pickers
4. `app/practice/[name]/quiz.tsx` — quiz engine
5. `app/practice/[name]/flashcards.tsx` — flashcard mode
6. `lib/store/history.ts` — add new `PracticeType` to union
7. `app/contest/[id].tsx` — add `if (legacyId === …)` block in `startPractice()`
8. `lib/tier.ts` — add feature key → tier mapping in `FEATURE_TIERS`
9. `constants/contests.ts` — set `is_active: true` when ready

**RAG prerequisite**: Ingest source PDF via `rag-knowledge-ingest` skill first.

## Stub Modules (Need Work)

- `food-science` — 851-line monolith, needs split into 4 screens
- `ag-advocacy` — stub routing
- `ag-issues` — stub routing

## Contest Routing: The "ID Handshake"

`app/(tabs)/cde.tsx` → `app/contest/[id].tsx` → `resolveContestId()` maps UUID or legacy string to `legacyId` (e.g., `cde-livestock`) → `startPractice()` chain of `if (legacyId === …)` guards → `router.push` to practice module.

## Related

- [[../concepts/agcoach-rag-architecture|RAG Architecture]]
- [[../concepts/agcoach-vet-science-cde|Veterinary Science CDE]]
- [[../concepts/agcoach-livestock-judging-cde|Livestock Judging CDE]]
- [[../concepts/agcoach-meat-science-cde|Meat Science CDE]]
- [[../concepts/agcoach-creed-speaking-lde|Creed Speaking LDE]]
- [[../sources/agcoach-wool-study-guide|Wool CDE Study Guide]]
- [[../sources/agcoach-business-brain|Business Brain]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
