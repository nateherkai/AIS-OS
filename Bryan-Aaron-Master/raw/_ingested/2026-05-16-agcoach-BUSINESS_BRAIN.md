# AgCoachPro — Business Brain Document

> Hand this document to any Claude session working on this codebase. It covers product, monetization, users, features, and architecture at a business level.

---

## What Is AgCoachPro?

**AgCoachPro** is an AI-powered FFA (Future Farmers of America) contest training platform built for Texas FFA students and their ag teachers. It replaces manual study packets and coaching sessions with an app that generates unlimited practice quizzes, grades video speeches with AI, evaluates livestock phenotypes with computer vision, and gives teachers real-time readiness dashboards.

- **Target market**: ~20,000 students across ~400 Texas FFA chapters
- **Platform**: iOS, Android, and Web (Expo Router 4 / React Native)
- **Custom domain**: agcoachpro.com (hosted on Vercel)

---

## The FFA Contest World (Why This Exists)

FFA has two contest types:
- **CDE (Career Development Events)** — Technical contests: Livestock Judging, Meats Evaluation, Dairy Cattle, Veterinary Science, Forestry, etc. (29 CDEs in the app)
- **LDE (Leadership Development Events)** — Presentation contests: Creed Speaking, Job Interview, Chapter Conducting, Ag Issues Forum, etc. (11 LDEs in the app)

Students compete at district → area → state level. A winning CDE team can qualify for nationals. Teachers ("ag advisors") coach 20–100 students simultaneously across multiple contests. There is no standardized practice software — teachers historically use paper packets, Google Forms, or nothing.

AgCoachPro fixes this with AI-generated quiz banks, video coaching, and team analytics.

---

## User Roles

| Role | Who | What They Do |
|------|-----|-------------|
| **student** | FFA members | Practice CDEs/LDEs, track XP/level/streak, complete teacher assignments, submit video speeches |
| **teacher** | Ag advisors / chapter advisors | Manage classrooms, create assessments, view student analytics, upload contest scores, set chapter goals |
| **superadmin** | Internal ops (you) | Manage school subscriptions, apply feature overrides, view billing dashboard, invoice management |

**Auth providers**: Email/password, Google OAuth, Clever OAuth (school district SSO)

**Student onboarding**: 500 free credits on signup, no card required. Tier inherited from teacher's subscription.

**Teacher onboarding**: Full 14-day free trial on "The Blue & Gold" tier automatically. Requires chapter name, phone, and address. Billing kicks in via invoice after trial.

---

## Subscription Tiers (Annual Site License)

| Tier | Price/Year | Seats | Credits Included | Best For |
|------|-----------|-------|-----------------|---------|
| **The Greenhand** | $495 | 1 login per LDE team + individual quiz student logins | 5M | Small chapters or single-focus teams (Creed, Radio, etc.) |
| **The Blue & Gold** | $895 | Same as Greenhand + 40 CDE logins | 15M | Active chapters with multiple LDE and CDE teams |
| **The Lone Star Elite** | $1,495 | Unlimited students | 40M | Large multi-teacher departments and high-volume programs |

**Tier-specific extras**:
- Greenhand: 24/7 AI feedback, LDE-specific modules, teacher progress tracking
- Blue & Gold: Full access to all Ag Coach modules, priority AI processing, enhanced teacher dashboard
- Lone Star Elite: Unlimited seats, custom chapter branding, white-glove technical support

**Add-on credits ("Feed Bags")**: Any tier can purchase 1M supplemental credits for $100. Unused supplemental credits roll over to the next billing cycle as long as an active license is maintained.

**Usage alerts**: Advisors receive a notification at 80% of their credit allocation.

**Fair Use**: Lone Star Elite includes 40M annual base credits. Usage above this may trigger an account review or require supplemental credit blocks.

**Feature gate logic** lives in `lib/tier.ts → FEATURE_TIERS`. Every feature key maps to a minimum tier. The `chapter_feature_overrides` Supabase table allows time-bound overrides (e.g., grant a chapter "The Lone Star Elite" for 30 days during a trial).

Students not in a classroom default to **"The Lone Star Elite"** (full access) — intentional for demo/onboarding.

---

## Contest Modules (40 Total)

### Active CDEs (28 of 29)
Agronomy, Ag Communications, Ag Technology & Mechanical Systems, Ag Sales, Applied Ag Engineering, Cotton, Dairy Cattle, Entomology, Environmental & Natural Resources, Farm & Agribusiness Management, Floriculture, Food Science, Forage, Forestry, Homesite Evaluation, Horse, Land, Livestock Judging, Marketing Plan, Meats, Nursery/Landscape, Poultry, Plant Identification, Range, Tractor Technician, Veterinary Science, Wildlife, Wool

