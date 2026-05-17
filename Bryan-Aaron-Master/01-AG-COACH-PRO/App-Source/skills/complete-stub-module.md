# Skill: Complete Stub CDE Module

## Purpose

Upgrade an existing stub CDE module to a full RAG-backed practice module. Stubs have an `index.tsx` that routes to the **generic shared screens** (`/practice/study`, `/practice/flashcard`, `/practice/test`) instead of module-specific RAG-powered screens.

This skill:
1. Replaces the stub `index.tsx` with the forages-style hub
2. Creates the missing `builder.tsx`, `quiz.tsx`, `flashcards.tsx`
3. Creates `lib/[MODULE_NAME]-quiz.ts`
4. Wires all 6 integration points (same as `scaffold-cde-module`)

**If the module directory doesn't exist at all, use `scaffold-cde-module` instead.**

---

## How to Identify a Stub

A stub `index.tsx` routes to any of these generic paths:
```typescript
router.push({ pathname: '/practice/study' as any, params })
router.push({ pathname: '/practice/flashcard' as any, params })
router.push({ pathname: '/practice/test' as any, params })
```

A complete module routes to its own screens:
```typescript
router.push('/practice/[MODULE_NAME]/builder' as any)
router.push({ pathname: '/practice/[MODULE_NAME]/quiz', params: { settings: JSON.stringify(settings) } })
router.push('/practice/[MODULE_NAME]/flashcards' as any)
```

---

## Inputs Required from User

Same as `scaffold-cde-module`:

