# Egg Evaluation: Build Image-Based Air Cell Training
## Start This Week — 3 Phases, 2 Weeks to First MVP

---

## What You're Building

**Current:** Text-based egg grading (read "air cell ≤ 1/8"" → pick AA)  
**New:** Image-based air cell measurement (see candled egg → estimate air cell size → get feedback)

**Outcome:** Students develop **visual muscle memory** for 1/8" vs 3/16" air cells

---

## Phase 1: Image Sourcing (Days 1–2)

### Option A: Use USDA Official Images (Fastest)

1. Go to [USDA Egg Grading Standards](https://www.ams.usda.gov/content/official-federal-egg-grading-standards)
2. Download the **Candling Photo Guide** PDF
3. Extract high-res images of candled eggs (AA, A, B grades)
4. Store in: `assets/images/eggs/candled/`

```
assets/images/eggs/candled/
├── aa_01.jpg          (AA grade - 1/8" air cell)
├── aa_02.jpg
├── a_01.jpg           (A grade - 3/16" air cell)
├── a_02.jpg
├── b_01.jpg           (B grade - >3/16" air cell)
├── b_02.jpg
├── loss_blood_spot.jpg (Loss grade - defect)
└── exterior_dirty.jpg
```

### Option B: Create Your Own (Best for Reality)

**Equipment needed:**
- Candling light (6-inch diameter commercial or homemade)
- Fresh eggs (variety of grades)
- Dark room
- Calipers (measure air cell depth)
- Camera with macro lens

**Process:**
```
1. Candle egg under bright light
2. Photograph from side (shows air pocket clearly)
3. Measure air cell with calipers (1/8", 3/16", etc.)
4. Label image: "aa_measured_0.125.jpg"
5. Repeat for 20 AA, 20 A, 20 B eggs
```

**Result:** 60 eggs × 3 angles = 180 reference images

**Pro tip:** Contact your local FFA chapter. Ask if students can photograph eggs they're already candling. Real, relatable images.

---

## Phase 2: Create Image Metadata File (Day 3)

Create `lib/data/egg-evaluation-images.ts`:

```typescript
/**
 * egg-evaluation-images.ts
 *
 * Image-based egg grading scenarios.
 * Each image has actual measured air cell size + derived grade.
 */

export interface AirCellMeasurement {
  depthInches: number;        // Actual measured depth (e.g., 0.125)
  grade: 'AA' | 'A' | 'B';    // Derived from USDA standards
}

export interface EggEvaluationImage {
  id: string;
  imageUrl: string;           // Path: /images/eggs/candled/[filename]
  interior: {
    airCell: AirCellMeasurement;
    whiteCuracy: 'firm' | 'reasonably_firm' | 'thin_watery';
    yolkDefinition: 'barely_visible' | 'fairly_visible' | 'plainly_visible';
    defects: Array<{
      type: 'blood_spot' | 'blood_ring' | 'meat_spot';
      size: 'minor' | 'major';  // > 1/8" = major = Loss
    }>;
    grade: 'AA' | 'A' | 'B' | 'Loss';
    explanation: string;
  };
  exterior: {
    shellCondition: 'clean' | 'slightly_stained' | 'prominently_stained';
    shape: 'normal' | 'slightly_abnormal';
    grade: 'AA' | 'A' | 'B' | 'Dirty';
  };
}

// Starter dataset (from USDA images or your photos)
export const EGG_IMAGES: EggEvaluationImage[] = [
  {
    id: 'egg-aa-001',
    imageUrl: '/images/eggs/candled/aa_01.jpg',
    interior: {
      airCell: { depthInches: 0.125, grade: 'AA' },
      whiteCuracy: 'firm',
      yolkDefinition: 'barely_visible',
      defects: [],
      grade: 'AA',
      explanation: 'Perfect AA. Air cell is minimal—exactly 1/8 inch or less. Firm white, barely visible yolk outline.',
    },
    exterior: {
      shellCondition: 'clean',
      shape: 'normal',
      grade: 'AA',
    },
  },
  {
    id: 'egg-a-001',
    imageUrl: '/images/eggs/candled/a_01.jpg',
    interior: {
      airCell: { depthInches: 0.1875, grade: 'A' },
      whiteCuracy: 'reasonably_firm',
      yolkDefinition: 'fairly_visible',
      defects: [],
      grade: 'A',
      explanation: 'Grade A interior. Air cell is 3/16 inch—noticeably larger than AA but still acceptable for premium grade.',
    },
    exterior: {
      shellCondition: 'clean',
      shape: 'normal',
      grade: 'A',
    },
  },
  {
    id: 'egg-b-001',
    imageUrl: '/images/eggs/candled/b_01.jpg',
    interior: {
      airCell: { depthInches: 0.25, grade: 'B' },
      whiteCuracy: 'thin_watery',
      yolkDefinition: 'plainly_visible',
      defects: [],
      grade: 'B',
      explanation: 'Grade B interior. Air cell exceeds 3/16 inch. White is thin/watery. Yolk outline is plainly visible.',
    },
    exterior: {
      shellCondition: 'clean',
      shape: 'normal',
      grade: 'B',
    },
  },
  {
    id: 'egg-loss-blood-001',
    imageUrl: '/images/eggs/candled/loss_blood_spot.jpg',
    interior: {
      airCell: { depthInches: 0.125, grade: 'AA' },
      whiteCuracy: 'firm',
      yolkDefinition: 'barely_visible',
      defects: [
        { type: 'blood_spot', size: 'major' },
      ],
      grade: 'Loss',
      explanation: 'LOSS grade. Although interior would be AA, the blood spot (>1/8") disqualifies it. Any visible blood/meat spot = Loss.',
    },
    exterior: {
      shellCondition: 'clean',
      shape: 'normal',
      grade: 'AA',
    },
  },
];
```

**Key insight:** Each image has **actual measured air cell depth in inches** + the **derived grade**. This grounds the practice in reality.

---

## Phase 3: Build UI Components (Days 4–7)

### Step 1: Create Air Cell Measurement Component

`components/egg-eval/AirCellMeasurementOverlay.tsx`:

```typescript
import React, { useState } from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import { AnimatedButton as TouchableOpacity } from '@/components/common/AnimatedButton';
import Slider from '@react-native-community/slider';

interface Props {
  imageUrl: string;
  actualAirCellInches: number;  // Ground truth: 0.125, 0.1875, 0.25
  airCellGrade: 'AA' | 'A' | 'B';
  onEstimate: (estimatedInches: number) => void;
}

export default function AirCellMeasurementOverlay({
  imageUrl,
  actualAirCellInches,
  airCellGrade,
  onEstimate,
}: Props) {
  const [estimate, setEstimate] = useState(0.15);
  const [submitted, setSubmitted] = useState(false);

  const GRADE_THRESHOLDS = {
    AA: 0.125,      // ≤ 1/8"
    A: 0.1875,      // ≤ 3/16"
    B: Infinity,    // > 3/16"
  };

  const estimatedGrade = estimate <= 0.125 ? 'AA' : estimate <= 0.1875 ? 'A' : 'B';
  const isCorrect = estimatedGrade === airCellGrade;

  const handleSubmit = () => {
    setSubmitted(true);
    onEstimate(estimate);
  };

  return (
    <View style={styles.container}>
      {/* Candled egg image */}
      <Image source={{ uri: imageUrl }} style={styles.eggImage} />

      {/* Measurement controls */}
      <View style={styles.controlsCard}>
        <Text style={styles.label}>ESTIMATE AIR CELL DEPTH</Text>

        {/* Visual reference */}
        <View style={styles.referenceScale}>
          <Text style={styles.refLabel}>1/8"</Text>
          <Text style={styles.refLabel}>3/16"</Text>
          <Text style={styles.refLabel}>3/8"</Text>
        </View>

        {/* Slider */}
        <Slider
          style={styles.slider}
          minimumValue={0.06}
          maximumValue={0.4}
          step={0.01}
          value={estimate}
          onValueChange={setEstimate}
          disabled={submitted}
        />

        {/* Live estimate display */}
        <View style={styles.estimateDisplay}>
          <Text style={styles.estimateValue}>
            {estimate.toFixed(3)}" ({(estimate * 8).toFixed(2)} eighths)
          </Text>
          <Text style={[styles.estimateGrade, { color: getGradeColor(estimatedGrade) }]}>
            GRADE: {estimatedGrade}
          </Text>
        </View>

        {/* Feedback (only after submission) */}
        {submitted && (
          <View style={[
            styles.feedbackBox,
            { backgroundColor: isCorrect ? '#00c85315' : '#ff525215' }
          ]}>
            <Text style={{ color: isCorrect ? '#00c853' : '#ff5252', fontWeight: '900' }}>
              {isCorrect ? '✓ Correct!' : '✗ Incorrect'}
            </Text>
            <Text style={{ color: '#bbb', fontSize: 12, marginTop: 8 }}>
              Air cell measured: {actualAirCellInches.toFixed(3)}" ({airCellGrade} grade)
            </Text>
            <Text style={{ color: '#aaa', fontSize: 11, marginTop: 4 }}>
              You estimated: {estimate.toFixed(3)}"
              {Math.abs(estimate - actualAirCellInches) <= 0.015 ? ' (excellent calibration!)' : ' (keep practicing)'}
            </Text>
          </View>
        )}

        {/* Submit button */}
        {!submitted && (
          <TouchableOpacity style={styles.submitBtn} onPress={handleSubmit}>
            <Text style={styles.submitBtnText}>SUBMIT ESTIMATE</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

function getGradeColor(grade: string) {
  return { AA: '#00c853', A: '#00f2ff', B: '#F2A900' }[grade] || '#fff';
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  eggImage: { width: '100%', height: 300, resizeMode: 'contain' },
  controlsCard: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 20,
    padding: 20,
    margin: 20,
  },
  label: { color: '#555', fontSize: 10, fontWeight: '900', letterSpacing: 2, marginBottom: 12 },
  referenceScale: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
    paddingHorizontal: 10,
  },
  refLabel: { color: '#666', fontSize: 10, fontWeight: '700' },
  slider: { width: '100%', height: 40 },
  estimateDisplay: { marginVertical: 16 },
  estimateValue: { color: '#fff', fontSize: 18, fontWeight: '900' },
  estimateGrade: { fontSize: 14, fontWeight: '900', marginTop: 4 },
  feedbackBox: {
    borderRadius: 12,
    padding: 16,
    marginVertical: 16,
    borderWidth: 1,
    borderColor: 'rgba(0,200,83,0.3)',
  },
  submitBtn: {
    backgroundColor: '#F2A900',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 16,
  },
  submitBtnText: { color: '#000', fontWeight: '900', fontSize: 14 },
});
```

### Step 2: Update eggs.tsx to Use Images

Replace text-based observations with image-based measurement:

```typescript
// app/practice/poultry-eval/eggs.tsx
import { EGG_IMAGES } from '@/lib/data/egg-evaluation-images';
import AirCellMeasurementOverlay from '@/components/egg-eval/AirCellMeasurementOverlay';

export default function EggEvaluationScreen() {
  const [imageIdx, setImageIdx] = useState(0);
  const [scores, setScores] = useState<boolean[]>([]);

  const eggImage = EGG_IMAGES[imageIdx];

  const handleEstimate = (estimatedInches: number) => {
    const estimatedGrade = estimatedInches <= 0.125 ? 'AA' : 
                           estimatedInches <= 0.1875 ? 'A' : 'B';
    const isCorrect = estimatedGrade === eggImage.interior.grade;
    setScores([...scores, isCorrect]);
  };

  if (scores.length >= 20) {
    // Show results screen
    const correct = scores.filter(Boolean).length;
    return <EggEvaluationResults score={correct} total={scores.length} />;
  }

  return (
    <View style={{ flex: 1 }}>
      <AirCellMeasurementOverlay
        imageUrl={eggImage.imageUrl}
        actualAirCellInches={eggImage.interior.airCell.depthInches}
        airCellGrade={eggImage.interior.airCell.grade}
        onEstimate={handleEstimate}
      />
    </View>
  );
}
```

---

## Phase 4: Add Teaching Slide Deck (Days 8–10)

Create `app/practice/poultry-eval/egg-teach.tsx`:

```typescript
// Teaching slides before practice
// Shows: AA image → A image → B image with overlays explaining differences

const TEACHING_SLIDES = [
  {
    title: 'AIR CELL DEFINITION',
    image: '/images/eggs/candled/aa_01.jpg',
    description: 'The air pocket at the large end of the egg.',
    annotations: [
      '↑ Air cell (dark space)',
      'Appears under candling light',
    ],
  },
  {
    title: 'AA GRADE AIR CELL',
    image: '/images/eggs/candled/aa_02.jpg',
    description: '≤ 1/8 inch deep. Barely visible. Tight against shell.',
    details: ['Measurement: 0.125"', 'Premium egg', 'Minimal depth'],
  },
  {
    title: 'A GRADE AIR CELL',
    image: '/images/eggs/candled/a_01.jpg',
    description: '≤ 3/16 inch deep. Noticeably larger than AA.',
    details: ['Measurement: 0.1875"', 'Standard commercial', 'See the difference?'],
  },
  {
    title: 'B GRADE AIR CELL',
    image: '/images/eggs/candled/b_01.jpg',
    description: '> 3/16 inch deep. Clearly visible large air space.',
    details: ['Measurement: 0.25"+', 'Acceptable for use', 'But not premium'],
  },
  {
    title: 'TRICK: DEFECTS OVERRIDE',
    image: '/images/eggs/candled/loss_blood_spot.jpg',
    description: 'Blood spot > 1/8" = LOSS, even if interior would be AA.',
    details: ['Check for defects first', 'Any blood/meat spot = Loss', 'Defects disqualify'],
  },
];
```

---

## Data Entry Checklist

Before launch, populate your image database:

```typescript
// At minimum, 15 images to get started
☐ 5 AA grade images (various lighting angles)
☐ 5 A grade images
☐ 3 B grade images
☐ 1 Loss (blood spot)
☐ 1 Exterior defect (dirty shell)

// Each image file should be:
☐ 1200x900px minimum (high-res but mobile-friendly)
☐ JPG format (optimized)
☐ Clear candling lighting (bright behind, dark background)
☐ Filename: [grade]_[number].jpg
☐ Metadata: Measured air cell depth & actual grade recorded in TypeScript
```

---

## Test Before Deploy

```typescript
// Quick validation in dev console
import { EGG_IMAGES } from '@/lib/data/egg-evaluation-images';

console.log('Total images:', EGG_IMAGES.length);
EGG_IMAGES.forEach(img => {
  console.log(`${img.id}: ${img.interior.airCell.depthInches}" (${img.interior.grade})`);
});

