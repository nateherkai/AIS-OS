# Ag Coach Pro — Supabase Schema (Source of Truth)

**Project:** Ag Coach Pro (`nkoyotdafqllgbpuklva`)
**Region:** us-west-2
**Postgres:** 17.6.1
**Captured:** 2026-04-26
**Schema:** `public` (47 tables)

> **Rule for Claude / future sessions / skills:** Always read this file before writing any query, view, or skill that touches the database. Do not assume table names. If the schema has changed, regenerate this file via `supabase/migrations/` workflow.

---

## Critical: There are TWO billing systems

This is the single biggest gotcha. Don't mix them up.

| | Legacy (school-level) | Current (chapter-level) |
|---|---|---|
| Subscription table | `subscriptions` | `biz_subscriptions` |
| Owner table | `schools` | `biz_chapters` |
| Invoicing | None | `biz_invoices` + `biz_invoice_line_items` |
| Payments | None | `biz_payments` |
| Plans | Inline (`subscriptions.plan`) | `biz_products_plans` |
| Stripe-aware | Partial | Full |
| Rows today | 7 subs / 7 schools | 2 subs / 561 chapters |

**Use `biz_*` tables for any new admin or billing work.** The `subscriptions`/`schools` tables are kept around for legacy users and the existing `users.school_id` link.

---

## Tables by domain (with row counts as of 2026-04-26)

### 1. Identity & Access

| Table | Rows | Purpose |
|---|---|---|
| `users` | 46 | App users (teachers + students). Mirrors `auth.users.id`. |
| `user_roles` | 0 | Reserved — currently unused. Role lives on `users.role` text col. |
| `memberships` | 5 | Teacher ↔ school link. Has role + status enums. |
| `invitations` | 2 | Pending teacher invites. Token-based, 7-day expiry. |
| `schools` | 7 | Legacy school table. Still referenced by `users.school_id`. |

### 2. Billing — Chapter-level (CURRENT system)

| Table | Rows | Purpose |
|---|---|---|
| `biz_chapters` | 561 | FFA chapters / schools — the billing customer. |
| `biz_subscriptions` | 2 | Active subscriptions per chapter. Tier + Stripe IDs. |
| `biz_products_plans` | 3 | Available plans (tier × school year). Stripe price IDs. |
| `biz_invoices` | 3 | Annual invoices. Has `status`, `due_date`, `grace_period_days`. |
| `biz_invoice_line_items` | — | Line items per invoice. |
| `biz_payments` | 1 | Recorded payments tied to invoices. |
| `biz_failed_payment_attempts` | — | Failed Stripe charges. |
| `biz_customer_tax_settings` | — | Per-chapter tax config. |
| `biz_financials` | — | Aggregated financial snapshots. |

### 3. Billing — School-level (LEGACY)

| Table | Rows | Purpose |
|---|---|---|
| `subscriptions` | 7 | Old school-level subs. Default plan: `professional` @ $450/yr. |

### 4. Classroom & Learning

| Table | Rows | Purpose |
|---|---|---|
| `classrooms` | 9 | Teacher-created classrooms with `join_code` + `contest_type`. |
| `classroom_members` | 6 | Student ↔ classroom join. |
| `student_assignments` | — | Student-level assignments. |
| `assessments` | — | Teacher-built assessments. |
| `assessment_questions` | — | Questions in an assessment. |
| `assessment_assignments` | — | Assessment ↔ classroom assignments. |

### 5. Practice & Quiz Engine

| Table | Rows | Purpose |
|---|---|---|
| `practice_sessions` | 9 | One session = one quiz attempt. |
| `question_responses` | 0 | Per-question answers within a session. |
| `questions` | 80 | Question bank (legacy — RAG generates dynamically now). |
| `contests` | 40 | CDE/LDE definitions. |
| `contest_events` | — | Scheduled contest events for a classroom. |

### 6. Specialized Modules

