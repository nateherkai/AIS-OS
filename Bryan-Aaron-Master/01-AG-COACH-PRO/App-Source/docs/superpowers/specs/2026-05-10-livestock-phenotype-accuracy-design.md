# Livestock Phenotype Drill — AI Accuracy Foundation

**Date:** 2026-05-10  
**Status:** Approved — pending implementation plan  
**Phase:** 1 of 3 (accuracy foundation; Phase 2 = visual overlays; Phase 3 = 3D/video scan)

---

## Context

The livestock phenotype drill (`app/practice/livestock-judging/drills.tsx`) evaluates 5 traits using Gemini 2.0 Flash vision. The current prompt (`lib/prompts/livestock-analyzer-prompts.ts`) has species-specific criteria and hock-set rules but no visual score anchors, no photo quality gate, no per-trait confidence scoring, and no human correction loop.

All 4 failure modes are present simultaneously:
- Wrong trait scores (AI scores a 4/10 steer as 8/10)
- Inconsistent runs (same photo, different scores)
- Generic non-judge commentary (sounds like ChatGPT, not a livestock evaluator)
- Hallucinated observations (scoring anatomy not visible in the submitted angle)

Root cause: the AI has no calibrated visual baseline, no mechanism to refuse bad inputs, and no human correction feeding back into the system. Every wrong evaluation disappears.

This spec fixes all three gaps.

---

## How Baselines Work

The AI has no baseline unless we seed one. Every proposed fix depends on Bryan scoring a gold-standard image set that becomes the system's ground truth.

### Anchor Seeding (one-time, ~2 hours)

Bryan uses a new super-admin screen (`app/(super-admin)/livestock-anchors.tsx`) to score 15–20 images — 3–5 per species, spanning the quality spectrum:

- **Strong:** expected trait scores 8–10 (show-winning quality)
- **Average:** expected 5–6 (middle of class)
- **Weak:** expected 2–4 (placing liability)

Each anchor image gets Bryan's trait scores (Muscle, Structure, Volume, Balance, Condition on 1–10) stored in `livestock_drills` with `is_anchor = true`.

### Anchor Injection (every evaluation)

`buildGeminiVisionPrompt()` fetches the 3 anchor images for the species being evaluated and injects them as calibration context:

```
CALIBRATION REFERENCES — use as your scoring scale only, do not re-evaluate:
- Weak Market Cattle [image]: Muscle=3, Structure=4, Volume=3, Balance=5, Condition=4
- Average Market Cattle [image]: Muscle=6, Structure=6, Volume=5, Balance=6, Condition=5
- Strong Market Cattle [image]: Muscle=9, Structure=8, Volume=8, Balance=8, Condition=7

Score the submitted animal relative to these reference animals.
```

This grounds every evaluation to Bryan's calibrated scale instead of the model's floating confidence.

### Accuracy Measurement

Target: AI scores land within 1.5 points of Bryan's baseline per trait on anchor re-runs. The accuracy dashboard tracks delta over time. As teacher corrections accumulate, the dataset grows and the delta should shrink.

---

## Component 1: Score Anchor System

### Problem

The current prompt defines the scale in words ("8–9 = competitive show winner") but gives the AI no visual basis for those words. Without visual anchors, scores float on the model's arbitrary confidence.

### Fix

Add `SCORE_ANCHORS` — a 5-tier visual indicator block per species × trait — to `lib/prompts/livestock-analyzer-prompts.ts`. Each tier describes what the AI should visually observe to assign that score range.

**Example: Cattle / Muscle**

```
MUSCLE SCORING ANCHORS — Cattle:
9–10: Dominant stifle pop visible from distance. Rear quarter fills from pin to hock. 
      Width through pins clearly exceeds hip width. Ham visible from front view.
      Thick, prominent loin definition. No question on muscle rank.

7–8:  Competitive stifle development. Above-average width through the quarter.
      Loin well-defined. Muscle expression obvious but not dominant.
      Would be competitive in a state-level class.

5–6:  Moderate stifle development. Width through quarter neither strong nor weak.
      Average loin definition. No clear muscle strength or liability.
      Would place mid-class — not winning, not eliminating.

3–4:  Light through the stifle. Narrow quarter. Loin lacks definition.
      Muscle is a placing liability relative to the class.
      Would not be competitive against above-average animals.

1–2:  Severely deficient. Narrow, flat, no expression through the quarter.
      Would not be competitive in any class. Bottom of any division.
```

All 5 traits × 4 species = 20 anchor blocks. Injected into `buildGeminiVisionPrompt()`.

---

## Component 2: Photo Quality Gate

### Problem

The AI scores obscured anatomy instead of refusing. Side-only photos get rear muscle scored. Blurry images get pastern angles evaluated. Garbage in = confident wrong output.

### Fix

