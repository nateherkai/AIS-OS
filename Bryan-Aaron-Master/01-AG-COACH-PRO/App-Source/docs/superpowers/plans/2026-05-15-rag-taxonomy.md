# RAG Taxonomy + Ingest Enforcement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Backfill `contest_category` + a new `subcategory` column on all 16k+ rows in `knowledge_documents` using a heuristic + Gemini Flash classifier, rewrite the ingest pipeline to require these fields, and plumb the subcategory hint through `match_knowledge_v2` → edge fn → client retrieval so Brain v2 stops returning noisy mixed-topic chunks.

**Architecture:** Additive schema migration adds `subcategory`, `classified_by`, `classified_at` to `knowledge_documents` plus a `classification_failures` table. A Python classifier (`scripts/classify_chunk.py`) maps each chunk to a `TOPIC_QUERIES` key using filename/path/frontmatter heuristics first, Gemini Flash fallback when confidence < 0.6 from heuristics. A backfill script applies the classifier to existing rows. A second migration adds an optional `p_subcategory` arg to `match_knowledge_v2` for additive similarity boost. Client adds `lib/ai/brain/queryRouter.ts` (regex keyword map) and forwards the hint through `brain-v2.ts` → `match-knowledge-v2` edge fn → RPC. A final enforcement migration flips `NOT NULL` after backfill is green.

**Tech Stack:** PostgreSQL (Supabase pgvector + halfvec), TypeScript (Expo / React Native), Python 3 (ingest + backfill), Gemini Flash (classification + existing app embeddings), Deno (Supabase edge functions), Jest, pytest.

**Spec:** `docs/superpowers/specs/2026-05-15-rag-taxonomy-design.md`

---

## Prerequisites

- New branch `feat/rag-taxonomy` cut from `main`. Do NOT continue on `feat/brain-personality` — that branch carries unrelated voice work pending its own merge.
- Python 3.11+ with `supabase`, `google-generativeai`, `pytest`, `pyyaml`, `tqdm` installed (most already in `requirements.txt`).
- `GEMINI_API_KEY` and `SUPABASE_SERVICE_ROLE_KEY` available in shell env when running scripts.
- `npm test` and `npx tsc --noEmit -p .` green at the prereq commit.

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `supabase/migrations/<ts>_rag_taxonomy.sql` | Additive: add `subcategory`, `classified_by`, `classified_at` + `classification_failures` table | Create |
| `supabase/migrations/<ts>_match_knowledge_v2_subcat.sql` | RPC accepts `p_subcategory`, adds additive boost | Create |
| `supabase/migrations/<ts>_rag_taxonomy_enforce.sql` | Flips `contest_category` / `source_path` NOT NULL | Create (apply last) |
| `scripts/classify_chunk.py` | Pure classifier: heuristic + Gemini Flash fallback | Create |
| `tests/test_classify_chunk.py` | pytest unit tests for classifier | Create |
| `scripts/backfill_taxonomy.py` | Idempotent batched backfill driver | Create |
| `tests/test_backfill_taxonomy.py` | pytest for batch + dry-run + flush logic | Create |
| `ingest_knowledge.py` | Add `classify_chunk` pass before insert; route low-conf to failures | Modify |
| `lib/ai/brain/queryRouter.ts` | Regex keyword map → `{ contestCategory?, subcategory? }` | Create |
| `__tests__/brain/queryRouter.test.ts` | Jest unit tests | Create |
| `lib/ai/brain-v2.ts` | Call `routeQuery`, forward `subcategory` to edge fn | Modify |
| `supabase/functions/match-knowledge-v2/index.ts` | Accept + forward `subcategory` body field | Modify |
| `SCHEMA.md` | Document new columns + table | Modify |
| `CLAUDE.md` | Append decision log entry | Modify |

---

## Task 1: Branch + additive schema migration

**Files:**
- Create: `supabase/migrations/<ts>_rag_taxonomy.sql`

- [ ] **Step 1: Cut new branch from main**

```bash
git checkout main
git pull --ff-only
git checkout -b feat/rag-taxonomy
```

- [ ] **Step 2: Create migration file**

Use the current timestamp for the filename, e.g. `20260515220000_rag_taxonomy.sql`. Content:

```sql
-- Taxonomy: add subcategory + classification audit columns; add failures table.

alter table public.knowledge_documents
  add column if not exists subcategory text,
  add column if not exists classified_by text
    check (classified_by in ('heuristic','llm','manual')),
  add column if not exists classified_at timestamptz;

create index if not exists knowledge_documents_subcat_idx
  on public.knowledge_documents (contest_category, subcategory)
  where contest_category is not null;

create table if not exists public.classification_failures (
  id uuid primary key default gen_random_uuid(),
  chunk_text_preview text not null,
  source_type text not null,
  source_path text,
  reason text not null,
  attempted_label jsonb,
  created_at timestamptz default now()
);

alter table public.classification_failures enable row level security;

drop policy if exists "classification_failures admin read"
  on public.classification_failures;
create policy "classification_failures admin read"
  on public.classification_failures
  for select to authenticated
  using (
    auth.uid() in (
      select id from public.users where role = 'superadmin'
    )
  );
```

- [ ] **Step 3: Apply migration to remote**

Run from repo root:

```bash
npx supabase db push
```

Expected output: lists the new migration file and confirms `Finished supabase db push`.

If it errors with "migration history out of sync", consult `docs/migration-drift-2026-05-15.md` and use `npx supabase migration repair --status applied <ts>` per CLAUDE.md migration discipline rule.

- [ ] **Step 4: Verify columns landed**

```bash
psql "$SUPABASE_DB_URL" -c "\d public.knowledge_documents" | grep -E "subcategory|classified_"
psql "$SUPABASE_DB_URL" -c "\d public.classification_failures"
```

Expected: three new columns shown; failures table shows id/chunk_text_preview/source_type/source_path/reason/attempted_label/created_at.

If `psql` is unavailable, use the Supabase MCP `execute_sql` tool with the same `\d`-equivalent SQL:

