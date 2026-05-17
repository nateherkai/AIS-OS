---
name: agcoach-brand-v0-docs
type: source
tags: [ag-coach-pro, brand, design, style-guide, stale, conflict]
source_files: [raw/_ingested/2026-05-16-agcoach-brand-app-description.md, raw/_ingested/2026-05-16-agcoach-brand-style-guide.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Brand v0 docs (`docs/brand/`)

Two early brand artifacts: `app_description.md` (sales/lead-gen overview) + `brand_style_guide.md` (color/typography spec). Both describe the pre-rebrand **"Cyber-Agronomy"** identity.

## ⚠️ Conflict with current CLAUDE.md brand system

| Field | Brand v0 docs | Current CLAUDE.md |
|---|---|---|
| Primary | `#F2A900` Ag Gold (Linear orange) | `#001F4D` Navy |
| Secondary | `#00f2ff` Cyber Blue | `#D4A574` Gold |
| Background | `#000000` Pure Black | Dark glass (Theme + GlassEffect) |
| Voice | "Gamify the path", "data-driven, gamified experience" | "Authoritative Coach + Competitive Motivator" — **`gamified` is a forbidden term** |
| Iconography | Checkered-flag racing milestones | (not specified) |
| Typography | Inter sans-serif | Bold serif or sans-serif; navy metric numbers 32–48px |

Anyone using these docs as the brand reference will produce assets that violate the current rules in [[../concepts/agcoach-app-internal-skills-catalog|brand-voice-lint skill]] and [[agcoach-app-working-instructions|CLAUDE.md]]. Treat as historical.

## Original "Cyber-Agronomy" pitch (for context)

- Premium dark mode with glassmorphism (`rgba(255,255,255,0.1)` borders, background blurs).
- "Bridging the gap between traditional agricultural education and modern competitive standards through data-driven Advisor Intelligence."
- Imagery: photorealistic livestock + clean infographics + 20–28px rounded corners.
- Lead-gen hook: *"Winning isn't accidental—it's engineered. Give your chapter the Ag Coach Pro edge and turn every contest into a data-driven victory."*

## Surviving elements

- Dark theme aesthetic (current is "dark glass," still dark).
- "Advisor Intelligence" naming (still the analytics surface).
- "High-Fidelity Visuals" / photorealistic livestock anatomy.

## Recommendation

Either rewrite both files to match current rules, or delete and rely on CLAUDE.md + the `brand-identity` dev skill. Leaving as-is risks copy-paste regression in marketing assets.

## Related

- [[agcoach-landing-page-guardrails|Landing Page Guardrails]]
- [[agcoach-app-working-instructions|App Working Instructions (CLAUDE.md)]]
- [[../concepts/agcoach-app-internal-skills-catalog|App Internal Skills Catalog]] (brand-identity + brand-voice-lint)
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
