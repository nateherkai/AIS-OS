# Admin Financial Panel — Design Spec
**Date:** 2026-05-12
**Owner:** Bryan Aaron
**Status:** Approved for implementation

---

## Overview

A superadmin-only financial panel embedded in `agcoachpro.com/admin` (`app/(admin)/index.tsx`). Shows Bryan his Ag Coach Pro revenue, burn, and school pipeline in one glance without opening the local AIOS dashboard. Invisible to all teachers — gated by `role === 'superadmin'`.

---

## Architecture

### Approach
Single-file edit. No new routes, no new API endpoints, no new Edge Functions. Add a `FinancialPanel` React Native component inside `app/(admin)/index.tsx`. Render it inside the existing `ScrollView`, immediately after the header row, gated by `role === 'superadmin'`.

### Data Sources

| Data | Source | How |
|------|--------|-----|
| Paid school count | Supabase `schools` table | Query inside `AdminDashboard` `useEffect` — same client already in use |
| Trial school count | Supabase `schools` table | Same query |
| MRR | Derived | `paid_count × 124.58` (Athens annual rate ÷ 12) |
| Monthly burn | Hardcoded constant | `MONTHLY_BURN = 373` at top of file — update manually after monthly CSV sync |

No new Supabase tables. No Edge Functions. No new dependencies.

### Supabase Query

```typescript
const { data } = await supabase
  .from('schools')
  .select('id, subscription_status')
  .not('id', 'like', '11111111%');

const paid = data.filter(s => s.subscription_status === 'active').length;
const trials = data.filter(s => s.subscription_status === 'trialing').length;
```

---

## UI Design

### Styling
Matches existing admin screen exactly:
- Background: `#000000`
- Glass cards: `rgba(255,255,255,0.04)` with `rgba(255,255,255,0.08)` border
- Gold accent: `#F2A900` (admin gold, not dashboard `#D4A574`)
- Red: `#f87171` · Green: `#4ADE80`
- Font: system default (matches rest of screen)

### Layout — 3 elements

#### 1. Net Income Banner (full width)
- Shows: net = MRR − burn
- Red background tint + red value when negative
- Green background tint + green value when positive
- Subtitle: "Close X more schools to break even" (negative) or "Profitable — X schools to goal" (positive)

#### 2. KPI Row (4 cards, horizontal scroll on narrow screens)
- **MRR** — gold value, `$X/mo`, sub: "X school paid"
- **Monthly Burn** — red value, `$373/mo`, sub: "update after CSV sync"
- **Paid Schools** — white value `X/50` with thin gold progress bar, sub: "goal: Aug 2026"
- **Active Trials** — yellow value, sub: "X in pipeline"

#### 3. Section separator
Thin `rgba(255,255,255,0.06)` line + "FINANCIAL OVERVIEW" label above the panel (matches existing section title style in the file).

---

## File Changes

### `app/(admin)/index.tsx`
- Add constant `MONTHLY_BURN = 373` near top of file
- Add `FinancialPanel` component (self-contained, reads props — no internal state/fetching)
- Add financial state to `AdminDashboard`: `paidSchools`, `trialSchools` (fetched in existing `useEffect` alongside current data)
- Render `{role === 'superadmin' && <FinancialPanel ... />}` after the header `<View>`, before the alerts section

No other files touched.

---

## What This Is NOT

- Not visible to teachers
- Not a replacement for the local AIOS dashboard (no debt tracker, no tasks, no expense breakdown, no skill buttons)
- Not real-time expense data — burn is a static constant updated manually once per month

---

## Success Criteria

Bryan opens agcoachpro.com/admin and sees net income, MRR, burn, and school pipeline count in under 2 seconds — without opening the local dashboard or logging into Supabase.
