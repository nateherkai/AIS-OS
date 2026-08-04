---
name: agcoach-livestock-judging-cde
type: concept
tags: [ag-coach-pro, cde, livestock-judging, ffa, contest]
source_files: [raw/_ingested/2026-05-16-agcoach-ffa-resource-audit.md, raw/_ingested/2026-05-16-agcoach-BUSINESS_BRAIN.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Livestock Judging (Evaluation) CDE

Bryan's area of deepest expertise — National Champion Livestock Judging Team member.

## Contest Format

| Component | Details |
|---|---|
| Written Test | 25 multiple-choice (2 pts each) = 50 pts |
| Oral Reasons | Justification of placement decisions |
| Scoring System | Points above/below official placings |
| Team Composition | 3-4 members; all scores count toward team total |
| Classes | Beef cattle, sheep, swine, market goats |

## Official Resources

- National FFA Livestock Evaluation CDE Handbook: https://www.ffa.org/participate/cdes/livestock-evaluation/
- Texas FFA Livestock Evaluation Rules (in Texas CDE Handbook 2022-2026)
- Texas-specific: https://www.texasffa.org/docs/LIVESTOCK%20EVALUATION_71585.pdf

## Practice Resources Available

- Past 3 years National FFA tests
- Washington FFA Livestock Evaluation Handbook
- Iowa FFA resources
- Florida FFA practice materials

## Content Gaps in Ag Coach Pro

- Breed standards database (cattle, sheep, swine)
- Market grading standards reference
- Scorecard templates
- Video tutorials on evaluation criteria

## AI Feature: Livestock Phenotype Analyzer

Ag Coach Pro has a computer vision tool that evaluates livestock images. Scores muscle, structure, volume, balance, and condition. Returns feedback + placing rationale. Powers the Phenotype Drill feature.

Multi-view drill (side/rear/front) is on the backlog — needs DB migration + upload UI + 3-view switcher.

## RAG Content

Livestock category has 574 classified chunks in `knowledge_documents` as of 2026-05-16. Also `Livestock-USDA-Grading` subcategory used by Brain Accuracy v1 (specifically fixes slaughter cattle grading score routing).

## Related

- [[../sources/agcoach-ffa-resource-audit|FFA Resource Audit]]
- [[../concepts/agcoach-contest-modules|Contest Modules]]
- [[../concepts/agcoach-rag-architecture|RAG Architecture]]
- [[../sources/agcoach-business-brain|Business Brain]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
