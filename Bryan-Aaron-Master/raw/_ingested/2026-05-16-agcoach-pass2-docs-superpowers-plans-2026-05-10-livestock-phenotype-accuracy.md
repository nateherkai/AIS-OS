# Livestock Phenotype Drill — AI Accuracy Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix AI livestock phenotype evaluation accuracy by adding score anchors, photo quality gate, per-trait confidence scoring, Bryan's calibrated baseline system, and a judge correction loop.

**Architecture:** Bryan seeds 15–20 anchor images with expert scores → those scores are injected as calibration text into every Gemini evaluation prompt → the photo quality gate fires before scoring to reject bad inputs → confidence scores flag obscured anatomy → teacher/admin corrections build the training dataset over time.

**Tech Stack:** Expo Router 4 / React Native / TypeScript / Supabase / Gemini 2.0 Flash (`@google/generative-ai`) / Dark glass aesthetic (`constants/theme.ts`)

---

## File Map

| File | Role |
|---|---|
| `supabase/migrations/YYYYMMDDHHMMSS_livestock_accuracy.sql` | New columns + corrections table |
| `lib/data/livestock-traits.ts` | Add `confidence?` to `LivestockTrait`; add `QualityCheckResult`, `AnchorRecord`, `AnalysisEnrichment` types |
| `lib/prompts/livestock-analyzer-prompts.ts` | Add `SCORE_ANCHORS`; add `buildAnchorCalibrationText()`; update `buildGeminiVisionPrompt()` to accept + inject anchors; add confidence/strengths/liabilities to JSON schema |
| `lib/ai/livestock-analyzer.ts` | Add `fetchAnchors()`, `checkPhotoQuality()`; update `analyzeImage()` to gate on quality, inject anchors, parse new fields |
| `app/(super-admin)/livestock-anchors.tsx` | New — Bryan scores anchor images to establish ground truth |
| `app/(super-admin)/livestock-corrections.tsx` | New — review and correct flagged evaluations |
| `app/(super-admin)/livestock-eval-accuracy.tsx` | New — accuracy delta dashboard |
| `app/practice/livestock-judging/drills.tsx` | Confidence badges, quality rejection UI, strengths/liabilities display, flag button |
| `app/(admin)/livestock-upload.tsx` | Quality rejection warning, flag button on result view |

---

## Task 1: DB Migration

**Files:**
- Create: `supabase/migrations/20260510120000_livestock_accuracy.sql`

- [ ] **Step 1: Create migration file**

```sql
-- supabase/migrations/20260510120000_livestock_accuracy.sql

-- Extend livestock_drills with accuracy columns
ALTER TABLE livestock_drills
  ADD COLUMN IF NOT EXISTS is_anchor         BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS anchor_scores     JSONB,
  ADD COLUMN IF NOT EXISTS confidence_scores JSONB,
  ADD COLUMN IF NOT EXISTS strengths         TEXT[],
  ADD COLUMN IF NOT EXISTS placing_liabilities TEXT[],
  ADD COLUMN IF NOT EXISTS judge_language    TEXT,
  ADD COLUMN IF NOT EXISTS photo_quality_status TEXT DEFAULT 'unreviewed',
  ADD COLUMN IF NOT EXISTS correction_status TEXT DEFAULT 'unreviewed';

-- correction_status values: 'unreviewed' | 'accurate' | 'corrected' | 'flagged'
-- photo_quality_status values: 'unreviewed' | 'pass' | 'warn' | 'reject'

-- Index for anchor lookups by species
CREATE INDEX IF NOT EXISTS idx_livestock_drills_anchor
  ON livestock_drills (species, is_anchor)
  WHERE is_anchor = TRUE;

-- Index for correction queue
CREATE INDEX IF NOT EXISTS idx_livestock_drills_correction
  ON livestock_drills (correction_status)
  WHERE correction_status = 'flagged';

-- Corrections table
CREATE TABLE IF NOT EXISTS livestock_eval_corrections (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  drill_id         UUID NOT NULL REFERENCES livestock_drills(id) ON DELETE CASCADE,
  corrected_by     UUID NOT NULL REFERENCES auth.users(id),
  original_traits  JSONB NOT NULL,
  corrected_traits JSONB NOT NULL,
  correction_type  TEXT CHECK (correction_type IN ('score', 'observation', 'terminology', 'hallucination')),
  notes            TEXT,
  created_at       TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE livestock_eval_corrections ENABLE ROW LEVEL SECURITY;

-- Only super-admins (role = 'superadmin') can read/write corrections
CREATE POLICY "superadmin_corrections_all"
  ON livestock_eval_corrections
  FOR ALL
  USING (
    (SELECT raw_user_meta_data->>'role' FROM auth.users WHERE id = auth.uid()) = 'superadmin'
  );
```

- [ ] **Step 2: Apply migration**

```bash
npx supabase db push --db-url "$SUPABASE_DB_URL"
# or via MCP: mcp__claude_ai_Supabase__apply_migration
```

Expected: migration applies cleanly, `livestock_drills` has 7 new columns, `livestock_eval_corrections` exists.

- [ ] **Step 3: Commit**

```bash
git add supabase/migrations/20260510120000_livestock_accuracy.sql
git commit -m "feat(db): add accuracy columns and corrections table for livestock drill eval"
```

---

## Task 2: TypeScript Types

**Files:**
- Modify: `lib/data/livestock-traits.ts`

- [ ] **Step 1: Write the failing test**

Create `__tests__/livestock-traits.test.ts`:

```typescript
import { LivestockTrait, QualityCheckResult, AnchorRecord, AnalysisEnrichment } from '../lib/data/livestock-traits';

describe('livestock-traits types', () => {
  it('LivestockTrait accepts confidence field', () => {
    const trait: LivestockTrait = {
      name: 'Muscle',
      score: 7,
      confidence: 0.9,
      description: 'Above average',
    };
    expect(trait.confidence).toBe(0.9);
  });

  it('LivestockTrait confidence is optional', () => {
    const trait: LivestockTrait = { name: 'Muscle', score: 7, description: 'Above average' };
    expect(trait.confidence).toBeUndefined();
  });

  it('QualityCheckResult accepts all statuses', () => {
    const result: QualityCheckResult = {
      status: 'reject',
      rejectionReason: 'Multiple animals detected',
      availableAngles: [],
      missingAngles: ['side', 'rear', 'front'],
      singleAnimal: false,
    };
    expect(result.status).toBe('reject');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npm test -- livestock-traits
```

Expected: FAIL — `QualityCheckResult` not found, `confidence` not on `LivestockTrait`.

- [ ] **Step 3: Add types to `lib/data/livestock-traits.ts`**

Add after the existing `PhenotypeObservation` interface (around line 1, before `SPECIES_TRAIT_CONFIGS`):

```typescript
export interface LivestockTrait {
  name: string;
  score: number;
  confidence?: number;     // 0.0–1.0; undefined = not assessed
  description: string;
  flawType?: string;
  observations?: PhenotypeObservation[];
}

export interface QualityCheckResult {
  status: 'pass' | 'warn' | 'reject';
  rejectionReason?: string;
  availableAngles: ('side' | 'rear' | 'front')[];
  missingAngles: ('side' | 'rear' | 'front')[];
  singleAnimal: boolean;
}

export interface AnchorRecord {
  id: string;
  species: Species;
  anchor_scores: Partial<Record<string, number>>;  // { muscle: 7, structure: 8, ... }
  image_url_side: string | null;
  image_url_rear: string | null;
  image_url_front: string | null;
}

export interface AnalysisEnrichment {
  strengths: string[];
  placingLiabilities: string[];
  judgeLanguage: string;
  photoQualityStatus: 'pass' | 'warn' | 'reject';
  confidenceScores: Partial<Record<string, number>>;
}

export type AnalysisResult = {
  traits: Record<string, LivestockTrait>;
  reasoning?: string;
} & Partial<AnalysisEnrichment>;
```

Note: `LivestockTrait` already exists in the file — **replace** the existing interface definition, adding `confidence?`. Do not add a second copy.

- [ ] **Step 4: Run test to verify it passes**

```bash
npm test -- livestock-traits
```

Expected: PASS

- [ ] **Step 5: Type-check**

```bash
npx tsc --noEmit -p .
```

