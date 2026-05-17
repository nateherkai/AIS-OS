# Revenue Model — Ag Coach Pro

> Human-curated revenue and financial model.
> Generated 2026-05-16 from ag-coach-app/BUSINESS_BRAIN.md + CLAUDE.md + Pricing.md + dashboard/data/expenses.json

---

## Pricing Tiers (Annual Site Licenses)

| Tier | Price/yr | Seats | Credits | Best For |
|---|---|---|---|---|
| The Greenhand | $495 | 1 LDE team login + individual quiz logins | 5M | Small chapters, single-focus teams |
| The Blue & Gold | $895 | Greenhand + 40 CDE logins | 15M | Active chapters, multi-CDE |
| The Lone Star Elite | $1,495 | Unlimited | 40M | Large districts, high-volume programs |

**Add-on: Feed Bags** — 1M supplemental credits for $100. Rollover with active license. Usage alert at 80%.

Full tier details → [[../Pricing|Pricing.md]]

---

## Revenue Status (as of 2026-05-16)

**Active paying accounts:** 1 (Athens ISD — Lone Star Elite, renewal 2027-05-11, no Stripe subscription ID = likely invoiced manually)

**Trial accounts (14-day Blue & Gold):** 12+ chapters across multiple schools (Athens ISD teachers ×4, Keys FFA ×2, Ore City, Bonham, Elton, Rowlett, Ness City, Merritt, Borger, Comfort)

**Demo leads (pipeline):** 10+ chapters in Area 1 (West Texas)

**MailerLite list size:** Unknown — not yet integrated into AIOS

**Revenue goal:** $120K/yr ARR = threshold to leave teaching

**Revenue to get there:**
- At $895/yr (Blue & Gold): 134 schools
- At $1,495/yr (Lone Star Elite): 80 schools
- Mixed portfolio assumption: ~100 schools at avg $1,200 = $120K

---

## Monthly Costs (Ag Coach Pro Tech Stack)

| Service | Monthly |
|---|---|
| Claude Max | $130 |
| Anthropic API | $47.43 |
| OpenRouter | $34.14 |
| n8n Cloud | $25.58 |
| Supabase | $25 |
| Vercel | $20 |
| MailerLite | $15 |
| Firecrawl | $19 |
| Fal.ai | $10.66 |
| ElevenLabs | $5.27 |
| **Total tech** | **~$332/mo** |

**Break-even on tech:** ~1 Blue & Gold school account covers monthly tech costs.

---

## LTV / Churn Assumptions (Draft)

- Annual billing = no monthly churn risk
- Expected renewal rate: Unknown (no data yet)
- Target renewal rate: ≥80%
- LTV at 80% renewal, $895/yr: ~$4,475 over 5 years
- At 100 schools: $89,500 year 1 → ~$71,600 year 2 (80% renewal)

---

## Path to $120K Target

1. Close 50+ schools at Blue & Gold ($895) = $44,750 first year
2. Upsell 20+ to Lone Star Elite ($1,495) = additional $12,000
3. Add Feed Bags revenue
4. Expand to other states after Texas traction
5. Year 2: renewals + new accounts

---

## Billing Infrastructure

- Stripe handles annual invoices + PO support
- `biz_*` tables are billing source of truth (since 2026-05-09)
- Trial: 14-day Blue & Gold, no card required, automatic via `start-trial` edge fn
- Renewal: Stripe invoice → `stripe-webhook` → `biz_subscriptions` update
- Onboarding v2 (shipped 2026-05-15): n8n killed; all signup/trial/notify in repo

---

## Related

- [[../Pricing|Pricing (public-facing)]]
- [[../../wiki/concepts/agcoach-pricing-tiers|Pricing Tiers Wiki]]
- [[../../wiki/concepts/agcoach-billing-systems|Billing Systems (dual biz_* vs legacy)]]
- [[../Sales-Pipeline/_Sales-Pipeline-Home|Sales Pipeline]]
- [[../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
