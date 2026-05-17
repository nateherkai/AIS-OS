# Skill: PDF to RAG

## Purpose

Wraps `rag-knowledge-ingest` with FFA-rulebook-tuned chunking. Generic ingest splits mid-table or mid-rubric. This adds heuristics for Texas FFA handbook layout.

---

## When to Use

- New FFA rulebook PDF
- Re-ingest after rulebook revision (annual)
- Suspected retrieval quality drop ("quiz cites wrong year's rules")

---

## Prerequisite

- PDF in `Texas_FFA_Resources/<category>/<file>.pdf` or `docs/`
- `FOLDER_TO_CATEGORY` in `ingest_knowledge.py` maps the folder → `contest_category`
- Python env with deps (`pip install -r requirements-ingest.txt` if exists)

---

## Procedure

### 1. Inspect PDF

```bash
pdftotext -layout "<file>.pdf" -        | head -200
pdftotext -layout "<file>.pdf" - | wc -l
```

Identify:
- Cover/TOC pages to skip
- Table-heavy sections (scorecards, rubrics) — need different chunking
- Footer/header noise (page numbers, "© Texas FFA")

### 2. Pre-process

Use `pypdf` or `pdfminer.six` to:

- Strip headers/footers (regex `^Page \d+`, `^© Texas FFA.*$`)
- Detect tables via `pdfplumber.extract_tables()` → keep as serialized markdown blocks (one chunk = one table)
- Detect rubric sections (heading regex `^(Scorecard|Rubric|Evaluation Criteria)`) → chunk by section, not by token count

### 3. Chunk strategy

| Content type | Strategy |
|---|---|
| Prose / paragraphs | Recursive split, 800 tokens, 100 overlap |
| Rubrics / scorecards | One section = one chunk (no split) |
| Tables | One table = one chunk, markdown-serialized |
| Code/formulas | Preserve whole expression in chunk |
| TOC / index | Skip entirely |

### 4. Metadata required

```python
metadata = {
  "source_file": "TEXAS FFA LDE RULES - 9.24.25.pdf",
  "contest_category": "LDE",           # from FOLDER_TO_CATEGORY
  "event_type": "LDE",                  # CDE | LDE | Quiz | General
  "section": "Chapter Conducting Rubric",  # detected heading
  "page_start": 23,
  "page_end": 25,
  "rulebook_year": "2025-26",
  "chunk_type": "rubric"                # prose | rubric | table | scorecard
}
```

`chunk_type` lets retrieval boost rubric chunks for grading queries.

### 5. Embed + insert

Use `gemini-embedding-2-preview@3072` (hardcoded across app). Assert dim == 3072 before insert.

```python
from google.generativeai import embed_content

res = embed_content(
  model="models/gemini-embedding-2-preview",
  content=chunk_text,
  task_type="RETRIEVAL_DOCUMENT",
  output_dimensionality=3072,
)
emb = res["embedding"]
assert len(emb) == 3072
```

### 6. Insert into `knowledge_documents`

Schema:

```sql
insert into knowledge_documents
  (content, embedding, source_file, contest_category, event_type, metadata)
values ($1, $2::vector(3072), $3, $4, $5, $6::jsonb)
on conflict (source_file, content_hash) do nothing;
```

`content_hash` = sha256(content). Idempotent re-ingest.

### 7. Verify

Run `rag-coverage-report` skill — expect chunk count ≥ minimum threshold for category.

Smoke query:

```sql
select id, source_file, left(content, 100) as preview, metadata->>'section' as section
from knowledge_documents
where source_file = '<filename>'
order by (metadata->>'page_start')::int
limit 10;
```

---

## Quality Probes

After ingest, ask Brain v2:

```
"What is the scoring breakdown for [event] according to the [year] rulebook?"
```

Expect citations → rubric chunks from new PDF, not prose. If prose-only, `chunk_type` boost not working.

```
"Quote the section title for the [specific rule] in [event]."
```

Expect exact heading from PDF. Mismatch = chunk boundaries broken.

---

## Re-ingest on Rulebook Update

```bash
# Delete old version chunks
psql ... <<SQL
delete from knowledge_documents
where source_file = 'TEXAS FFA LDE RULES - 9.24.25.pdf';
SQL

# Re-run ingest with new PDF
python3 ingest_knowledge.py --file "TEXAS FFA LDE RULES - 9.24.26.pdf"
```

Update `rulebook_year` metadata. Old citations in `brain_conversations` will be orphaned — acceptable.

---

## Related

- `rag-knowledge-ingest` — base ingest workflow
- `rag-coverage-report` — verify chunks landed
- `brain-v2-citation-check` — verify retrieval uses new chunks