**Inactive**: Milk Quality (`is_active: false` in `constants/contests.ts`)

### Active LDEs (11 of 11)
Agricultural Issues Forum, Agricultural Skill Demonstration, Senior FFA Quiz, Greenhand FFA Quiz, Chapter Conducting, Creed Speaking, Spanish Creed Speaking, FFA Broadcasting, Public Relations, Job Interview, Ag Advocacy

---

## AI Features

### 1. RAG Quiz Generation (backbone of all CDE modules)
When a student starts a practice quiz, the app:
1. Sends a semantic query to the `match-knowledge` Supabase Edge Function
2. Edge function embeds query with `gemini-embedding-2-preview` (3072 dimensions)
3. Runs pgvector cosine similarity search against `knowledge_documents` table
4. Returns top-K matching chunks as grounding context
5. Sends context + prompt to `gemini-2.0-flash` with structured JSON output schema
6. Returns `QuizQuestion[]` (multiple choice + true/false + explanations)

**Source material**: Official FFA contest manuals, exam banks, USDA grading guides, livestock selection guides, etc. — ingested via `ingest_knowledge.py`. ~380+ chunks per major topic.

**Key files**: `lib/ai/rag-quiz.ts` (engine + 150+ TOPIC_QUERIES), `supabase/functions/match-knowledge/index.ts`

### 2. Livestock Phenotype Analyzer
AI computer vision evaluation of cattle, swine, sheep, goat images. Scores muscle, structure, volume, balance, and condition. Returns feedback + placing rationale. Powers the Phenotype Drill feature.

### 3. Ag Skills / LDE Video Scorer
1,000-point rubric AI-grades video speech submissions:
- Introduction: 100 pts
- Performance: 550 pts (content, accuracy, demonstration)
- Communication: 250 pts (delivery, pace, tone, body language)
- Summary: 100 pts

Target benchmarks: 400–550 (learning), 650–800 (competition-ready), 850+ (state finalist)

### 4. Job Interview AI Scorer
AI parses resumes/cover letters and evaluates interview responses against FFA judging criteria.

### 5. AI Models Used
- **Google Gemini 2.0 Flash** — Quiz generation, structured output, coaching feedback
- **Google gemini-embedding-2-preview** — 3072-dim embeddings for RAG
- **Anthropic Claude** — Secondary AI coaching (via `anthropic-proxy` edge function)

---

## Teacher Portal (19 Screens — `app/(admin)/`)

| Screen | What It Does |
|--------|-------------|
| Dashboard | Contest readiness heatmap, team alerts, upcoming events |
| Assessments | Create/assign custom quizzes, grade submissions |
| Analytics | Per-student/team/contest progress, trend lines |
| Intelligence | AI-powered readiness recommendations |
| Classroom | Create teams, generate join codes, manage roster |
| Students | Individual student performance view |
| Chapter Goals | Set target scores and deadlines per contest |
| Events / Calendar | Track district/area/state contest dates |
| Livestock Upload | Photo/PDF upload of post-contest scoring cards |
| Livestock Scores | View/edit judging totals |
| CDE Materials | Instructor study guides per contest |
| Image Library | Curated livestock/plant/meats media assets |
| Subscription | View plan tier, manage seat limits |
| Answer Key Editor | Override AI-generated answer keys |

---

## Student Dashboard (6 Tabs — `app/(tabs)/`)

| Screen | What It Does |
|--------|-------------|
| Home | XP level bar, streak, stats (sessions, time, avg score), assignment banner, quick actions |
| CDE | Browse & launch all 29 CDE practice modules |
| LDE | Browse & launch all 11 LDE modules (speech events have video recording) |
| Premier Chapter | Chapter leaderboard / team rankings |
| Profile | User settings, logout |

**Gamification**: XP per session (weighted by score), level = `floor(sqrt(xp/100)) + 1`, 5-day streak = 2× XP multiplier.

---

## Practice Module Architecture

Each CDE has 4 screens under `app/practice/[module]/`:

```
index.tsx      — Hub: Contest Hub card + Study & Practice + Flashcards
builder.tsx    — Topic/count/format picker → launches quiz
quiz.tsx       — Live quiz engine with scoring + results
flashcards.tsx — Flip-card study mode
```

Supporting lib: `lib/[module]-quiz.ts` wraps `generateRAGBatch()` and defines `QUIZ_SOURCES`, `QuizSettings`, `generateXxxQuiz()`, `generateXxxFlashcards()`.

**Stub modules** (routing to generic screens, not RAG-backed):
- `food-science` — 851-line monolith, needs split into 4 screens
- `ag-advocacy` — stub routing
- `ag-issues` — stub routing

---

## Data Model (Key Tables)

