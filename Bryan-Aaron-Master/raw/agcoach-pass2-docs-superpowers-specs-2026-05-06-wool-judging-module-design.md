# Wool Judging CDE Module — Design Spec

**Date:** 2026-05-06  
**Status:** Approved  
**Stack:** Expo Router 4 / React Native / TypeScript / Supabase / Gemini AI

---

## Context

Texas FFA Wool CDE is an active contest (`cde-wool` in `constants/contests.ts`, currently `is_active: false`). A prior wool module was built and removed. This spec replaces it with a complete implementation covering study mode and a full two-phase contest simulation matching the official Texas FFA event format. No timers — student works at own pace.

---

## Architecture

### New Files

```
app/practice/wool/
  index.tsx           — Hub screen
  builder.tsx         — Study quiz builder (topic/count/type pickers)
  quiz.tsx            — RAG knowledge quiz
  flashcards.tsx      — Flashcard mode
  fleece-eval.tsx     — Contest Phase 1: 30 fleece evaluation
  placing.tsx         — Contest Phase 2: 4–6 class placing + questions
  contest-results.tsx — Full contest score breakdown

lib/wool-quiz.ts               — generateWoolQuiz(), generateWoolFlashcards()
lib/prompts/wool-prompts.ts    — AI prompts for wool quiz/flashcard generation
lib/data/wool-contest-data.ts  — Static FLEECE_PROFILES + PLACING_CLASSES datasets

lib/data/slide-decks/
  wool-fineness.ts    — 5 grade bands, spinning count, crimp assessment
  wool-length.ts      — Staple/Fr.combing/clothing thresholds per grade
  wool-yield.ts       — Yield estimation, factors, visual cues
  wool-evaluation.ts  — Evaluation order, handling, reading a fleece
```

### Modified Files (6)

| File | Change |
|---|---|
| `constants/contests.ts` | `is_active: true` for `cde-wool` |
| `app/contest/[id].tsx` | Add `if (legacyId === 'cde-wool')` block in `startPractice()` |
| `lib/tier.ts` | Add `'wool': 'The Blue & Gold'` to `FEATURE_TIERS` |
| `lib/store/history.ts` | PracticeTypes already present (`wool-quiz`, `wool-evaluation`, `wool-flashcard`) — verify only |
| `lib/ai/rag-quiz.ts` | Verify/add wool entry in `TOPIC_QUERIES` |
| `lib/data/slide-decks/index.ts` | Register 4 new wool decks in `getDeck()` lookup |

---

## Study Mode

### Hub Section: STUDY & PRACTICE
Three entry points: Slide Decks, Flashcards, Quiz.

### Slide Decks (4 decks, `species: 'wool'`)

| Deck ID | Title | Focus |
|---|---|---|
| `wool-fineness` | Spinning Count & Fineness | 5 grade bands (Fine/½ Blood/⅜ Blood/¼ Blood/Low ¼ Blood), spinning count numbers, crimp frequency, how to assess without instruments |
| `wool-length` | Staple Length Classification | Staple/French combing/clothing definitions, length thresholds per grade band from official table, what to look for |
| `wool-yield` | Yield Estimation | What yield means (lbs clean wool / grease weight), factors affecting yield (grease, VM, moisture, cotting), visual estimation cues |
| `wool-evaluation` | Fleece Evaluation Technique | Evaluation order, legal handling (no measuring devices), reading fineness/length/yield together, common mistakes |

Content sourced from NotebookLM notebook `7e3b47a2-384b-4b1c-814e-1f09355c6851` (Wool Judging CDE — Texas FFA, 38 sources). During implementation: `notebooklm ask` to generate slide bullets per topic.

Each deck follows `BriefingSlide` interface from `lib/data/slide-decks/types.ts`:
```typescript
{ title, subtitle?, points: string[], image, accent: string }
```
Images: `assets/images/wool/wool_fleece_sample.png` and `assets/images/wool/wool_staple_length.png`.

