---
name: agcoach-landing-page-guardrails
type: source
tags: [ag-coach-pro, landing-page, design, guardrails, branding]
source_files: [raw/_ingested/2026-05-16-agcoach-landing-page-guardrails.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Landing Page Guardrails

Rules to keep the landing page design consistent and untouched.

## Rules

1. **No changes to `components/landing/`** — Do not modify `LandingPage.tsx`, `Hero.tsx`, `Packages.tsx`, or any file in this directory unless explicitly requested for a design update.
2. **Visual Consistency** — The 3D Canvas, lighting, typography, and brand-specific hex codes in `constants/theme.ts` must remain static.
3. **No Safety UI Overlays** — Do not add "stuck detection" or "error fallback" UI that overlays or interrupts the landing page flow.
4. **Initialization Logic** — Keep authentication initialization (`initialize`) separate from the visual rendering of the landing page.

## Why

The landing page uses a custom-built premium design. These rules protect it while allowing ongoing optimization of underlying performance without breaking the frontend.

## Related

- [[../sources/agcoach-agent-global-rules|Agent Global Rules]]
- [[../sources/agcoach-app-working-instructions|App Working Instructions]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
