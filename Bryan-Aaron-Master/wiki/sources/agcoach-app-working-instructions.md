---
name: agcoach-app-working-instructions
type: source
tags: [ag-coach-pro, architecture, rules, development, rag, supabase]
source_files: [raw/_ingested/2026-05-16-agcoach-CLAUDE.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — App Working Instructions (CLAUDE.md)

Authoritative operating rules for every Claude session touching the Ag Coach Pro codebase. Any rule here overrides defaults.

## Purpose

AgCoachPro is an AI-powered FFA CDE/LDE training platform for Texas FFA students and teachers. Stack: Expo Router 4 / React Native / Supabase / TypeScript / Gemini AI.

**Why it exists:** Texas FFA teachers cannot give 24/7 CDE feedback at scale. Students lack rubric-grounded practice between contests.

**Done looks like:** Annual site-license revenue from chapters (Greenhand / Blue & Gold / Lone Star Elite).

**Out of scope:** Social feed, friend leaderboards, non-Texas state standards, gamified XP/badges.

## Key Architecture Rules

- Never modify the database schema directly — always write a migration file.
- Schema source of truth: `SCHEMA.md` — read before any query, view, RPC, or skill.
- AI prompts belong in `lib/prompts/` — one file per domain.
- Every new CDE module needs: routing block in `app/contest/[id].tsx`, tier mapping in `lib/tier.ts`, and `is_active: true` in `constants/contests.ts`.
- Never use `router.back()` on deep-linkable screens — use `safeBack()` from `lib/navigation.ts`.
- Never use light backgrounds — all screens use dark glass aesthetic from `constants/theme.ts`.
- Never gate Edge Function proxies on JWT shape — Supabase anon keys are `sb_publishable_...` format.
- Role promotion goes through the outbox (`pending_role_promotions`) — never call `auth.admin.updateUserById` in webhook hot paths.
- Stripe webhook is idempotent at the gate via `stripe_event_log`.
- `.catch()` on PostgREST builders is forbidden — always use `try { await supabase... } catch {}`.
- Ops notifications via `notifyOps` in `supabase/functions/_shared/notifyOps.ts` (Resend + Telegram Gravity Claw).

## Route Groups

- `(auth)` → unauthenticated
- `(tabs)` → students
- `(admin)` → teachers
- `(super-admin)` → internal ops

## Live Infra IDs

- Supabase: `nkoyotdafqllgbpuklva` (us-west-2, PG17)
- Vercel: `prj_4xPOIb5yS0qzoJFmLstwRURR9KC9`
- Production URL: https://www.agcoachpro.com

## Recent Decisions (Key)

- 2026-05-16 — Brain Accuracy v1 shipped: Gemini Flash intent classifier → taxonomy → strict_category RAG routing.
- 2026-05-16 — Brain v3 (taxonomy-aware retrieval): `match_knowledge_v3` RPC with hard `strict_category` filter.
- 2026-05-15 — Brain v2 (Second Brain): chip-less unified retrieval, Gemini function-calling with 6 tools.
- 2026-05-15 — Onboarding v2: n8n killed, all signup/purchase/trial/notify/CRM lives in repo.
- 2026-05-09 — `biz_*` billing tables are current source of truth; legacy `subscriptions`/`schools` grandfathered.
- 2026-03 — RAG = Supabase pgvector (`knowledge_documents`, 768→3072-dim) via `match-knowledge` edge fn.

## Session Protocol

End every session with `/wrapup` → saves memories + pushes to AI Brain notebook (ID: `ba26ba14-ac37-4ce8-acea-f00ea2d9dc50`).

## Related

- [[../concepts/agcoach-pricing-tiers|Pricing Tiers]]
- [[../concepts/agcoach-rag-architecture|RAG Architecture]]
- [[../sources/agcoach-schema|Database Schema]]
- [[../sources/agcoach-business-brain|Business Brain]]
- [[../concepts/agcoach-app-internal-skills-catalog|Skills Catalog]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