| Field | Example | Notes |
|---|---|---|
| `MODULE_NAME` | `dairy-cattle` | Matches existing folder under `app/practice/` |
| `DISPLAY_TITLE` | `Dairy Cattle Evaluation CDE` | Shown in headers |
| `LEGACY_ID` | `cde-dairy` | Used in routing check (verify against `constants/contests.ts`) |
| `TIER` | `The Blue & Gold` | Verify existing entry in `lib/tier.ts` — update if wrong |
| `PRACTICE_TYPE` | `dairy-cattle` | Verify existing entry in `lib/store/history.ts` — add if missing |
| `ACCENT_COLOR` | `#00f2ff` | Hex neon highlight for this module |
| `ICON` | `water-outline` | Valid Ionicons name |
| `TOPICS` | `['Nutrition', 'Management', 'Dairy Production', ...]` | Pulled from the stub's CATEGORIES array if present |
| `TOPIC_QUERIES` | `{ 'Nutrition': 'dairy cattle feeding nutrition TDN...' }` | Semantic retrieval query per topic |
| `CONTEST_FORMAT` | `[{ name: 'Nutrition', count: 5 }, ...]` | Per-topic MC question counts for official exam |
| `CONTEST_TOTAL` | `25` | Official total questions (visible in stub's heroDesc) |
| `RESOURCE_NOTE` | `2022–2026 Dairy Cattle Exam Bank` | Usually visible in the stub's heroCard text |

**Tip:** Read the existing stub `index.tsx` first — `CATEGORIES`, `contestId`, `heroDesc` text, and question counts are usually already there.

---

## Step 0 — Audit the Stub

Before writing anything, read the existing `app/practice/[MODULE_NAME]/index.tsx` and note:
- The `CATEGORIES` array → these become your `TOPICS`
- The `heroDesc` text → shows contest format (e.g., "25 questions × 3 pts")
- The `contestId` param → confirms `LEGACY_ID`
- What files already exist in the directory (run `ls app/practice/[MODULE_NAME]/`)

---

## Step 1 — Create `lib/[MODULE_NAME]-quiz.ts`

Follow the same pattern as `scaffold-cde-module` Step 1 exactly.

**Topics come from the stub's CATEGORIES**, not invented. If the stub has:
```typescript
const CATEGORIES = [
  { label: 'Nutrition', ... },
  { label: 'Management', ... },
  { label: 'Dairy Production', ... },
  { label: 'Reproduction', ... },
  { label: 'Diseases and Parasites', ... },
  { label: 'Breeds', ... },
]
```
Then `QUIZ_SOURCES` = `['Nutrition', 'Management', 'Dairy Production', 'Reproduction', 'Diseases and Parasites', 'Breeds']`.

---

## Step 2 — Replace `app/practice/[MODULE_NAME]/index.tsx`

**Overwrite** the stub with the forages-style hub. Key differences from the stub:

| Stub (remove) | Complete (replace with) |
|---|---|
| `router.push('/practice/study')` | `router.push('/practice/[MODULE_NAME]/builder')` |
| `router.push('/practice/flashcard')` | `router.push('/practice/[MODULE_NAME]/flashcards')` |
| `router.push('/practice/test')` | `router.push({ pathname: '/practice/[MODULE_NAME]/quiz', params: { settings: JSON.stringify({ topics, questionCount: CONTEST_TOTAL, type: 'multiple_choice', isMock: true }) } })` |
| Generic category accordion/picker UI | Forages-style hub: Contest Hub → Study & Practice → Flashcards cards |
| `import { Theme }` | Inline color constants (GOLD, NEON_BLUE, ACCENT_COLOR, CARD, etc.) |
| Manual `router.back()` or `router.canGoBack()` | `safeBack(router, '/(tabs)/cde')` |

The new `index.tsx` should look exactly like `app/practice/forages/index.tsx` with module-specific substitutions (see `scaffold-cde-module` Step 2).

---

## Step 3 — Create `app/practice/[MODULE_NAME]/builder.tsx`

Same as `scaffold-cde-module` Step 3.

---

## Step 4 — Create `app/practice/[MODULE_NAME]/quiz.tsx`

Same as `scaffold-cde-module` Step 4.

---

## Step 5 — Create `app/practice/[MODULE_NAME]/flashcards.tsx`

Same as `scaffold-cde-module` Step 5.

---

## Step 6 — Verify/Add PracticeType in `lib/store/history.ts`

The stub may already have the type registered. Check first — only add if missing.

```typescript
// Check: grep for '[PRACTICE_TYPE]' in lib/store/history.ts
// Add if not present:
| '[PRACTICE_TYPE]'
```

---

## Step 7 — Verify routing block in `app/contest/[id].tsx`

The stub routing in `startPractice()` may already exist. Check:
```typescript
// grep for 'MODULE_NAME' in app/contest/[id].tsx
```
If already present and correct, no change needed.
If missing, add per `scaffold-cde-module` Step 7.

---

## Step 8 — Verify tier mapping in `lib/tier.ts`

Check if `'[MODULE_NAME]'` already exists in `FEATURE_TIERS`. Only update if wrong or missing.

---

## Step 9 — Verify `is_active` in `constants/contests.ts`

No change needed if already `true`.

---

## Step 10 — Add TOPIC_QUERIES in `lib/ai/rag-quiz.ts`

Add one entry per topic — same as `scaffold-cde-module` Step 10. Check if any already exist from a prior partial implementation before adding.

Also add to `TOPIC_CONTEST_CATEGORY`:
```typescript
'[Topic 1]': '[Contest Category matching FOLDER_TO_CATEGORY in ingest_knowledge.py]',
'[Topic 2]': '[Same category]',
```

The category string must exactly match what `ingest_knowledge.py` assigns. Check `FOLDER_TO_CATEGORY` in `ingest_knowledge.py` for the correct value.

---

## Execution Order

1. Read the existing stub + audit (Step 0)
2. `lib/[MODULE_NAME]-quiz.ts` (Step 1)
3. `lib/store/history.ts` — verify/add (Step 6)
4. `lib/tier.ts` — verify/add (Step 8)
5. `lib/ai/rag-quiz.ts` — add TOPIC_QUERIES + TOPIC_CONTEST_CATEGORY (Step 10)
6. Replace `app/practice/[MODULE_NAME]/index.tsx` (Step 2)
7. Create `app/practice/[MODULE_NAME]/builder.tsx` (Step 3)
8. Create `app/practice/[MODULE_NAME]/quiz.tsx` (Step 4)
9. Create `app/practice/[MODULE_NAME]/flashcards.tsx` (Step 5)
10. `app/contest/[id].tsx` — verify/add routing (Step 7)
11. `constants/contests.ts` — verify is_active (Step 9)

---

## Known Stub Modules (as of 2026-04-04)

These modules have `index.tsx` routing to generic screens and need completing:

| Module | Topics from Stub | Contest Total | Ingested Source |
|---|---|---|---|
| `dairy-cattle` | Nutrition, Management, Dairy Production, Reproduction, Diseases and Parasites, Breeds | 25 | `Dairy_Cattle_Evaluation_Exam_Bank_2022-2026.pdf` |
| `livestock-judging` | Cattle, Swine, Sheep, Goats | varies | `Livestock_Evaluation_Exam_Bank__2022-2026.pdf` |
| `floral-id` | check stub | check stub | `Floriculture_Exam_Bank_2022-2026.pdf` |
| `entomology-id` | check stub | check stub | `Entomology_Exam_Bank_2022-2026.pdf` |
| `vet-science-id` | check stub | check stub | Rules + ID list only |
| `poultry-eval` | check stub | check stub | check folder |
| `wildlife` | check stub | check stub | Regional guides |
| `food-science` | check stub | check stub | Example scenarios |
| `agronomy` | check stub | check stub | Sample exam |
| `ag-comm` | check stub | check stub | check folder |
| `ag-sales` | check stub | check stub | check folder |
| `ag-issues` | check stub | check stub | check folder |
| `ag-advocacy` | check stub | check stub | check folder |
| `public-relations` | check stub | check stub | check folder |
| `radio-broadcasting` | check stub | check stub | check folder |
| `job-interview` | check stub | check stub | check folder |
| `land` | check stub | check stub | Land judging manual |

---

## Verification

Same checklist as `scaffold-cde-module`:
1. `npm run web` — no TypeScript errors
2. CDE tab → contest → tap Practice → routes to module hub (not a generic screen)
3. Contest Exam → loads, generates questions, scores, records to history
4. Study Mode → builder loads → quiz generates
5. Flashcard Mode → picks topic → cards flip correctly
