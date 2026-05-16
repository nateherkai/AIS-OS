---
name: agcoach-readme
type: source
tags: [ag-coach-pro, setup, development, quickstart, tech-stack]
source_files: [raw/_ingested/2026-05-16-agcoach-README.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — README (Starter)

Developer quickstart and project structure documentation. Reflects initial scaffold state; current architecture is more evolved.

## Quick Start

1. Install Node.js (v18+), Git, Expo CLI
2. `npm install`
3. Create Supabase project, copy URL + anon key to `.env`
4. `npm run db:setup` (runs migrations)
5. `npm start` → scan QR with Expo Go

## Key Commands

```bash
npm start          # Expo dev server
npm run web        # Web only
npm run ios        # iOS simulator
npm run android    # Android emulator
npm run db:migrate # Apply new migrations
npm test           # Jest
```

## Core Project Structure

```
app/          — Expo Router screens
  (auth)/     — login, signup
  (tabs)/     — home, cde, lde, profile
  contest/    — dynamic [id].tsx routing hub
lib/          — AI, store, scoring, navigation
components/   — reusable UI
supabase/     — migrations, edge functions, config
constants/    — theme, contests, colors, rules
```

## Environment Variables

- `EXPO_PUBLIC_SUPABASE_URL`
- `EXPO_PUBLIC_SUPABASE_ANON_KEY`
- `OPENAI_API_KEY` (for Whisper speech-to-text)
- `ANTHROPIC_API_KEY` (for Claude feedback)

*Note: Current production uses Gemini as primary AI; Anthropic is secondary. See [[../sources/agcoach-app-working-instructions|App Working Instructions]] for current rules.*

## Related

- [[../sources/agcoach-project-summary|Project Summary]]
- [[../sources/agcoach-app-working-instructions|App Working Instructions]]
- [[../sources/agcoach-schema|Database Schema]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
