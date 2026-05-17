## 🏗️ Existing Architecture
- **Framework**: Expo (React Native / Web) with `expo-router`.
- **Primary Logic**: Separated into `app/practice` (UI), `lib/store` (State - Zustand), and `lib/scoring` (Deterministic Logic).
- **AI Integrations**: Gemini (`lib/ai/gemini.ts`) and Claude (`lib/ai/claude.ts`) for grading and content generation.
- **State Management**: Zustand with persistence for module-specific data (e.g., `job-interview`).
- **Styles**: `constants/theme.ts` (Theme) and `GlassEffect` used throughout for premium UI.

## 🎯 North Star
Build out a comprehensive training tool with high-fidelity simulations that strictly adhere to official **FFA Rules and Rubrics**.

## 🚀 Research & Discoveries
- **Job Interview Module**: Recently restored. Fully functional with document prep, phone sim, and video sim.
- **Spanish Creed Speaking**: Placeholder file found. Needs implementation following FFA Creed rubrics.
- **Nursery & Landscape ID**: Ongoing work found in `app/practice/nursery-landscape-id`.

## ⚠️ Constraints
- **FFA Strictness**: No derivation from official rules/rubrics unless explicitly directed.
- **Integration**: Anthropic (Claude) is a required integration for secondary processing/backups.
- **Platform Limitation**: Native video recording via `MediaRecorder` is unavailable on mobile.