| Table | Rows | Purpose |
|---|---|---|
| `livestock_drills` | 92 | Livestock judging drill content. |
| `livestock_contest_sessions` | — | Live contest sessions. |
| `horse_lead_videos` | — | Horse lead-line judging videos. |
| `horse_lead_progress` | — | Per-student progress on horse-lead. |
| `horse_lead_responses` | — | Per-video judging responses. |
| `video_submissions` | — | Generic video submissions for a contest. |

### 7. CRM & Sales

| Table | Rows | Purpose |
|---|---|---|
| `crm_contact_notes` | — | Sales notes per chapter. |
| `crm_followups` | — | Followup queue per chapter. |
| `chapter_goals` | — | Chapter-set goals. |
| `chapter_results` | — | Contest results rolled up per chapter. |
| `chapter_usage` | — | Per-chapter usage metrics. |

### 8. Knowledge & RAG

| Table | Rows | Purpose |
|---|---|---|
| `knowledge_documents` | 20,987 | pgvector chunks (3072-dim halfvec HNSW). **~390 MB.** Backs all RAG quiz + Brain. 100% taxonomy-classified after 2026-05-16 backfill — `contest_category` (e.g. `Livestock`, `Forestry`, `FFA Knowledge`, `App Meta`) + `subcategory` + `classified_by` ∈ {`heuristic`, `llm`}. |
| `classification_failures` | 12,015 | Backfill log: rows the heuristic + LLM rejected as `low_confidence` or `no_contest`. Drives Phase 3 LLM-fallback work. |

**RPCs:**
- `match_knowledge(query_embedding, …)` — legacy v1, returns `{context, sources}` string. Still wired to `lib/ai/rag-quiz.ts` fallback + media path.
- `match_knowledge_v2(query_embedding, match_count, filter_category, filter_event, exclude_source_paths)` — Brain v2 path. Soft category boost.
- `match_knowledge_v3(query_embedding, match_count, filter_category, filter_subcategory, filter_event, strict_category, exclude_source_paths)` — Brain v3. Hard `strict_category` filter with 8× ANN widening + `+0.04` subcategory boost.

### 9. Activity & Telemetry

| Table | Rows | Purpose |
|---|---|---|
| `student_activity_logs` | 170 | Student app actions. |
| `feature_engagement` | 23 | Per-feature usage tracking. |
| `user_progress` | 4 | Per-user progress snapshots. |
| `user_stats` | — | Aggregated user stats. |
| `email_log` | 102 | Outbound email log. |
| `webhook_log` | 46 | Inbound webhook log (Stripe etc). |
| `admin_audit_log` | 29 | Admin action audit trail. |
| `brain_verification_misses` | 0 | Brain chatbot verification-gate rejections. RLS: owner SELECT/UPDATE, superadmin SELECT, authenticated INSERT own rows. |

### 10. Tier & Config

| Table | Rows | Purpose |
|---|---|---|
| `tier_config` | 3 | Tier limits — tokens/month, requests/month, cost/token. |

### 11. Support

| Table | Rows | Purpose |
|---|---|---|
| `support_tickets` | — | Support ticket headers. |
| `support_messages` | — | Messages within a ticket. |

---

## Key foreign key relationships

```
schools (legacy)
  ├── users.school_id
  ├── memberships.school_id
  ├── invitations.school_id
  ├── subscriptions.school_id
  └── biz_chapters.school_id          ← bridge between systems

biz_chapters (current billing customer, PK = chapter_id)
  ├── biz_subscriptions.chapter_id
  ├── biz_invoices.chapter_id
  ├── biz_payments.chapter_id
  ├── biz_customer_tax_settings.chapter_id
  ├── biz_failed_payment_attempts.chapter_id
  ├── biz_financials.chapter_id
  ├── chapter_usage.chapter_id
  ├── crm_contact_notes.chapter_id
  ├── crm_followups.chapter_id
  └── feature_engagement.chapter_id

biz_invoices
  ├── biz_invoice_line_items.invoice_id
  ├── biz_payments.invoice_id
  └── biz_failed_payment_attempts.invoice_id

users (PK = id, mirrors auth.users.id)
  ├── memberships.user_id
  ├── practice_sessions.user_id
  ├── question_responses.user_id
  ├── student_activity_logs.user_id
  ├── student_assignments.student_id
  ├── horse_lead_progress.student_id
  ├── horse_lead_responses.student_id
  ├── livestock_contest_sessions.user_id
  ├── video_submissions.user_id
  ├── user_progress.user_id
  ├── assessments.teacher_id
  ├── contest_events.teacher_id
  └── invitations.invited_by

classrooms (PK = id)
  ├── classroom_members.classroom_id
  ├── student_assignments.classroom_id
  ├── assessment_assignments.classroom_id
  ├── contest_events.classroom_id
  ├── livestock_contest_sessions.classroom_id
  └── student_activity_logs.classroom_id

contests (PK = id)
  ├── questions.contest_id
  └── video_submissions.contest_id

practice_sessions (PK = id)
  ├── question_responses.session_id
  └── video_submissions.session_id

assessments (PK = id)
  ├── assessment_questions.assessment_id
  ├── assessment_assignments.assessment_id
  └── student_assignments.assessment_id
```

