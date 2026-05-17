# Skill: Module Readiness

## Purpose

Consolidation of `module-status` + `rag-coverage-report`. Single dashboard: which modules are scaffolded, which are stubs, which have RAG coverage, which can ship.

Run at start of every build session.

---

## When to Use

- Session start (replaces running two separate skills)
- Before planning sprint work
- After bulk ingest or scaffold pass

---

## Output Format

```
| Module          | Files | State    | Category          | Chunks | Ready |
|-----------------|-------|----------|-------------------|--------|-------|
| forages         | 5/5   | complete | Forage            | 87     | ✅    |
| dairy-cattle    | 5/5   | complete | Dairy Cattle      | 0      | ⚠️ RAG |
| widget-eval     | 1/5   | stub     | —                 | —      | ❌    |
| land            | 0/5   | missing  | Land              | 42     | ❌    |
```

State key:
- **complete** = 5 files (index, builder, quiz, flashcards, lib) + routed in `startPractice()`
- **stub** = index.tsx exists but routes to generic `/practice/study` or `/practice/test`
- **missing** = directory absent

Ready key:
- ✅ Complete + RAG coverage met
- ⚠️ Code complete, RAG missing → blocked on `pdf-to-rag`
- ❌ Needs scaffold or completion

---

## Procedure

### 1. Scan practice dirs

```bash
for dir in app/practice/*/; do
  name=$(basename "$dir")
  files=$(ls "$dir" 2>/dev/null | grep -cE "^(index|builder|quiz|flashcards)\.tsx$")
  lib=$(ls "lib/${name}-quiz.ts" 2>/dev/null | wc -l)
  echo "$name $files $lib"
done
```

### 2. Detect stubs

```bash
for f in app/practice/*/index.tsx; do
  if grep -q "router.push.*'/practice/study'" "$f" || \
     grep -q "router.push.*'/practice/test'" "$f"; then
    echo "STUB: $(dirname $f)"
  fi
done
```

### 3. Check `startPractice()` routing

```bash
grep -E "if \(legacyId === " app/contest/\[id\].tsx | wc -l
# Count routed modules — should match complete count
```

### 4. RAG coverage

```sql
select contest_category, event_type,
  count(*) as chunks, count(distinct source_file) as files
from knowledge_documents
group by contest_category, event_type
order by event_type, contest_category;
```

### 5. Tier registration

```bash
# Modules with tier mapping
grep -E "^\s*'cde-" lib/tier.ts | wc -l

# Modules in PracticeType union
grep -E "^\s*\| '" lib/store/history.ts | wc -l
```

### 6. Join + render

Combine results into single table. Flag rows with mismatches:
- Code complete but no tier entry
- Code complete but no `PracticeType` member
- RAG coverage but no module
- Module but no RAG coverage

---

## Coverage Map

See `rag-coverage-report` skill for full `Module → contest_category` mapping + minimum thresholds. Quick reference:

| Module | Category | Min chunks |
|---|---|---|
| forages | Forage | 50 |
| livestock-judging | Livestock | 100 |
| dairy-cattle | Dairy Cattle | 100 |
| forestry | Forestry | 80 |
| horse-eval | Horse | 40 |
| meats-id | Meats | 40 |
| floral-id | Floriculture | 80 |
| entomology-id | Entomology | 80 |

---

## Next-Action Decision Tree

| Row state | Skill to run |
|---|---|
| missing | `scaffold-cde-module` |
| stub | `complete-stub-module` |
| complete + no RAG | `pdf-to-rag` |
| complete + RAG + no tier entry | `tier-feature-register` |
| ready ✅ | smoke-test, then `check-site` post-deploy |

---

## Related

- `scaffold-cde-module`
- `complete-stub-module`
- `pdf-to-rag`
- `tier-feature-register`
- `rag-coverage-report` (legacy, this skill replaces it for joined view)