| Table | Purpose |
|-------|---------|
| `knowledge_documents` | RAG chunks (pgvector 3072-dim, HNSW indexed) |
| `contests` | 40 FFA contests with metadata |
| `practice_sessions` | Student session records with scores |
| `question_responses` | Individual answer tracking |
| `user_progress` | Per-user/contest mastery + gamification |
| `video_submissions` | LDE speech videos + AI scores (JSONB) |
| `classrooms` | Teacher teams with join codes |
| `classroom_members` | Student ↔ classroom membership |
| `assessments` | Teacher-created tests |
| `assessment_assignments` | Assignment distribution + due dates |
| `livestock_contest_sessions` | Post-contest card data (725-pt scoring model) |
| `biz_chapters` | School/chapter info |
| `biz_subscriptions` | Tier + status (trialing/active/past_due/canceled) |
| `biz_products_plans` | Price catalog with Stripe price IDs |
| `biz_invoices` | Annual invoices with 30-day grace period |
| `biz_payments` | Payment event log |
| `chapter_feature_overrides` | Time-bound tier grants/denials |
| `tier_config` | Token/request limits per tier |
| `chapter_usage` | Monthly usage tracking + caps |

---

## External Services

| Service | Purpose |
|---------|---------|
| **Supabase** | PostgreSQL, Auth, Storage, Edge Functions, pgvector |
| **Google Gemini API** | Quiz generation + embeddings |
| **Anthropic Claude API** | Secondary AI coaching |
| **Stripe** | Payment processing, annual invoices |
| **Clever OAuth** | School district SSO (teacher + student login via school credentials) |
| **Resend** | Transactional email (`no-reply@agcoachpro.com`) |
| **Vercel** | Web hosting |
| **Expo** | Cross-platform mobile build + distribution |

---

## Edge Functions (9 Total — `supabase/functions/`)

| Function | Purpose |
|----------|---------|
| `match-knowledge` | RAG similarity search (pgvector) |
| `gemini-proxy` | Gemini API proxy |
| `anthropic-proxy` | Claude API proxy |
| `clever-auth` | Clever OAuth callback |
| `create-payment-intent` | Stripe one-time payment setup |
| `stripe-webhook` | Stripe invoice/payment webhook handler |
| `generate-annual-invoices` | Batch annual invoicing (cron candidate) |
| `notify-assignment` | Push notifications for new assignments |
| `process-support-email` | Parse inbound support emails → tickets |

---

## Billing Model

- **Annual invoice** per school, sent in September
- **30-day grace period** before access suspended
- **PO support** — schools pay by purchase order (standard for school districts)
- **Tax exempt** tracking for districts
- Stripe handles card payments; invoices also tracked natively in `biz_invoices`
- Trial → Active transition: superadmin confirms PO or payment received

---

## Known Gaps / Active Backlog

1. **Food Science** — `app/practice/food-science/index.tsx` is an 851-line monolith. Needs split into `builder.tsx`, `quiz.tsx`, `flashcards.tsx`.
2. **Ag Advocacy + Ag Issues** — Both stub modules routing to generic screens.
3. **Phenotype Drill** — Multi-view (side/rear/front) drill screens need DB migration + upload UI + 3-view switcher.
4. **TOPIC_QUERIES gaps** — Entomology, Nursery/Landscape, Poultry, Vet Science, Wildlife, Wool, Job Interview, Creed Speaking may have incomplete RAG topic entries.
5. **Milk Quality** — Module exists in DB but `is_active: false`.

---

## Key File Index

| File | What It Is |
|------|-----------|
| `CLAUDE.md` | Architecture rules + CLI commands + skill catalog |
| `constants/contests.ts` | All 40 contests (source of truth for module list) |
| `constants/theme.ts` | Design system (Theme, GlassEffect — dark glass only) |
| `lib/tier.ts` | Feature gating + tier access logic |
| `lib/store/auth.ts` | Auth state + subscription fetch |
| `lib/store/history.ts` | Practice result history (38 PracticeType variants) |
| `lib/ai/rag-quiz.ts` | RAG engine + TOPIC_QUERIES (150+ entries) |
| `lib/navigation.ts` | `safeBack()` — never use `router.back()` directly |
| `lib/prompts/` | All AI prompt strings (one file per domain) |
| `app/(tabs)/` | Student app (6 screens) |
| `app/(admin)/` | Teacher portal (19 screens) |
| `app/(super-admin)/` | Ops/billing dashboard |
| `app/contest/[id].tsx` | Contest routing hub — `startPractice()` chain |
| `app/practice/` | 37 practice module directories |
| `supabase/migrations/` | 34 SQL migrations (schema history) |
| `supabase/functions/` | 9 Deno edge functions |