```sql
select column_name, data_type from information_schema.columns
where table_schema='public' and table_name='knowledge_documents'
  and column_name in ('subcategory','classified_by','classified_at');
```

- [ ] **Step 5: Commit**

```bash
git add supabase/migrations/<ts>_rag_taxonomy.sql
git commit -m "feat(rag): add subcategory + classified_by columns + failures table"
```

---

## Task 2: Heuristic classifier (TDD, no LLM yet)

**Files:**
- Create: `scripts/classify_chunk.py` (heuristic stage only)
- Create: `tests/test_classify_chunk.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_classify_chunk.py`:

```python
from scripts.classify_chunk import classify_chunk, ClassificationResult

def test_app_meta_static_mapping():
    r = classify_chunk(
        chunk_text="livestock judging quiz topic descriptor",
        source_type="app_meta",
        source_path="livestock-judging",
        frontmatter=None,
    )
    assert r.contest_category == "Livestock"
    assert r.subcategory == "Livestock-Judging-Basics"
    assert r.classified_by == "heuristic"
    assert r.confidence == 1.0

def test_obsidian_frontmatter_takes_precedence():
    r = classify_chunk(
        chunk_text="random body text",
        source_type="obsidian",
        source_path="Notes/Misc/page.md",
        frontmatter={"contest": "Horse", "subcategory": "Horse-Reining-Maneuvers"},
    )
    assert r.contest_category == "Horse"
    assert r.subcategory == "Horse-Reining-Maneuvers"
    assert r.classified_by == "heuristic"
    assert r.confidence == 1.0

def test_obsidian_path_fallback():
    r = classify_chunk(
        chunk_text="...",
        source_type="obsidian",
        source_path="Livestock/Slaughter Cattle/grading.md",
        frontmatter=None,
    )
    assert r.contest_category == "Livestock"
    assert r.classified_by == "heuristic"

def test_rulebook_filename_match():
    r = classify_chunk(
        chunk_text="...",
        source_type="rulebook",
        source_path="rulebooks/livestock_evaluation_2024.pdf",
        frontmatter=None,
    )
    assert r.contest_category == "Livestock"
    assert r.classified_by == "heuristic"

def test_rulebook_toc_regex_for_subcategory():
    r = classify_chunk(
        chunk_text="Slaughter Cattle Grading Class\n\nStudents will be required to grade...",
        source_type="rulebook",
        source_path="rulebooks/livestock_evaluation_2024.pdf",
        frontmatter=None,
    )
    assert r.contest_category == "Livestock"
    assert r.subcategory == "Livestock-USDA-Grading"

def test_heuristic_miss_returns_none():
    r = classify_chunk(
        chunk_text="generic agricultural content with no keywords",
        source_type="rulebook",
        source_path="rulebooks/unknown_doc.pdf",
        frontmatter=None,
    )
    assert r.contest_category is None
    assert r.subcategory is None
```

- [ ] **Step 2: Run tests to verify failure**

```bash
pytest tests/test_classify_chunk.py -v
```

Expected: `ModuleNotFoundError: No module named 'scripts.classify_chunk'`.

- [ ] **Step 3: Implement heuristic classifier**

Create `scripts/classify_chunk.py`:

```python
"""Chunk classifier for knowledge_documents.

Stage 1: heuristics (filename, frontmatter, path, TOC regex).
Stage 2: Gemini Flash fallback (added in Task 3).
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Literal, Optional

ClassifiedBy = Literal["heuristic", "llm"]


@dataclass
class ClassificationResult:
    contest_category: Optional[str]
    subcategory: Optional[str]
    classified_by: ClassifiedBy
    confidence: float


# Static map for app_meta — mirrors lib/ai/rag-quiz.ts TOPIC_QUERIES contest assignment.
APP_META_MAP: dict[str, tuple[str, str]] = {
    "livestock-judging": ("Livestock", "Livestock-Judging-Basics"),
    "horse-eval":        ("Horse",     "Horse-Phenotype"),
    "wool":              ("Wool",      "Wool-Grading"),
    "forages":           ("Forage",    "Forage-Quality"),
    "milk-quality":      ("Milk Quality", "MilkQuality-Grading-Standards"),
    "meats":             ("Meats",     "Meats-Retail-ID"),
    "forestry":          ("Forestry",  "Forestry-Q1-Hardwood"),
    "land":              ("Land",      "Land-Soil-Profile"),
    "dairy":             ("Dairy Cattle", "Dairy-Linear"),
    "entomology":        ("Entomology", "Entomology-Order-ID"),
    "wildlife":          ("Wildlife",  "Wildlife-Species-ID"),
    "poultry":           ("Poultry",   "Poultry-Carcass-Grading"),
    "ag-tech":           ("Ag Technology", "AgTech-Concepts"),
    "tractor-tech":      ("Tractor Technician", "TractorTech-Diagnosis"),
    "homesite":          ("Homesite Evaluation", "Homesite-Soil"),
    "range":             ("Range",     "Range-Plant-ID"),
    "agronomy":          ("Agronomy",  "Agronomy-Crops"),
    "vet-sci":           ("Veterinary Science", "VetSci-Anatomy"),
    "nursery":           ("Nursery/Landscape", "Nursery-Plant-ID"),
    "food-sci":          ("Food Science", "FoodSci-Sensory"),
    "cotton":            ("Cotton",    "Cotton-Grading"),
    "floriculture":      ("Floriculture", "Floriculture-ID"),
    "ag-comm":           ("Ag Communications", "AgComm-Editorial"),
    "ag-sales":          ("Ag Sales",  "AgSales-Pitch"),
    "ffa-quiz-senior":   ("Senior FFA Quiz", "FFA Manual"),
    "ffa-quiz-greenhand":("Greenhand FFA Quiz", "FFA Manual"),
    "farm-bus":          ("Farm Business Management", "FBM-Records"),
    "ag-issues":         ("Ag Issues Forum", "AgIssues-Topics"),
    "chapter-conducting":("Chapter Conducting", "Parliamentary Guide"),
    "ag-advocacy":       ("Ag Advocacy", "AgAdvocacy-Topics"),
    "ag-broadcast":      ("FFA Broadcasting", "Broadcast-Script"),
    "marketing-plan":    ("Marketing Plan", "MarketingPlan-Sections"),
    "ag-skill":          ("Ag Skill Demonstration", "AgSkill-Steps"),
    "public-relations":  ("Public Relations", "PR-Campaign"),
    "plant-id":          ("Plant ID", "PlantID-Texas"),
    "env-natural":       ("Environmental & Natural Resources", "ENR-Topics"),
}

# Rulebook filename → contest. Substring match, case-insensitive.
RULEBOOK_FILENAME_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"livestock", re.I),       "Livestock"),
    (re.compile(r"horse", re.I),           "Horse"),
    (re.compile(r"wool", re.I),            "Wool"),
    (re.compile(r"forag", re.I),           "Forage"),
    (re.compile(r"milk", re.I),            "Milk Quality"),
    (re.compile(r"meat", re.I),            "Meats"),
    (re.compile(r"forestry", re.I),        "Forestry"),
    (re.compile(r"land", re.I),            "Land"),
    (re.compile(r"dairy", re.I),           "Dairy Cattle"),
    (re.compile(r"entomolog", re.I),       "Entomology"),
    (re.compile(r"wildlife", re.I),        "Wildlife"),
    (re.compile(r"poultry", re.I),         "Poultry"),
    (re.compile(r"ag[_\- ]?tech", re.I),   "Ag Technology"),
    (re.compile(r"tractor", re.I),         "Tractor Technician"),
    (re.compile(r"homesite", re.I),        "Homesite Evaluation"),
    (re.compile(r"range", re.I),           "Range"),
    (re.compile(r"agronomy", re.I),        "Agronomy"),
    (re.compile(r"vet[_\- ]?sci", re.I),   "Veterinary Science"),
    (re.compile(r"nursery|landscape", re.I), "Nursery/Landscape"),
    (re.compile(r"food[_\- ]?sci", re.I),  "Food Science"),
    (re.compile(r"cotton", re.I),          "Cotton"),
    (re.compile(r"floriculture", re.I),    "Floriculture"),
    (re.compile(r"ag[_\- ]?comm", re.I),   "Ag Communications"),
    (re.compile(r"ag[_\- ]?sales", re.I),  "Ag Sales"),
    (re.compile(r"ffa[_\- ]?manual|creed|parliamentary", re.I), "Senior FFA Quiz"),
    (re.compile(r"farm[_\- ]?business", re.I), "Farm Business Management"),
]

# TOC heading → subcategory. Matches near top of chunk.
RULEBOOK_TOC_RULES: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"slaughter cattle.*grading", re.I | re.S),
        "Livestock", "Livestock-USDA-Grading"),
    (re.compile(r"placing class", re.I),
        "Livestock", "Livestock-Phenotype-Cattle"),
    (re.compile(r"female selection", re.I),
        "Livestock", "Livestock-Selection-Genetics"),
    (re.compile(r"reining|maneuver", re.I),
        "Horse", "Horse-Reining-Maneuvers"),
    (re.compile(r"halter", re.I),
        "Horse", "Horse-Halter-Class"),
    (re.compile(r"hardwood.*identif", re.I | re.S),
        "Forestry", "Forestry-Q1-Hardwood"),
    (re.compile(r"pine.*identif", re.I | re.S),
        "Forestry", "Forestry-Q2-Pine"),
    (re.compile(r"somatic cell count|scc", re.I),
        "Milk Quality", "MilkQuality-Grading-Standards"),
    # Extend as new ingest sources surface.
]


def classify_chunk(
    chunk_text: str,
    source_type: str,
    source_path: Optional[str],
    frontmatter: Optional[dict] = None,
) -> ClassificationResult:
    # 1. app_meta — deterministic map.
    if source_type == "app_meta":
        key = (source_path or "").lower()
        if key in APP_META_MAP:
            contest, sub = APP_META_MAP[key]
            return ClassificationResult(contest, sub, "heuristic", 1.0)

    # 2. obsidian — frontmatter wins.
    if source_type == "obsidian" and frontmatter:
        contest = frontmatter.get("contest")
        sub = frontmatter.get("subcategory")
        if contest:
            return ClassificationResult(contest, sub, "heuristic", 1.0)

    # 3. obsidian path fallback.
    if source_type == "obsidian" and source_path:
        first_seg = source_path.split("/", 1)[0]
        contest = _match_contest_segment(first_seg)
        if contest:
            return ClassificationResult(contest, None, "heuristic", 0.8)

    # 4. rulebook filename + TOC.
    if source_type == "rulebook" and source_path:
        contest = _match_filename(source_path)
        sub = None
        if contest:
            for pat, c, s in RULEBOOK_TOC_RULES:
                if c == contest and pat.search(chunk_text[:1500]):
                    sub = s
                    break
            return ClassificationResult(contest, sub, "heuristic",
                                        1.0 if sub else 0.7)

    return ClassificationResult(None, None, "heuristic", 0.0)


def _match_filename(path: str) -> Optional[str]:
    name = path.rsplit("/", 1)[-1]
    for pat, contest in RULEBOOK_FILENAME_RULES:
        if pat.search(name):
            return contest
    return None


def _match_contest_segment(segment: str) -> Optional[str]:
    seg = segment.lower()
    for pat, contest in RULEBOOK_FILENAME_RULES:
        if pat.search(seg):
            return contest
    return None
```

- [ ] **Step 4: Run tests to verify pass**

```bash
pytest tests/test_classify_chunk.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/classify_chunk.py tests/test_classify_chunk.py
git commit -m "feat(rag): heuristic chunk classifier with pytest coverage"
```

---

## Task 3: Add Gemini Flash LLM fallback to classifier

**Files:**
- Modify: `scripts/classify_chunk.py`
- Modify: `tests/test_classify_chunk.py`

