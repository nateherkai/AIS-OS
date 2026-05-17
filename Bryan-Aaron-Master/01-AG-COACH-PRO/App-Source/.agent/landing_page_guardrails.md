# Landing Page Guardrails

To ensure the landing page design remains consistent and untouched, follow these rules:

1. **NO CHANGES to `components/landing/`**: Do not modify any files in this directory (e.g., `LandingPage.tsx`, `Hero.tsx`, `Packages.tsx`) unless explicitly requested by the user for a design update.
2. **Visual Consistency**: High-level visual components like the 3D Canvas, lighting, typography, and brand-specific hex codes in `constants/theme.ts` must remain static.
3. **No Safety UI Overlays**: Do not add "stuck detection" or "error fallback" UI that overlays or interrupts the landing page flow.
4. **Initialization Logic**: Keep authentication initialization (`initialize`) separate from the visual rendering of the landing page.

By following these rules, we protect the premium, custom-built design of the landing page while continuing to optimize underlying performance.
