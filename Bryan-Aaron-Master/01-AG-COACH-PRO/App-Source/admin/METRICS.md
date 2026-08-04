# Admin Dashboard Metrics — Source of Truth

**Last audited:** 2026-04-26

This document maps every admin metric to its source RPC, the SQL behind it, and the data layer function in `lib/admin-data.ts`. **Read this before adding a new metric — there's a good chance it already exists.**

---

## Status snapshot

| Layer | State |
|---|---|
| RPCs in DB | 9 declared, **9 working** (as of 2026-04-26 after fixes 057 + 058) |
| Data layer (`lib/admin-data.ts`) | Complete — wraps all 9 RPCs + bare-table CRM queries |
| Admin UI (`app/admin.tsx`) | Imports the data layer |
| RLS / auth | RPCs granted to `anon` (migration 055). Page-level password gate. |

### Bugs fixed 2026-04-26

1. **`get_admin_chapters()`** was erroring with `column reference "chapter_id" is ambiguous` — broken since deploy. Fixed by `057_fix_admin_chapters_ambiguity.sql` (qualified all CTE columns). Now returns 561 rows.
2. **`ai_usage_events` table was missing** — declared in 043 but never landed. Fixed by `058_create_ai_usage_events.sql` (recreated table + indexes + RLS). `get_admin_ai_usage()` now returns 561 rows (one per chapter; usage values are 0 until the app starts logging events).

---

## Top-level KPIs

Source: `get_admin_kpis()` → `fetchKPIs()` → top of `app/admin.tsx`

| Metric | Field | Sample value (2026-04-26) | Source |
|---|---|---|---|
| Total chapters | `total_chapters` | 561 | `COUNT(*) FROM biz_chapters` |
| Active users (7d) | `active_users_7d` | 3 | distinct `user_id` from `student_activity_logs` ≤ 7d |
| Total students | `total_students` | 41 | `COUNT(*) FROM users WHERE role='student'` |
| Total revenue (paid) | `total_revenue` | $1,495.00 | `SUM(amount_paid) FROM biz_payments` |
| Unpaid revenue | `unpaid_revenue` | $0.00 | `SUM(amount_due) FROM biz_invoices WHERE status IN ('open','overdue','draft')` |
| Avg mastery | `avg_mastery` | 0 | `AVG(mastery_level) FROM user_progress WHERE mastery_level > 0` |
| Growth 30/60/90d | `growth_30d` / `_60d` / `_90d` | 9 / 9 / 9 | distinct `user_id` from `student_activity_logs` over window |
| Tier — Greenhand | `tier_greenhand` | 0 | `COUNT FROM biz_subscriptions WHERE tier_level='The Greenhand'` |
| Tier — Blue & Gold | `tier_blue_gold` | 0 | `tier_level='The Blue & Gold'` |
| Tier — Lone Star Elite | `tier_elite` | 2 | `tier_level='The Lone Star Elite'` |
| Invoices paid / open / overdue | `invoices_paid` / `_open` / `_overdue` | 1 / 1 / 0 | `biz_invoices.status` |

---

## Chapters list

Source: `get_admin_chapters()` → `fetchChapters()` → chapters table in admin UI
**STATUS: BROKEN — see bug #1 above**

Returns one row per chapter with:
- Chapter info (`chapter_name`, `area_district`, advisor name/email/phone)
- Subscription summary (`tier_level`, `sub_status`, `renewal_date`, Stripe IDs)
- Student count (joined via `users.school_id`)
- 30d activity (`active_students_30d`, `distinct_login_days_30d`, `last_login_at`)
- `unpaid_total` (sum of open/overdue/draft invoices)
- `open_followups` count

---

## Invoices

Source: `get_admin_invoices()` → `fetchInvoices()` → 3 rows today

Returns invoice + chapter name + computed `amount_paid` (sum of `biz_payments` per invoice).

---

## Chapter detail (drill-down)

Source: `get_chapter_detail(p_chapter_id)` → `fetchChapterDetail(id)`

Returns a single JSON object containing:
- `chapter` — full `biz_chapters` row
- `subscription` — full `biz_subscriptions` row
- `invoices[]` — all invoices for the chapter
- `payments[]` — all payments
- `students[]` — full student roster with last activity
- `top_features[]` — feature engagement ordered by interactions
- `recent_activity[]` — last 14d of student activity, capped at 50 rows
- `notes[]` — CRM contact notes with author email
- `followups[]` — sorted open → snoozed → done, then by due date
- `engagement` — sessions/avg score/avg session seconds for 7d + 30d windows

