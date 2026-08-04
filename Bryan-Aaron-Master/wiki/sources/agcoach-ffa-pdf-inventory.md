---
name: agcoach-ffa-pdf-inventory
type: source
tags: [ag-coach-pro, ffa, pdf, rag, reference, inventory]
source_files: [repo:/docs/*.pdf, repo:/docs/*.docx, repo:/docs/*.csv]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — FFA Source PDF Inventory (`docs/`)

Primary Texas / National FFA reference materials staged in `docs/` at repo root. Not extracted into wiki — bulk text belongs in `knowledge_documents` (pgvector) via the `rag-knowledge-ingest` skill. This page is an index for traceability.

## PDFs

| File | Likely purpose | Suggested ingest category |
|---|---|---|
| `2023-24 National FFA Official Manual (2)_98126.pdf` | National FFA Manual EN — Creed, FFA Quiz, Greenhand grounding | `FFA Knowledge` |
| `2025 Texas FFA Farm Facts - 8.6.25_31506.pdf` | Texas-specific farm-fact briefing | `Ag Issues` / `FFA Knowledge` |
| `2025 Ag Issues & Current Events - Briefs 8.6.25_31506.pdf` | Current-events briefs for Ag Issues LDE | `Ag Issues` |
| `2025-2026 District Officer Guide (2)_37424.pdf` | District officer handbook | `FFA Admin` |
| `2025-2026 Leadership Guide (2)_07352.pdf` | Texas FFA leadership handbook | `FFA Admin` |
| `TEXAS FFA LDE RULES - 9.24.25_35566.pdf` | Authoritative Texas LDE contest rules | `FFA Admin` / per-LDE category |
| `Gray's.pdf` | Likely Gray's anatomy reference for livestock judging | `Livestock` |
| `Gray's Front Table_08.24_02684.pdf` | Front-table view subset of Gray's | `Livestock` |

## DOCX / CSV

| File | Likely purpose |
|---|---|
| `4852_2018_29014 (1).docx` | Single legacy form/document (origin unclear from filename) |
| `Texas FFA Chapter Quiz Questions.csv` | Chapter quiz question bank — feeds Greenhand / FFA Quiz modules |
| `Texas Livestock CDE Questions.csv` | Livestock CDE question bank |
| `Texas Livestock CDE Questions.numbers` | Apple Numbers source for the CSV above |

## Ingest checklist

For each PDF/CSV not yet processed:

1. Run `rag-knowledge-ingest` skill with `--category <Suggested>` mapping above.
2. Verify chunks appear in `knowledge_documents` (e.g. `select count(*) from knowledge_documents where source_file = '<filename>'`).
3. Re-run Brain v3 backfill if classification heuristics need a new pattern.
4. Re-run `rag-coverage-report` skill to confirm the relevant CDE/LDE module gains chunks.

## Notes

- File naming has `_NNNNN` suffixes — likely auto-export numeric IDs from the upstream Texas FFA portal. Keep originals; they are the canonical source.
- Two `Gray's` PDFs suggest one full + one cropped subset; verify both ingest cleanly (cropped may have OCR drift).
- Per Brain v3 backfill (2026-05-16 decisions), the manual + admin PDFs land in sentinel categories `FFA Knowledge` / `FFA Admin` rather than a contest category.

## Related

- [[../concepts/agcoach-rag-architecture|RAG Architecture]] (taxonomy backfill)
- [[../concepts/agcoach-app-internal-skills-catalog|Skills Catalog]] (rag-knowledge-ingest, rag-coverage-report)
- [[agcoach-ffa-resource-audit|FFA Resource Audit]] (gap analysis these PDFs feed)
- [[agcoach-wool-study-guide|Wool & Mohair Study Guide]] (already RAG-ingested example)
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
