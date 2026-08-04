---
name: agcoach-prompt-catalog
type: concept
tags: [ag-coach-pro, prompts, gemini, ai, catalog]
source_files: [repo:/lib/prompts/]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Prompt Catalog (`lib/prompts/`)

Per [[../sources/agcoach-app-working-instructions|CLAUDE.md]] rule: **"AI prompts belong in `lib/prompts/`, not inline in logic files. One file per domain."** The `prompt-extract` skill enforces this. 10 files currently:

| File | Domain | Notes |
|---|---|---|
| `core-prompts.ts` | Shared / Brain | `AG_COACH_PRO_SYSTEM_PROMPT` (Ag Coach Brain chatbot system prompt) and `AG_COACH_PRO_V2_PROMPT` (Brain v2 with ag-teacher personality from 2026-05-15 `brain-personality` plan). **Hardcoded CDE scores in this file are fallback defaults only — retrieved RAG rulebook excerpts take precedence.** |
| `evaluationPrompt.ts` | Cross-cutting | Generic evaluation/grading scaffold |
| `ag-skills-prompts.ts` | Ag Skills module | Quiz + study prompts for general ag-skills topics |
| `ag-tech-prompts.ts` | Ag Tech CDE | Pairs with the `ag-tech-gauntlet` plan (Formula Gauntlet) |
| `fbm-problem-prompts.ts` | Farm Business Management | Worked-problem prompts for FBM LDE; expects sourcing per [[agcoach-ffa-prerequisite-materials\|FBM Prerequisite Materials]] |
| `job-interview-rubrics.ts` | Job Interview LDE | `PHONE_INTERVIEW_RUBRIC` (50pt) + video rubric (combined out of 400pt). Pairs with the `job-interview-rag-voice-agent` plan |
| `livestock-analyzer-prompts.ts` | Livestock Phenotype Analyzer | Coordinates with anchor-image calibration from the `livestock-phenotype-accuracy` plan |
| `milk-quality-prompts.ts` | Milk Quality CDE | Dairy quality assessment prompts |
| `training-plan-prompts.ts` | Teacher / Training Plan | Used by `lib/training-plan.ts` to generate per-student training plans |
| `wool-prompts.ts` | Wool CDE | Pairs with the `wool-judging-module-design` spec and ingested [[../sources/agcoach-wool-study-guide\|Wool study guide]] |

## Conventions

- Default Gemini structured-output: build a `Schema` from `@google/generative-ai`, pass `generationConfig: { responseMimeType: 'application/json', responseSchema }`, parse with `parseAIJson` from `lib/ai/parser.ts`, then normalize (sort, renumber, default missing fields) — model occasionally returns short / non-contiguous arrays.
- Prompts that depend on retrieved chunks must explicitly instruct: "When grounding context is present, defer to it over any baked-in scores or rules" (the `core-prompts.ts` pattern).
- `PracticeType`-bearing prompts must keep wording aligned with [[../concepts/agcoach-contest-modules|contest module conventions]] so RAG topic strings, prompt vocabulary, and `TOPIC_QUERIES` keys stay in sync.

## Gap (no dedicated prompt file yet)

- **Poultry** — `lib/prompts/poultry-prompts.ts` is missing; required by the [[agcoach-poultry-judging-cde|Poultry Judging CDE]] build (Phase 1 of the 3-phase roadmap).

## Related

- [[../sources/agcoach-app-working-instructions|App Working Instructions]] (prompts-in-prompts/ rule)
- [[agcoach-app-internal-skills-catalog|Skills Catalog]] (prompt-extract, brain-v2-citation-check)
- [[agcoach-rag-architecture|RAG Architecture]]
- [[agcoach-creed-speaking-lde|Creed Speaking LDE]] (uses CreedResult schema, see [[../sources/agcoach-gemini-schemas|Gemini Schemas]])
- [[agcoach-poultry-judging-cde|Poultry Judging CDE]] (missing prompt file)
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