---

## Column reference — admin-relevant tables

### `users` (46 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | uuid | NO | — (mirrors auth.users.id) |
| email | text | NO | — |
| name | text | NO | — |
| role | text | YES | `'student'` |
| school_id | uuid | YES | → `schools.id` |
| grade_level | integer | YES | — |
| avatar_url | text | YES | — |
| total_practice_time | integer | YES | 0 |
| total_sessions | integer | YES | 0 |
| created_at | timestamptz | YES | `now()` |
| updated_at | timestamptz | YES | `now()` |
| push_token | text | YES | — |

### `subscriptions` (7 rows — LEGACY)

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | uuid | NO | `uuid_generate_v4()` |
| school_id | uuid | NO | → `schools.id` |
| plan | text | YES | `'professional'` |
| price_cents | integer | YES | `45000` |
| status | text | YES | `'active'` |
| stripe_customer_id | text | YES | — |
| stripe_subscription_id | text | YES | — |
| current_period_start | timestamptz | YES | — |
| current_period_end | timestamptz | YES | — |
| created_at | timestamptz | YES | `now()` |
| updated_at | timestamptz | YES | `now()` |

### `biz_subscriptions` (2 rows — CURRENT)

| Column | Type | Nullable | Default |
|---|---|---|---|
| subscription_id | uuid | NO | `gen_random_uuid()` |
| chapter_id | uuid | YES | → `biz_chapters.chapter_id` |
| tier_level | text | NO | — |
| status | text | NO | `'Pending PO'` |
| renewal_date | date | YES | — |
| stripe_subscription_id | text | YES | — |
| stripe_customer_id | text | YES | — |
| created_at | timestamptz | NO | `now()` |
| updated_at | timestamptz | NO | `now()` |

### `biz_chapters` (561 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| chapter_id | uuid | NO | `gen_random_uuid()` |
| chapter_name | text | NO | — |
| area_district | text | YES | — |
| primary_advisor_name | text | YES | — |
| advisor_email | text | YES | — |
| phone_number | text | YES | — |
| owner_id | uuid | YES | — |
| lead_stage | text | YES | `'trial'` |
| trial_started_at | timestamptz | YES | — |
| ffa_area | text | YES | — |
| lead_source | text | YES | — |
| school_id | uuid | YES | → `schools.id` |
| target_tier | text | YES | — |
| created_at | timestamptz | NO | `now()` |
| updated_at | timestamptz | NO | `now()` |

### `biz_invoices` (3 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| invoice_id | uuid | NO | `gen_random_uuid()` |
| chapter_id | uuid | NO | → `biz_chapters.chapter_id` |
| subscription_id | uuid | YES | → `biz_subscriptions.subscription_id` |
| plan_id | uuid | YES | → `biz_products_plans.plan_id` |
| invoice_type | text | NO | `'annual_subscription'` |
| school_year | text | NO | — |
| issue_date | date | NO | — |
| due_date | date | NO | — |
| grace_period_days | integer | NO | `30` |
| status | text | NO | `'open'` |
| amount_due | numeric | NO | `0` |
| currency | text | NO | `'usd'` |
| stripe_invoice_id | text | YES | — |
| stripe_customer_id | text | YES | — |
| idempotency_key | text | NO | — |
| paid_at | timestamptz | YES | — |
| created_at | timestamptz | NO | `now()` |
| updated_at | timestamptz | NO | `now()` |

