---
name: stripe
type: organization
tags: [stripe, payments, billing, invoices, saas, infrastructure]
source_files: [raw/_ingested/2026-05-16-agcoach-BUSINESS_BRAIN.md, raw/_ingested/2026-05-16-agcoach-SCHEMA.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Stripe

Payment processing platform for Ag Coach Pro's annual school subscriptions.

## Role in Ag Coach Pro

- Handles card payments for annual site licenses
- Annual invoices generated in September
- Stripe sync writes to `biz_*` tables (legacy `subscriptions`/`schools` grandfathered)
- Stripe IDs stored in: `biz_subscriptions.stripe_subscription_id`, `biz_subscriptions.stripe_customer_id`, `biz_invoices.stripe_invoice_id`

## Webhook Architecture

- `stripe-webhook` edge function processes all invoice/payment events
- Idempotent via `stripe_event_log` (INSERT ON CONFLICT DO NOTHING keyed on `stripe_event_id`)
- Failed processing: row deleted so next retry re-runs fresh
- Tombstones after `MAX_RETRY_ATTEMPTS = 5` to stop 72h retry storm
- Role promotion goes through `pending_role_promotions` outbox — never direct admin API in webhook hot path

## Trial → Paid Flow

Trial → superadmin confirms PO or Stripe payment → `stripe-reconcile` (runs every 15m) syncs status → `drain-role-promotions` (runs every 5m) promotes role.

## PO Support

Schools commonly pay by purchase order (standard for school districts). PO tracked in `biz_invoices`; 30-day grace period before access suspension.

## Related

- [[../concepts/agcoach-billing-systems|Billing Systems]]
- [[../concepts/agcoach-pricing-tiers|Pricing Tiers]]
- [[../sources/agcoach-schema|Database Schema]]
- [[../organizations/supabase|Supabase]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