Add `LivestockAnalyzer.checkPhotoQuality()` — a fast Gemini pre-call that fires before any scoring. If rejected, the scoring call never happens.

```typescript
type QualityResult = {
  status: 'pass' | 'warn' | 'reject';
  rejectionReason?: string;     // user-facing message
  availableAngles: string[];    // ['side', 'rear', 'front']
  missingAngles: string[];      // traits that can't be assessed
  singleAnimal: boolean;
};
```

**Rejection criteria (hard block):**
- Multiple animals clearly visible in frame → "Multiple animals detected — submit one animal at a time"
- No animal visible or fully obstructed → "Animal not fully visible — retake photo"
- Image too blurry to read anatomical detail → "Image quality too low — retake in better lighting"

**Warning criteria (soft warn, scoring proceeds with caveats):**
- Only side view submitted (no rear/front) → warn + suppresses rear muscle confidence
- Animal not standing square → warn + notes in `overallNotes`

**Used in:**
- `LivestockAnalyzer.analyzeImage()` — gates the scoring call
- `app/practice/livestock-judging/drills.tsx` — shows "Retake photo" rejection UI
- `app/(admin)/livestock-upload.tsx` — shows warning before completing upload

---

## Component 3: Per-Trait Confidence Scoring

### Problem

The AI assigns identical confidence to all traits regardless of what's visible. A side-only submission scores rear muscle the same as a three-view submission.

### Fix

Add `confidence: 0.0–1.0` to each trait in the JSON output, driven by what's actually visible:

```json
"muscle": {
  "score": 7,
  "confidence": 0.9,
  "description": "...",
  "flawType": null,
  "observations": [...]
}
```

**Confidence rules injected into prompt:**
- 1.0: Trait fully visible from submitted angles
- 0.7–0.9: Mostly visible, minor angle limitation
- 0.4–0.6: Partially visible — inference required
- Below 0.4: Insufficient visibility — do not score, flag instead

**UI in `drills.tsx`:**
- Confidence < 0.5 on a trait → show "⚠ Limited view" instead of score bar
- Show prompt: "Submit rear view for better muscle assessment"
- Confidence renders as a thin indicator under each trait score (full bar = high confidence)

---

## Component 4: Enhanced Structured Output

Extend the JSON schema returned by `buildGeminiVisionPrompt()`:

```json
{
  "traits": {
    "muscle":    { "score": 1–10, "confidence": 0.0–1.0, "description": "...", "flawType": "...", "observations": [...] },
    "structure": { ... },
    "volume":    { ... },
    "balance":   { ... },
    "condition": { ... }
  },
  "photoQualityStatus": "pass | warn | reject",
  "strengths": [
    "Primary competitive advantage (specific anatomical observation)",
    "Secondary strength"
  ],
  "placingLiabilities": [
    "Primary placing risk (specific anatomical observation)",
    "Secondary liability"
  ],
  "judgeLanguage": "One sentence in oral-reasons style: 'I placed this steer first because...'",
  "imageViewAssessment": "side | rear | front | multiple views | unclear",
  "overallNotes": "One-sentence competitive standing assessment"
}
```

`strengths` and `placingLiabilities` are the 2–3 most important factors in each direction — the judge voice that students need. These display prominently in the drill results UI.

---

## Component 5: Judge Correction Loop

### Problem

Every inaccurate AI evaluation currently disappears. There is no way to capture what was wrong, measure accuracy trends, or improve the system over time.

### Fix

Three pieces: corrections table, teacher flag flow, admin correction screen.

### DB Migration

```sql
-- Anchor flag on existing table
ALTER TABLE livestock_drills ADD COLUMN IF NOT EXISTS is_anchor BOOLEAN DEFAULT FALSE;
ALTER TABLE livestock_drills ADD COLUMN IF NOT EXISTS anchor_scores JSONB;
ALTER TABLE livestock_drills ADD COLUMN IF NOT EXISTS confidence_scores JSONB;
ALTER TABLE livestock_drills ADD COLUMN IF NOT EXISTS placing_liabilities TEXT[];
ALTER TABLE livestock_drills ADD COLUMN IF NOT EXISTS strengths TEXT[];
ALTER TABLE livestock_drills ADD COLUMN IF NOT EXISTS correction_status TEXT DEFAULT 'unreviewed';
-- correction_status: 'unreviewed' | 'accurate' | 'corrected' | 'flagged'

-- New corrections table
CREATE TABLE livestock_eval_corrections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  drill_id UUID REFERENCES livestock_drills(id) ON DELETE CASCADE,
  corrected_by UUID REFERENCES auth.users(id),
  original_traits JSONB NOT NULL,
  corrected_traits JSONB NOT NULL,
  correction_type TEXT CHECK (correction_type IN ('score', 'observation', 'terminology', 'hallucination')),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- RLS: super-admins only
ALTER TABLE livestock_eval_corrections ENABLE ROW LEVEL SECURITY;
```

