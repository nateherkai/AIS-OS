---
name: agcoach-schema
type: source
tags: [ag-coach-pro, database, supabase, schema, tables, billing]
source_files: [raw/_ingested/2026-05-16-agcoach-SCHEMA.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Supabase Schema

**Project:** `nkoyotdafqllgbpuklva` | Region: us-west-2 | Postgres 17.6.1 | 47 public tables | Captured: 2026-04-26

## Critical: Two Billing Systems

The biggest gotcha — do not mix them.

| | Legacy (school-level) | Current (chapter-level) |
|---|---|---|
| Subscription table | `subscriptions` | `biz_subscriptions` |
| Owner table | `schools` | `biz_chapters` |
| Invoicing | None | `biz_invoices` + line items |
| Stripe-aware | Partial | Full |
| Rows today | 7 subs / 7 schools | 2 subs / 561 chapters |

**Use `biz_*` tables for any new admin or billing work.**

## Tables by Domain

### Identity & Access
- `users` (46) — App users, mirrors `auth.users.id`
- `memberships` (5) — Teacher ↔ school link, role + status enums
- `invitations` (2) — Pending teacher invites, token-based, 7-day expiry
- `schools` (7) — Legacy; still referenced by `users.school_id`

### Billing — Chapter-level (CURRENT)
- `biz_chapters` (561) — FFA chapters / billing customer
- `biz_subscriptions` (2) — Active subscriptions per chapter, tier + Stripe IDs
- `biz_products_plans` (3) — Available plans (tier × school year), Stripe price IDs
- `biz_invoices` (3) — Annual invoices with `status`, `due_date`, `grace_period_days`
- `biz_invoice_line_items` — Line items per invoice
- `biz_payments` (1) — Recorded payments
- `biz_failed_payment_attempts` — Failed Stripe charges
- `biz_customer_tax_settings` — Per-chapter tax config
- `biz_financials` — Aggregated financial snapshots

### Billing — School-level (LEGACY)
- `subscriptions` (7) — Old school-level subs, default plan: `professional` @ $450/yr

### Classroom & Learning
- `classrooms` (9) — Teacher-created with `join_code` + `contest_type`
- `classroom_members` (6) — Student ↔ classroom join
- `assessments`, `assessment_questions`, `assessment_assignments` — Teacher-built tests
- `student_assignments` — Student-level assignments

### Practice & Quiz Engine
- `practice_sessions` (9) — One session = one quiz attempt
- `question_responses` (0) — Per-question answers
- `questions` (80) — Legacy question bank (RAG generates dynamically now)
- `contests` (40) — CDE/LDE definitions
- `contest_events` — Scheduled contest events

### Specialized Modules
- `livestock_drills` (92) — Livestock judging drill content
- `livestock_contest_sessions` — Live contest sessions
- `horse_lead_videos`, `horse_lead_progress`, `horse_lead_responses` — Horse lead-line judging
- `video_submissions` — Generic video submissions

### CRM & Sales
- `crm_contact_notes`, `crm_followups` — Sales notes/followup queue per chapter
- `chapter_goals`, `chapter_results`, `chapter_usage` — Goals, results, metrics

### Knowledge & RAG
- `knowledge_documents` (20,987) — pgvector chunks (3072-dim halfvec HNSW, ~390 MB). 100% taxonomy-classified as of 2026-05-16 backfill. Fields: `contest_category`, `subcategory`, `classified_by` ∈ {heuristic, llm}
- `classification_failures` (12,015) — Backfill log for low-confidence/rejected rows

**RPCs:**
- `match_knowledge` — legacy v1, returns string
- `match_knowledge_v2` — Brain v2, soft category boost
- `match_knowledge_v3` — Brain v3, hard `strict_category` filter with 8× ANN widening + `+0.04` subcategory boost

### Activity & Telemetry
- `student_activity_logs` (170), `feature_engagement` (23), `user_progress` (4)
- `email_log` (102), `webhook_log` (46), `admin_audit_log` (29)
- `brain_verification_misses` (0) — Brain chatbot rejection log

### Tier & Config
- `tier_config` (3) — Token/request limits + cost per token per tier

### Support
- `support_tickets`, `support_messages`

## Key FK Relationships

```
schools → users.school_id, memberships, invitations, subscriptions, biz_chapters.school_id
biz_chapters → biz_subscriptions, biz_invoices, biz_payments, chapter_usage, crm_*, feature_engagement
users → memberships, practice_sessions, question_responses, student_activity_logs, assessments, horse_lead_*
classrooms → classroom_members, student_assignments, assessment_assignments, contest_events, livestock_contest_sessions
```

## Related

- [[../sources/agcoach-business-brain|Business Brain]]
- [[../sources/agcoach-plan-supabase-admin|Supabase Admin Plan]]
- [[../concepts/agcoach-rag-architecture|RAG Architecture]]
- [[../concepts/agcoach-billing-systems|Billing Systems (Dual)]]
- [[../organizations/supabase|Supabase]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
