---
name: weekly-pipeline-check
description: Monday morning pipeline review. Pulls live data from Supabase and Stripe, shows school count vs 50-school goal, flags trials going cold, and gives Bryan one action to take before the school week starts. Trigger: /weekly-pipeline-check, "weekly check", "monday check", "pipeline check".
---

## What this skill does

Single Monday morning ritual. Takes under 3 minutes. Produces one clear action item.

1. Pulls school + trial data from Supabase
2. Pulls revenue data from Stripe (invoices/customers)
3. Displays a pipeline scoreboard against Bryan's 50-school goal
4. Flags trials going cold (>14 days with no conversion)
5. Surfaces one action to take this week

## Execution

### Step 1: Supabase — school count + trial status

Query project `nkoyotdafqllgbpuklva`:

```sql
SELECT
  subscription_status,
  subscription_tier,
  COUNT(*) as count
FROM schools
WHERE id NOT LIKE '11111111%'
GROUP BY subscription_status, subscription_tier
ORDER BY subscription_status, subscription_tier;
```

Also pull cold trials (>14 days):

```sql
SELECT name, advisor_name, advisor_email, created_at,
  EXTRACT(DAY FROM NOW() - created_at)::int AS days_in_trial
FROM schools
WHERE subscription_status = 'trialing'
  AND id NOT LIKE '11111111%'
  AND created_at < NOW() - INTERVAL '14 days'
ORDER BY created_at ASC;
```

### Step 2: Display scoreboard

```
=== Weekly Pipeline Check — [DATE] ===

GOAL: 50 paid schools by August 2026
Paid:    [n] / 50  ([n]% to goal)
Trials:  [n]
Gap:     [50 - paid] schools to close

REVENUE (Stripe)
MRR: $[n]  |  ARR: $[n]

TRIALS GOING COLD (>14 days)
[list or "None — you're on top of it"]
```

### Step 3: One action

Based on the data, surface exactly ONE action:

- If cold trials exist → "Follow up with [oldest trial school] — [X] days in trial, no conversion. Run /trial-follow-up."
- If trials = 0 and paid < 10 → "Send a new MailerLite blast. You have no active pipeline. Draft subject line: [suggest one in Bryan's voice]."
- If paid ≥ 10 → "You're at [n]% of goal. [Oldest paid school] has been active [X] days — check in and ask for a referral."
- If trials > 5 → "Pipeline is full. Focus on closing, not generating. Run /trial-follow-up."

### Step 4: Log the check

Append to `decisions/log.md`:

```
## YYYY-MM-DD — Weekly pipeline check
**Decision:** Reviewed pipeline. Paid: [n]. Trials: [n]. Action: [one action].
**Owner:** Bryan
```

## Notes

- Exclude seed schools (IDs starting with `11111111`).
- If Stripe returns no data, note it: "Stripe: no subscription data — payments tracked manually."
- Keep the whole output under 20 lines. One number, one action. That's the ritual.
