---
name: agcoach-findings
type: source
tags: [ag-coach-pro, architecture, findings, constraints, ai-integration]
source_files: [raw/_ingested/2026-05-16-agcoach-findings.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Findings Notes

Architecture discoveries and constraints captured during the B.L.A.S.T. Architect phase.

## Existing Architecture (Confirmed)

- **Framework**: Expo (React Native / Web) with `expo-router`
- **Primary Logic**: `app/practice` (UI), `lib/store` (State — Zustand), `lib/scoring` (Deterministic logic)
- **AI Integrations**: Gemini (`lib/ai/gemini.ts`) and Claude (`lib/ai/claude.ts`) for grading/content
- **State Management**: Zustand with persistence for module-specific data (e.g., `job-interview`)
- **Styles**: `constants/theme.ts` (Theme) and `GlassEffect` used throughout for premium UI

## North Star

Build a comprehensive training tool with high-fidelity simulations that strictly adhere to official **FFA Rules and Rubrics**.

## Key Discoveries

- **Job Interview Module**: Recently restored. Fully functional with document prep, phone sim, and video sim.
- **Spanish Creed Speaking**: Placeholder file found. Needs implementation following FFA Creed rubrics.
- **Nursery & Landscape ID**: Ongoing work found in `app/practice/nursery-landscape-id`.

## Constraints

- **FFA Strictness**: No deviation from official rules/rubrics unless explicitly directed.
- **Claude Integration**: Anthropic (Claude) is a required integration for secondary processing/backups.
- **Platform Limitation**: Native video recording via `MediaRecorder` is unavailable on mobile.

## Related

- [[../sources/agcoach-progress-log|Progress Log]]
- [[../sources/agcoach-app-working-instructions|App Working Instructions]]
- [[../sources/agcoach-business-brain|Business Brain]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