### Teacher Flag UI

"Flag as inaccurate" button on drill results screen and livestock-upload result view. Sets `correction_status = 'flagged'` on the `livestock_drills` row. No score editing from teacher side — corrections happen in super-admin only.

### Super-Admin Correction Screen (`app/(super-admin)/livestock-corrections.tsx`)

- Lists all `correction_status = 'flagged'` evaluations sorted by newest
- Each row: thumbnail + species/class + date flagged + which traits are suspect
- Detail view: original AI scores vs image side-by-side
- Judge edits each trait score (slider 1–10) and selects correction type
- On save: writes to `livestock_eval_corrections`, sets `correction_status = 'corrected'`
- Dark glass aesthetic, `AnimatedButton` for all interactive elements

---

## Component 6: Accuracy Dashboard (`app/(super-admin)/livestock-eval-accuracy.tsx`)

Metrics tracked per species × trait:
- Average AI score vs average corrected score (delta)
- % of evaluations: unreviewed / accurate / corrected / flagged
- Most common correction types
- Trend over time (delta shrinking = AI improving)

Powered by a Supabase view joining `livestock_drills` and `livestock_eval_corrections`.

---

## Anchor Seeding Screen (`app/(super-admin)/livestock-anchors.tsx`)

Simple one-time-use admin tool:
- Species selector (Cattle / Swine / Sheep / Goat)
- Image picker — select from existing `livestock_drills` images or upload new
- Trait score sliders (1–10) for each of 5 traits
- Descriptive label beside each score (shows tier text: "Show winner", "Middle class", "Placing liability")
- Save sets `is_anchor = true`, stores `anchor_scores` JSONB on the `livestock_drills` row

Target: 3–5 anchors per species before going live. Minimum 1 weak / 1 average / 1 strong per species.

---

## Files to Modify / Create

| File | Change |
|---|---|
| `lib/prompts/livestock-analyzer-prompts.ts` | Add `SCORE_ANCHORS` (20 blocks); update `buildGeminiVisionPrompt()` to accept + inject anchors; add confidence/strengths/liabilities to JSON schema |
| `lib/ai/livestock-analyzer.ts` | Add `checkPhotoQuality()`; update `analyzeImage()` to gate on quality; extract confidence scores and new fields; add `fetchAnchors()` for prompt injection |
| `app/practice/livestock-judging/drills.tsx` | Confidence badges; quality rejection UI; flag button on results |
| `app/(admin)/livestock-upload.tsx` | Quality warning; flag button on upload result view |
| `app/(super-admin)/livestock-anchors.tsx` | New — anchor seeding screen |
| `app/(super-admin)/livestock-corrections.tsx` | New — flagged evaluation correction screen |
| `app/(super-admin)/livestock-eval-accuracy.tsx` | New — accuracy dashboard |
| `supabase/migrations/YYYYMMDDHHMMSS_livestock_accuracy.sql` | New columns + corrections table + RLS |

---

## Build Order

1. DB migration — all new columns and corrections table
2. Anchor seeding screen — Bryan scores 15–20 images before prompt work begins
3. Score anchor blocks (`SCORE_ANCHORS`) + anchor injection in `buildGeminiVisionPrompt()`
4. Enhanced structured output (confidence, strengths, liabilities, judgeLanguage)
5. Photo quality gate (`checkPhotoQuality()` in analyzer)
6. Confidence + strengths/liabilities UI in `drills.tsx`
7. Teacher flag flow in `drills.tsx` and `livestock-upload.tsx`
8. Super-admin correction screen
9. Accuracy dashboard

---

## Verification

1. Bryan seeds 15–20 anchor images → `is_anchor = true` confirmed in DB with `anchor_scores` stored.
2. Re-run AI on 3 anchor images → scores within 1.5 pts of Bryan's baseline per trait (spot-check manually).
3. Submit blurry or multi-animal photo to upload or drill → rejected before scoring; rejection reason shown to user.
4. Submit side-only cattle photo → rear muscle confidence < 0.7; "⚠ Limited view" badge visible in drill UI.
5. Completed drill result shows `strengths` and `placingLiabilities` fields (not just trait scores).
6. Teacher taps "Flag as inaccurate" → `correction_status = 'flagged'` confirmed in `livestock_drills`.
7. Super-admin correction screen shows flagged eval; judge edits scores → row written to `livestock_eval_corrections`.
8. Accuracy dashboard loads and shows delta table per species × trait.

---

## Out of Scope (Phase 2+)

- Visual keypoint overlays (topline, shoulder angle, stifle width measurement)
- OpenAI vision fine-tuning or Gemini multimodal tuning
- Roboflow keypoint detection model
- 3D/video phenotype scan
- Oral/written reasons (nationals scope only)
