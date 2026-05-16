---
name: trial-follow-up
description: Pull all trial schools from Supabase, show pipeline status, and draft personalized close emails in Bryan's voice. Run when you want to work your trial pipeline without logging into Supabase manually. Trigger: /trial-follow-up, "work my trials", "follow up on trials", "who's in trial".
---

## What this skill does

1. Queries Supabase for all schools with `subscription_status = 'trialing'`
2. Displays a pipeline table: school, advisor, email, days in trial, tier
3. Drafts a personalized close email for each trial using Bryan's voice register
4. Recommends Blue & Gold vs Lone Star Elite based on school size (max_students)

## Execution

### Step 1: Pull trial schools from Supabase

Run this query against project `nkoyotdafqllgbpuklva`:

```sql
SELECT
  name,
  advisor_name,
  advisor_email,
  subscription_tier,
  max_students,
  created_at,
  NOW() - created_at AS days_in_trial
FROM schools
WHERE subscription_status = 'trialing'
ORDER BY created_at ASC;
```

### Step 2: Display pipeline table

Print a markdown table:

| School | Advisor | Email | Days in Trial | Seats | Recommended Plan |
|--------|---------|-------|---------------|-------|-----------------|
| ...    | ...     | ...   | ...           | ...   | ...             |

Recommended plan logic:
- `max_students` > 40 OR NULL → Lone Star Elite ($1,495)
- `max_students` ≤ 40 → Blue & Gold ($895)

### Step 3: Draft close emails

For each trial school, draft a personalized close email using Bryan's voice (see `references/voice.md`):
- Use advisor's first name
- Reference their school name
- Recommend the correct plan based on seat count
- Use the close template from `templates/email-sequences/trial-to-paid-close.md`
- Personalize the middle paragraph with a believable specific detail (e.g., contest season timing, CDE module relevance)

Print each email clearly labeled: `--- Email: [School Name] ---`

### Step 4: Ask what to do next

After showing all emails, ask:
> "Want me to copy any of these to your clipboard, save them to a drafts file, or mark any school as contacted in the decisions log?"

If user says mark as contacted: append an entry to `decisions/log.md`:
```
## YYYY-MM-DD — Contacted [School Name]
**Decision:** Sent close email to [Advisor Name] at [email].
**Why:** Trial school — following up to convert to [plan].
**Owner:** Bryan
```

## Voice rules (from references/voice.md)

- Warm, direct, unpretentious
- Short sentences, conversational
- Accountability-forward ("I'm still building this")
- Genuine gratitude, not performative
- No corporate tone

## Notes

- If Supabase returns 0 trials: "No active trials right now. Good time to run a new blast to your MailerLite list."
- If a school has no advisor_email: flag it — "Missing email for [School]. You'll need to find their contact manually."
- Never send emails directly — draft only. Bryan reviews before sending.