- [ ] **Step 1: Append failing test for LLM branch**

Append to `tests/test_classify_chunk.py`:

```python
from unittest.mock import patch

def test_llm_fallback_invoked_on_heuristic_miss():
    fake_response = {
        "contest_category": "Livestock",
        "subcategory": "Livestock-USDA-Grading",
        "confidence": 0.82,
    }
    with patch("scripts.classify_chunk._gemini_classify", return_value=fake_response):
        r = classify_chunk(
            chunk_text="USDA quality grades for beef carcasses are Prime, Choice, Select...",
            source_type="rulebook",
            source_path="rulebooks/unknown_doc.pdf",
            frontmatter=None,
            use_llm=True,
        )
    assert r.contest_category == "Livestock"
    assert r.subcategory == "Livestock-USDA-Grading"
    assert r.classified_by == "llm"
    assert r.confidence == 0.82

def test_llm_low_confidence_returns_none():
    fake_response = {
        "contest_category": "Livestock",
        "subcategory": "Livestock-USDA-Grading",
        "confidence": 0.4,
    }
    with patch("scripts.classify_chunk._gemini_classify", return_value=fake_response):
        r = classify_chunk(
            chunk_text="generic content",
            source_type="rulebook",
            source_path="rulebooks/unknown.pdf",
            frontmatter=None,
            use_llm=True,
        )
    assert r.contest_category is None
    assert r.subcategory is None

def test_use_llm_false_skips_fallback():
    with patch("scripts.classify_chunk._gemini_classify") as mock:
        r = classify_chunk(
            chunk_text="x",
            source_type="rulebook",
            source_path="rulebooks/unknown.pdf",
            frontmatter=None,
            use_llm=False,
        )
        mock.assert_not_called()
    assert r.contest_category is None
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/test_classify_chunk.py -v
```

Expected: 3 new tests FAIL with `TypeError: classify_chunk() got an unexpected keyword argument 'use_llm'` (or similar).

- [ ] **Step 3: Add LLM fallback**

At the bottom of `scripts/classify_chunk.py`, add the import group + function. Update the `classify_chunk` signature and body:

```python
import json
import os
from google import generativeai as genai

CONFIDENCE_THRESHOLD = 0.6


def _gemini_classify(chunk_text: str, candidate_contests: list[str]) -> dict:
    """Call Gemini Flash with structured output. Returns dict matching schema."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    schema = {
        "type": "object",
        "properties": {
            "contest_category": {"type": "string"},
            "subcategory": {"type": "string"},
            "confidence": {"type": "number"},
        },
        "required": ["contest_category", "subcategory", "confidence"],
    }
    prompt = (
        "Classify the following FFA-CDE knowledge chunk. Choose contest_category "
        f"from this list: {candidate_contests}. Then choose the most specific "
        "subcategory key from TOPIC_QUERIES that fits. Return confidence 0..1 "
        "based on how clearly the chunk text matches. If unsure, return low "
        "confidence (under 0.5).\n\nCHUNK:\n" + chunk_text[:1000]
    )
    resp = model.generate_content(
        prompt,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": schema,
        },
    )
    return json.loads(resp.text)


def classify_chunk(
    chunk_text: str,
    source_type: str,
    source_path: Optional[str],
    frontmatter: Optional[dict] = None,
    use_llm: bool = False,
) -> ClassificationResult:
    # (existing heuristic body — see Task 2) returns ClassificationResult
    heuristic_result = _classify_heuristic(chunk_text, source_type, source_path, frontmatter)
    if heuristic_result.contest_category and heuristic_result.subcategory:
        return heuristic_result
    if not use_llm:
        return heuristic_result if heuristic_result.contest_category else \
               ClassificationResult(None, None, "heuristic", 0.0)

    # LLM stage
    candidates = list({c for _, c in RULEBOOK_FILENAME_RULES})
    raw = _gemini_classify(chunk_text, candidates)
    conf = float(raw.get("confidence", 0))
    if conf < CONFIDENCE_THRESHOLD:
        return ClassificationResult(None, None, "llm", conf)
    return ClassificationResult(
        contest_category=raw["contest_category"],
        subcategory=raw["subcategory"],
        classified_by="llm",
        confidence=conf,
    )
```

Rename the original `classify_chunk` body to `_classify_heuristic(chunk_text, source_type, source_path, frontmatter)` so the new `classify_chunk` can compose it. Do NOT delete heuristic logic.

- [ ] **Step 4: Run all classifier tests**

```bash
pytest tests/test_classify_chunk.py -v
```

Expected: 9/9 pass (6 heuristic + 3 LLM).

- [ ] **Step 5: Commit**

```bash
git add scripts/classify_chunk.py tests/test_classify_chunk.py
git commit -m "feat(rag): Gemini Flash fallback for chunk classifier"
```

---

## Task 4: Backfill driver script

**Files:**
- Create: `scripts/backfill_taxonomy.py`
- Create: `tests/test_backfill_taxonomy.py`

- [ ] **Step 1: Write failing batch logic test**

Create `tests/test_backfill_taxonomy.py`:

```python
from unittest.mock import MagicMock, patch
from scripts.backfill_taxonomy import process_batch, BatchSummary

def test_process_batch_calls_classifier_per_row():
    rows = [
        {"id": "u1", "content": "x", "source_type": "rulebook", "source_path": "p.pdf", "frontmatter": None, "contest_category": None, "subcategory": None},
        {"id": "u2", "content": "y", "source_type": "obsidian", "source_path": "Livestock/n.md", "frontmatter": None, "contest_category": None, "subcategory": None},
    ]
    classifier = MagicMock(side_effect=[
        MagicMock(contest_category="Livestock", subcategory="Livestock-USDA-Grading", classified_by="heuristic", confidence=1.0),
        MagicMock(contest_category="Livestock", subcategory=None, classified_by="heuristic", confidence=0.8),
    ])
    updates, failures, summary = process_batch(rows, classifier, confidence_threshold=0.6)
    assert len(updates) == 2
    assert updates[0]["subcategory"] == "Livestock-USDA-Grading"
    assert updates[1]["subcategory"] is None
    assert len(failures) == 0
    assert summary.heuristic == 2
    assert summary.llm == 0

def test_process_batch_routes_low_confidence_to_failures():
    rows = [{"id": "u1", "content": "x", "source_type": "rulebook", "source_path": "p.pdf", "frontmatter": None, "contest_category": None, "subcategory": None}]
    classifier = MagicMock(return_value=MagicMock(
        contest_category=None, subcategory=None, classified_by="llm", confidence=0.3
    ))
    updates, failures, summary = process_batch(rows, classifier, confidence_threshold=0.6)
    assert len(updates) == 0
    assert len(failures) == 1
    assert failures[0]["reason"] == "low_confidence"
    assert summary.failures == 1
```

