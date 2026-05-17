# Egg Evaluation — THIS WEEK Action Plan
## Start Monday, MVP by Friday

---

## The Goal

**By Friday:** Students open Poultry → Egg Grading → See a candled egg image → Estimate air cell size (1/8" vs 3/16") → Get feedback.

**Why this matters:** Egg grading is the most **visual, measurable** CDE component. Air cell size determines the grade. This is NOT about memorizing; it's about **seeing** grades.

---

## Monday: Prep Images & Data

### Task 1: Source Candled Egg Images (1 hour)

**Option A (Fast):** Download USDA official images
- Go: [ams.usda.gov/content/official-federal-egg-grading-standards](https://www.ams.usda.gov/content/official-federal-egg-grading-standards)
- Look for: "Candling Photo Guide" or "Official Grade Photos"
- Download: 15 images (3× AA, 3× A, 3× B, 2× Loss, 2× Exterior)
- Save to: `assets/images/eggs/candled/[filename].jpg`

**Option B (Better):** Candled eggs yourself
- Get: 1 dozen eggs (mixed grades)
- Equipment: Candling light + dark room
- Photograph: Backlit (light behind egg)
- Measure: Air cell depth with ruler or calipers
- Save with filename: `aa_0125.jpg` (includes measurement)

**Option C (Best):** Partner with local FFA
- Call your high school FFA advisor
- Ask: "Can students candled eggs this week? We'll photograph them."
- Real eggs → real photos → best learning

### Task 2: Create Image Data File (30 min)

Copy the code from **EGG_EVAL_QUICK_START.md** (Phase 2) into a new file:

```bash
touch lib/data/egg-evaluation-images.ts
```

Paste the TypeScript code with your 15 images. Example:

```typescript
export const EGG_IMAGES: EggEvaluationImage[] = [
  {
    id: 'egg-aa-001',
    imageUrl: '/images/eggs/candled/aa_01.jpg',
    interior: {
      airCell: { depthInches: 0.125, grade: 'AA' },
      // ... rest of fields
    },
  },
  // Add all 15 images
];
```

**⚠️ Key:** Each image must have **actual measured air cell depth** (0.125", 0.1875", etc.). This is the ground truth.

### Task 3: Create AirCellMeasurementOverlay Component (45 min)

Create new file:

```bash
touch components/egg-eval/AirCellMeasurementOverlay.tsx
```

Copy the full component code from **EGG_EVAL_QUICK_START.md** (Phase 3, Step 1).

Test that it compiles:

```bash
npm start
```

Look for errors. Fix any TypeScript issues.

---

## Tuesday & Wednesday: Wire UI & Test

### Task 4: Update eggs.tsx (1 hour)

Edit `app/practice/poultry-eval/eggs.tsx`:

**Remove:** The text-based scenario system (EGG_GRADING_SCENARIOS)

**Add:** Image-based measurement system

```typescript
import { EGG_IMAGES } from '@/lib/data/egg-evaluation-images';
import AirCellMeasurementOverlay from '@/components/egg-eval/AirCellMeasurementOverlay';

export default function EggEvaluationScreen() {
  const [imageIdx, setImageIdx] = useState(0);
  const [scores, setScores] = useState<boolean[]>([]);
  const [finished, setFinished] = useState(false);

  const eggImage = EGG_IMAGES[imageIdx];

  const handleEstimate = (estimatedInches: number) => {
    const estimatedGrade = estimatedInches <= 0.125 ? 'AA' : 
                           estimatedInches <= 0.1875 ? 'A' : 'B';
    const isCorrect = estimatedGrade === eggImage.interior.airCell.grade;
    setScores([...scores, isCorrect]);

    // Move to next image after 2 seconds
    setTimeout(() => {
      if (imageIdx + 1 >= EGG_IMAGES.length) {
        setFinished(true);
      } else {
        setImageIdx(prev => prev + 1);
      }
    }, 2000);
  };

  if (finished) {
    const correct = scores.filter(Boolean).length;
    const pct = Math.round((correct / scores.length) * 100);
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <Text style={{ fontSize: 40, fontWeight: '900', color: '#fff' }}>
          {correct}/{scores.length}
        </Text>
        <Text style={{ fontSize: 24, fontWeight: '900', color: '#F2A900' }}>
          {pct}%
        </Text>
        <TouchableOpacity onPress={() => router.back()} style={{ marginTop: 20 }}>
          <Text style={{ color: '#fff' }}>Back to Hub</Text>
        </TouchableOpacity>
      </View>
    );
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

### Task 5: Test on Device (1 hour)

```bash
# Start dev server
npm start

# Open on web or simulator
npm run web
```

Navigate: **CDE → Poultry → Egg Grading**

**Expected behavior:**
1. See candled egg image
2. Slider appears below image
3. Move slider → see "Grade: AA" / "Grade: A" / "Grade: B" update
4. Click "Submit" → see feedback
5. Next button → move to next egg

**If broken:**
- Check console for errors
- Verify images exist in `assets/images/eggs/candled/`
- Verify TypeScript compilation (types correct?)

### Task 6: Get Feedback from One Student (30 min)

Have **one student** test it for 5 minutes. Ask:
- "Can you understand the slider?"
- "Does the feedback make sense?"
- "Is it hard to estimate the air cell?"

**Note:** If slider is confusing, swap it for **tap buttons** (AA / A / B only).

---

## Thursday: Add Teaching Slides

### Task 7: Create egg-teach.tsx (1 hour)

Create new file:

```bash
touch app/practice/poultry-eval/egg-teach.tsx
```

This screen teaches students BEFORE they practice.

```typescript
import React, { useState } from 'react';
import { View, Text, Image, ScrollView, StyleSheet } from 'react-native';
import { AnimatedButton as TouchableOpacity } from '@/components/common/AnimatedButton';
import { useRouter } from 'expo-router';

const TEACHING_SLIDES = [
  {
    id: 1,
    title: 'AIR CELL: THE KEY TO EGG GRADING',
    image: '/images/eggs/candled/aa_01.jpg',
    text: 'The air pocket at the large end of the egg.\nWhen you candled the egg under bright light, you see it as a dark space.',
  },
  {
    id: 2,
    title: 'AA GRADE: ≤ 1/8 INCH',
    image: '/images/eggs/candled/aa_02.jpg',
    text: 'AA eggs have tiny air cells.\nLess than 1/8 inch deep.\nPerfect for premium use.',
  },
  {
    id: 3,
    title: 'A GRADE: ≤ 3/16 INCH',
    image: '/images/eggs/candled/a_01.jpg',
    text: 'A eggs have slightly larger air cells.\nUp to 3/16 inch (0.1875 inches).\nStill very good quality.',
  },
  {
    id: 4,
    title: 'B GRADE: > 3/16 INCH',
    image: '/images/eggs/candled/b_01.jpg',
    text: 'B eggs have noticeably larger air cells.\nAnything bigger than 3/16 inch.\nAcceptable for commercial use.',
  },
  {
    id: 5,
    title: 'DEFECTS TRUMP EVERYTHING',
    image: '/images/eggs/candled/loss_blood_spot.jpg',
    text: 'If an egg has blood spots or meat spots > 1/8", it\'s LOSS grade.\nNo matter what the air cell grade is.',
  },
];

export default function EggTeachingScreen() {
  const router = useRouter();
  const [slideIdx, setSlideIdx] = useState(0);
  const slide = TEACHING_SLIDES[slideIdx];

  const handleNext = () => {
    if (slideIdx + 1 >= TEACHING_SLIDES.length) {
      router.push('/practice/poultry-eval/eggs'); // Go to practice
    } else {
      setSlideIdx(prev => prev + 1);
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Back button */}
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <Text style={{ color: '#fff' }}>← Back</Text>
        </TouchableOpacity>

        {/* Slide content */}
        <Text style={styles.slideNum}>SLIDE {slideIdx + 1} OF {TEACHING_SLIDES.length}</Text>
        <Text style={styles.title}>{slide.title}</Text>

        <Image source={{ uri: slide.image }} style={styles.image} />

        <Text style={styles.text}>{slide.text}</Text>

        {/* Navigation */}
        <TouchableOpacity style={styles.nextBtn} onPress={handleNext}>
          <Text style={styles.nextBtnText}>
            {slideIdx + 1 >= TEACHING_SLIDES.length ? 'Start Practice' : 'Next Slide'}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  scroll: { padding: 20, paddingTop: 60 },
  backBtn: { marginBottom: 20 },
  slideNum: { color: '#555', fontSize: 12, fontWeight: '900', marginBottom: 8 },
  title: { color: '#fff', fontSize: 24, fontWeight: '900', marginBottom: 20 },
  image: { width: '100%', height: 300, resizeMode: 'contain', marginBottom: 20 },
  text: { color: '#ddd', fontSize: 16, lineHeight: 24, marginBottom: 40 },
  nextBtn: {
    backgroundColor: '#F2A900',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  nextBtnText: { color: '#000', fontWeight: '900', fontSize: 16 },
});
```

### Task 8: Update Egg Hub to Route to Teaching First

Edit `app/practice/poultry-eval/index.tsx`:

Change the egg grading card:

```typescript
{
  id: 'eggs',
  title: 'Egg Grading',
  desc: 'Learn air cell measurement, practice visual estimation',
  icon: 'egg-outline',
  color: '#60A5FA',
  route: '/practice/poultry-eval/egg-teach',  // ← CHANGED (was eggs, now egg-teach)
}
```

Now the flow is: **Egg Grading → Teaching Slides → Practice**

---

## Friday: Test & Deploy

### Task 9: End-to-End Test (1 hour)

```
1. Launch app
2. Navigate: CDE → Poultry → Egg Grading
3. Complete 5 teaching slides
4. Complete 15 practice eggs
5. See final score: X/15 (Y%)
6. Go back to hub
```

**Checklist:**
- ☐ Images load without errors
- ☐ Slider works smoothly
- ☐ Feedback is clear
- ☐ Score calculation is correct
- ☐ Navigation works

### Task 10: Have 3 Students Beta Test (1 hour)

Give 3 students 10 minutes each. Ask:
- "Can you understand how to use the slider?"
- "Did the feedback help you learn?"
- "What would make this better?"

**Note feedback. Plan fixes for next week.**

### Task 11: Deploy to Web (30 min)

```bash
npm run build
npm run export
# Deploy to Vercel or your hosting
```

---

## By Friday EOD You Have:

✅ **Working MVP:**
- Teaching slides (why air cell matters)
- Practice mode with real images
- Feedback system (correct/incorrect + why)
- Score tracking

✅ **Reusable Code:**
- `lib/data/egg-evaluation-images.ts` (extensible to 50+ images)
- `AirCellMeasurementOverlay` component (reusable for other visual tasks)
- `egg-teach.tsx` (teaching pattern for other CDEs)

✅ **Validation:**
- 3 students tested it
- Feedback recorded
- Bug list for Week 2

---

## Week 2 (Next Week) — Scale Up

- [ ] Add 35 more images (total 50 eggs)
- [ ] Add exterior grading (shell condition)
- [ ] Add timed mode (30 sec per egg)
- [ ] Add comparison cards (AA vs A side-by-side)
- [ ] Real-world validation (candled actual eggs, compare grades)

---

## Files You're Creating

```
NEW FILES:
  lib/data/egg-evaluation-images.ts              (15+ image metadata)
  components/egg-eval/AirCellMeasurementOverlay.tsx
  app/practice/poultry-eval/egg-teach.tsx

MODIFIED FILES:
  app/practice/poultry-eval/eggs.tsx             (swap text → images)
  app/practice/poultry-eval/index.tsx            (route to teach, not eggs)

ASSET FOLDER:
  assets/images/eggs/candled/                    (15+ JPG files)
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Images don't load | Check paths in egg-evaluation-images.ts match actual files in assets/ |
| Slider jumps around | Reduce step size or add debounce |
| Air cell detection is wrong | Verify air cell measurements in TypeScript are accurate |
| Feedback is confusing | Simplify: "Correct!" vs "Not quite. It was AA." |
| Student thinks it's boring | Add comparison slides (AA vs A difference) + make it visual, not text |

---

## Success Metric (This Week)

**3 students can:**
1. Complete 15 egg images in <10 minutes
2. Score 70%+ on first attempt
3. Understand why they got one wrong

If hitting 70%, you're ready to scale up next week.

---

## Let's Go

**Monday at 9am:** Start with images.  
**Friday at 5pm:** Students testing.

This is the right move. Egg grading is visual. Make it visual. Your students will get it.

🥚🕯️
