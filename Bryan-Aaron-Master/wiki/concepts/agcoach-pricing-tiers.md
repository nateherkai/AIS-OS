---
name: agcoach-pricing-tiers
type: concept
tags: [ag-coach-pro, pricing, revenue, saas, subscription]
source_files: [raw/_ingested/2026-05-16-agcoach-CLAUDE.md, raw/_ingested/2026-05-16-agcoach-BUSINESS_BRAIN.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Pricing Tiers

Annual site licenses for Texas FFA chapters. Buyer = ag teacher/advisor. Users = FFA students.

## Three Tiers

| Tier | Price/Year | Seats | Credits | Best For |
|------|-----------|-------|---------|---------|
| **The Greenhand** | $495 | 1 login per LDE team + individual quiz logins | 5M | Small chapters or single-focus teams (Creed, Radio, etc.) |
| **The Blue & Gold** | $895 | Greenhand + 40 CDE logins | 15M | Active chapters with multiple LDE and CDE teams |
| **The Lone Star Elite** | $1,495 | Unlimited students | 40M | Large multi-teacher departments, high-volume programs |

## Tier-Specific Extras

- **Greenhand**: 24/7 AI feedback, LDE-specific modules, teacher progress tracking
- **Blue & Gold**: Full access to all Ag Coach modules, priority AI processing, enhanced teacher dashboard
- **Lone Star Elite**: Unlimited seats, custom chapter branding, white-glove technical support

## Add-On: Feed Bags

- 1M supplemental credits for $100
- Unused supplemental credits roll over as long as an active license is maintained
- Usage alert at 80% of credit allocation

## Teacher Trial

New teachers get 14-day free trial on Blue & Gold tier automatically. Requires chapter name, phone, and address. Billing via invoice after trial.

## Student Default

Students not in a classroom default to **Lone Star Elite** (full access) — intentional for demo/onboarding.

## Feature Gating

Logic lives in `lib/tier.ts → FEATURE_TIERS`. Every feature key maps to a minimum tier. The `chapter_feature_overrides` Supabase table allows time-bound overrides (e.g., grant a chapter Lone Star Elite for 30 days during a trial).

## Revenue Context

Bryan's target: $120K/year revenue to retire from teaching. At current tiered pricing:
- 85 Blue & Gold accounts = ~$76K
- Mix of 50 Lone Star Elite + 50 Blue & Gold = ~$119.5K

## Related

- [[../sources/agcoach-business-brain|Business Brain]]
- [[../sources/agcoach-app-working-instructions|App Working Instructions]]
- [[../concepts/agcoach-billing-systems|Billing Systems]]
- [[../organizations/stripe|Stripe]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