- [ ] **Step 2: Run tests, expect ImportError**

```bash
pytest tests/test_backfill_taxonomy.py -v
```

Expected: `ModuleNotFoundError: No module named 'scripts.backfill_taxonomy'`.

- [ ] **Step 3: Implement backfill driver**

Create `scripts/backfill_taxonomy.py`:

```python
"""Idempotent, resumable backfill of contest_category + subcategory."""
from __future__ import annotations
import argparse
import os
import sys
from dataclasses import dataclass, field
from typing import Callable
from supabase import create_client
from tqdm import tqdm
from scripts.classify_chunk import classify_chunk, ClassificationResult

BATCH = 100
CONF_THRESHOLD = 0.6


@dataclass
class BatchSummary:
    heuristic: int = 0
    llm: int = 0
    failures: int = 0


def process_batch(
    rows: list[dict],
    classifier: Callable[..., ClassificationResult],
    confidence_threshold: float = CONF_THRESHOLD,
) -> tuple[list[dict], list[dict], BatchSummary]:
    updates: list[dict] = []
    failures: list[dict] = []
    summary = BatchSummary()
    for row in rows:
        r = classifier(
            chunk_text=row["content"],
            source_type=row["source_type"],
            source_path=row.get("source_path"),
            frontmatter=row.get("frontmatter"),
            use_llm=True,
        )
        if r.contest_category is None or r.confidence < confidence_threshold:
            failures.append({
                "chunk_text_preview": (row["content"] or "")[:300],
                "source_type": row["source_type"],
                "source_path": row.get("source_path"),
                "reason": "low_confidence",
                "attempted_label": {
                    "contest": r.contest_category,
                    "subcategory": r.subcategory,
                    "confidence": r.confidence,
                },
            })
            summary.failures += 1
            continue
        updates.append({
            "id": row["id"],
            "contest_category": r.contest_category,
            "subcategory": r.subcategory,
            "classified_by": r.classified_by,
        })
        if r.classified_by == "heuristic":
            summary.heuristic += 1
        else:
            summary.llm += 1
    return updates, failures, summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--batch-size", type=int, default=BATCH)
    ap.add_argument("--source-type", default=None,
                    help="Filter to one source_type (rulebook|obsidian|app_meta)")
    args = ap.parse_args()

    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    sb = create_client(url, key)

    base = sb.table("knowledge_documents").select(
        "id, content, source_type, source_path, frontmatter, contest_category, subcategory"
    ).or_("contest_category.is.null,subcategory.is.null")
    if args.source_type:
        base = base.eq("source_type", args.source_type)

    total = sb.rpc("count_estimate",
                   {"sql": "select count(*) from knowledge_documents "
                           "where contest_category is null or subcategory is null"}).execute()
    print(f"Estimated rows to process: {total.data}")

    cursor = None
    total_summary = BatchSummary()
    pbar = tqdm()
    while True:
        q = base.order("id").limit(args.batch_size)
        if cursor:
            q = q.gt("id", cursor)
        rows = q.execute().data
        if not rows:
            break
        updates, failures, summary = process_batch(rows, classify_chunk)
        if not args.dry_run:
            for u in updates:
                sb.table("knowledge_documents").update({
                    "contest_category": u["contest_category"],
                    "subcategory": u["subcategory"],
                    "classified_by": u["classified_by"],
                    "classified_at": "now()",
                }).eq("id", u["id"]).execute()
            if failures:
                sb.table("classification_failures").insert(failures).execute()
        total_summary.heuristic += summary.heuristic
        total_summary.llm += summary.llm
        total_summary.failures += summary.failures
        cursor = rows[-1]["id"]
        pbar.update(len(rows))
        pbar.set_postfix({
            "heuristic": total_summary.heuristic,
            "llm": total_summary.llm,
            "failures": total_summary.failures,
        })
    pbar.close()
    print(f"Done. heuristic={total_summary.heuristic} "
          f"llm={total_summary.llm} failures={total_summary.failures}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_backfill_taxonomy.py -v
```

Expected: 2/2 pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/backfill_taxonomy.py tests/test_backfill_taxonomy.py
git commit -m "feat(rag): backfill driver with dry-run + batch summary"
```

---

## Task 5: Backfill dry-run + spot-check

**Files:** none (operational task)

- [ ] **Step 1: Run dry-run against production**

```bash
SUPABASE_URL=https://nkoyotdafqllgbpuklva.supabase.co \
SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY \
GEMINI_API_KEY=$GEMINI_API_KEY \
python3 scripts/backfill_taxonomy.py --dry-run --batch-size 100
```

Expected output: progress bar + final summary like `Done. heuristic=11000 llm=3800 failures=900`.

- [ ] **Step 2: Sample 20 random rows for spot-check**

Use Supabase MCP `execute_sql`:

```sql
select id, source_type, source_path, contest_category, subcategory,
       left(content, 200) as preview