### Knowledge Quiz

- RAG-backed via `generateRAGBatch(topic, type, count, 'senior')` from `lib/ai/rag-quiz.ts`
- Topics from `TOPIC_QUERIES` wool entry
- Builder: topic multi-select, question count (5/10/20/30), type (mixed/MC/TF)
- Pattern: identical to forages module (`builder.tsx` → `quiz.tsx`)

### Flashcards

- Generated via `generateWoolFlashcards(topic, count)` in `lib/wool-quiz.ts`
- Topics: Fineness & Spinning Counts, Length Classification, Yield Estimation, Contest Rules & Scoring, Terminology
- NotebookLM (`7e3b47a2`) backs term definitions during implementation
- Pattern: identical to forages flashcards

---

## Contest Simulation

### Hub Section: CONTEST SIMULATION
Single CTA: **Start Full Contest**. Launches `fleece-eval.tsx`. No timers.

### Phase 1 — Fleece Evaluation (`fleece-eval.tsx`)

**Format:** 30 fleeces, one at a time. No timer.

**Each fleece card:**
- Photo (from `assets/images/wool/` — 2 available images, alternated/varied by description)
- Text description: color, crimp character, grease level, staple appearance, any defects
- Three grade inputs:

| Input | Options | Scoring |
|---|---|---|
| Fineness | Fine / ½ Blood / ⅜ Blood / ¼ Blood / Low ¼ Blood | Exact=4pts, 1 grade away=2pts, 2+ grades away=0pts |
| Length | Staple / French Combing / Clothing | Exact=2pts, wrong=0pts |
| Yield % | Numeric text input (0–100) | Within ±4%=4pts, ±5–8%=2pts, ±9%+=0pts |

Max 10 pts/fleece × 30 = **300 pts**

**Grade adjacency for fineness partial credit:**
Fine → ½ Blood → ⅜ Blood → ¼ Blood → Low ¼ Blood (5 ordered grades)

**Data:** `FLEECE_PROFILES` in `lib/data/wool-contest-data.ts` — static array of 60 curated profiles. Each contest draw randomizes which 30 appear. Profile shape:
```typescript
interface FleeceProfile {
  id: number;
  photo: 'sample' | 'staple'; // 'sample' → wool_fleece_sample.png, 'staple' → wool_staple_length.png
  description: string;         // text description of color, crimp, grease, defects
  correctFineness: FinenesGrade;
  correctLength: LengthClass;
  correctYield: number;        // percentage, e.g. 52 = 52%
}
```

After all 30: show Phase 1 subtotal, then CTA to start Phase 2.

### Phase 2 — Placing & Questions (`placing.tsx`)

**Format:** 4 classes per contest run (standard Texas FFA minimum), 4 fleeces each. No timer. Dataset includes 8 curated classes so each run can draw a varied set.

**Per class — two sections:**

**Placing (50 pts):**
- 4 fleece cards displayed with drag handle (☰)
- Student drags to rank 1–4 using `react-native-gesture-handler` PanGestureHandler + `react-native-reanimated` (both already installed — no new dependency needed)
- Scoring: standard CDE placing card formula
  - Perfect (matches official): 50 pts
  - Each adjacent transposition: −4 pts
  - Each non-adjacent transposition (skip): −6 pts
  - Floor: 0 pts

**Questions (50 pts):**
- 16 descriptors shown (from official list)
- Each: tap [1] [2] [3] [4] to assign fleece number
- Only one answer per descriptor (officials may allow ties — implementation: allow single selection only for simplicity)
- Scoring: start 50, −3 per wrong answer, floor 0

Official 16 question descriptors:
1. Longest staple
2. Shortest staple
3. Most uniform staple length
4. Finest in class
5. Coarsest in class
6. Most uniform fineness (DIA.)
7. Heaviest grease WT
8. Lightest grease WT
9. Most LBS clean wool
10. Least LBS clean wool
11. Highest yielding
12. Lowest yielding
13. Most character
14. Most vegetable matter
15. Most stained wool
16. Least fiber strength

