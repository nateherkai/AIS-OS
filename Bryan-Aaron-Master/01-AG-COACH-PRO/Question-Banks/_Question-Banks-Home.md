# Question Banks — Ag Coach Pro

> Human-curated question bank inventory.
> Generated 2026-05-16 from wiki/sources/agcoach-ffa-pdf-inventory + wiki/sources/agcoach-ffa-resource-audit
> Full PDF inventory → [[../../wiki/sources/agcoach-ffa-pdf-inventory|FFA Source PDF Inventory]]

---

## RAG Knowledge Store

All question banks are ingested into Supabase `knowledge_documents` via `python3 ingest_knowledge.py`.

**Current stats (as of 2026-05-16):**
- Total chunks classified: 20,987 (100%)
- Top categories by chunk count: Ag Tech 3,600 / Horse 2,158 / Meats 1,988 / Wildlife 1,240 / Forestry 934 / Livestock 574
- Embedding model: `gemini-embedding-2-preview` (3072 dimensions)
- HNSW index active (was 14s seq scan → now ~400ms)

---

## Known Source PDFs in `docs/` (ag-coach-app repo)

| File | Category | Status |
|---|---|---|
| `Texas Livestock CDE Questions.pdf` | Livestock | In RAG |
| `Texas Livestock CDE Questions.csv` | Livestock | In RAG |
| `Livestock_Rules_UPDATED_8.20.24.pdf` | Livestock | In RAG (critical — USDA grading fix) |
| `Texas FFA CDE Handbook 2022-2026.pdf` | FFA Admin | In RAG |
| `USDA Meat Grading Standards.pdf` | Meats | In RAG |
| `Veterinary Science Practice Bank.docx` | Vet Science | In RAG |
| `Wool CDE Study Guide.pdf` | Wool | In RAG |
| `Texas Livestock CDE Questions.numbers` | Livestock | Apple Numbers source — use .csv sibling |

---

## Question Bank Counts by CDE (Known)

| CDE | Known Q Count | Source | Status |
|---|---|---|---|
| Livestock Judging | 2022–2026 bank available | Texas FFA / National FFA | Active |
| Veterinary Science | 150 questions (2025) | Texas A&M AgriLife Extension | Active |
| Meat Science | Handbook + USDA standards | National FFA handbook | Active |
| Farm Business Management | 50+ questions in content pack | Built internally | Active |
| Creed Speaking | Past competition questions needed | Various | Gap ⚠️ |
| Wool & Mohair | Study guide complete | Built internally | Active |
| Poultry Judging | Pending NotebookLM ingest | Planned | Pending |

---

## Official Sources

- **National FFA CDE Hub:** https://www.ffa.org/resource_tag/cde-handbooks/
- **Texas FFA CDE Hub:** https://www.texasffa.org/cde
- **Texas CDE Handbook 2022-2026 (primary authority for Texas rules):** https://www.texasffa.org/docs/CDE%20Handbook%202022-2026%20-%2010.9.2025_61720.pdf
- **Texas A&M AgriLife Vet Science Test Bank (150 Qs):** https://agrilifeextension.tamu.edu/asset-external/veterinary-science-cde-test-bank-2025/

---

## High-Priority Gaps

- [ ] Breed standards database (cattle, sheep, swine) — visual + written
- [ ] USDA meat grading visual guides + carcass images
- [ ] Livestock anatomy diagrams (large + small animal)
- [ ] Parasite ID images + surgical instruments guide (Vet Science)
- [ ] Creed Speaking question bank from past competitions
- [ ] Interactive scoring calculators (all events)
- [ ] Poultry Judging questions (NotebookLM ingest planned)

---

## Related

- [[../../wiki/sources/agcoach-ffa-pdf-inventory|FFA Source PDF Inventory]]
- [[../../wiki/sources/agcoach-ffa-resource-audit|FFA Resource Audit (Gap Analysis)]]
- [[../../wiki/sources/agcoach-wool-study-guide|Wool & Mohair Study Guide]]
- [[../../wiki/concepts/agcoach-rag-architecture|RAG Architecture]]
- [[../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
