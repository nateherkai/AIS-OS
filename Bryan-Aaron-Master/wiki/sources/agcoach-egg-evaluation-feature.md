---
name: agcoach-egg-evaluation-feature
type: source
tags: [ag-coach-pro, poultry, egg, candling, vision, ux]
source_files: [raw/_ingested/2026-05-16-agcoach-egg-evaluation-feature.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Egg Evaluation Feature (Image-Based Air Cell Measurement)

`docs/EGG_EVALUATION_FEATURE.md`. Design spec for replacing text-based egg grading with high-res candled-egg images + visual measurement tools. Sister docs `EGG_EVAL_QUICK_START.md` and `EGG_EVAL_THIS_WEEK.md` are tactical subsets and not separately ingested.

## Problem

Current `eggs.tsx` shows text observations ("Air cell 1/8 inch, firm white, yolk barely visible") → student picks AA. Trains memorization, not visual recognition. Real contest = candle 150 eggs, grade in 3 seconds each, by pattern.

## Three-phase training design

1. **Teach** — 7 annotated candled-egg slides covering air-cell definition, 1/8" vs 3/16" measurement, edge cases (blood spot = Loss), trick scenarios.
2. **Calibrate** — interactive slider over real candled-egg image; student estimates air-cell depth; feedback shows measurement overlay on same image.
3. **Rapid-fire** — 20 eggs × 30 sec, grade interior + exterior. Feedback delayed until batch end (mirrors real contest).

## Enhanced data model

```typescript
interface EggEvaluationImage {
  id: string;
  imageUrl: string;
  interior: {
    airCellSizeInches: number;
    airCellGrade: 'AA' | 'A' | 'B';
    whiteCuracy: 'firm' | 'reasonably_firm' | 'thin_watery';
    yolkDefinition: 'barely_visible' | 'fairly_visible' | 'plainly_visible';
    specialDefects?: { type: 'blood_spot' | 'blood_ring' | 'meat_spot' | 'rooster_semen'; severity: 'minor' | 'major' }[];
    grade: 'AA' | 'A' | 'B' | 'Loss';
    explanation: string;
  };
  exterior: { shellCondition: string; shape: string; grade: 'AA' | 'A' | 'B' | 'Dirty' | 'Check'; explanation: string };
  measurementOverlay?: { x, y, width, height, referenceLines: { label, pixelPosition }[] };
  trickNote?: string;
  teachingContext?: { relatedSlide: number; compareToImageId: string };
}
```

## UI components needed

- `AirCellMeasurementOverlay` — ruler overlay on candled image, draggable slider.
- `ComparisonCard` — side-by-side AA vs A vs B for pattern recognition.
- `TimedGradingSession` — 20-egg batch, `showFeedbackAfter: 'all'`.

## Content acquisition options

1. NotebookLM project off USDA Egg Grading Manual + AMS candling procedure guide.
2. Source/shoot real candled-egg photos (caliper-measured for ground truth).
3. AI-generated measurement overlays via computer vision on real photos.

## 4-week roadmap

- Week 1: data schema + 7-slide teaching deck + `AirCellMeasurementOverlay`.
- Week 2: 50+ annotated images + calibration practice + rapid-fire mode.
- Week 3: comparison cards + delayed-feedback loop.
- Week 4: tier gating + Supabase score persistence + ship.

## Success metric

Student candles a real egg and grades AA/A/B within 10 seconds at 90% accuracy vs certified standard.

## Open questions (from spec)

1. Image source (USDA / self-shot / FFA partner).
2. Ground-truth measurement method (calipers / USDA data).
3. Real-world cross-check after app training.
4. Feedback timing (per-egg teaching vs batch contest mode).
5. Whether exterior grading also goes image-based.

## Related

- [[../concepts/agcoach-egg-evaluation-cde|Egg Evaluation CDE]]
- [[../concepts/agcoach-poultry-judging-cde|Poultry Judging CDE]]
- [[agcoach-poultry-judging-feature|Poultry Judging Feature spec]]
- [[../concepts/agcoach-contest-modules|Contest Modules]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