Per class max: 100 pts. Total Phase 2: 400–600 pts (4–6 classes).

**Data:** `PLACING_CLASSES` in `lib/data/wool-contest-data.ts` — static array of 8 curated classes (contest uses 4–6, drawn from this set). Each class has 4 fleece profiles + official placing order + correct question answers.

### Results (`contest-results.tsx`)

Sections:
- Total score with range context (700–900 pts possible)
- Phase 1 breakdown: fineness accuracy %, length accuracy %, yield accuracy (avg error %)
- Phase 2 breakdown: placing score per class, questions score per class
- Overall accuracy by category
- History logged as `PracticeType: 'wool-evaluation'`

---

## Data Layer

### `lib/data/wool-contest-data.ts`

```typescript
type FinenesGrade = 'fine' | 'half_blood' | 'three_eighths' | 'quarter' | 'low_quarter';
type LengthClass = 'staple' | 'french_combing' | 'clothing';

interface FleeceProfile { ... }       // 60 entries
interface PlacingClass {
  id: string;
  fleeces: FleeceProfile[];           // always 4
  officialPlacing: [number, number, number, number]; // indices into fleeces[]
  questionAnswers: Record<string, number>; // descriptor → fleece index (1-based)
}
```

Fineness grade order for partial credit scoring: `['fine', 'half_blood', 'three_eighths', 'quarter', 'low_quarter']`

### Spinning Count Reference Table (official)

| Grade | Spinning Counts | Staple | French Combing | Clothing |
|---|---|---|---|---|
| Fine | 64s, 70s, 80s+ | >3" | 2"–3" | <2" |
| ½ Blood | 60s, 62s | >3¼" | 2¼"–3¼" | <2¼" |
| ⅜ Blood | 56s, 58s | >3½" | n/a | <3½" |
| ¼ Blood | 50s, 54s | >4" | n/a | <4" |
| Low ¼ Blood | 48s and coarser | >4" | n/a | <4" |

---

## RAG & NotebookLM

- **Knowledge quiz + flashcards:** `generateRAGBatch` → `knowledge_documents` (pgvector). TOPIC_QUERIES entry for wool already exists — verify content.
- **Slide deck content:** Query NotebookLM `7e3b47a2` during implementation to generate accurate bullet points per topic. Use `notebooklm ask "..."` targeted at relevant sources.
- **Fleece/class descriptions:** Written by hand using notebook as reference for authentic characteristics.

---

## Integration Checklist

1. `constants/contests.ts` → `is_active: true` on `cde-wool`
2. `app/contest/[id].tsx → startPractice()` → add `if (legacyId === 'cde-wool') { router.push('/practice/wool'); return; }`
3. `lib/tier.ts → FEATURE_TIERS` → `'wool': 'The Blue & Gold'`
4. `lib/store/history.ts` → confirm `wool-quiz`, `wool-evaluation`, `wool-flashcard` present
5. `lib/ai/rag-quiz.ts → TOPIC_QUERIES` → confirm/add wool entry
6. `lib/data/slide-decks/index.ts` → register `wool-fineness`, `wool-length`, `wool-yield`, `wool-evaluation`

---

## Verification

1. `npm run web` → CDE list shows Wool card active
2. Tap Wool → routes to `app/practice/wool/index.tsx` hub
3. Study: open each slide deck (4 decks load, swipe through), launch quiz (questions generate), launch flashcards (cards flip)
4. Contest: Start Full Contest → 30 fleece cards render with photo + description + grade inputs → submit all → Phase 2 loads → drag-rank works → tap questions → submit → results screen shows score breakdown
5. Scores verify against official rubric (fineness partial credit, yield tolerance bands, placing formula)
6. `npx tsc --noEmit -p .` — no type errors
