# Skill: RAG Knowledge Base Ingest

## Objective
Chunk Texas FFA resource files (PDFs + CSVs), embed each chunk via Google `gemini-embedding-001`, and upsert into Supabase `knowledge_documents` for RAG-powered chatbot retrieval.

---

## Inputs

| Input | Description |
|---|---|
| `Texas_FFA_Resources/` | Directory of PDFs organized under `CDE_Events/<Category>/` and `LDE_Events/<Category>/` |
| `docs/Texas Livestock CDE Questions.csv` | Q&A CSV with columns: `Cdequestion`, `Answer Correct`, `answer_option_a–d`, `Category`, `CDE event type` |
| `nursery-landscape.csv` | Q&A CSV with columns: `Question`, `Correct_Answer`, `Option_A–D`, `Category` |
| `GOOGLE_API_KEY` | Google Generative AI API key (must have Generative Language API enabled) |
| `SUPABASE_URL` | Supabase project URL (e.g. `https://xxxx.supabase.co`) |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key — bypasses RLS for bulk inserts |

---

## Logic

```
1. PREFLIGHT
   └─ Validate all 3 env vars present, exit(1) if missing

2. FETCH EXISTING
   └─ Page through knowledge_documents, collect all (source_file, chunk_index) pairs
   └─ Purpose: skip already-ingested chunks (idempotent runs)

3. INGEST PDFs
   ├─ Recursively glob Texas_FFA_Resources/**/*.pdf
   ├─ For each PDF:
   │   ├─ derive_metadata(path):
   │   │   └─ Walk path parts → if "CDE_Events" → event_type="CDE", contest_category=FOLDER_TO_CATEGORY[folder]
   │   │   └─ If "LDE_Events" → event_type="LDE", contest_category=FOLDER_TO_CATEGORY[folder]
   │   ├─ extract_pdf_text() via pdfplumber (strip null bytes)
   │   ├─ split_text() → 800-char chunks, 120 overlap, separators=["\n\n","\n",". "," ",""]
   │   └─ For each NEW chunk (not in already_done):
   │       ├─ embed(chunk) → POST gemini-embedding-001, taskType=RETRIEVAL_DOCUMENT → float[768]
   │       ├─ sleep(0.05)  ← rate limit
   │       └─ yield row dict

4. INGEST CSVs
   ├─ For each CSV file in CSV_FILES list:
   │   ├─ Detect layout A ("Cdequestion" header) vs layout B ("Question" header)
   │   ├─ Format content = "Q: {q}\nAnswer: {a}\nOptions: A) ... B) ... C) ... D) ...\nCategory: {cat}"
   │   └─ For each NEW row (not in already_done):
   │       ├─ embed(content) → float[768]
   │       ├─ sleep(0.05)
   │       └─ yield row dict

5. BATCH UPSERT
   └─ Collect yielded rows into batches of 50
   └─ supabase.table("knowledge_documents").upsert(batch, on_conflict="source_file,chunk_index")
   └─ Log running total after each batch
```

---

## Output

Rows written to Supabase `knowledge_documents`:

| Column | Type | Value |
|---|---|---|
| `id` | UUID | auto-generated |
| `content` | TEXT | raw text chunk |
| `embedding` | VECTOR(768) | gemini-embedding-001 output |
| `source_file` | TEXT | relative path or filename |
| `contest_category` | TEXT | e.g. "Livestock", "Nursery/Landscape" |
| `event_type` | TEXT | "CDE" \| "LDE" \| "General" |
| `chunk_index` | INT | 0-based position in source |
| `metadata` | JSONB | `{path}` for PDFs, `{row, category}` for CSVs |

Console summary on completion:
```
INGEST COMPLETE — N total vectors upserted.
```

---

## Storage

- **Script:** `ingest_knowledge.py` (project root)
- **Destination table:** `knowledge_documents` in Supabase
- **Schema migration:** `supabase/migrations/017_knowledge_base.sql`
- **Query function:** `supabase/functions/match-knowledge/index.ts` (Edge Function)

---

## Run Command

```bash
# 1. Install deps (one-time)
pip install requests pdfplumber supabase langchain-text-splitters

# 2. Set env vars
export GOOGLE_API_KEY="AIza..."
export SUPABASE_URL="https://xxxx.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="eyJ..."

# 3. Run (re-running is safe — duplicates are skipped)
python3 ingest_knowledge.py
```

---

## Re-run Safety
Idempotent via unique index on `(source_file, chunk_index)`. Already-ingested chunks are pre-fetched and skipped before any embedding calls are made, so re-runs only process genuinely new files.

---

## Extension Points

| Scenario | Change |
|---|---|
| Add a new contest category | Add entry to `FOLDER_TO_CATEGORY` dict in `ingest_knowledge.py` |
| Add a new CSV source | Append path to `CSV_FILES` list; add layout detection in `iter_csv_chunks` |
| Change embedding model | Update `EMBED_MODEL` constant and `VECTOR(768)` dimension in migration |
| Add metadata fields | Extend `metadata` JSONB dict in yield statements |
