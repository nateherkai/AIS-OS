---
name: revenue-snapshot
description: Pull Stripe active subs + trials, compute MRR/ARR + schools-vs-50 goal, write dashboard/data/revenue.json. Run daily via cron or on demand. Trigger on /revenue, "revenue snapshot", "show MRR", "where are we vs 50 schools".
---

# Revenue Snapshot

Pulls live Stripe data for Ag Coach Pro. Writes JSON for dashboard rendering. Run daily 6am via cron, or on demand.

## Inputs

None. Reads `STRIPE_SECRET_KEY` from `.env`.

## Logic

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS"
python3 scripts/revenue_snapshot.py
```

The script:
1. Loads `STRIPE_SECRET_KEY` from `.env`.
2. Lists active subscriptions, classifies by plan (Greenhand / Blue & Gold / Lone Star Elite).
3. Computes MRR (sum of subscription line-items / 100) + ARR (× 12).
4. Counts schools vs the 50-school Q3 goal.
5. Lists trials with `trial_end` dates (cold-trial detection lives in `trial-follow-up` skill — not duplicated here).
6. Writes `dashboard/data/revenue.json`.

## Output

JSON at `dashboard/data/revenue.json`:
```json
{
  "ts": "2026-05-21T12:00:00+00:00",
  "stale": false,
  "total_schools": 12,
  "school_goal": 50,
  "mrr": 1234.56,
  "arr": 14814.72,
  "by_plan": {"Greenhand ($495)": [...], "Blue & Gold ($895)": [...]},
  "trials": [{"name": "...", "trial_end": "2026-06-01"}]
}
```

If `STRIPE_SECRET_KEY` missing or Stripe call fails, sets `stale: true` and writes error message.

## Verification

- Run skill → check `dashboard/data/revenue.json` mtime is recent.
- Open dashboard → school count tile + MRR match expected.
- If stale, check `.env` has STRIPE_SECRET_KEY set.

## Provenance

Built manually 2026-05-21 as L4 capability. Reuses plan-label logic from `scripts/stripe-snapshot.py`.
