# Livestock Module Premium Upgrade — Design Spec
**Date:** 2026-05-08  
**Status:** Awaiting implementation plan

---

## Context

The livestock judging module is the most complex and commercially important module in AgCoachPro. It must be the best livestock CDE training tool in Texas — ideally the country. Two critical gaps drive this work:

1. **Image contamination** — Some of the 175 bundled phenotype images contain multiple animals. Students evaluating multi-animal images learn incorrect evaluation habits. Must be fixed before any other improvement.
2. **Drill/question silo** — Phenotype drills and the 275-question written bank are completely disconnected. Students who can identify a sickle-hocked animal still fail written questions about hock angles, EPDs, and structural genetics — because they never learned the vocabulary anchored to the visual. The drill is the teachable moment and it's being wasted.

Texas FFA livestock CDE does not include oral/written reasons — scope is strictly visual evaluation + written knowledge test.

---

## Goals

1. Remove all multi-animal images from drill rotation
2. Build image quality pipeline that prevents future contamination
3. Connect phenotype evaluation to contextual written questions ("Drill → Question Bridge")
4. Scorecard after each animal summarizes trait eval + bridge question performance
5. Lay groundwork for difficulty progression (Phase 2)

---

## Part 1: Image Audit & Quality Pipeline

### Problem
175 bundled images in `drills.tsx` (`CATTLE_IMAGES`, `SWINE_IMAGES`, `SHEEP_IMAGES`, `GOAT_IMAGES`). Some contain multiple animals. No quality metadata exists. No filtering logic.

### Solution

#### 1A — Batch AI Audit (one-time)
- Run Gemini Vision on all 175 images in a new admin script or admin screen
- For each image, detect:
  - `animal_count`: number of animals clearly visible in frame
  - `quality_score`: 0–100 (lighting, focus, angle, single-subject framing)
  - `usable`: boolean (`animal_count === 1 && quality_score >= 60`)
- Store results in `livestock_drills` table using `batch_key` field (already exists)
- New columns needed: `animal_count INT`, `quality_score INT`, `is_flagged BOOLEAN`

#### 1B — Admin Review Queue
- `image-library.tsx` (already exists) gets a new "Flagged" tab
- Shows all images where `is_flagged = true` or `animal_count > 1`
- Admin can: **Remove from rotation** (sets `is_active = false`) or **Clear flag** (marks as acceptable)
- Removal sets metadata on the batch entry; `drills.tsx` filters out inactive images at load time

#### 1C — drills.tsx Load Filter
- `loadAnimals()` already fetches from `livestock_drills` by `batch_key`
- Add filter: skip batch images where `is_flagged = true` or `animal_count > 1`
- Images without a `livestock_drills` row (not yet audited) are shown normally — audit is additive

#### 1D — Upload Validation (ongoing prevention)
- `livestock-upload.tsx` already calls Gemini Vision on upload
- Add `animal_count` check to upload flow: if `> 1`, show warning "Multiple animals detected — this image may confuse learners. Are you sure?"
- Non-blocking warning, not a hard block

### Migration needed
```sql
-- Add to livestock_drills table
ALTER TABLE livestock_drills ADD COLUMN IF NOT EXISTS animal_count INT;
ALTER TABLE livestock_drills ADD COLUMN IF NOT EXISTS quality_score INT;
ALTER TABLE livestock_drills ADD COLUMN IF NOT EXISTS is_flagged BOOLEAN DEFAULT FALSE;
```

---

## Note: Written Exam Module (275-question bank)

The existing `quiz.tsx` written exam module is **separate and untouched** by this work. It keeps its three modes — Practice, Contest simulation, Flashcards. Only verification needed: confirm the workflow (builder → quiz → results → history) runs correctly end-to-end. No structural changes.

---

## Part 2: Drill → Question Bridge

### Problem
Students evaluate phenotype traits visually and move to the next animal. The visual evaluation is the teachable moment — but nothing asks them to apply FFA judging vocabulary to what they just saw.

### What the bridge questions are NOT
These are **not** drawn from the 275-question written exam bank. That bank is a standalone exam prep tool.

### What the bridge questions ARE
AI-generated (Gemini) questions built contextually from the animal the student just evaluated, using **official FFA livestock characteristics vocabulary**:

**Market animal characteristics:**
1. Muscularity
2. Structure/Design
3. Volume/Capacity
4. Fat/Condition
5. Frame

**Breeding animal characteristics:**
1. Volume/Capacity
2. Sex Character (masculinity/femininity)
3. Structure/Design
4. Frame
5. Muscle

### Bridge Question Generation

New function: `lib/livestock-drill-bridge.ts → generateBridgeQuestions(animal, evalResult)`

**Input:**
```typescript
{
  species: 'Cattle' | 'Swine' | 'Sheep' | 'Goat',
  classType: 'Market' | 'Breeding',
  traits: {
    muscle:    { score: number, flawType: string | null, observations: Observation[] },
    structure: { score: number, flawType: string | null, observations: Observation[] },
    volume:    { score: number, flawType: string | null, observations: Observation[] },
    balance:   { score: number, flawType: string | null, observations: Observation[] },
    condition: { score: number, flawType: string | null, observations: Observation[] },
  },
  count: number  // 3–5
}
```

