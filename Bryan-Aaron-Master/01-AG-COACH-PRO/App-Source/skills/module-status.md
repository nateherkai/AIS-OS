# Skill: Module Status Audit

## Purpose

Scan all 37 practice modules and produce a completeness report. Run this at the start of any build session to know exactly what's done, what's a stub, and what's missing entirely.

---

## When to Use

- Start of every build session to orient yourself
- After completing a batch of modules to confirm they're wired correctly
- When a module isn't working and you need to diagnose what's missing

---

## How to Run

Use the Glob and Grep tools to check each module directory. Do NOT use bash find/ls commands.

### Step 1 — Check screen files

For each module under `app/practice/`, check which of these exist:
- `index.tsx` — hub screen
- `builder.tsx` — topic/count/format pickers
- `quiz.tsx` — live quiz engine
- `flashcards.tsx` — flashcard mode

```
Glob: app/practice/*/builder.tsx   → which modules have a builder
Glob: app/practice/*/quiz.tsx      → which modules have a quiz
Glob: app/practice/*/flashcards.tsx → which modules have flashcards
```

### Step 2 — Check lib files

```
Glob: lib/*-quiz.ts   → which modules have a quiz generation lib
```

### Step 3 — Identify stub vs. complete index.tsx

A stub routes to generic screens. Check for the stub pattern:

```
Grep: pattern="/practice/study"   in app/practice/*/index.tsx  → stubs
Grep: pattern="/practice/test"    in app/practice/*/index.tsx  → stubs
Grep: pattern="/practice/flashcard" in app/practice/*/index.tsx → stubs
```

Any `index.tsx` matching these patterns is a stub needing `complete-stub-module`.

### Step 4 — Check integration points

```
Grep: PracticeType union in lib/store/history.ts
Grep: FEATURE_TIERS in lib/tier.ts
Grep: TOPIC_QUERIES in lib/ai/rag-quiz.ts
Grep: startPractice routing blocks in app/contest/[id].tsx
```

---

## Output Format

Produce a status table:

| Module | index | builder | quiz | flashcards | lib | history | tier | topic_queries | routing | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| forages | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ Complete |
| dairy-cattle | ⚠️ stub | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | 🔧 Use complete-stub-module |
| forestry | ⚠️ stub | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | 🔧 Use complete-stub-module |

**Status key:**
- ✅ Complete — all 4 screens + lib + all integrations present
- 🔧 Use complete-stub-module — `index.tsx` exists but routes to generic screens
- 🏗️ Use scaffold-cde-module — module directory is missing entirely
- ⚠️ Partial — some screens exist but not all (check which are missing)

---

## Known Module List (37 total as of 2026-04-04)

Use this as the canonical list to check against. Every module here should be accounted for:

**CDE Modules (26):**
ag-comm, ag-eng, ag-sales, ag-tech, agronomy, cotton, dairy-cattle, entomology-id, env-resources, floral-id, food-science, forages, forages-id, forestry, homesite, horse-eval, land, livestock-anatomy, livestock-judging, marketing-plan, meats-id, nursery-landscape-id, plant-id, poultry-eval, range, tractor, vet-science-id, wildlife, cotton

**LDE Modules (11):**
ag-advocacy, ag-issues, ag-skills, chapter-conducting, creed-speaking (if exists), greenhand-quiz, job-interview, public-relations, radio-broadcasting, senior-quiz

---

## What to Do With the Results

| Status | Action |
|---|---|
| ✅ Complete | No action — verify with `check-site` skill if suspicious |
| 🔧 complete-stub-module | Run `/complete-stub-module` with module inputs |
| 🏗️ scaffold-cde-module | Run `/scaffold-cde-module` with module inputs |
| ⚠️ Partial | Read each missing file and determine if it's a stub or genuinely incomplete — then run the appropriate skill |
| RAG missing | Run `rag-coverage-report` then `python3 ingest_knowledge.py` before building |
