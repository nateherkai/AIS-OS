---
name: agcoach-egg-evaluation-cde
type: concept
tags: [ag-coach-pro, cde, poultry, egg, candling, vision]
source_files: [raw/_ingested/2026-05-16-agcoach-egg-evaluation-feature.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Egg Evaluation CDE

Subdomain of [[agcoach-poultry-judging-cde|Poultry Judging CDE]]. Trains students to **see** grades, not memorize text descriptions. Lives at `app/practice/poultry-eval/eggs.tsx`.

## Why text-based grading fails

Real contest: candle 150 eggs, glance at air pocket, grade in 3 seconds, move on. Current `eggs.tsx` shows text observations ("air cell 1/8 inch, firm white"). Student picks AA. No calibration to visual reality; no muscle memory.

## USDA grade thresholds

| Interior grade | Air cell size | Notes |
|---|---|---|
| AA | ≤ 1/8" (0.125") | Firm white, yolk barely visible |
| A | ≤ 3/16" (0.1875") | Reasonably firm, fairly visible yolk |
| B | > 3/16" | Thin/watery, plainly visible yolk |
| Loss | — | Blood spot > 1/8", blood ring, etc. |

Exterior: Clean / Slightly stained / Prominently stained → A / B / Dirty. Checked shells → Check.

## Three-phase training design

1. **Teach** — 7 annotated candled-egg slides (air-cell definition, 1/8" vs 3/16" measurement, blood-spot edge cases, trick scenarios where AA-looking eggs are actually Loss).
2. **Calibrate** — interactive slider over real candled-egg image. Feedback shows measurement overlay on the same image: "you said 1/4", actual was 3/16" — see how the air space stops at this line."
3. **Rapid-fire** — 20 eggs × 30 sec, grade interior + exterior. Feedback delayed until batch end (real contest behavior).

## Data model

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
  exterior: { shellCondition; shape; grade: 'AA' | 'A' | 'B' | 'Dirty' | 'Check'; explanation };
  measurementOverlay?: { x, y, width, height, referenceLines: { label, pixelPosition }[] };
  trickNote?: string;
  teachingContext?: { relatedSlide: number; compareToImageId: string };
}
```

## UI components (planned)

- `AirCellMeasurementOverlay` — ruler + draggable slider on candled image.
- `ComparisonCard` — AA vs A vs B side-by-side for visual pattern recognition.
- `TimedGradingSession` — 20-egg batch, `showFeedbackAfter: 'all'`.

## Content acquisition

1. USDA Egg Grading Manual + AMS candling procedure guide via NotebookLM.
2. Self-shot candled-egg photos with caliper-measured ground truth.
3. AI vision to auto-detect air-cell bounds on real photos → generate measurement overlay.

## Success metric

Student candles a real egg and grades AA/A/B within 10s at 90% accuracy vs certified standard.

## Open questions

Image source, ground-truth measurement method, real-world cross-check protocol, feedback timing (per-egg teaching vs batch contest), whether exterior grading also goes image-based.

## Related

- [[../sources/agcoach-egg-evaluation-feature|Egg Evaluation Feature spec]]
- [[agcoach-poultry-judging-cde|Poultry Judging CDE]]
- [[agcoach-rag-architecture|RAG Architecture]]
- [[agcoach-contest-modules|Contest Modules]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
