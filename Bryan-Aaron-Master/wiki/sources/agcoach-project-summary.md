---
name: agcoach-project-summary
type: source
tags: [ag-coach-pro, project, overview, tech-stack, financial-model]
source_files: [raw/_ingested/2026-05-16-agcoach-PROJECT_SUMMARY.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Project Summary (Starter Code Delivery)

Early-stage starter code delivery document describing the initial scaffold for the FFA Training App. This predates current production state and used an older pricing model ($450/school/year flat vs current tiered model).

## What Was Delivered

Complete React Native (Expo) starter project with:
- 17 code files, 3 documentation files, full TypeScript, Expo Router navigation
- Authentication (email/password, session management, protected routes)
- Tab-based navigation: Dashboard, 29 CDEs, 11 LDEs, Profile
- 9 database tables, all 40 contests pre-configured
- Row-level security (RLS)
- FFA brand colors (#003366 Navy Blue)

## Tech Stack (Initial)

- React Native + Expo — single codebase for iOS, Android, Web
- Supabase — PostgreSQL + Auth + Storage (free tier → $25/month Pro)
- TypeScript — type safety
- Expo Router — file-based routing

## Financial Model (Early Projection — Now Superseded)

This document projected $450/school/year flat model. **Current pricing is tiered** — see [[../concepts/agcoach-pricing-tiers|Pricing Tiers]].

| Year | Schools | Revenue |
|------|---------|---------|
| 1 | 50 | $22,500 |
| 2 | 150 | $67,500 |
| 3 | 400 | $180,000 |
| Op costs | — | ~$1K/month at scale |

## Database Tables (Initial Schema — See SCHEMA.md for Current)

- `users`, `schools`, `subscriptions` — identity/billing
- `contests` — all 40 CDE/LDE definitions
- `practice_sessions`, `question_responses` — practice tracking
- `video_submissions` — LDE recordings
- `user_progress` — learning analytics

## Phase Roadmap (Historical)

- Phase 1: Creed Speaking LDE (video, speech-to-text, AI scoring)
- Phase 2: CDE Questions (quiz interface, timed practice, scoring)
- Phase 3: Teacher Dashboard (analytics, exports)
- Phase 4: All 40 events, competition mode, offline practice

## Design System

Navy #003366 (primary), Light Gray #f5f5f5 (background), Green #28a745 (success), Red #dc3545 (error).
Note: Current production uses dark glass theme — see app working instructions.

## Related

- [[../sources/agcoach-business-brain|Business Brain (current)]]
- [[../sources/agcoach-schema|Database Schema (current)]]
- [[../concepts/agcoach-pricing-tiers|Pricing Tiers]]
- [[../concepts/agcoach-contest-modules|Contest Modules]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