from knowledge_documents
where contest_category is not null and subcategory is not null
order by random() limit 20;
```

Eyeball: is the (contest, subcategory) plausible given the preview? If accuracy < 90%, fix the heuristic rules (Task 2 file) and re-run dry-run. Do NOT proceed to live run until spot-check is acceptable.

- [ ] **Step 3: If heuristics needed adjustment, commit them**

```bash
git add scripts/classify_chunk.py
git commit -m "fix(rag): tighten classifier heuristics after dry-run review"
```

(Skip this step if no changes.)

---

## Task 6: Live backfill

- [ ] **Step 1: Run live backfill**

```bash
SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... GEMINI_API_KEY=... \
python3 scripts/backfill_taxonomy.py --batch-size 100
```

Expected: same summary as dry-run, but `classification_failures` now populated.

- [ ] **Step 2: Verify post-state**

Run via Supabase MCP `execute_sql`:

```sql
select source_type, classified_by, count(*)
from knowledge_documents
group by 1, 2 order by 1, 2;

select count(*) as nulls from knowledge_documents
where contest_category is null;

select count(*) as failures from classification_failures;
```

Expected:
- `classified_by` populated on ≥ 90% of rows.
- NULL contest_category count is small (<1000) and matches `failures` count roughly.

- [ ] **Step 3: No commit** (data change only, no code)

---

## Task 7: RPC migration — `match_knowledge_v2` accepts `p_subcategory`

**Files:**
- Create: `supabase/migrations/<ts>_match_knowledge_v2_subcat.sql`

- [ ] **Step 1: Read current RPC definition**

```bash
psql "$SUPABASE_DB_URL" -c "\df+ match_knowledge_v2"
```

Or via MCP:

```sql
select pg_get_functiondef(p.oid)
from pg_proc p join pg_namespace n on p.pronamespace=n.oid
where n.nspname='public' and p.proname='match_knowledge_v2';
```

- [ ] **Step 2: Write new RPC migration**

Create `supabase/migrations/<ts>_match_knowledge_v2_subcat.sql`. Base it on the existing definition; add the new arg + boost. Replacing the function in place:

```sql
create or replace function public.match_knowledge_v2(
  p_query_embedding halfvec(3072),
  p_contest_category text default null,
  p_subcategory text default null,
  p_event_type text default null,
  p_source_types text[] default null,
  p_match_count int default 12,
  p_uid uuid default null
)
returns table (
  id uuid,
  content text,
  source_type text,
  source_path text,
  contest_category text,
  subcategory text,
  similarity float
)
language sql stable as $$
  with ann as (
    select
      kd.id, kd.content, kd.source_type, kd.source_path,
      kd.contest_category, kd.subcategory,
      1 - (kd.embedding <=> p_query_embedding) as base_sim
    from public.knowledge_documents kd
    where (p_source_types is null or kd.source_type = any(p_source_types))
    order by kd.embedding <=> p_query_embedding
    limit p_match_count * 4
  )
  select
    id, content, source_type, source_path, contest_category, subcategory,
    base_sim
      + case when p_contest_category is not null
                  and contest_category = p_contest_category
             then 0.10 else 0 end
      + case when p_subcategory is not null
                  and subcategory = p_subcategory
             then 0.15 else 0 end
      as similarity
  from ann
  order by similarity desc
  limit p_match_count;
$$;

grant execute on function public.match_knowledge_v2 to authenticated;
```

If the current signature has extra params, preserve them. The ONLY net change should be the new `p_subcategory` arg + the new `case` clause.

- [ ] **Step 3: Apply migration**

```bash
npx supabase db push
```

Expected: confirms new migration applied.

- [ ] **Step 4: Smoke-test RPC**

```sql
select id, contest_category, subcategory, similarity
from match_knowledge_v2(
  (select embedding from knowledge_documents limit 1),
  null,                            -- p_contest_category
  'Livestock-USDA-Grading',        -- p_subcategory
  null, null, 5, null);
```

Expected: 5 rows. Any row whose `subcategory='Livestock-USDA-Grading'` should appear at the top with elevated `similarity`.

- [ ] **Step 5: Commit**

```bash
git add supabase/migrations/<ts>_match_knowledge_v2_subcat.sql
git commit -m "feat(rag): match_knowledge_v2 accepts p_subcategory with additive boost"
```

---

## Task 8: Edge function forwards subcategory

**Files:**
- Modify: `supabase/functions/match-knowledge-v2/index.ts`

- [ ] **Step 1: Read current edge fn body**

```bash
cat supabase/functions/match-knowledge-v2/index.ts
```

Note exact line where body is parsed and where RPC is called.

- [ ] **Step 2: Add subcategory to body parsing**

In `match-knowledge-v2/index.ts`, locate the body parse block (looks like `const { query, contest_category, ... } = await req.json();`). Add `subcategory`:

```ts
const {
  query,
  contest_category,
  subcategory,            // new
  event_type,
  source_types,
  match_count,
} = body;
```

In the RPC call, add the matching arg:

```ts
const { data, error } = await supabaseClient.rpc("match_knowledge_v2", {
  p_query_embedding: embedding,
  p_contest_category: contest_category ?? null,
  p_subcategory: subcategory ?? null,    // new
  p_event_type: event_type ?? null,
  p_source_types: source_types ?? null,
  p_match_count: match_count ?? 12,
  p_uid: uid,
});
```

Do not touch retrieval logic, sanitize, rate-limit, or response shape.

- [ ] **Step 3: Type-check the function locally**

```bash
deno check supabase/functions/match-knowledge-v2/index.ts
```

Expected: no errors.

- [ ] **Step 4: Deploy**

```bash
npx supabase functions deploy match-knowledge-v2
```

Expected: `Function match-knowledge-v2 deployed`.

- [ ] **Step 5: Commit**

```bash
git add supabase/functions/match-knowledge-v2/index.ts
git commit -m "feat(rag): match-knowledge-v2 edge fn forwards subcategory"
```

---

## Task 9: Query router (Jest, TDD)

**Files:**
- Create: `lib/ai/brain/queryRouter.ts`
- Create: `__tests__/brain/queryRouter.test.ts`

- [ ] **Step 1: Write failing tests**

Create `__tests__/brain/queryRouter.test.ts`:

```ts
import { routeQuery } from '@/lib/ai/brain/queryRouter';