**Output:** `BridgeQuestion[]` (multiple-choice, 4 options, correct answer, explanation)

**Gemini prompt strategy:**
- Pass animal's class type → determines which characteristic set (Market or Breeding)
- Pass trait scores + identified flaws as context
- Ask Gemini to generate `count` multiple-choice questions that:
  - Use the official characteristic category names (Muscularity, Structure/Design, etc.)
  - Reference what the student just observed ("This animal showed a sickle-hocked rear leg...")
  - Test whether they can name, classify, and explain the flaw in FFA terminology
  - Vary difficulty: 1–2 recall questions + 1–2 application questions
- Use Gemini structured output (`responseMimeType: 'application/json'`) with schema
- Parse with `parseAIJson` from `lib/ai/parser.ts`

**Prompt location:** `lib/prompts/livestock-analyzer-prompts.ts` (add `BRIDGE_QUESTION_PROMPT`)

**Caching:** Generated questions cached in component state for the session. Not persisted to DB (fresh per drill session).

### drills.tsx Flow Changes

Current flow:
```
traits evaluation → scorecard → next animal
```

New flow:
```
traits evaluation → trait scorecard → bridge questions (3–5) → question scorecard → next animal
```

New state vars in `drills.tsx`:
```typescript
type DrillPhase = 'traits' | 'trait-scorecard' | 'bridge-questions' | 'bridge-scorecard';
const [phase, setPhase] = useState<DrillPhase>('traits');
const [bridgeQuestions, setBridgeQuestions] = useState<BridgeQuestion[]>([]);
const [bridgeAnswers, setBridgeAnswers] = useState<Record<string, string>>({});
const [bridgeLoading, setBridgeLoading] = useState(false);
```

Bridge generation starts **in background** when trait scorecard displays (no wait).

### Trait Scorecard Enhancement
- "Now test your knowledge" CTA at bottom
- Shows characteristic categories relevant to this animal (Market or Breeding list)
- Auto-advances to bridge questions after 4s OR on tap

### Bridge Question UI
- Species icon + class type header: "MARKET CATTLE — Test Your Knowledge"
- Shows which characteristic category each question targets (e.g., "Structure/Design")
- Image stays visible at top (collapsed, ~20% height) so student can reference what they evaluated
- Progress: "Question 2 of 4"
- Immediate feedback per question with explanation referencing the characteristic

### Bridge Scorecard
After all bridge questions answered:
- Combined scorecard: Trait eval score + Bridge question score
- "Strongest characteristic" and "Needs work" callout using official category names
- "Next Animal" button

---

## Part 3: History Tracking

- Bridge question results logged to same `PracticeType: 'livestock-judging'` attempt in Supabase
- Add `bridge_correct` / `bridge_total` fields to attempt metadata JSONB
- Teacher dashboard can surface: "Students who struggle with structural questions after correct visual ID" — the gap between seeing and knowing

---

## Files to Create/Modify

| File | Change |
|---|---|
| `app/practice/livestock-judging/drills.tsx` | Add phase state, bridge question rendering, scorecard update |
| `lib/livestock-drill-bridge.ts` | New — `generateBridgeQuestions()` via Gemini structured output |
| `lib/prompts/livestock-analyzer-prompts.ts` | Add `BRIDGE_QUESTION_PROMPT` with Market/Breeding characteristics vocab |
| `app/(admin)/image-library.tsx` | Add Flagged tab, is_active toggle |
| `lib/livestock-admin-audit.ts` | New — batch Gemini Vision audit runner |
| `supabase/migrations/YYYYMMDDHHMMSS_livestock_image_quality.sql` | New columns on `livestock_drills` |

---

## What We're NOT Building (Texas scope)

- Oral/written reasons — nationals only, Phase 2
- 4-animal side-by-side placing — separate feature, Phase 2
- Difficulty progression — Phase 2 (data collected from this phase informs it)
- Cross-school leaderboards — Phase 3

---

## Verification

1. Run image audit on all 175 bundled images → confirm multi-animal images flagged
2. Check `image-library.tsx` Flagged tab shows flagged images
3. Remove a flagged image → confirm it no longer appears in `drills.tsx`
4. Confirm written exam module (`quiz.tsx`) — practice / contest / flashcard modes all route and score correctly (no regression)
5. Complete a drill on a Market steer with structural flaws → confirm bridge questions use Market characteristic vocabulary (Muscularity, Structure/Design, etc.)
6. Complete a drill on a Breeding animal → confirm bridge questions use Breeding characteristic vocabulary (Sex Character, Volume/Capacity, etc.)
7. Verify image stays visible (collapsed) during bridge questions
8. Verify bridge questions generate in background while trait scorecard displays (no spinner blocking)
9. Check `livestock_judging` attempt in Supabase includes `bridge_correct` / `bridge_total`
