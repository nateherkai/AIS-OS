---
name: agcoach-billing-systems
type: concept
tags: [ag-coach-pro, billing, supabase, stripe, legacy, biz-tables]
source_files: [raw/_ingested/2026-05-16-agcoach-SCHEMA.md, raw/_ingested/2026-05-16-agcoach-BUSINESS_BRAIN.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Dual Billing Systems

The single biggest gotcha in the codebase. Two billing systems coexist; do not mix them.

## Current System: Chapter-Level (`biz_*` tables)

| Table | Purpose |
|---|---|
| `biz_chapters` (561 rows) | FFA chapters — the billing customer |
| `biz_subscriptions` (2 rows) | Active subscriptions per chapter, tier + Stripe IDs |
| `biz_products_plans` (3 rows) | Available plans (tier × school year), Stripe price IDs |
| `biz_invoices` (3 rows) | Annual invoices with status, due_date, grace_period_days |
| `biz_invoice_line_items` | Line items per invoice |
| `biz_payments` (1 row) | Recorded payments tied to invoices |
| `biz_failed_payment_attempts` | Failed Stripe charges |
| `biz_customer_tax_settings` | Per-chapter tax config |
| `biz_financials` | Aggregated financial snapshots |

**Rule: Use `biz_*` for any new admin or billing work.**

## Legacy System: School-Level

| Table | Purpose |
|---|---|
| `subscriptions` (7 rows) | Old school-level subs, default plan: `professional` @ $450/yr |
| `schools` (7 rows) | Legacy school table; still referenced by `users.school_id` |

Kept around for legacy users and the `users.school_id` link. `biz_chapters.school_id` bridges the two systems.

## Billing Model

- Annual invoice per school, sent in September
- 30-day grace period before access suspended
- PO support — schools pay by purchase order (standard for school districts)
- Tax exempt tracking for districts
- Trial → Active: superadmin confirms PO or payment received

## Stripe Webhook Rules

- Idempotent at the gate: first op after sig verify is `INSERT ... ON CONFLICT DO NOTHING` into `stripe_event_log` keyed on `stripe_event_id`
- On processing failure, row is DELETED so next retry re-runs fresh
- Tombstone after `MAX_RETRY_ATTEMPTS = 5` to stop Stripe's 72h retry storm

## Role Promotion

Never call `auth.admin.updateUserById` for role changes in webhook hot paths. Insert into `pending_role_promotions`; the `drain-role-promotions` cron (every 5m) + `stripe-reconcile` (every 15m) handle the admin API call.

## Trial System

- `start-trial` edge function with TOCTOU per-IP rate limit + repair path
- `trial-reminder` daily cron (14:00 UTC) — 7/3/1/0/-7-day milestones via `trial_reminder_log` idempotency
- `stripe-reconcile` — self-heals stale role promotions + canceled-drift

## Related

- [[../sources/agcoach-schema|Database Schema]]
- [[../concepts/agcoach-pricing-tiers|Pricing Tiers]]
- [[../organizations/stripe|Stripe]]
- [[../organizations/supabase|Supabase]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