### `biz_payments` (1 row)

| Column | Type | Nullable | Default |
|---|---|---|---|
| payment_id | uuid | NO | `gen_random_uuid()` |
| invoice_id | uuid | YES | → `biz_invoices.invoice_id` |
| chapter_id | uuid | YES | → `biz_chapters.chapter_id` |
| stripe_invoice_id | text | YES | — |
| stripe_payment_intent_id | text | YES | — |
| stripe_charge_id | text | YES | — |
| amount_paid | numeric | NO | — |
| currency | text | NO | `'usd'` |
| paid_at | timestamptz | NO | `now()` |
| created_at | timestamptz | NO | `now()` |

### `biz_products_plans` (3 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| plan_id | uuid | NO | `gen_random_uuid()` |
| tier_level | text | NO | — |
| school_year | text | NO | — |
| display_name | text | NO | — |
| stripe_price_id | text | YES | — |
| unit_amount_cents | integer | NO | — |
| currency | text | NO | `'usd'` |
| billing_month | integer | NO | `9` |
| grace_period_days | integer | NO | `30` |
| is_active | boolean | NO | `true` |

### `memberships` (5 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | uuid | NO | `gen_random_uuid()` |
| school_id | uuid | NO | → `schools.id` |
| user_id | uuid | NO | → `users.id` |
| role | enum `membership_role` | NO | `'member'` |
| status | enum `membership_status` | NO | `'active'` |
| created_at | timestamptz | NO | `now()` |
| updated_at | timestamptz | NO | `now()` |

### `invitations` (2 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | uuid | NO | `gen_random_uuid()` |
| school_id | uuid | NO | → `schools.id` |
| email | text | NO | — |
| role | enum `membership_role` | NO | `'member'` |
| token | text | NO | hex(24) |
| invited_by | uuid | NO | → `users.id` |
| expires_at | timestamptz | NO | `now() + 7 days` |
| accepted_at | timestamptz | YES | — |
| revoked_at | timestamptz | YES | — |
| created_at | timestamptz | NO | `now()` |

### `schools` (7 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | uuid | NO | `uuid_generate_v4()` |
| name | text | NO | — |
| city | text | YES | — |
| district | text | YES | — |
| area | text | YES | — |
| region | text | YES | — |
| state | text | YES | `'TX'` |
| advisor_name | text | YES | — |
| advisor_email | text | YES | — |
| subscription_status | text | YES | `'inactive'` |
| subscription_tier | text | YES | `'starter'` |
| max_students | integer | YES | `50` |

### `classrooms` (9 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| id | uuid | NO | `gen_random_uuid()` |
| teacher_id | uuid | NO | → `users.id` |
| name | text | NO | — |
| description | text | NO | `''` |
| contest_type | text | NO | `''` |
| join_code | text | NO | — |
| created_at | timestamptz | NO | `now()` |

### `tier_config` (3 rows)

| Column | Type | Nullable | Default |
|---|---|---|---|
| tier_level | text | NO | — |
| max_tokens_per_month | integer | NO | — |
| max_requests_per_month | integer | NO | — |
| cost_per_token | numeric | YES | `0.0002` |

---

## Custom enum types

- `membership_role` — used by `memberships.role` and `invitations.role`
- `membership_status` — used by `memberships.status`

(Run `SELECT * FROM pg_type WHERE typname IN ('membership_role','membership_status')` for current values.)

---

## How to regenerate this file

```bash
# Via Supabase MCP (in a Claude session):
1. list_tables(project_id='nkoyotdafqllgbpuklva', schemas=['public'], verbose=true)
2. SQL queries for: row counts, FKs, columns
3. Update this file

# Or via Supabase CLI on your machine:
npx supabase gen types typescript --project-id nkoyotdafqllgbpuklva > lib/types/supabase.ts
```

When you regenerate, update the **Captured** date at the top.
