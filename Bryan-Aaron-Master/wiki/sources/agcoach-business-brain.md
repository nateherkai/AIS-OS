---
name: agcoach-business-brain
type: source
tags: [ag-coach-pro, business, strategy, revenue, users, features, architecture]
source_files: [raw/_ingested/2026-05-16-agcoach-BUSINESS_BRAIN.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Business Brain

Comprehensive business-level reference for product, monetization, users, features, and architecture.

## What Is AgCoachPro?

AI-powered FFA contest training platform for Texas FFA students and ag teachers. Replaces manual study packets and coaching sessions with an app that generates unlimited practice quizzes, grades video speeches with AI, evaluates livestock phenotypes with computer vision, and gives teachers real-time readiness dashboards.

- **Target market**: ~20,000 students across ~400 Texas FFA chapters
- **Platform**: iOS, Android, Web (Expo Router 4 / React Native)
- **Domain**: agcoachpro.com (hosted on Vercel)

## The FFA Contest World

FFA has two contest types:
- **CDE (Career Development Events)** — Technical contests: Livestock Judging, Meats Evaluation, Dairy Cattle, Veterinary Science, Forestry, etc. (29 CDEs in app)
- **LDE (Leadership Development Events)** — Presentation contests: Creed Speaking, Job Interview, Chapter Conducting, etc. (11 LDEs in app)

Students compete at district → area → state level. A winning CDE team can qualify for nationals.

## User Roles

| Role | Who | What |
|------|-----|------|
| student | FFA members | Practice CDEs/LDEs, track XP/level/streak, complete assignments |
| teacher | Ag advisors | Manage classrooms, view analytics, set chapter goals |
| superadmin | Internal ops | School subscriptions, billing, feature overrides |

- Auth providers: Email/password, Google OAuth, Clever OAuth
- Student onboarding: 500 free credits on signup, no card required
- Teacher onboarding: 14-day free trial on Blue & Gold tier automatically

## AI Features

1. **RAG Quiz Generation** — semantic query → pgvector → Gemini Flash → QuizQuestion[]
2. **Livestock Phenotype Analyzer** — computer vision, scores muscle/structure/volume/balance/condition
3. **Ag Skills / LDE Video Scorer** — 1,000-point rubric (Introduction 100, Performance 550, Communication 250, Summary 100)
4. **Job Interview AI Scorer** — parses resumes/cover letters, evaluates against FFA criteria

AI models: Google Gemini 2.0 Flash (primary), gemini-embedding-2-preview 3072-dim (embeddings), Anthropic Claude (secondary).

## Teacher Portal (19 Screens — `app/(admin)/`)

Dashboard, Assessments, Analytics, Intelligence, Classroom, Students, Chapter Goals, Events/Calendar, Livestock Upload, Livestock Scores, CDE Materials, Image Library, Subscription, Answer Key Editor.

## Student Dashboard (6 Tabs)

Home (XP, streak, stats), CDE, LDE, Premier Chapter, Profile.

**Gamification**: XP per session (weighted by score), level = `floor(sqrt(xp/100)) + 1`, 5-day streak = 2× XP multiplier.

## Practice Module Architecture

Each CDE has 4 screens under `app/practice/[module]/`:
- `index.tsx` — Hub
- `builder.tsx` — topic/count/format pickers
- `quiz.tsx` — live quiz engine
- `flashcards.tsx` — flip-card study mode

## External Services

Supabase (DB/Auth/pgvector), Google Gemini API, Anthropic Claude API, Stripe, Clever OAuth, Resend, Vercel, Expo.

## Edge Functions (9 Total)

match-knowledge, gemini-proxy, anthropic-proxy, clever-auth, create-payment-intent, stripe-webhook, generate-annual-invoices, notify-assignment, process-support-email.

## Billing Model

- Annual invoice per school, sent September
- 30-day grace period before access suspended
- PO support — schools pay by purchase order
- Tax exempt tracking for districts
- Trial → Active: superadmin confirms PO or payment received

## Known Gaps / Active Backlog

1. Food Science — 851-line monolith, needs split into 4 screens
2. Ag Advocacy + Ag Issues — stub modules
3. Phenotype Drill — needs DB migration + upload UI + 3-view switcher
4. TOPIC_QUERIES gaps — Entomology, Nursery/Landscape, Poultry, Vet Science, Wildlife, Wool, Job Interview, Creed Speaking

## Related

- [[../concepts/agcoach-pricing-tiers|Pricing Tiers]]
- [[../concepts/agcoach-contest-modules|Contest Modules (40 Total)]]
- [[../concepts/agcoach-rag-architecture|RAG Architecture]]
- [[../sources/agcoach-schema|Database Schema]]
- [[../sources/agcoach-app-working-instructions|App Working Instructions]]
- [[../organizations/supabase|Supabase]]
- [[../organizations/vercel|Vercel]]
- [[../organizations/stripe|Stripe]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