// Expected output:
// Total images: 15
// egg-aa-001: 0.125" (AA)
// egg-a-001: 0.1875" (A)
// ... etc
```

---

## Week 1 Outcome

✅ **Students can:**
1. View teaching slides (understand AA vs A vs B)
2. Estimate air cell size on images (practice measurement)
3. Get feedback (see if they're calibrated)
4. Grade 20 eggs in 10 minutes

✅ **You have:**
1. Image metadata file (reusable)
2. Measurement UI component (reusable)
3. 15+ reference images (extensible)

✅ **Next step:** Add exterior grading (shell condition), then move to live placing scenarios.

---

## Real-World Validation

After students train on images, **candled real eggs**:

```
VALIDATION DAY
─────────────
1. Student practices on app: 20 eggs, measures air cells
2. Same day: Student candled 20 real fresh eggs
3. USDA-certified grader evaluates the real eggs
4. Compare app grades vs certified grades
5. Calculate accuracy

Goal: 85%+ match (app grades align with certified standard)
```

If accuracy is <85%, adjust:
- Image selection (maybe your reference images are off)
- Slider sensitivity (maybe 0.01" steps are too fine)
- Student calibration time (need more practice slides)

---

## Questions to Answer

1. **Image source:** USDA official, shoot your own, or hybrid?
2. **Timing:** When do you want this live? Next 2 weeks?
3. **Scale:** Start with 15 images or go straight to 60?
4. **Feedback:** After each egg or after 20-egg batch?

Go. 🥚
