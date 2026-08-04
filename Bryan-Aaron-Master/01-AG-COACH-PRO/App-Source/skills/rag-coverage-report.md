# Skill: RAG Coverage Report

## Purpose

Before building any module, confirm the `knowledge_documents` table in Supabase actually has ingested content for it. Without this check, you can scaffold a perfect module and it will silently return "No questions generated" at runtime.

This skill queries Supabase and produces a per-module coverage table showing chunk counts, so you know which modules are ready to build and which still need PDFs ingested.

---

## When to Use

- At the start of a build session, before scaffolding any modules
- After running `python3 ingest_knowledge.py`, to confirm it worked
- When a module returns empty quiz results in production

---

## How to Run

Use the Supabase MCP tool `mcp__claude_ai_Supabase__execute_sql` with the project ID.

### Query 1 — Coverage summary by contest category

```sql
SELECT
  contest_category,
  event_type,
  COUNT(*)           AS chunk_count,
  COUNT(DISTINCT source_file) AS file_count
FROM knowledge_documents
GROUP BY contest_category, event_type
ORDER BY event_type, contest_category;
```

### Query 2 — Check a specific module

```sql
SELECT
  contest_category,
  source_file,
  COUNT(*) AS chunks
FROM knowledge_documents
WHERE contest_category = 'Forage'   -- swap in the category you're checking
GROUP BY contest_category, source_file
ORDER BY source_file;
```

### Query 3 — Find modules with zero coverage

```sql
-- Returns categories present in TOPIC_CONTEST_CATEGORY that have no ingested docs.
-- Run the coverage summary and manually compare against the expected list below.
SELECT contest_category, COUNT(*) AS chunks
FROM knowledge_documents
GROUP BY contest_category
HAVING COUNT(*) < 10   -- flag anything with suspiciously low coverage
ORDER BY chunks;
```

---

## Expected Coverage Map

These are the `contest_category` values (from `FOLDER_TO_CATEGORY` in `ingest_knowledge.py`) that each module depends on:

| Module | Expected contest_category | Minimum healthy chunks |
|---|---|---|
| `forages` | `Forage` | 50+ |
| `forestry` | `Forestry` | 80+ |
| `dairy-cattle` | `Dairy Cattle` | 100+ |
| `livestock-judging` | `Livestock` | 100+ |
| `floral-id` | `Floriculture` | 80+ |
| `entomology-id` | `Entomology` | 80+ |
| `vet-science-id` | `Veterinary Science` | 30+ |
| `meats-id` | `Meats` | 40+ |
| `horse-eval` | `Horse` | 40+ |
| `land` | `Land` | 40+ |
| `agronomy` | `Agronomy` | 30+ |
| `poultry-eval` | `Poultry` | 30+ |
| `wildlife` | `Wildlife` | 30+ |
| `food-science` | `Food Science` | 30+ |
| `cotton` | `Cotton` | 40+ |
| `env-resources` | `Environmental & Natural Resources` | 40+ |
| `homesite` | `Homesite Evaluation` | 30+ |
| `marketing-plan` | `Marketing Plan` | 30+ |
| `plant-id` | `Plant ID` | 40+ |
| `range` | `Range` | 40+ |
| `tractor` | `Tractor Technician` | 40+ |
| `ag-eng` | `Ag Technology` | 30+ |
| `ag-comm` | `Ag Communications` | 20+ |
| `ag-sales` | `Ag Sales` | 20+ |
| `wildlife` | `Wildlife` | 30+ |
| `greenhand-quiz` | `Greenhand FFA Quiz` | 50+ |
| `senior-quiz` | `Senior FFA Quiz` | 50+ |

---

## Output Format

Report results as a table:

| Module | contest_category | Chunks | Files | Status |
|---|---|---|---|---|
| forages | Forage | 87 | 3 | ✅ Ready |
| dairy-cattle | Dairy Cattle | 0 | 0 | ❌ Not ingested |
| forestry | Forestry | 124 | 1 | ✅ Ready |

**Status key:**
- ✅ Ready — above minimum threshold, safe to build
- ⚠️ Low — below threshold, quiz quality will be poor
- ❌ Not ingested — must run `python3 ingest_knowledge.py` first

---

## If Coverage is Missing

1. Confirm the PDF exists: `find Texas_FFA_Resources -name "*.pdf" | grep -i [module]`
2. Confirm the folder name maps correctly in `FOLDER_TO_CATEGORY` in `ingest_knowledge.py`
3. Run: `python3 ingest_knowledge.py` (safe to re-run — skips already-ingested chunks)
4. Re-run this skill to confirm chunks appear