---

## Engagement / learning analytics

| Metric | RPC | Data layer |
|---|---|---|
| Feature adoption (weekly) | `get_feature_adoption_trends(p_weeks)` | `fetchFeatureAdoptionTrends(8)` — 9 rows |
| Module funnel (opened → started → completed) | `get_module_funnel()` | `fetchModuleFunnel()` — 5 rows |
| Struggle heatmap (error rate by contest+subcategory) | `get_struggle_heatmap()` | `fetchStruggleHeatmap()` — 0 rows (no question_responses yet) |
| Top features (raw) | bare-table read of `feature_engagement` | `fetchFeatureUsage()` — 12 rows max |

---

## AI usage / cost

Source: `get_admin_ai_usage()` → `fetchAIUsage()`
**STATUS: BROKEN — see bug #2 above**

Per-chapter monthly tokens, requests, est cost, % of tier limit, capped flag. Joins `biz_chapters` × `biz_subscriptions` × `tier_config` × `ai_usage_events` (current month) × `chapter_usage`.

---

## Support tickets

Source: `get_admin_support_tickets()` → `fetchSupportTickets()` → 0 rows today

Returns last 200 tickets with AI-classified `ai_category`, `ai_urgency`, `ai_summary`, `ai_solution`.

---

## CRM / Sales pipeline

Bare-table reads (not RPCs — these go through RLS):

| Function | Table | What it returns |
|---|---|---|
| `fetchProspects()` | `biz_chapters` | chapters with `lead_stage = 'demo_lead'` |
| `fetchAllContacts()` | `biz_chapters` | chapters with non-null `lead_stage` |
| `fetchContactNotes(chapterId)` | `crm_contact_notes` | notes for one chapter |
| `fetchContactFollowups(chapterId)` | `crm_followups` | followups for one chapter |
| `getCrmFunnel()` | `biz_chapters` | counts grouped by `lead_stage` |

Mutations: `addCRMNote`, `addFollowup`, `updateFollowupStatus`, `updateLeadStage`, `updateTargetTier`.

---

## Self-heal / audit

Source: bare-table read of `admin_audit_log` → `getSelfHealStatus()`

Returns most recent self-heal run (`run_id`, time, fixes applied, alerts pending, abandoned items). 29 audit rows today.

---

## Stripe sync

`bulkSyncFromStripe(chapterIds)` → calls Edge Function `stripe-sync` per chapter, 300ms delay between calls.

---

## Gap analysis — what's missing from the dashboard

Things you might want but don't have today:

1. **MRR / ARR projection** — current revenue is "paid to date." No forward-looking subscription book.
2. **Churn rate** — `lead_stage='churned'` exists on `biz_chapters` but no time-series of churn events.
3. **Trial → paid conversion rate** — would need to track `lead_stage` history (currently only the latest stage is stored).
4. **Activation funnel** — signup → first practice → first contest. `student_activity_logs` has the data; no RPC built yet.
5. **Per-teacher view** — admin focuses on chapters. No "show me everything teacher X owns."
6. **Email log integration** — `email_log` has 102 rows but isn't surfaced anywhere.
7. **Webhook log integration** — `webhook_log` has 46 rows; useful for debugging Stripe issues but not on the admin page.

Each of these is a candidate for a future RPC. Don't build any of them until current bugs are fixed.

---

## How to add a new metric

1. Decide if it's a chapter-level metric (add to `get_admin_chapters` row), a global KPI (add to `get_admin_kpis`), or a new dimension (new RPC).
2. Write the RPC in a new migration `supabase/migrations/0NN_<name>.sql`. Use `SECURITY DEFINER` and `GRANT EXECUTE ... TO anon`.
3. Add the wrapper to `lib/admin-data.ts` returning a typed shape.
4. Add the UI element to `app/admin.tsx`.
5. Test the RPC directly first via SQL editor — don't trust deploy until you've seen rows.

---

## How to verify the dashboard

```sql
-- Run in Supabase SQL editor. Each line should return rows or 0 cleanly.
SELECT * FROM get_admin_kpis();
SELECT COUNT(*) FROM get_admin_chapters();    -- BROKEN until 057
SELECT COUNT(*) FROM get_admin_invoices();
SELECT COUNT(*) FROM get_feature_adoption_trends(8);
SELECT COUNT(*) FROM get_module_funnel();
SELECT COUNT(*) FROM get_struggle_heatmap();
SELECT COUNT(*) FROM get_admin_support_tickets();
SELECT COUNT(*) FROM get_admin_ai_usage();    -- BROKEN until 058
```
