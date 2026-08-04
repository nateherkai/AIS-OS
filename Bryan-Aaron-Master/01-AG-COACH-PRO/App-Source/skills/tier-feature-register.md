# Skill: Tier Feature Register

## Purpose

New CDE module needs 4-file registration. Humans miss one → module invisible / wrong tier / no scoring. This skill is the checklist.

---

## When to Use

- Just scaffolded new module (`scaffold-cde-module`)
- Just completed stub (`complete-stub-module`)
- Adding module from older state where registration drifted

---

## The Four Files

### 1. `constants/contests.ts` — Activate

```ts
{
  id: '<uuid>',
  legacyId: 'cde-widget',
  name: 'Widget Eval',
  is_active: true,  // ← flip to true when ready
  // ...
}
```

### 2. `app/contest/[id].tsx` — Route

Add `if`-block in `startPractice()`:

```ts
if (legacyId === 'cde-widget') {
  router.push('/practice/widget');
  return;
}
```

### 3. `lib/tier.ts` — Gate

Add feature → tier mapping in `FEATURE_TIERS`:

```ts
'cde-widget': 'blue-and-gold',  // greenhand | blue-and-gold | lone-star-elite
```

Decide tier:
- Foundation (LDE, quizzes) → `greenhand`
- Standard CDE → `blue-and-gold`
- Premium/multi-judge → `lone-star-elite`

### 4. `lib/store/history.ts` — Score record

Add `PracticeType` union member:

```ts
export type PracticeType =
  | 'forages'
  | 'horse-eval'
  | 'widget'  // ← new
  | ...;
```

Without this, score writes fail silently — student progress invisible in dashboard.

---

## Bonus — TOPIC_QUERIES

If module uses RAG (`generateRAGBatch`), add entries to `TOPIC_QUERIES` in `lib/ai/rag-quiz.ts`:

```ts
'widget-anatomy': 'widget anatomy parts identification structure',
'widget-judging': 'widget judging criteria scorecard placing',
```

Missing entry = generic retrieval = poor question quality.

---

## Verification Sequence

```bash
# 1. Type check
npx tsc --noEmit -p .

# 2. Grep all four registrations
grep -n "cde-widget" constants/contests.ts app/contest/\[id\].tsx lib/tier.ts
grep -n "'widget'" lib/store/history.ts

# 3. Confirm RAG coverage (if applicable)
# Run rag-coverage-report skill
```

All four greps must hit. Type check must pass.

---

## Tier Pricing Reference

| Tier | $/yr | Seats | Credits |
|---|---|---|---|
| Greenhand | $495 | LDE + individual quiz | 5M |
| Blue & Gold | $895 | + 40 CDE | 15M |
| Lone Star Elite | $1495 | Unlimited | 40M |

Premium modules (multi-judge livestock w/ video, horse leads w/ AI video) → Lone Star Elite. Justify high-credit-burn features by tier credit pool, not arbitrary gates.

---

## Anti-Patterns

| Miss | Symptom |
|---|---|
| `is_active: false` | Module hidden from CDE list |
| No `if`-block in `startPractice()` | "Coming soon" placeholder shown |
| No `FEATURE_TIERS` entry | Defaults to most-restrictive tier or crashes |
| No `PracticeType` member | Score writes type-error or fail silently |
| No `TOPIC_QUERIES` | Generic retrieval, poor questions |