Expected: 0 errors (existing code uses `LivestockTrait` without `confidence`, which is fine since it's optional).

- [ ] **Step 6: Commit**

```bash
git add lib/data/livestock-traits.ts __tests__/livestock-traits.test.ts
git commit -m "feat(types): add confidence, QualityCheckResult, AnchorRecord, AnalysisEnrichment types"
```

---

## Task 3: Score Anchor Text Blocks

**Files:**
- Modify: `lib/prompts/livestock-analyzer-prompts.ts`

These 20 anchor blocks (4 species × 5 traits × 5 tiers each) are the core of prompt calibration. Write them carefully — they set the AI's scoring standard.

- [ ] **Step 1: Write the failing test**

Create `__tests__/livestock-analyzer-prompts.test.ts`:

```typescript
import { SCORE_ANCHORS } from '../lib/prompts/livestock-analyzer-prompts';

const SPECIES = ['Cattle', 'Swine', 'Sheep', 'Goat'] as const;
const TRAITS = ['muscle', 'structure', 'volume', 'balance', 'condition'] as const;
const TIERS = ['9-10', '7-8', '5-6', '3-4', '1-2'] as const;

describe('SCORE_ANCHORS', () => {
  it('has entries for all 4 species', () => {
    for (const species of SPECIES) {
      expect(SCORE_ANCHORS[species]).toBeDefined();
    }
  });

  it('has all 5 traits per species', () => {
    for (const species of SPECIES) {
      for (const trait of TRAITS) {
        expect(SCORE_ANCHORS[species][trait]).toBeDefined();
      }
    }
  });

  it('has all 5 score tiers per trait', () => {
    for (const species of SPECIES) {
      for (const trait of TRAITS) {
        for (const tier of TIERS) {
          expect(SCORE_ANCHORS[species][trait][tier]).toBeTruthy();
          expect(typeof SCORE_ANCHORS[species][trait][tier]).toBe('string');
        }
      }
    }
  });

  it('each anchor tier is descriptive (>20 chars)', () => {
    for (const species of SPECIES) {
      for (const trait of TRAITS) {
        for (const tier of TIERS) {
          expect(SCORE_ANCHORS[species][trait][tier].length).toBeGreaterThan(20);
        }
      }
    }
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npm test -- livestock-analyzer-prompts
```

Expected: FAIL — `SCORE_ANCHORS` not exported.

- [ ] **Step 3: Add `SCORE_ANCHORS` to `lib/prompts/livestock-analyzer-prompts.ts`**

Add before `SPECIES_CRITERIA`:

```typescript
export type ScoreTier = '9-10' | '7-8' | '5-6' | '3-4' | '1-2';
export type TraitKey = 'muscle' | 'structure' | 'volume' | 'balance' | 'condition';

export const SCORE_ANCHORS: Record<Species, Record<TraitKey, Record<ScoreTier, string>>> = {
  Cattle: {
    muscle: {
      '9-10': 'Dominant stifle pop clearly visible from distance. Rear quarter fills completely from pin to hock. Width through pins visibly exceeds hip width. Ham depth obvious from side profile. Thick, prominent loin. No question this animal would rank first in muscle in any competitive class.',
      '7-8':  'Above-average stifle development. Competitive width through the rear quarter. Loin well-defined from side. Muscle expression obvious and would be an asset at state level, not a liability.',
      '5-6':  'Moderate stifle development. Width through quarter is neither a strength nor weakness. Average loin definition. This animal places mid-class on muscle — not winning the trait category, not losing it.',
      '3-4':  'Light through the stifle. Narrow rear quarter. Loin lacks definition. Muscle is a placing liability — this animal would rank near the bottom of the class on this trait.',
      '1-2':  'Severely deficient. Flat, narrow, almost no stifle pop or quarter development. Would not be competitive in any class on muscle. Rare in show animals.',
    },
    structure: {
      '9-10': 'Textbook correct hock set (150–160°). Strong, correctly angled pasterns (45–50°). Square, sound feet. Smooth shoulder layback. Fluid, correct movement. Would be the structural reference animal in the class.',
      '7-8':  'Sound and correct throughout. Hock set appropriate. Pasterns adequate. Minor imperfection at most — not a liability. Moves fluidly.',
      '5-6':  'Adequate structure. Hock set within acceptable range. No severely disqualifying flaw but one minor weakness present (slightly steep pastern, minor unevenness in feet). Not penalized heavily.',
      '3-4':  'Clear structural fault present and identifiable: post-legged (>165°) OR sickle-hocked (<135°, dramatic curvature) OR weak/knuckling pasterns OR turned-out feet. Is a placing penalty.',
      '1-2':  'Multiple obvious structural flaws. Severely post-legged or dramatically sickle-hocked with additional issues. Would place last or near last on structure in any class.',
    },
    volume: {
      '9-10': 'Exceptional body capacity. Deep-sided with wide, prominent spring of rib. Deep in the rear flank, not tucked up. Wide-based, high-volume body. Would be a class leader in volume.',
      '7-8':  'Good spring of rib. Above-average flank depth. Wide enough to project volume as a strength. Not quite exceptional but clearly above the class average.',
      '5-6':  'Moderate body capacity. Ribs spring adequately, flank depth is average. Not a strength or a weakness. Places mid-class on volume.',
      '3-4':  'Shallow-bodied. Tight-ribbed or tucked up in the rear flank. Lacks the depth and spring to be competitive. Volume is a placing penalty.',
      '1-2':  'Severely lacking in volume. Flat-ribbed, extremely shallow, pinched through the flank. Would not be competitive against average animals.',
    },
    balance: {
      '9-10': 'Level topline from shoulder to tailhead. Correct, natural slope from hooks to pins. Proportionate hip and shoulder width. Eye-catching profile. Would be the most attractive, balanced animal in the class.',
      '7-8':  'Balanced and attractive. Topline level with at most a very slight imperfection. Proportions correct front to rear. Above-average eye appeal.',
      '5-6':  'Adequate balance. Topline mostly level. Minor cosmetic issue (slightly high-tailed, very slight rounding over loin) but not penalizing. Average eye appeal.',
      '3-4':  'Clear balance fault: roach-backed (humped topline), sway-backed (dip behind shoulder), high-tailed (tailhead obviously higher than topline), or steep-rumped. Is a placing penalty.',
      '1-2':  'Multiple severe balance faults. Dramatically unbalanced profile. Would place at the bottom of any class on design and eye appeal.',
    },
    condition: {
      '9-10': 'Smooth, uniform finish over the loin and ribs appropriate for market weight. Shows bloom and excellent hair coat. Not wasty. Not hard. Ideal cover for the class.',
      '7-8':  'Good finish. Smooth cover over ribs and loin. Uniform. Slight variation from ideal but not a liability. Positive condition.',
      '5-6':  'Average finish. Adequate cover without being wasty or hard. Minor unevenness. Not a placing factor.',
      '3-4':  'Clear condition fault: either under-finished/hard (ribs too prominent, loin lacks cover) OR wasty/over-fat (excessive cover over loin, patchy). Is a placing penalty.',
      '1-2':  'Severely out of condition. Either extremely hard with prominent ribs and no cover, or extremely over-fat and wasty. Would not be competitive.',
    },
  },

  Swine: {
    muscle: {
      '9-10': 'Exceptional ham depth. Thick, wide ham clearly visible from distance. Prominent muscle seam between ham and loin. Wide loin with great eye area. Dominant rear-third development. Would lead any class in muscle.',
      '7-8':  'Above-average ham development. Competitive width and depth through the ham. Loin eye above average. Muscle seam visible. Would be an asset at state level.',
      '5-6':  'Moderate ham depth. Average loin width. Muscle seam present but not prominent. Mid-class muscle — not winning or losing on this trait.',
      '3-4':  'Light ham. Narrow through the loin. Muscle seam lacking or absent. Muscle is a placing liability in a competitive class.',
      '1-2':  'Severely deficient ham and loin. Flat, narrow, poor muscle expression. Would not place near the top of any class.',
    },
    structure: {
      '9-10': 'Correct leg angles throughout (hock 140–155°, natural slight set is normal). Strong, correct pasterns. Square, sound feet. Fluid movement. No unsoundness present.',
      '7-8':  'Sound and correct. Hock set appropriate. Pasterns adequate. Moves well. Minor at most.',
      '5-6':  'Adequate soundness. No dramatically disqualifying flaw but one minor issue. Not heavily penalized.',
      '3-4':  'Clear structural fault: post-legged (obviously straight) OR sickle-hocked (dramatically excessive, foot forward under belly) OR buck-kneed OR weak/knuckling pasterns. Placing penalty.',
      '1-2':  'Multiple severe structural flaws. Unsound throughout. Would place at bottom of class on structure.',
    },
    volume: {
      '9-10': 'Exceptional belly spring and rib shape. Wide-based. Deep through the flank. Great body capacity. Would be a class leader in volume and capacity.',
      '7-8':  'Good spring of rib. Above-average flank depth. Adequate width. Volume is an asset.',
      '5-6':  'Moderate rib spring. Average flank depth. Neither a strength nor weakness.',
      '3-4':  'Flat-ribbed. Shallow through the flank. Pinched. Volume is a placing liability.',
      '1-2':  'Severely lacking volume. Extremely shallow and narrow. Not competitive.',
    },
    balance: {
      '9-10': 'Long-bodied. Level topline from shoulder through ham. Proportionate hip-to-elbow distance. Attractive, balanced profile. Would be a class leader in design.',
      '7-8':  'Above-average body length. Balanced proportions. Level topline. Good eye appeal.',
      '5-6':  'Average length and proportions. Topline mostly level. Adequate balance.',
      '3-4':  'Short-bodied OR unbalanced proportions OR high-pinned OR roach-backed. Placing penalty.',
      '1-2':  'Severely short or unbalanced. Would place at the bottom on balance and design.',
    },
    condition: {
      '9-10': 'Trim, correct finish for the weight class. No excessive cover over jowl, loin, or ham. Not hard. Ideal market condition.',
      '7-8':  'Good condition. Trim with appropriate cover. Not wasty. Minor variation from ideal.',
      '5-6':  'Average condition. Adequate cover. Not a placing factor.',
      '3-4':  'Condition fault: wasty/over-fat (heavy jowl, excessive loin cover, obvious fat deposits over ham) OR under-finished/hard. Placing penalty.',
      '1-2':  'Severely over-fat or extremely hard. Would not be competitive on condition.',
    },
  },

  Sheep: {
    muscle: {
      '9-10': 'Exceptional leg of lamb thickness. Loin width dominant. Rack depth prominent. Heavy-shouldered. Thick, round leg visible from side and rear. Would lead any class in muscle.',
      '7-8':  'Above-average leg thickness. Competitive loin width. Rack depth evident. Muscle is an asset at state level.',
      '5-6':  'Moderate leg thickness. Average loin width. Rack adequate. Mid-class muscle — not a strength or liability.',
      '3-4':  'Light-muscled. Narrow loin. Thin leg. Lacks rack depth. Muscle is a placing liability.',
      '1-2':  'Severely light. Flat, narrow throughout. Would not place near the top of any class.',
    },
    structure: {
      '9-10': 'Sound and correct throughout. Correct hock set (natural slight curvature — normal). Strong pasterns, not knuckling. Square, correct feet. Fluid movement.',
      '7-8':  'Sound. Correct angles. Pasterns adequate. Minor variation at most.',
      '5-6':  'Adequate structure. No disqualifying flaw but one minor weakness.',
      '3-4':  'Clear structural fault: weak/knuckling pasterns OR post-legged (obviously straight) OR dramatically sickle-hocked OR turned-out feet. Placing penalty.',
      '1-2':  'Multiple severe structural flaws. Would place at bottom of class.',
    },
    volume: {
      '9-10': 'Well-sprung ribs. Deep-flanked. Good body capacity for the age and weight. Width and depth both present. Class leader in volume.',
      '7-8':  'Good spring of rib. Above-average flank depth. Volume is an asset.',
      '5-6':  'Moderate rib spring. Average flank depth. Neither strong nor weak.',
      '3-4':  'Flat-ribbed. Shallow-flanked. Lacking capacity. Volume is a placing liability.',
      '1-2':  'Severely lacking volume. Not competitive.',
    },
    balance: {
      '9-10': 'Level dock from shoulder to tailhead. Correct, attractive proportions. Smooth, stylish profile. Correct shoulder layback. Eye-catching.',
      '7-8':  'Balanced and attractive. Level dock with minor variation at most. Good eye appeal.',
      '5-6':  'Adequate balance. Minor imperfection (slightly high-tailed, short-bodied) but not heavily penalized.',
      '3-4':  'Balance fault: high-tailed OR steep dock OR unbalanced proportions OR short-bodied. Placing penalty.',
      '1-2':  'Severely unbalanced. Would place at bottom on design.',
    },
    condition: {
      '9-10': 'Smooth, uniform cover. Appropriate finish for weight and age. Not wasty. Not hard. Bloom and excellent wool/hair presentation.',
      '7-8':  'Good finish. Smooth and uniform. Minor variation from ideal.',
      '5-6':  'Average condition. Adequate cover. Not a placing factor.',
      '3-4':  'Condition fault: under-finished/hard-backed (prominent backbone, lacking cover) OR patchy OR over-fat. Placing penalty.',
      '1-2':  'Severely out of condition. Not competitive.',
    },
  },

  Goat: {
    muscle: {
      '9-10': 'Thick leg of goat. Wide loin clearly visible. Well-shouldered. Round, prominent leg from side and rear. Would lead any class in muscle.',
      '7-8':  'Above-average leg thickness and loin width. Muscle is an asset. Competitive at state level.',
      '5-6':  'Moderate leg thickness. Average loin width. Mid-class — neither a strength nor weakness.',
      '3-4':  'Light-muscled. Narrow loin. Thin leg. Placing liability.',
      '1-2':  'Severely deficient muscle. Would not be competitive.',
    },
    structure: {
      '9-10': 'Sound and correct throughout. Correct hock angles (natural slight curvature is normal). Strong pasterns. Square feet. Fluid.',
      '7-8':  'Sound. Correct angles. Minor variation at most.',
      '5-6':  'Adequate. No disqualifying flaw. One minor weakness.',
      '3-4':  'Clear structural fault: weak pasterns OR post-legged (obviously straight) OR dramatically sickle-hocked OR turned-out feet. Placing penalty.',
      '1-2':  'Multiple severe structural flaws. Would place at bottom.',
    },
    volume: {
      '9-10': 'Good spring of rib. Deep-flanked. Wide-based. Excellent capacity for the weight. Class leader in volume.',
      '7-8':  'Good rib spring. Above-average flank depth. Volume is an asset.',
      '5-6':  'Moderate capacity. Average spring of rib and flank. Neither strong nor weak.',
      '3-4':  'Shallow. Flat-ribbed. Lacking capacity. Placing liability.',
      '1-2':  'Severely lacking volume. Not competitive.',
    },
    balance: {
      '9-10': 'Level topline. Balanced, attractive proportions. Stylish and correct profile. Eye-catching from any angle.',
      '7-8':  'Balanced. Level topline with minor variation. Good eye appeal.',
      '5-6':  'Adequate balance. Minor imperfection. Not heavily penalized.',
      '3-4':  'Balance fault: unbalanced proportions OR plain appearance OR short-bodied OR level dock fault. Placing penalty.',
      '1-2':  'Severely unbalanced or plain. Would place at bottom on design.',
    },
    condition: {
      '9-10': 'Appropriate finish for weight and age. Smooth, uniform cover. Not wasty. Not hard. Good bloom.',
      '7-8':  'Good condition. Adequate cover, well-distributed. Minor variation from ideal.',
      '5-6':  'Average finish. Adequate. Not a placing factor.',
      '3-4':  'Condition fault: under-finished/hard OR over-fat OR patchy cover. Placing penalty.',
      '1-2':  'Severely out of condition. Not competitive.',
    },
  },
};
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npm test -- livestock-analyzer-prompts
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add lib/prompts/livestock-analyzer-prompts.ts __tests__/livestock-analyzer-prompts.test.ts
git commit -m "feat(prompts): add SCORE_ANCHORS — 20 visual calibration blocks for all species × traits"
```

---

## Task 4: Anchor Calibration Text Builder + Updated Prompt

**Files:**
- Modify: `lib/prompts/livestock-analyzer-prompts.ts`

- [ ] **Step 1: Write the failing test**

Add to `__tests__/livestock-analyzer-prompts.test.ts`:

```typescript
import { buildAnchorCalibrationText, buildGeminiVisionPrompt, SCORE_ANCHORS } from '../lib/prompts/livestock-analyzer-prompts';
import type { AnchorRecord } from '../lib/data/livestock-traits';

describe('buildAnchorCalibrationText', () => {
  const mockAnchors: AnchorRecord[] = [
    {
      id: '1',
      species: 'Cattle',
      anchor_scores: { muscle: 3, structure: 4, volume: 3, balance: 5, condition: 4 },
      image_url_side: null, image_url_rear: null, image_url_front: null,
    },
    {
      id: '2',
      species: 'Cattle',
      anchor_scores: { muscle: 6, structure: 6, volume: 5, balance: 6, condition: 5 },
      image_url_side: null, image_url_rear: null, image_url_front: null,
    },
    {
      id: '3',
      species: 'Cattle',
      anchor_scores: { muscle: 9, structure: 8, volume: 8, balance: 8, condition: 7 },
      image_url_side: null, image_url_rear: null, image_url_front: null,
    },
  ];

  it('returns empty string when no anchors', () => {
    expect(buildAnchorCalibrationText([])).toBe('');
  });

  it('includes score values from each anchor', () => {
    const text = buildAnchorCalibrationText(mockAnchors);
    expect(text).toContain('Muscle=3');
    expect(text).toContain('Muscle=9');
  });

  it('labels weak/average/strong based on average overall score', () => {
    const text = buildAnchorCalibrationText(mockAnchors);
    expect(text).toMatch(/WEAK|AVERAGE|STRONG/i);
  });
});

describe('buildGeminiVisionPrompt', () => {
  it('includes score anchor text for the species', () => {
    const prompt = buildGeminiVisionPrompt('Cattle', 'Market');
    expect(prompt).toContain('MUSCLE SCORING ANCHORS');
  });

  it('includes confidence instructions', () => {
    const prompt = buildGeminiVisionPrompt('Cattle', 'Market');
    expect(prompt).toContain('confidence');
  });

  it('includes strengths and placingLiabilities in JSON schema', () => {
    const prompt = buildGeminiVisionPrompt('Cattle', 'Market');
    expect(prompt).toContain('strengths');
    expect(prompt).toContain('placingLiabilities');
  });

  it('includes calibration text when anchors provided', () => {
    const anchors: AnchorRecord[] = [{
      id: '1', species: 'Cattle',
      anchor_scores: { muscle: 9 },
      image_url_side: null, image_url_rear: null, image_url_front: null,
    }];
    const prompt = buildGeminiVisionPrompt('Cattle', 'Market', anchors);
    expect(prompt).toContain('CALIBRATION');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npm test -- livestock-analyzer-prompts
```

Expected: FAIL — `buildAnchorCalibrationText` not exported, `buildGeminiVisionPrompt` missing confidence/anchors.

- [ ] **Step 3: Add `buildAnchorCalibrationText()` and update `buildGeminiVisionPrompt()` in `lib/prompts/livestock-analyzer-prompts.ts`**

Add after `SCORE_ANCHORS`:

```typescript
// Classifies anchors by their average score across traits
function anchorLabel(scores: Partial<Record<string, number>>): 'WEAK' | 'AVERAGE' | 'STRONG' {
  const vals = Object.values(scores).filter((v): v is number => typeof v === 'number');
  if (vals.length === 0) return 'AVERAGE';
  const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
  if (avg <= 4.5) return 'WEAK';
  if (avg <= 6.5) return 'AVERAGE';
  return 'STRONG';
}

export function buildAnchorCalibrationText(anchors: AnchorRecord[]): string {
  if (!anchors.length) return '';

  const lines = anchors.map((a) => {
    const label = anchorLabel(a.anchor_scores);
    const scoreStr = Object.entries(a.anchor_scores)
      .map(([k, v]) => `${k.charAt(0).toUpperCase() + k.slice(1)}=${v}`)
      .join(', ');
    return `- ${label}: ${scoreStr}`;
  });

  return `
JUDGE CALIBRATION SCALE (Bryan's expert baseline — use as your scoring reference only):
${lines.join('\n')}
Score the submitted animal relative to these calibration points. If the submitted animal's muscle clearly exceeds the STRONG anchor, score muscle 9–10. If it matches the WEAK anchor, score 2–4.
`.trim();
}
```

Then update `buildGeminiVisionPrompt()` signature and body:

```typescript
// Replace the existing function signature:
export function buildGeminiVisionPrompt(
  species: Species,
  classType: ClassType,
  anchors: AnchorRecord[] = []
): string {
  const anchorText = buildAnchorCalibrationText(anchors);
  const anchorSection = anchorText ? `\n\n${anchorText}\n` : '';

  // Build score anchor blocks for this species
  const speciesAnchors = SCORE_ANCHORS[species];
  const anchorBlocks = Object.entries(speciesAnchors)
    .map(([trait, tiers]) => {
      const tierLines = Object.entries(tiers)
        .map(([tier, desc]) => `  ${tier}: ${desc}`)
        .join('\n');
      return `${trait.toUpperCase()} SCORING ANCHORS — ${species}:\n${tierLines}`;
    })
    .join('\n\n');

  return `You are an expert livestock judge with 30+ years of experience judging at the National Western Stock Show, San Antonio Livestock Show, Houston Livestock Show, and Texas State FFA conventions. You have trained dozens of state champions.

Analyze the provided ${species} (${classType}) image(s) using official livestock judging standards.
${anchorSection}

SCORE CALIBRATION — use these visual anchors to assign accurate scores:
${anchorBlocks}

CRITICAL RULES:
1. Only evaluate traits VISIBLE in the provided images. Note if an angle is suboptimal for a trait.
2. Use ONLY official livestock judging terminology.
3. DO NOT evaluate genetics, Average Daily Gain (ADG), EPDs, or any non-visual metric.
4. Score each trait 1-10 using the SCORING ANCHORS above as your guide. Match the visual indicators you observe to the appropriate tier.
5. Each observation MUST reference a specific anatomical location (e.g., "stifle", "rear flank", "hock", "topline").
6. HOCK SET — MOST CRITICAL RULE: A slight, natural set to the hock is CORRECT for all species.
   Cattle ideal hock angle: 150–160°. Swine/sheep/goat: 140–155°. This slight curve is NORMAL.
   Only call "sickle-hocked" if curvature is dramatically excessive (<135°) AND hind foot sits far forward under belly.
   Only call "post-legged" if the leg is nearly perfectly straight (>165°). Default to "Correct" when in doubt.
7. Identify structural flaws by their official name ONLY when clearly and obviously present.
8. Provide 2-4 observations per trait minimum. Be precise and specific.
9. If multiple images are provided, integrate all views for a complete evaluation.
10. CONFIDENCE: Score each trait's confidence (0.0–1.0) based on how clearly visible that trait is in the submitted images:
    - 1.0: Trait fully visible from the angles provided
    - 0.7–0.9: Mostly visible, minor angle limitation
    - 0.4–0.6: Partially visible, some inference required
    - Below 0.4: Insufficient visibility — set score to null and note what angle is needed
11. STRENGTHS: Identify the 2–3 most significant competitive advantages of this animal.
12. PLACING LIABILITIES: Identify the 2–3 most significant reasons this animal would place lower in a competitive class.
13. JUDGE LANGUAGE: Write one sentence in oral-reasons style (e.g., "I placed this steer first because he is heavier muscled and more structurally correct than his classmates, with superior balance and eye appeal.").
${SPECIES_CRITERIA[species]}

Return ONLY valid JSON (no markdown, no commentary):
{
  "traits": {
    "muscle":    { "score": 1-10, "confidence": 0.0-1.0, "description": "expert 1-sentence summary", "flawType": "specific flaw name or null", "observations": [{ "location": "anatomical location", "observation": "official terminology", "level": "Ideal|Moderate|Flawed", "explanation": "1-2 sentence expert justification" }] },
    "structure": { "score": 1-10, "confidence": 0.0-1.0, "description": "...", "flawType": "...", "observations": [...] },
    "volume":    { "score": 1-10, "confidence": 0.0-1.0, "description": "...", "flawType": "...", "observations": [...] },
    "balance":   { "score": 1-10, "confidence": 0.0-1.0, "description": "...", "flawType": "...", "observations": [...] },
    "condition": { "score": 1-10, "confidence": 0.0-1.0, "description": "...", "flawType": "...", "observations": [...] }
  },
  "strengths": ["Primary competitive advantage with specific anatomical reference", "Secondary strength"],
  "placingLiabilities": ["Primary placing risk with specific anatomical reference", "Secondary liability"],
  "judgeLanguage": "One sentence in oral-reasons style.",
  "photoQualityStatus": "pass|warn|reject",
  "imageViewAssessment": "side profile|rear|front|multiple views|unclear",
  "overallNotes": "1-sentence competitive standing assessment"
}`;
}
```

Also add the import at the top of the file:

```typescript
import type { AnchorRecord } from '../data/livestock-traits';
```

- [ ] **Step 4: Run tests**

```bash
npm test -- livestock-analyzer-prompts
```

Expected: PASS all tests

- [ ] **Step 5: Type-check**

```bash
npx tsc --noEmit -p .
```

Expected: 0 errors

- [ ] **Step 6: Commit**

```bash
git add lib/prompts/livestock-analyzer-prompts.ts __tests__/livestock-analyzer-prompts.test.ts
git commit -m "feat(prompts): add anchor calibration injection and enhanced structured output schema"
```

---

## Task 5: Photo Quality Gate + `fetchAnchors()`

**Files:**
- Modify: `lib/ai/livestock-analyzer.ts`

- [ ] **Step 1: Write the failing test**

Create `__tests__/livestock-analyzer.test.ts`:

```typescript
import { parseQualityResponse } from '../lib/ai/livestock-analyzer';

describe('parseQualityResponse', () => {
  it('returns reject when singleAnimal is false', () => {
    const raw = { singleAnimal: false, animalVisible: true, imageClear: true, availableAngles: ['side'], recommendation: 'reject', reason: 'Multiple animals' };
    const result = parseQualityResponse(raw);
    expect(result.status).toBe('reject');
    expect(result.singleAnimal).toBe(false);
    expect(result.rejectionReason).toBe('Multiple animals');
  });

  it('returns reject when animalVisible is false', () => {
    const raw = { singleAnimal: true, animalVisible: false, imageClear: true, availableAngles: [], recommendation: 'reject', reason: 'Animal not visible' };
    const result = parseQualityResponse(raw);
    expect(result.status).toBe('reject');
  });

  it('returns pass for a clean side view', () => {
    const raw = { singleAnimal: true, animalVisible: true, imageClear: true, availableAngles: ['side'], recommendation: 'pass', reason: '' };
    const result = parseQualityResponse(raw);
    expect(result.status).toBe('pass');
    expect(result.availableAngles).toContain('side');
  });

  it('returns warn when no rear view available', () => {
    const raw = { singleAnimal: true, animalVisible: true, imageClear: true, availableAngles: ['side'], recommendation: 'warn', reason: 'No rear view' };
    const result = parseQualityResponse(raw);
    expect(result.status).toBe('warn');
    expect(result.missingAngles).toContain('rear');
  });

  it('computes missingAngles correctly', () => {
    const raw = { singleAnimal: true, animalVisible: true, imageClear: true, availableAngles: ['side', 'front'], recommendation: 'pass', reason: '' };
    const result = parseQualityResponse(raw);
    expect(result.missingAngles).toContain('rear');
    expect(result.missingAngles).not.toContain('side');
    expect(result.missingAngles).not.toContain('front');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npm test -- livestock-analyzer
```

Expected: FAIL — `parseQualityResponse` not exported.

- [ ] **Step 3: Add `parseQualityResponse`, `fetchAnchors`, `checkPhotoQuality` to `lib/ai/livestock-analyzer.ts`**

Add these after the imports:

```typescript
import type { QualityCheckResult, AnchorRecord, AnalysisResult } from '../data/livestock-traits';
import { buildAnchorCalibrationText } from '../prompts/livestock-analyzer-prompts';

const ALL_ANGLES = ['side', 'rear', 'front'] as const;

// Exported for testing — parses the raw Gemini quality check JSON
export function parseQualityResponse(raw: any): QualityCheckResult {
  const available = (raw.availableAngles || []) as string[];
  const missing = ALL_ANGLES.filter(a => !available.includes(a));
  const status: QualityCheckResult['status'] =
    raw.recommendation === 'reject' ? 'reject' :
    raw.recommendation === 'warn'   ? 'warn'   : 'pass';

  return {
    status,
    rejectionReason: status !== 'pass' ? (raw.reason || undefined) : undefined,
    availableAngles: available.filter((a): a is 'side' | 'rear' | 'front' =>
      ALL_ANGLES.includes(a as any)
    ),
    missingAngles: missing,
    singleAnimal: !!raw.singleAnimal,
  };
}
```

Add `fetchAnchors` inside `LivestockAnalyzer`:

```typescript
  fetchAnchors: async (species: Species): Promise<AnchorRecord[]> => {
    try {
      const { data, error } = await supabase
        .from('livestock_drills')
        .select('id, species, anchor_scores, image_url_side, image_url_rear, image_url_front')
        .eq('species', species)
        .eq('is_anchor', true)
        .not('anchor_scores', 'is', null)
        .limit(5);

      if (error || !data) return [];
      return data as AnchorRecord[];
    } catch {
      return [];
    }
  },
```

Add `checkPhotoQuality` inside `LivestockAnalyzer`:

```typescript
  checkPhotoQuality: async (images: LivestockImages): Promise<QualityCheckResult> => {
    const primaryUri = images.side || images.rear || images.front;
    if (!primaryUri) {
      return {
        status: 'reject',
        rejectionReason: 'No image provided.',
        availableAngles: [],
        missingAngles: ['side', 'rear', 'front'],
        singleAnimal: false,
      };
    }

    const [sideData, rearData, frontData] = await Promise.all([
      images.side  ? readImageAsBase64(images.side)  : Promise.resolve(null),
      images.rear  ? readImageAsBase64(images.rear)  : Promise.resolve(null),
      images.front ? readImageAsBase64(images.front) : Promise.resolve(null),
    ]);

    const qualityPrompt = `You are checking if this livestock image is suitable for phenotype evaluation.

Return ONLY valid JSON:
{
  "singleAnimal": boolean,
  "animalVisible": boolean,
  "imageClear": boolean,
  "availableAngles": ["side" | "rear" | "front"],
  "recommendation": "pass" | "warn" | "reject",
  "reason": "brief reason if warn or reject, empty string if pass"
}

Rules:
- singleAnimal: false if 2 or more animals are clearly visible in any image
- animalVisible: false if the animal is more than 50% obscured or barely visible
- imageClear: false if the image is too blurry to read anatomical detail
- availableAngles: list which views are actually present (side = broadside view, rear = from behind, front = from the front)
- recommendation = "reject" if: !singleAnimal OR !animalVisible OR !imageClear
- recommendation = "warn" if: pass conditions met but no rear view AND no front view (side only)
- recommendation = "pass" otherwise`;

    const parts: any[] = [qualityPrompt];
    if (sideData)  { parts.push('Image provided:'); parts.push({ inlineData: { data: sideData.data, mimeType: sideData.mimeType } }); }
    if (rearData)  { parts.push('Additional image:'); parts.push({ inlineData: { data: rearData.data, mimeType: rearData.mimeType } }); }
    if (frontData) { parts.push('Additional image:'); parts.push({ inlineData: { data: frontData.data, mimeType: frontData.mimeType } }); }

    try {
      const model = getModel({ model: 'gemini-2.0-flash', generationConfig: { responseMimeType: 'application/json' } });
      const result = await Promise.race([
        model.generateContent(parts),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 30000)),
      ]) as any;

      const rawText = result.response.text().replace(/```json|```/g, '').trim();
      const parsed = JSON.parse(rawText);
      return parseQualityResponse(parsed);
    } catch {
      // If quality check fails, default to pass (don't block the user)
      return { status: 'pass', availableAngles: ['side'], missingAngles: ['rear', 'front'], singleAnimal: true };
    }
  },
```

- [ ] **Step 4: Run tests**

```bash
npm test -- livestock-analyzer
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add lib/ai/livestock-analyzer.ts __tests__/livestock-analyzer.test.ts
git commit -m "feat(analyzer): add checkPhotoQuality, fetchAnchors, parseQualityResponse"
```

---

## Task 6: Update `analyzeImage()` to Use New Features

**Files:**
- Modify: `lib/ai/livestock-analyzer.ts`

- [ ] **Step 1: Update `analyzeImage()` in `LivestockAnalyzer`**

Replace the existing `analyzeImage` function body with this updated version. The new version: (1) runs quality gate first, (2) fetches anchors, (3) injects anchors into prompt, (4) parses `confidence`, `strengths`, `placingLiabilities`, `judgeLanguage` from response.

```typescript
  analyzeImage: async (
    images: LivestockImages,
    species: Species,
    classType: ClassType,
    feedback?: string,
    existingTraits?: Record<string, LivestockTrait>
  ): Promise<AnalysisResult> => {

    // ── FEEDBACK MODE ──────────────────────────────────────────────────────────
    if (feedback && existingTraits) {
      return LivestockAnalyzer._refineWithClaude(existingTraits, species, feedback);
    }

    // ── INITIAL ANALYSIS MODE ─────────────────────────────────────────────────
    if (!genAI) throw new Error('Gemini service not configured.');

    const primaryUri = images.side || images.rear || images.front;
    if (!primaryUri) throw new Error('At least one image is required for analysis.');

    // 1. Quality gate (runs in parallel with anchor fetch)
    const [qualityResult, anchors] = await Promise.all([
      LivestockAnalyzer.checkPhotoQuality(images),
      LivestockAnalyzer.fetchAnchors(species),
    ]);

    if (qualityResult.status === 'reject') {
      throw new Error(`QUALITY_REJECT:${qualityResult.rejectionReason || 'Image quality insufficient'}`);
    }

    // 2. Read all available images as base64
    const [sideData, rearData, frontData] = await Promise.all([
      images.side  ? readImageAsBase64(images.side)  : Promise.resolve(null),
      images.rear  ? readImageAsBase64(images.rear)  : Promise.resolve(null),
      images.front ? readImageAsBase64(images.front) : Promise.resolve(null),
    ]);

    if (!sideData && !rearData && !frontData) throw new Error('Failed to read image data.');

    // 3. Build parts with anchor-injected prompt
    const parts: any[] = [buildGeminiVisionPrompt(species, classType, anchors)];

    if (sideData)  { parts.push('SIDE PROFILE VIEW (primary):'); parts.push({ inlineData: { data: sideData.data, mimeType: sideData.mimeType } }); }
    if (rearData)  { parts.push('REAR VIEW (use for muscle/quarter evaluation):'); parts.push({ inlineData: { data: rearData.data, mimeType: rearData.mimeType } }); }
    if (frontData) { parts.push('FRONT VIEW (use for chest/shoulder/front leg evaluation):'); parts.push({ inlineData: { data: frontData.data, mimeType: frontData.mimeType } }); }

    const model = getModel({ model: 'gemini-2.0-flash', generationConfig: { responseMimeType: 'application/json' } });

    let lastError: any;
    const delays = [1000, 2000, 4000];

    for (let attempt = 0; attempt <= delays.length; attempt++) {
      try {
        const result = await Promise.race([
          model.generateContent(parts),
          new Promise((_, reject) => setTimeout(() => reject(new Error('Gemini timeout after 120s')), 120000)),
        ]) as any;

        const rawText = result.response.text().replace(/```json|```/g, '').trim();
        const parsed = JSON.parse(rawText);

        if (!parsed.traits) throw new Error('Invalid response: missing traits object');

        const traitNames = { muscle: 'Muscle', structure: 'Structure', volume: 'Volume', balance: 'Balance', condition: 'Condition' };
        const traits: Record<string, LivestockTrait> = {};
        const confidenceScores: Record<string, number> = {};

        for (const [key, name] of Object.entries(traitNames)) {
          const t = parsed.traits[key];
          if (t) {
            const confidence = typeof t.confidence === 'number'
              ? Math.max(0, Math.min(1, t.confidence))
              : 1.0;
            confidenceScores[key] = confidence;
            traits[key] = {
              name,
              score: Math.max(1, Math.min(10, Math.round(t.score || 5))),
              confidence,
              description: t.description || '',
              flawType: t.flawType || undefined,
              observations: (t.observations || []).map((o: any): PhenotypeObservation => ({
                location: o.location || '',
                observation: o.observation || '',
                level: (['Ideal', 'Moderate', 'Flawed'].includes(o.level) ? o.level : 'Moderate') as PhenotypeObservation['level'],
                explanation: o.explanation || '',
              })),
            };
          }
        }

        const reasoning = parsed.overallNotes
          ? `${parsed.imageViewAssessment ? `View: ${parsed.imageViewAssessment}. ` : ''}${parsed.overallNotes}`
          : undefined;

        return {
          traits,
          reasoning,
          strengths: Array.isArray(parsed.strengths) ? parsed.strengths : [],
          placingLiabilities: Array.isArray(parsed.placingLiabilities) ? parsed.placingLiabilities : [],
          judgeLanguage: parsed.judgeLanguage || '',
          photoQualityStatus: qualityResult.status,
          confidenceScores,
        };
      } catch (err: any) {
        lastError = err;
        const msg = err.message?.toLowerCase() || '';
        const retryable = msg.includes('503') || msg.includes('429') || msg.includes('overloaded') || msg.includes('rate limit') || msg.includes('network') || msg.includes('timeout');
        if (!retryable || attempt === delays.length) break;
        await new Promise(r => setTimeout(r, delays[attempt]));
      }
    }

    throw new Error(`AI analysis failed: ${lastError?.message || 'Unknown error'}`);
  },
```

Note: The `QUALITY_REJECT:` prefix in the error message is used by the UI layer (Task 9) to show the right rejection message.

- [ ] **Step 2: Update the `_refineWithClaude` return type**

The return type must now match `AnalysisResult`. Update the Claude refinement function signature:

```typescript
  _refineWithClaude: async (
    existingTraits: Record<string, LivestockTrait>,
    species: Species,
    feedback: string
  ): Promise<AnalysisResult> => {
```

The existing return `{ traits: merged, reasoning }` is compatible with `AnalysisResult` (which has `traits` required, enrichment fields optional).

- [ ] **Step 3: Type-check**

```bash
npx tsc --noEmit -p .
```

Expected: 0 errors. If callers of `analyzeImage()` that only used `{ traits }` get type errors, they're fine — `AnalysisResult` extends the old shape.

- [ ] **Step 4: Commit**

```bash
git add lib/ai/livestock-analyzer.ts
git commit -m "feat(analyzer): update analyzeImage to gate on quality, inject anchors, parse enrichment fields"
```

---

## Task 7: Anchor Seeding Screen

**Files:**
- Create: `app/(super-admin)/livestock-anchors.tsx`

This screen lets Bryan score 15–20 images to establish the ground truth baseline. The `is_anchor` flag and `anchor_scores` JSONB column were added in Task 1.

- [ ] **Step 1: Create `app/(super-admin)/livestock-anchors.tsx`**

```tsx
import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, ScrollView, StyleSheet, Alert, Image } from 'react-native';
import Slider from '@react-native-community/slider';
import { supabase } from '@/lib/supabase';
import { Theme, GlassEffect } from '@/constants/theme';
import AnimatedButton from '@/components/common/AnimatedButton';
import { Species } from '@/lib/data/livestock-traits';

const SPECIES: Species[] = ['Cattle', 'Swine', 'Sheep', 'Goat'];
const TRAITS = ['muscle', 'structure', 'volume', 'balance', 'condition'] as const;
const TRAIT_LABELS: Record<string, string> = {
  muscle: 'Muscle', structure: 'Structure', volume: 'Volume',
  balance: 'Balance', condition: 'Condition',
};

type DrillRow = {
  id: string;
  species: string;
  image_url_side: string | null;
  image_url_rear: string | null;
  image_url_front: string | null;
  is_anchor: boolean;
  anchor_scores: Record<string, number> | null;
  batch_key: string | null;
};

export default function LivestockAnchorsScreen() {
  const [selectedSpecies, setSelectedSpecies] = useState<Species>('Cattle');
  const [images, setImages] = useState<DrillRow[]>([]);
  const [selectedImage, setSelectedImage] = useState<DrillRow | null>(null);
  const [scores, setScores] = useState<Record<string, number>>({ muscle: 5, structure: 5, volume: 5, balance: 5, condition: 5 });
  const [saving, setSaving] = useState(false);
  const [anchors, setAnchors] = useState<DrillRow[]>([]);

  const loadImages = useCallback(async () => {
    const { data } = await supabase
      .from('livestock_drills')
      .select('id, species, image_url_side, image_url_rear, image_url_front, is_anchor, anchor_scores, batch_key')
      .eq('species', selectedSpecies)
      .not('image_url_side', 'is', null)
      .order('created_at', { ascending: false })
      .limit(30);
    setImages(data || []);
    setAnchors((data || []).filter(d => d.is_anchor));
  }, [selectedSpecies]);

  useEffect(() => { loadImages(); }, [loadImages]);

  const selectImage = (img: DrillRow) => {
    setSelectedImage(img);
    if (img.anchor_scores) {
      setScores({ muscle: 5, structure: 5, volume: 5, balance: 5, condition: 5, ...img.anchor_scores });
    } else {
      setScores({ muscle: 5, structure: 5, volume: 5, balance: 5, condition: 5 });
    }
  };

  const saveAnchor = async () => {
    if (!selectedImage) return;
    setSaving(true);
    const { error } = await supabase
      .from('livestock_drills')
      .update({ is_anchor: true, anchor_scores: scores })
      .eq('id', selectedImage.id);
    setSaving(false);
    if (error) { Alert.alert('Error', error.message); return; }
    Alert.alert('Saved', 'Anchor scores saved successfully.');
    await loadImages();
    setSelectedImage(null);
  };

  const removeAnchor = async (id: string) => {
    const { error } = await supabase
      .from('livestock_drills')
      .update({ is_anchor: false, anchor_scores: null })
      .eq('id', id);
    if (!error) loadImages();
  };

  const tierLabel = (score: number) => {
    if (score >= 9) return '🔴 Strong';
    if (score >= 7) return '🟡 Above Avg';
    if (score >= 5) return '🟢 Average';
    if (score >= 3) return '🔵 Below Avg';
    return '⚫ Weak';
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Anchor Seeding</Text>
      <Text style={styles.subtitle}>Score 3–5 images per species to calibrate the AI's scoring scale.</Text>

      {/* Species selector */}
      <View style={styles.speciesRow}>
        {SPECIES.map(s => (
          <AnimatedButton
            key={s}
            style={[styles.speciesBtn, selectedSpecies === s && styles.specieBtnActive]}
            onPress={() => { setSelectedSpecies(s); setSelectedImage(null); }}
          >
            <Text style={[styles.speciesBtnText, selectedSpecies === s && styles.speciesBtnTextActive]}>{s}</Text>
          </AnimatedButton>
        ))}
      </View>

      {/* Anchor count */}
      <Text style={styles.anchorCount}>{anchors.length} anchor{anchors.length !== 1 ? 's' : ''} set for {selectedSpecies}</Text>

      {/* Current anchors */}
      {anchors.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Current Anchors</Text>
          {anchors.map(a => (
            <View key={a.id} style={styles.anchorCard}>
              {a.image_url_side && <Image source={{ uri: a.image_url_side }} style={styles.thumbSmall} />}
              <View style={styles.anchorScores}>
                {TRAITS.map(t => (
                  <Text key={t} style={styles.anchorScoreText}>
                    {TRAIT_LABELS[t]}: <Text style={styles.bold}>{a.anchor_scores?.[t] ?? '—'}</Text>
                  </Text>
                ))}
              </View>
              <AnimatedButton style={styles.removeBtn} onPress={() => removeAnchor(a.id)}>
                <Text style={styles.removeBtnText}>Remove</Text>
              </AnimatedButton>
            </View>
          ))}
        </View>
      )}

      {/* Image picker */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Select Image to Score</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {images.filter(img => !img.is_anchor).map(img => (
            <AnimatedButton
              key={img.id}
              style={[styles.thumbContainer, selectedImage?.id === img.id && styles.thumbSelected]}
              onPress={() => selectImage(img)}
            >
              {img.image_url_side
                ? <Image source={{ uri: img.image_url_side }} style={styles.thumb} />
                : <View style={[styles.thumb, styles.thumbPlaceholder]}><Text style={styles.thumbPlaceholderText}>No img</Text></View>
              }
            </AnimatedButton>
          ))}
        </ScrollView>
      </View>

      {/* Score sliders */}
      {selectedImage && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Score This Animal</Text>
          {selectedImage.image_url_side && (
            <Image source={{ uri: selectedImage.image_url_side }} style={styles.previewImage} resizeMode="contain" />
          )}
          {TRAITS.map(trait => (
            <View key={trait} style={styles.sliderRow}>
              <View style={styles.sliderHeader}>
                <Text style={styles.traitLabel}>{TRAIT_LABELS[trait]}</Text>
                <Text style={styles.traitScore}>{scores[trait]} — {tierLabel(scores[trait])}</Text>
              </View>
              <Slider
                minimumValue={1}
                maximumValue={10}
                step={1}
                value={scores[trait]}
                onValueChange={v => setScores(prev => ({ ...prev, [trait]: v }))}
                minimumTrackTintColor={Theme.colors.gold}
                maximumTrackTintColor={Theme.colors.border}
                thumbTintColor={Theme.colors.gold}
              />
            </View>
          ))}
          <AnimatedButton style={styles.saveBtn} onPress={saveAnchor} disabled={saving}>
            <Text style={styles.saveBtnText}>{saving ? 'Saving…' : 'Save as Anchor'}</Text>
          </AnimatedButton>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container:           { flex: 1, backgroundColor: Theme.colors.background },
  content:             { padding: 20, paddingBottom: 60 },
  title:               { fontSize: 24, fontWeight: '700', color: Theme.colors.text, marginBottom: 4 },
  subtitle:            { fontSize: 14, color: Theme.colors.textSecondary, marginBottom: 20 },
  speciesRow:          { flexDirection: 'row', gap: 8, marginBottom: 12 },
  speciesBtn:          { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 8, borderWidth: 1, borderColor: Theme.colors.border, backgroundColor: Theme.colors.surface },
  specieBtnActive:     { backgroundColor: Theme.colors.gold, borderColor: Theme.colors.gold },
  speciesBtnText:      { fontSize: 13, color: Theme.colors.textSecondary, fontWeight: '500' },
  speciesBtnTextActive:{ color: '#000', fontWeight: '700' },
  anchorCount:         { fontSize: 13, color: Theme.colors.textSecondary, marginBottom: 16 },
  section:             { marginBottom: 24 },
  sectionTitle:        { fontSize: 16, fontWeight: '600', color: Theme.colors.text, marginBottom: 10 },
  anchorCard:          { flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: Theme.colors.surface, borderRadius: 10, padding: 10, marginBottom: 8 },
  anchorScores:        { flex: 1 },
  anchorScoreText:     { fontSize: 12, color: Theme.colors.textSecondary, marginBottom: 2 },
  bold:                { fontWeight: '700', color: Theme.colors.text },
  thumbSmall:          { width: 60, height: 60, borderRadius: 6 },
  removeBtn:           { backgroundColor: 'rgba(255,80,80,0.2)', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 6 },
  removeBtnText:       { color: '#ff5050', fontSize: 12, fontWeight: '600' },
  thumbContainer:      { marginRight: 8, borderRadius: 8, overflow: 'hidden', borderWidth: 2, borderColor: 'transparent' },
  thumbSelected:       { borderColor: Theme.colors.gold },
  thumb:               { width: 80, height: 80 },
  thumbPlaceholder:    { backgroundColor: Theme.colors.surface, alignItems: 'center', justifyContent: 'center' },
  thumbPlaceholderText:{ fontSize: 10, color: Theme.colors.textSecondary },
  previewImage:        { width: '100%', height: 200, borderRadius: 10, marginBottom: 16, backgroundColor: Theme.colors.surface },
  sliderRow:           { marginBottom: 16 },
  sliderHeader:        { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 },
  traitLabel:          { fontSize: 14, fontWeight: '600', color: Theme.colors.text },
  traitScore:          { fontSize: 13, color: Theme.colors.gold, fontWeight: '500' },
  saveBtn:             { backgroundColor: Theme.colors.gold, paddingVertical: 14, borderRadius: 10, alignItems: 'center', marginTop: 8 },
  saveBtnText:         { fontSize: 15, fontWeight: '700', color: '#000' },
});
```

- [ ] **Step 2: Verify screen renders**

```bash
npm run web
```

Navigate to the super-admin section and verify the anchors screen renders without errors.

- [ ] **Step 3: Commit**

```bash
git add app/\(super-admin\)/livestock-anchors.tsx
git commit -m "feat(super-admin): livestock anchor seeding screen for AI calibration baseline"
```

---

## Task 8: Drill UI — Confidence Badges, Quality Rejection, Strengths/Liabilities, Flag Button

**Files:**
- Modify: `app/practice/livestock-judging/drills.tsx`

This task adds UI for the new data fields. Read `drills.tsx` before editing to understand current state structure. The key areas to modify:

1. `analyzeImage()` call site — handle `QUALITY_REJECT:` errors
2. Trait scorecard rendering — add confidence badge
3. Results section — add strengths/liabilities cards
4. Results section — add "Flag as inaccurate" button

- [ ] **Step 1: Read current error handling in drills.tsx**

Search for where `analyzeImage` is called and how errors are displayed. The call is around line 433 based on the earlier exploration.

```bash
grep -n "analyzeImage\|QUALITY_REJECT\|correction_status" "/Volumes/Samsung PSSD T7/ag-coach-app/app/practice/livestock-judging/drills.tsx"
```

- [ ] **Step 2: Add state vars for new data**

Add to the existing state declarations in `PhenotypeDrillsScreen`:

```typescript
const [analysisEnrichment, setAnalysisEnrichment] = useState<{
  strengths: string[];
  placingLiabilities: string[];
  judgeLanguage: string;
} | null>(null);
const [qualityRejection, setQualityRejection] = useState<string | null>(null);
const [flagging, setFlagging] = useState(false);
const [flagged, setFlagged] = useState(false);
```

- [ ] **Step 3: Update `analyzeImage` call site to handle rejection and parse enrichment**

Find the existing `try/catch` around `LivestockAnalyzer.analyzeImage(...)` and update:

```typescript
try {
  setQualityRejection(null);
  const result = await LivestockAnalyzer.analyzeImage(images, animal.species, animal.classType);
  // ... existing trait handling ...
  // Add after existing trait parsing:
  if (result.strengths || result.placingLiabilities) {
    setAnalysisEnrichment({
      strengths: result.strengths || [],
      placingLiabilities: result.placingLiabilities || [],
      judgeLanguage: result.judgeLanguage || '',
    });
  }
} catch (err: any) {
  const msg = err.message || '';
  if (msg.startsWith('QUALITY_REJECT:')) {
    setQualityRejection(msg.replace('QUALITY_REJECT:', '').trim());
    return;  // Don't proceed to scoring phase
  }
  // existing error handling...
}
```

- [ ] **Step 4: Add quality rejection UI**

In the render section, before the trait evaluation UI, add:

```typescript
{qualityRejection && (
  <View style={styles.rejectionCard}>
    <Text style={styles.rejectionIcon}>⚠️</Text>
    <Text style={styles.rejectionTitle}>Photo Quality Issue</Text>
    <Text style={styles.rejectionText}>{qualityRejection}</Text>
    <Text style={styles.rejectionHint}>Please retake the photo and try again.</Text>
  </View>
)}
```

Add to StyleSheet:
```typescript
rejectionCard:  { backgroundColor: 'rgba(255,80,80,0.15)', borderRadius: 12, padding: 16, margin: 16, alignItems: 'center', borderWidth: 1, borderColor: 'rgba(255,80,80,0.4)' },
rejectionIcon:  { fontSize: 32, marginBottom: 8 },
rejectionTitle: { fontSize: 16, fontWeight: '700', color: '#ff5050', marginBottom: 4 },
rejectionText:  { fontSize: 14, color: Theme.colors.text, textAlign: 'center', marginBottom: 8 },
rejectionHint:  { fontSize: 12, color: Theme.colors.textSecondary, textAlign: 'center' },
```

- [ ] **Step 5: Add confidence badge to trait rendering**

Find where individual trait scores are rendered (the trait scorecard section). For each trait that has `confidence !== undefined`, add a badge:

```typescript
// After the trait score display, add:
{trait.confidence !== undefined && trait.confidence < 0.5 && (
  <View style={styles.confidenceBadge}>
    <Text style={styles.confidenceBadgeText}>⚠ Limited view</Text>
  </View>
)}
{trait.confidence !== undefined && trait.confidence >= 0.5 && (
  <View style={styles.confidenceBar}>
    <View style={[styles.confidenceFill, { width: `${trait.confidence * 100}%` }]} />
  </View>
)}
```

Add to StyleSheet:
```typescript
confidenceBadge:     { backgroundColor: 'rgba(255,165,0,0.2)', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4, marginTop: 4, alignSelf: 'flex-start' },
confidenceBadgeText: { fontSize: 11, color: '#FFA500', fontWeight: '600' },
confidenceBar:       { height: 3, backgroundColor: Theme.colors.border, borderRadius: 2, marginTop: 6, overflow: 'hidden' },
confidenceFill:      { height: '100%', backgroundColor: Theme.colors.gold, borderRadius: 2 },
```

- [ ] **Step 6: Add strengths/liabilities and judge language to scorecard**

After the trait scorecard section, when `analysisEnrichment` is set, render:

```typescript
{analysisEnrichment && (
  <>
    {analysisEnrichment.judgeLanguage ? (
      <View style={styles.judgeCard}>
        <Text style={styles.judgeCardLabel}>JUDGE PERSPECTIVE</Text>
        <Text style={styles.judgeCardText}>"{analysisEnrichment.judgeLanguage}"</Text>
      </View>
    ) : null}
    {analysisEnrichment.strengths.length > 0 && (
      <View style={styles.strengthsCard}>
        <Text style={styles.cardLabel}>TOP STRENGTHS</Text>
        {analysisEnrichment.strengths.map((s, i) => (
          <Text key={i} style={styles.strengthItem}>✓ {s}</Text>
        ))}
      </View>
    )}
    {analysisEnrichment.placingLiabilities.length > 0 && (
      <View style={styles.liabilitiesCard}>
        <Text style={styles.cardLabel}>PLACING LIABILITIES</Text>
        {analysisEnrichment.placingLiabilities.map((l, i) => (
          <Text key={i} style={styles.liabilityItem}>△ {l}</Text>
        ))}
      </View>
    )}
  </>
)}
```

Add to StyleSheet:
```typescript
judgeCard:       { backgroundColor: GlassEffect.background, borderRadius: 12, padding: 14, marginBottom: 12, borderLeftWidth: 3, borderLeftColor: Theme.colors.gold },
judgeCardLabel:  { fontSize: 10, fontWeight: '700', color: Theme.colors.gold, letterSpacing: 1, marginBottom: 6 },
judgeCardText:   { fontSize: 14, color: Theme.colors.text, fontStyle: 'italic', lineHeight: 20 },
strengthsCard:   { backgroundColor: 'rgba(0,200,100,0.1)', borderRadius: 12, padding: 14, marginBottom: 12 },
liabilitiesCard: { backgroundColor: 'rgba(255,100,80,0.1)', borderRadius: 12, padding: 14, marginBottom: 12 },
cardLabel:       { fontSize: 10, fontWeight: '700', letterSpacing: 1, marginBottom: 8, color: Theme.colors.textSecondary },
strengthItem:    { fontSize: 13, color: '#00C864', marginBottom: 4, lineHeight: 18 },
liabilityItem:   { fontSize: 13, color: '#FF6450', marginBottom: 4, lineHeight: 18 },
```

- [ ] **Step 7: Add "Flag as inaccurate" button**

Add to the results section, after scores are displayed, before the "Next animal" button:

```typescript
{currentDrillId && !flagged && (
  <AnimatedButton
    style={styles.flagBtn}
    onPress={async () => {
      if (flagging) return;
      setFlagging(true);
      await supabase
        .from('livestock_drills')
        .update({ correction_status: 'flagged' })
        .eq('id', currentDrillId);
      setFlagging(false);
      setFlagged(true);
    }}
    disabled={flagging}
  >
    <Text style={styles.flagBtnText}>{flagging ? 'Flagging…' : '⚑ Flag as inaccurate'}</Text>
  </AnimatedButton>
)}
{flagged && <Text style={styles.flaggedConfirm}>Flagged for review</Text>}
```

This requires `currentDrillId` state — the `id` from `livestock_drills` returned when the analysis is cached. Check where `batch_key` upsert returns the row ID and store it in `currentDrillId` state.

Add to StyleSheet:
```typescript
flagBtn:         { borderWidth: 1, borderColor: 'rgba(255,165,0,0.5)', borderRadius: 8, padding: 10, alignItems: 'center', marginTop: 8 },
flagBtnText:     { fontSize: 13, color: Theme.colors.gold, fontWeight: '500' },
flaggedConfirm:  { fontSize: 12, color: Theme.colors.textSecondary, textAlign: 'center', marginTop: 8 },
```

- [ ] **Step 8: Type-check**

```bash
npx tsc --noEmit -p .
```

Expected: 0 errors

- [ ] **Step 9: Test in browser**

```bash
npm run web
```

Navigate to the livestock judging drill. Verify:
- Existing drill flow still works end-to-end
- No TypeScript errors in console

- [ ] **Step 10: Commit**

```bash
git add app/practice/livestock-judging/drills.tsx
git commit -m "feat(drills): confidence badges, quality rejection UI, strengths/liabilities, flag button"
```

---

## Task 9: Upload UI Updates

**Files:**
- Modify: `app/(admin)/livestock-upload.tsx`

Add quality warning display and flag button to the upload result view.

- [ ] **Step 1: Check current upload result rendering**

```bash
grep -n "analyzeImage\|result\|traits\|onPress" "/Volumes/Samsung PSSD T7/ag-coach-app/app/(admin)/livestock-upload.tsx" | head -40
```

- [ ] **Step 2: Handle `QUALITY_REJECT:` error in upload flow**

Find the `try/catch` around `LivestockAnalyzer.analyzeImage()` in the upload screen. Add handling for quality rejection:

```typescript
} catch (err: any) {
  const msg = err.message || '';
  if (msg.startsWith('QUALITY_REJECT:')) {
    Alert.alert(
      'Photo Quality Issue',
      msg.replace('QUALITY_REJECT:', '').trim() + '\n\nPlease retake the photo with a single animal, good lighting, and the animal clearly visible.',
      [{ text: 'OK' }]
    );
    setAnalyzing(false);
    return;
  }
  // existing error handling...
}
```

- [ ] **Step 3: Add flag button to upload result view**

After the analysis result is shown (trait scores visible), add:

```typescript
{savedDrillId && !flagged && (
  <AnimatedButton
    style={styles.flagBtn}
    onPress={async () => {
      setFlagging(true);
      await supabase
        .from('livestock_drills')
        .update({ correction_status: 'flagged' })
        .eq('id', savedDrillId);
      setFlagging(false);
      setFlagged(true);
    }}
  >
    <Text style={styles.flagBtnText}>{flagging ? 'Flagging…' : '⚑ Flag AI evaluation as inaccurate'}</Text>
  </AnimatedButton>
)}
{flagged && <Text style={styles.flaggedText}>Flagged for super-admin review</Text>}
```

Add state:
```typescript
const [flagging, setFlagging] = useState(false);
const [flagged, setFlagged] = useState(false);
```

- [ ] **Step 4: Type-check and commit**

```bash
npx tsc --noEmit -p .
git add app/\(admin\)/livestock-upload.tsx
git commit -m "feat(upload): quality rejection alert and flag button on analysis result"
```

---

## Task 10: Super-Admin Correction Screen

**Files:**
- Create: `app/(super-admin)/livestock-corrections.tsx`

- [ ] **Step 1: Create `app/(super-admin)/livestock-corrections.tsx`**

```tsx
import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, ScrollView, StyleSheet, Alert, Image } from 'react-native';
import Slider from '@react-native-community/slider';
import { supabase } from '@/lib/supabase';
import { Theme, GlassEffect } from '@/constants/theme';
import AnimatedButton from '@/components/common/AnimatedButton';

const TRAITS = ['muscle', 'structure', 'volume', 'balance', 'condition'] as const;
const TRAIT_LABELS: Record<string, string> = {
  muscle: 'Muscle', structure: 'Structure', volume: 'Volume',
  balance: 'Balance', condition: 'Condition',
};
type CorrectionType = 'score' | 'observation' | 'terminology' | 'hallucination';

type FlaggedRow = {
  id: string;
  species: string;
  class_type: string;
  image_url_side: string | null;
  image_url_rear: string | null;
  traits: Record<string, any>;
  correction_status: string;
  created_at: string;
};

export default function LivestockCorrectionsScreen() {
  const [flagged, setFlagged] = useState<FlaggedRow[]>([]);
  const [selected, setSelected] = useState<FlaggedRow | null>(null);
  const [correctedScores, setCorrectedScores] = useState<Record<string, number>>({});
  const [correctionType, setCorrectionType] = useState<CorrectionType>('score');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadFlagged = useCallback(async () => {
    setLoading(true);
    const { data } = await supabase
      .from('livestock_drills')
      .select('id, species, class_type, image_url_side, image_url_rear, traits, correction_status, created_at')
      .eq('correction_status', 'flagged')
      .order('created_at', { ascending: false })
      .limit(50);
    setFlagged(data || []);
    setLoading(false);
  }, []);

  useEffect(() => { loadFlagged(); }, [loadFlagged]);

  const selectRow = (row: FlaggedRow) => {
    setSelected(row);
    const initial: Record<string, number> = {};
    for (const trait of TRAITS) {
      initial[trait] = row.traits?.[trait]?.score ?? 5;
    }
    setCorrectedScores(initial);
    setNotes('');
  };

  const saveCorrection = async () => {
    if (!selected) return;
    setSaving(true);

    const correctedTraits = { ...selected.traits };
    for (const trait of TRAITS) {
      if (correctedTraits[trait]) {
        correctedTraits[trait] = { ...correctedTraits[trait], score: correctedScores[trait] };
      }
    }

    const { error: corrErr } = await supabase
      .from('livestock_eval_corrections')
      .insert({
        drill_id: selected.id,
        corrected_by: (await supabase.auth.getUser()).data.user?.id,
        original_traits: selected.traits,
        corrected_traits: correctedTraits,
        correction_type: correctionType,
        notes: notes || null,
      });

    if (corrErr) { Alert.alert('Error', corrErr.message); setSaving(false); return; }

    await supabase
      .from('livestock_drills')
      .update({ correction_status: 'corrected' })
      .eq('id', selected.id);

    setSaving(false);
    setSelected(null);
    await loadFlagged();
    Alert.alert('Saved', 'Correction recorded.');
  };

  const markAccurate = async (id: string) => {
    await supabase.from('livestock_drills').update({ correction_status: 'accurate' }).eq('id', id);
    await loadFlagged();
  };

  const CORRECTION_TYPES: { key: CorrectionType; label: string }[] = [
    { key: 'score', label: 'Wrong score' },
    { key: 'observation', label: 'Wrong observation' },
    { key: 'terminology', label: 'Wrong terminology' },
    { key: 'hallucination', label: 'Hallucinated trait' },
  ];

  if (loading) return (
    <View style={styles.center}><Text style={styles.loadingText}>Loading flagged evaluations…</Text></View>
  );

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Flagged Evaluations</Text>
      <Text style={styles.subtitle}>{flagged.length} pending correction{flagged.length !== 1 ? 's' : ''}</Text>

      {!selected ? (
        flagged.map(row => (
          <View key={row.id} style={styles.rowCard}>
            {row.image_url_side && (
              <Image source={{ uri: row.image_url_side }} style={styles.rowThumb} />
            )}
            <View style={styles.rowInfo}>
              <Text style={styles.rowSpecies}>{row.species} — {row.class_type}</Text>
              <Text style={styles.rowDate}>{new Date(row.created_at).toLocaleDateString()}</Text>
              <Text style={styles.rowScores}>
                {TRAITS.map(t => `${TRAIT_LABELS[t]}: ${row.traits?.[t]?.score ?? '?'}`).join(' · ')}
              </Text>
            </View>
            <View style={styles.rowActions}>
              <AnimatedButton style={styles.correctBtn} onPress={() => selectRow(row)}>
                <Text style={styles.correctBtnText}>Correct</Text>
              </AnimatedButton>
              <AnimatedButton style={styles.accurateBtn} onPress={() => markAccurate(row.id)}>
                <Text style={styles.accurateBtnText}>Accurate</Text>
              </AnimatedButton>
            </View>
          </View>
        ))
      ) : (
        <View>
          <AnimatedButton style={styles.backBtn} onPress={() => setSelected(null)}>
            <Text style={styles.backBtnText}>← Back</Text>
          </AnimatedButton>

          <Text style={styles.sectionTitle}>{selected.species} — {selected.class_type}</Text>

          {selected.image_url_side && (
            <Image source={{ uri: selected.image_url_side }} style={styles.previewImage} resizeMode="contain" />
          )}
          {selected.image_url_rear && (
            <Image source={{ uri: selected.image_url_rear }} style={styles.previewImage} resizeMode="contain" />
          )}

          <Text style={styles.sectionTitle}>Correct Trait Scores</Text>
          {TRAITS.map(trait => (
            <View key={trait} style={styles.sliderRow}>
              <View style={styles.sliderHeader}>
                <Text style={styles.traitLabel}>{TRAIT_LABELS[trait]}</Text>
                <Text style={styles.traitBoth}>
                  AI: {selected.traits?.[trait]?.score ?? '?'} → Corrected: <Text style={styles.corrected}>{correctedScores[trait]}</Text>
                </Text>
              </View>
              <Slider
                minimumValue={1}
                maximumValue={10}
                step={1}
                value={correctedScores[trait]}
                onValueChange={v => setCorrectedScores(prev => ({ ...prev, [trait]: v }))}
                minimumTrackTintColor={Theme.colors.gold}
                maximumTrackTintColor={Theme.colors.border}
                thumbTintColor={Theme.colors.gold}
              />
            </View>
          ))}

          <Text style={styles.sectionTitle}>Correction Type</Text>
          <View style={styles.typeRow}>
            {CORRECTION_TYPES.map(ct => (
              <AnimatedButton
                key={ct.key}
                style={[styles.typeBtn, correctionType === ct.key && styles.typeBtnActive]}
                onPress={() => setCorrectionType(ct.key)}
              >
                <Text style={[styles.typeBtnText, correctionType === ct.key && styles.typeBtnTextActive]}>
                  {ct.label}
                </Text>
              </AnimatedButton>
            ))}
          </View>

          <AnimatedButton style={styles.saveBtn} onPress={saveCorrection} disabled={saving}>
            <Text style={styles.saveBtnText}>{saving ? 'Saving…' : 'Save Correction'}</Text>
          </AnimatedButton>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container:        { flex: 1, backgroundColor: Theme.colors.background },
  content:          { padding: 20, paddingBottom: 60 },
  center:           { flex: 1, alignItems: 'center', justifyContent: 'center' },
  loadingText:      { color: Theme.colors.textSecondary },
  title:            { fontSize: 24, fontWeight: '700', color: Theme.colors.text, marginBottom: 4 },
  subtitle:         { fontSize: 14, color: Theme.colors.textSecondary, marginBottom: 20 },
  rowCard:          { flexDirection: 'row', backgroundColor: Theme.colors.surface, borderRadius: 10, padding: 10, marginBottom: 10, gap: 10 },
  rowThumb:         { width: 70, height: 70, borderRadius: 6 },
  rowInfo:          { flex: 1, justifyContent: 'center' },
  rowSpecies:       { fontSize: 14, fontWeight: '600', color: Theme.colors.text },
  rowDate:          { fontSize: 11, color: Theme.colors.textSecondary, marginBottom: 2 },
  rowScores:        { fontSize: 11, color: Theme.colors.textSecondary },
  rowActions:       { justifyContent: 'center', gap: 6 },
  correctBtn:       { backgroundColor: Theme.colors.gold, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 6 },
  correctBtnText:   { fontSize: 12, fontWeight: '700', color: '#000' },
  accurateBtn:      { backgroundColor: 'rgba(0,200,100,0.2)', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 6 },
  accurateBtnText:  { fontSize: 12, fontWeight: '600', color: '#00C864' },
  backBtn:          { marginBottom: 16 },
  backBtnText:      { color: Theme.colors.gold, fontSize: 14 },
  sectionTitle:     { fontSize: 16, fontWeight: '600', color: Theme.colors.text, marginBottom: 10 },
  previewImage:     { width: '100%', height: 180, borderRadius: 10, marginBottom: 10, backgroundColor: Theme.colors.surface },
  sliderRow:        { marginBottom: 16 },
  sliderHeader:     { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 },
  traitLabel:       { fontSize: 14, fontWeight: '600', color: Theme.colors.text },
  traitBoth:        { fontSize: 12, color: Theme.colors.textSecondary },
  corrected:        { fontWeight: '700', color: Theme.colors.gold },
  typeRow:          { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 20 },
  typeBtn:          { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8, borderWidth: 1, borderColor: Theme.colors.border, backgroundColor: Theme.colors.surface },
  typeBtnActive:    { backgroundColor: Theme.colors.gold, borderColor: Theme.colors.gold },
  typeBtnText:      { fontSize: 12, color: Theme.colors.textSecondary },
  typeBtnTextActive:{ color: '#000', fontWeight: '700' },
  saveBtn:          { backgroundColor: Theme.colors.gold, paddingVertical: 14, borderRadius: 10, alignItems: 'center' },
  saveBtnText:      { fontSize: 15, fontWeight: '700', color: '#000' },
});
```

- [ ] **Step 2: Type-check**

```bash
npx tsc --noEmit -p .
```

- [ ] **Step 3: Commit**

```bash
git add app/\(super-admin\)/livestock-corrections.tsx
git commit -m "feat(super-admin): flagged evaluation correction screen with trait score sliders"
```

---

## Task 11: Accuracy Dashboard

**Files:**
- Create: `app/(super-admin)/livestock-eval-accuracy.tsx`

- [ ] **Step 1: Create Supabase view for accuracy metrics**

Add to a new migration `supabase/migrations/20260510120001_livestock_accuracy_view.sql`:

```sql
CREATE OR REPLACE VIEW livestock_eval_accuracy_summary AS
SELECT
  d.species,
  unnest(ARRAY['muscle','structure','volume','balance','condition']) AS trait,
  count(*) FILTER (WHERE d.correction_status = 'corrected') AS correction_count,
  count(*) FILTER (WHERE d.correction_status = 'accurate')  AS accurate_count,
  count(*) FILTER (WHERE d.correction_status = 'flagged')   AS flagged_count,
  avg(
    abs(
      (d.traits->unnest(ARRAY['muscle','structure','volume','balance','condition']))->>'score')::numeric
      - (c.corrected_traits->unnest(ARRAY['muscle','structure','volume','balance','condition'])->>'score')::numeric
    )
  ) AS avg_score_delta
FROM livestock_drills d
LEFT JOIN livestock_eval_corrections c ON c.drill_id = d.id
GROUP BY d.species, trait;
```

Note: If the lateral unnest approach is too complex for PostgREST, use a simpler approach in the screen (fetch raw corrections and compute client-side). See Step 3.

Apply:
```bash
npx supabase db push --db-url "$SUPABASE_DB_URL"
```

- [ ] **Step 2: Create `app/(super-admin)/livestock-eval-accuracy.tsx`**

```tsx
import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { supabase } from '@/lib/supabase';
import { Theme } from '@/constants/theme';

const SPECIES = ['Cattle', 'Swine', 'Sheep', 'Goat'] as const;
const TRAITS = ['muscle', 'structure', 'volume', 'balance', 'condition'] as const;
const TRAIT_LABELS: Record<string, string> = {
  muscle: 'Muscle', structure: 'Structure', volume: 'Volume',
  balance: 'Balance', condition: 'Condition',
};

type AccuracyRow = {
  species: string;
  trait: string;
  aiScore: number;
  correctedScore: number;
  delta: number;
};

export default function LivestockEvalAccuracyScreen() {
  const [rows, setRows] = useState<AccuracyRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState({ totalFlagged: 0, totalCorrected: 0, totalAccurate: 0 });

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);

    // Fetch all corrections with original + corrected traits
    const { data: corrections } = await supabase
      .from('livestock_eval_corrections')
      .select('original_traits, corrected_traits, drill_id')
      .limit(500);

    // Fetch status counts
    const { data: drills } = await supabase
      .from('livestock_drills')
      .select('correction_status, species')
      .in('correction_status', ['flagged', 'corrected', 'accurate']);

    if (!corrections || !drills) { setLoading(false); return; }

    const totalFlagged   = drills.filter(d => d.correction_status === 'flagged').length;
    const totalCorrected = drills.filter(d => d.correction_status === 'corrected').length;
    const totalAccurate  = drills.filter(d => d.correction_status === 'accurate').length;
    setSummary({ totalFlagged, totalCorrected, totalAccurate });

    // Compute per-trait delta from corrections (across all species — species breakdown is Phase 2)
    const traitDeltas: Record<string, number[]> = {};
    for (const trait of TRAITS) { traitDeltas[trait] = []; }

    for (const corr of corrections) {
      for (const trait of TRAITS) {
        const ai = corr.original_traits?.[trait]?.score;
        const corrected = corr.corrected_traits?.[trait]?.score;
        if (typeof ai === 'number' && typeof corrected === 'number') {
          traitDeltas[trait].push(Math.abs(ai - corrected));
        }
      }
    }

    const computed: AccuracyRow[] = TRAITS.flatMap(trait => {
      const deltas = traitDeltas[trait];
      if (!deltas.length) return [];
      const avgDelta = deltas.reduce((a, b) => a + b, 0) / deltas.length;
      return [{ species: 'All', trait, aiScore: 0, correctedScore: 0, delta: avgDelta }];
    });

    setRows(computed);
    setLoading(false);
  }

  const deltaColor = (delta: number) => {
    if (delta < 1) return '#00C864';
    if (delta < 2) return Theme.colors.gold;
    return '#FF6450';
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>AI Accuracy Dashboard</Text>
      <Text style={styles.subtitle}>Target: &lt;1.5 point average delta per trait</Text>

      <View style={styles.summaryRow}>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryNum}>{summary.totalFlagged}</Text>
          <Text style={styles.summaryLabel}>Flagged</Text>
        </View>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryNum}>{summary.totalCorrected}</Text>
          <Text style={styles.summaryLabel}>Corrected</Text>
        </View>
        <View style={styles.summaryCard}>
          <Text style={[styles.summaryNum, { color: '#00C864' }]}>{summary.totalAccurate}</Text>
          <Text style={styles.summaryLabel}>Accurate</Text>
        </View>
      </View>

      {loading ? (
        <Text style={styles.loadingText}>Computing accuracy metrics…</Text>
      ) : rows.length === 0 ? (
        <Text style={styles.emptyText}>No corrections yet. Flag evaluations in the drill to build accuracy data.</Text>
      ) : (
        <>
          <Text style={styles.sectionTitle}>Average Score Delta by Trait</Text>
          <Text style={styles.sectionHint}>Lower is better. &lt;1.5 = target. &gt;2.0 = needs prompt work.</Text>
          {rows.map(row => (
            <View key={`${row.species}-${row.trait}`} style={styles.deltaRow}>
              <Text style={styles.deltaTrait}>{TRAIT_LABELS[row.trait]}</Text>
              <View style={styles.deltaBar}>
                <View style={[styles.deltaFill, {
                  width: `${Math.min(100, (row.delta / 5) * 100)}%`,
                  backgroundColor: deltaColor(row.delta),
                }]} />
              </View>
              <Text style={[styles.deltaVal, { color: deltaColor(row.delta) }]}>
                {row.delta.toFixed(1)} pts
              </Text>
            </View>
          ))}
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container:    { flex: 1, backgroundColor: Theme.colors.background },
  content:      { padding: 20, paddingBottom: 60 },
  title:        { fontSize: 24, fontWeight: '700', color: Theme.colors.text, marginBottom: 4 },
  subtitle:     { fontSize: 14, color: Theme.colors.textSecondary, marginBottom: 20 },
  summaryRow:   { flexDirection: 'row', gap: 10, marginBottom: 24 },
  summaryCard:  { flex: 1, backgroundColor: Theme.colors.surface, borderRadius: 10, padding: 14, alignItems: 'center' },
  summaryNum:   { fontSize: 28, fontWeight: '700', color: Theme.colors.text },
  summaryLabel: { fontSize: 11, color: Theme.colors.textSecondary, marginTop: 2 },
  loadingText:  { color: Theme.colors.textSecondary, textAlign: 'center', marginTop: 40 },
  emptyText:    { color: Theme.colors.textSecondary, textAlign: 'center', marginTop: 40, lineHeight: 22 },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: Theme.colors.text, marginBottom: 4 },
  sectionHint:  { fontSize: 12, color: Theme.colors.textSecondary, marginBottom: 16 },
  deltaRow:     { flexDirection: 'row', alignItems: 'center', marginBottom: 12, gap: 10 },
  deltaTrait:   { width: 72, fontSize: 13, color: Theme.colors.text, fontWeight: '500' },
  deltaBar:     { flex: 1, height: 8, backgroundColor: Theme.colors.border, borderRadius: 4, overflow: 'hidden' },
  deltaFill:    { height: '100%', borderRadius: 4 },
  deltaVal:     { width: 50, fontSize: 13, fontWeight: '700', textAlign: 'right' },
});
```

- [ ] **Step 3: Type-check**

```bash
npx tsc --noEmit -p .
```

- [ ] **Step 4: Commit**

```bash
git add app/\(super-admin\)/livestock-eval-accuracy.tsx supabase/migrations/20260510120001_livestock_accuracy_view.sql
git commit -m "feat(super-admin): livestock AI accuracy dashboard with trait delta tracking"
```

---

## Final Verification Checklist

- [ ] Bryan opens `livestock-anchors.tsx`, scores 3–5 images per species → confirm `is_anchor=true` and `anchor_scores` JSONB visible in Supabase dashboard
- [ ] Re-run AI on one anchor image → log the raw scores → compare to Bryan's baseline (target: within 1.5 pts per trait)
- [ ] Submit multi-animal photo to drill → confirm `QUALITY_REJECT:` surfaces as "Multiple animals detected" in UI (not a crash)
- [ ] Submit blurry photo → confirm quality rejection UI shown
- [ ] Submit side-only cattle photo → confirm at least one trait shows confidence < 0.7 and "⚠ Limited view" badge
- [ ] Complete drill → confirm "Judge Perspective" card and Strengths/Liabilities cards render
- [ ] Tap "Flag as inaccurate" → confirm `correction_status='flagged'` in `livestock_drills` table
- [ ] Open corrections screen → flagged row visible → adjust scores → save → row shows `correction_status='corrected'` in DB, row in `livestock_eval_corrections`
- [ ] Open accuracy dashboard → summary counts match DB → delta bars render
- [ ] `npx tsc --noEmit -p .` → 0 errors
- [ ] `npm test` → all tests pass