describe('routeQuery', () => {
  it('matches slaughter cattle keywords', () => {
    expect(routeQuery('how do i score slaughter cattle?'))
      .toEqual({ contestCategory: 'Livestock', subcategory: 'Livestock-USDA-Grading' });
  });
  it('matches USDA grading mentions', () => {
    expect(routeQuery('what is usda choice grade?'))
      .toEqual({ contestCategory: 'Livestock', subcategory: 'Livestock-USDA-Grading' });
  });
  it('matches reining horse manoeuvres', () => {
    expect(routeQuery('reining maneuver scores'))
      .toEqual({ contestCategory: 'Horse', subcategory: 'Horse-Reining-Maneuvers' });
  });
  it('returns empty hint when no pattern matches', () => {
    expect(routeQuery('what time is the contest?')).toEqual({});
  });
  it('is case-insensitive', () => {
    expect(routeQuery('SLAUGHTER cattle')).toMatchObject({ contestCategory: 'Livestock' });
  });
});
```

- [ ] **Step 2: Run tests, expect failure**

```bash
npm test -- queryRouter
```

Expected: `Cannot find module '@/lib/ai/brain/queryRouter'`.

- [ ] **Step 3: Implement router**

Create `lib/ai/brain/queryRouter.ts`:

```ts
export type QueryHint = { contestCategory?: string; subcategory?: string };

type Rule = { pattern: RegExp; contest: string; sub: string };

const RULES: Rule[] = [
  { pattern: /\b(slaughter|carcass|usda\s+(choice|prime|select))\b/i,
    contest: 'Livestock', sub: 'Livestock-USDA-Grading' },
  { pattern: /\b(usda\s+grad|quality\s+grad|yield\s+grad)/i,
    contest: 'Livestock', sub: 'Livestock-USDA-Grading' },
  { pattern: /\b(reining|maneuver|spin|rollback|sliding\s+stop)\b/i,
    contest: 'Horse', sub: 'Horse-Reining-Maneuvers' },
  { pattern: /\b(halter\s+class)\b/i,
    contest: 'Horse', sub: 'Horse-Halter-Class' },
  { pattern: /\b(wool\s+grading|fleece\s+grade|micron\s+count)\b/i,
    contest: 'Wool', sub: 'Wool-Grading' },
  { pattern: /\b(somatic\s+cell|scc|milk\s+grade\s+a)\b/i,
    contest: 'Milk Quality', sub: 'MilkQuality-Grading-Standards' },
  { pattern: /\b(loblolly|longleaf|slash\s+pine|shortleaf)\b/i,
    contest: 'Forestry', sub: 'Forestry-Q2-Pine' },
  { pattern: /\b(hardwood\s+identif|oak\s+leaf|hickory)\b/i,
    contest: 'Forestry', sub: 'Forestry-Q1-Hardwood' },
  { pattern: /\b(female\s+selection|epd|breeding\s+gilt|replacement\s+heifer)\b/i,
    contest: 'Livestock', sub: 'Livestock-Selection-Genetics' },
  { pattern: /\b(creed|ffa\s+motto|emblem)\b/i,
    contest: 'Senior FFA Quiz', sub: 'FFA Manual' },
  // Extend as common queries surface in `classification_failures` and chat logs.
];

export function routeQuery(text: string): QueryHint {
  for (const r of RULES) {
    if (r.pattern.test(text)) {
      return { contestCategory: r.contest, subcategory: r.sub };
    }
  }
  return {};
}
```

- [ ] **Step 4: Run tests to verify pass**

```bash
npm test -- queryRouter
```

Expected: 5/5 pass.

- [ ] **Step 5: Commit**

```bash
git add lib/ai/brain/queryRouter.ts __tests__/brain/queryRouter.test.ts
git commit -m "feat(rag): client-side queryRouter for subcategory hints"
```

---

## Task 10: Wire `routeQuery` into `brain-v2.ts`

**Files:**
- Modify: `lib/ai/brain-v2.ts`

- [ ] **Step 1: Read current retrieval call site**

```bash
grep -n "match-knowledge-v2\|contest_category\|retrieve" lib/ai/brain-v2.ts | head -30
```

Identify the spot where the edge fn is invoked.

- [ ] **Step 2: Add import + call**

Near the top of `lib/ai/brain-v2.ts` add:

```ts
import { routeQuery } from '@/lib/ai/brain/queryRouter';
```

Before the edge fn invocation (where `contest_category` is sent), insert:

```ts
const hint = routeQuery(question);
```

In the fetch body sent to `match-knowledge-v2`, add the `subcategory` field:

```ts
const body = JSON.stringify({
  query: question,
  contest_category: hint.contestCategory ?? null,
  subcategory: hint.subcategory ?? null,
  // …existing fields preserved
});
```

If `contest_category` was previously sourced from elsewhere (e.g. a user-selected chip), prefer that existing value and fall back to `hint.contestCategory`. The `subcategory` is new and uses the hint directly.

- [ ] **Step 3: Type-check**

```bash
npx tsc --noEmit -p .
```

Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git add lib/ai/brain-v2.ts
git commit -m "feat(rag): brain-v2 forwards subcategory hint to retrieval"
```

---

## Task 11: Rewrite `ingest_knowledge.py` to require taxonomy

**Files:**
- Modify: `ingest_knowledge.py`

- [ ] **Step 1: Read current ingest path**

```bash
grep -n "insert\|knowledge_documents\|contest_category" ingest_knowledge.py | head
```

- [ ] **Step 2: Add classifier pass before insert**

In the per-chunk loop, replace direct insert with:

```python
from scripts.classify_chunk import classify_chunk, CONFIDENCE_THRESHOLD

result = classify_chunk(
    chunk_text=chunk.text,
    source_type=src_type,
    source_path=file_path,
    frontmatter=chunk.frontmatter,
    use_llm=True,
)
if result.contest_category is None or result.subcategory is None \
   or result.confidence < CONFIDENCE_THRESHOLD:
    sb.table("classification_failures").insert({
        "chunk_text_preview": chunk.text[:300],
        "source_type": src_type,
        "source_path": file_path,
        "reason": "ingest_low_confidence",
        "attempted_label": {
            "contest": result.contest_category,
            "subcategory": result.subcategory,
            "confidence": result.confidence,
        },
    }).execute()
    continue

sb.table("knowledge_documents").insert({
    "content": chunk.text,
    "embedding": embed(chunk.text),
    "source_type": src_type,
    "source_path": file_path,
    "contest_category": result.contest_category,
    "subcategory": result.subcategory,
    "classified_by": result.classified_by,
    "classified_at": "now()",
}).execute()
```

Remove any older code path that allowed insert without `contest_category`.

- [ ] **Step 3: Dry-test on a tiny sample**

If `ingest_knowledge.py` has a `--limit` or `--file` flag, use it to ingest a single small file. Otherwise, run it against an isolated test PDF in a scratch dir. Confirm:
- Chunks land in `knowledge_documents` with all taxonomy fields populated.
- Low-confidence chunks land in `classification_failures`.

- [ ] **Step 4: Commit**

```bash
git add ingest_knowledge.py
git commit -m "feat(rag): ingest blocks NULL taxonomy; routes failures to table"
```

---

## Task 12: Enforcement migration (NOT NULL)

**Files:**
- Create: `supabase/migrations/<ts>_rag_taxonomy_enforce.sql`

- [ ] **Step 1: Pre-flight check**

```sql
select count(*) from knowledge_documents
where contest_category is null
  and source_type in ('rulebook','obsidian');
```

This MUST be 0 before applying the migration. If non-zero, inspect:

```sql
select id, source_type, source_path, left(content,200)
from knowledge_documents
where contest_category is null and source_type in ('rulebook','obsidian')
limit 20;
```

Either re-run backfill on the survivors with adjusted heuristics, or hand-update them via UPDATE statements. Decide per-row.

- [ ] **Step 2: Write enforcement migration**

Create `supabase/migrations/<ts>_rag_taxonomy_enforce.sql`:

```sql
-- Enforce taxonomy fields. Pre-flight count must be 0 (see plan Task 12).
alter table public.knowledge_documents
  alter column contest_category set not null,
  alter column source_path set not null;
```

- [ ] **Step 3: Apply**

```bash
npx supabase db push
```

Expected: success. If failure (NULL rows remain), the migration fails atomically and DB state is unchanged. Return to step 1.

- [ ] **Step 4: Commit**

```bash
git add supabase/migrations/<ts>_rag_taxonomy_enforce.sql
git commit -m "feat(rag): enforce NOT NULL on contest_category + source_path"
```

---

## Task 13: E2E QA + docs + decision log

**Files:**
- Modify: `SCHEMA.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: E2E smoke in browser**

```bash
npm run web
```

Sign in. Open `/study/ai-brain`. Ask:

> "How do I score slaughter cattle?"

Expected:
- Response cites Livestock-USDA-Grading rulebook chunks.
- No clarifying-question loop.
- Sources badge tap-opens chunk text from rulebook chunk.

If clarifying loop still fires:
- Open Network tab, inspect `match-knowledge-v2` request body. Confirm `subcategory: "Livestock-USDA-Grading"` is present.
- Inspect response — top chunk should have `subcategory: "Livestock-USDA-Grading"` and higher `similarity` than peers.
- If both true and model still asks for clarification, the prompt is the next adjustment (separate spec, retrieval-tuning).

- [ ] **Step 2: Regenerate `SCHEMA.md`**

Update the `knowledge_documents` section in `SCHEMA.md` to list the three new columns and add a new section for `classification_failures`. Keep the surrounding 50+ tables intact.

- [ ] **Step 3: Append decision log to `CLAUDE.md`**

Add at the top of the `## Decisions` list:

```
- `2026-05-15` — RAG taxonomy shipped on branch `feat/rag-taxonomy`. Added `subcategory`, `classified_by`, `classified_at` columns + `classification_failures` table. New `scripts/classify_chunk.py` (heuristic + Gemini Flash fallback, threshold 0.6) + `scripts/backfill_taxonomy.py` ran on all ~16k rows. `ingest_knowledge.py` rewritten to require taxonomy at insert. `match_knowledge_v2` RPC now accepts `p_subcategory` with +0.15 additive boost; edge fn forwards. Client `lib/ai/brain/queryRouter.ts` derives subcategory from query via regex map. Spec: `docs/superpowers/specs/2026-05-15-rag-taxonomy-design.md`.
```

- [ ] **Step 4: Final verification**

```bash
npx tsc --noEmit -p .
npm test
```

Both green (worktree test noise excepted per prior runs).

- [ ] **Step 5: Commit**

```bash
git add SCHEMA.md CLAUDE.md
git commit -m "docs(rag): update SCHEMA.md + decision log for taxonomy ship"
```

- [ ] **Step 6: Push branch + open PR (optional, user decision)**

```bash
git push -u origin feat/rag-taxonomy
gh pr create --title "feat(rag): taxonomy backfill + ingest enforcement" \
  --body "$(cat <<'EOF'
## Summary
- Adds `subcategory` + classification audit columns to `knowledge_documents`.
- Backfills ~16k existing rows via heuristic + Gemini Flash classifier.
- Rewrites ingest pipeline to require taxonomy at insert (no more NULL leak).
- Plumbs subcategory hint through RPC → edge fn → client (`queryRouter.ts`).
- Enforcement migration flips NOT NULL after backfill green.

## Spec
`docs/superpowers/specs/2026-05-15-rag-taxonomy-design.md`

## Test plan
- [ ] pytest passes
- [ ] `npm test` passes
- [ ] `npx tsc --noEmit -p .` clean
- [ ] E2E: "how do I score slaughter cattle?" cites Livestock-USDA-Grading
- [ ] `classification_failures` row count reviewed by hand

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```
