# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**AgCoachPro** — AI-powered FFA CDE/LDE training platform for Texas FFA students and teachers.
Stack: Expo Router 4 / React Native / Supabase / TypeScript / Gemini AI

---

## Goal

- **Why it exists:** Texas FFA teachers cannot give 24/7 CDE feedback at scale. Students lack rubric-grounded practice between contests.
- **Done looks like:** Annual site-license revenue from chapters (Greenhand / Blue & Gold / Lone Star Elite). Teachers retain via readiness dashboards; students retain via AI-graded practice across all active CDE modules.
- **Out of scope:** Social feed, friend leaderboards, non-Texas state standards, gamified XP/badges (brand voice forbids).

---

## Decisions

*One line each. Date · what · why.*

- `2026-05-16` — Brain Accuracy v1 shipped to `main` (PR feat/brain-accuracy-v1). Brain chatbot (`app/study/ai-brain.tsx` → `askBrainV2`) now: (1) Gemini Flash intent classifier (`lib/ai/brain-intent-classifier.ts`) maps query → `{contest_category, subcategory, confidence}` via fixed taxonomy (`lib/ai/taxonomy.ts`, 41 cats from live DB); (2) retrieval routes — confidence ≥0.85 → `match-knowledge-v3` with `strict_category=true`, 0.6-0.85 → v3 boost-only, <0.6 → v2 fallback; (3) post-answer verifier (`lib/ai/brain-verifier.ts`, Flash, structured output) checks cited-chunk subcategory matches question; (4) on mismatch logs to `brain_verification_misses` (RLS: superadmin SELECT, owner SELECT/UPDATE, authenticated INSERT) + re-retrieves with `strict_category=true` AND client-side subcategory hard-filter (v3 only boosts subcategory, doesn't filter), updates `second_answer_succeeded=true` if retry produced answer. Skip-verifier when classifier ≥0.9 AND a *cited* chunk matches predicted subcategory. Flag `EXPO_PUBLIC_BRAIN_ACCURACY_V1_ENABLED` (default true). v3 body fields: `contest_category` + `subcategory` (NOT `filter_*` — edge fn reads those exact names). Models: `gemini-2.0-flash` (NOT `gemini-flash-latest` — SDK doesn't resolve). Regression closed: slaughter cattle grading score now routes to `Livestock-USDA-Grading` chunks.
- `2026-05-16` — Brain v3 (taxonomy-aware retrieval) shipped to branch `feat/rag-taxonomy`. New RPC `match_knowledge_v3` adds `filter_subcategory` (+0.04 boost) + `strict_category` boolean (hard filter, 8x ANN widening to preserve top-N signal under rare-category filters). New edge fn `match-knowledge-v3` (`verify_jwt=true`, same per-uid rate limit + rulebook floor reservation as v2). Client `lib/ai/brain-v3.ts` w/ v2 fallback on retrieval error. `lib/ai/rag-quiz.ts` flips to v3 path via `EXPO_PUBLIC_RAG_QUIZ_V3_ENABLED` (default true, strict_category=true when topic has a contest_category map entry; falls back to legacy `match-knowledge` on empty/error). Backfill: 20,987 / 20,987 classified (100%). Phase 1 heuristic = 18,716 (89.2%) into 25+ contest cats — top: Ag Tech 3600, Horse 2158, Meats 1988, Wildlife 1240, Forestry 934, Livestock 574. Phase 2 (migration `20260516010000`) assigned sentinel cats to remaining 2,271: `FFA Knowledge` (FFA Official Manual EN+ES, grounds Creed/FFA Quiz/Greenhand/Discussion Meet), `FFA Admin` (CDE handbook/minutes/waivers/dress code/maps), `Forestry` (woodland clinic handbook), `Ag Sales` (LDE order forms), `App Meta` (obsidian session logs + repo dev docs). Backfill bug fix: PostgREST `.upsert()` with partial cols nulled `content` — switched to per-row `.update().eq("id",…)`. Pagination drifts as rows update; script must be re-run until `unclassified` stabilizes. Integration smoke: `tests/test_match_knowledge_v3_smoke.py` (3 tests, skipped without live creds).
- `2026-05-15` — Brain v2 (Second Brain) shipped to branch `feat/brain-v2`. Chip-less unified retrieval across rulebook + Obsidian vault + app-meta. New `match-knowledge-v2` edge fn (`verify_jwt=true`, per-uid rate limit, two-phase ANN+boost RPC `match_knowledge_v2`, rulebook slot reservation). New `match_knowledge_v2` SQL RPC bypasses HNSW-unsafe composite ORDER BY via inner CTE. Client `lib/ai/brain-v2.ts` orchestrates: retrieve → sanitize chunks (frontmatter + injection markers stripped, `<chunk trust="untrusted">` wrap) → Gemini function-calling (6 tools: open_screen, start_practice, show_progress, get_contest_info, lookup_pricing, escalate_to_support) → server-validate UUID citations (drop fabricated) → deterministic confidence calc (not model-emitted). Feature flag `EXPO_PUBLIC_BRAIN_V2_ENABLED` (default true) + legacy fallback on retrieval error. Legacy `match-knowledge` and `askBrain` retained for `rag-quiz.ts` + media path. Embeddings hardcoded `gemini-embedding-2-preview@3072` everywhere — dim assertion at runtime. Obsidian ingest defends against symlink escape + `01_Bryan/` private path leak.
- `2026-05-15` — Onboarding v2 shipped. n8n killed; all signup/purchase/trial/notify/CRM lives in repo. Hardened `stripe-webhook` (sig verify, atomic `stripe_event_log` idempotency, outbox role promote, fire-forget `notifyOps`, bounded 5-retry tombstone). New `start-trial` fn with TOCTOU per-IP rate limit + repair path. `stripe-reconcile` self-heals stale role promos + canceled-drift. `trial-reminder` daily cron (14:00 UTC) drives 7/3/1/0/-7-day milestones via `trial_reminder_log` idempotency.
- `2026-05-15` — Cron auth via dedicated vault secret `internal_cron_key` + `private.internal_cron_key()` helper, NOT `sb_secret_*` (diverges from edge fn `SUPABASE_SERVICE_ROLE_KEY`). pg_net `timeout_milliseconds` bumped to 60s/120s — default 5s aborted reconcile.
- `2026-05-15` — `app/(auth)/signup.tsx` is student-only. Bare arrivals redirect to `/get-started` (paid) or `/start-trial` (trial). Only `?role=teacher` (accept-invite) keeps teacher path.
- `2026-05-13` — Owner memberships backfilled + read-fallback added because Athens ISD teachers were missing from staff list (commit b80b10bb).
- `2026-05-12` — Granted `authenticated` EXECUTE on 14 client RPCs + removed finance from teacher dashboard. Anon-key callers were 401'ing silently.
- `2026-05-11` — Superadmin gate moved from hardcoded list to Supabase auth + `view-as` impersonation. Hardcoded gate did not scale and blocked dual-role testing.
- `2026-05-09` — `biz_*` billing tables are current source of truth; legacy `subscriptions`/`schools` grandfathered. Stripe sync writes only to `biz_*`.
- `2026-05-08` — RLS restricts subscription writes to `role=teacher`; SELECT policies added to preserve client reads on gated tables.
- `2026-05-07` — `promote-to-teacher` edge function + `drain-role-promotions` pg_cron job. Replaces manual role flips after invite accept.
- `2026-04` — Supabase publishable keys (`sb_publishable_...`) replaced JWT anon keys. Never gate proxies on JWT shape — use `verify_jwt = true` or non-empty length check.
- `2026-04` — Horse-lead video swapped from Vertex AI to fal-ai / Kling. Synthetic AQHA lead clips remain unreliable; source real footage where possible.
- `2026-03` — RAG = Supabase pgvector (`knowledge_documents`, 768-dim) via `match-knowledge` edge function. Not Pinecone (Pinecone reserved for Claude session memory).
- `2026-03` — Migration numbering split: legacy `NNN_*.sql` grandfathered through ~073, all new work uses `YYYYMMDDHHMMSS_*.sql`.

---

## Rules

These override all defaults. Read before touching any code.

- **Token efficiency** — Do not re-read files already read in this session unless the file may have changed. Skip files over 100KB unless explicitly required. Suggest `/cost` when a session runs long. Recommend starting a new session when switching to an unrelated task.
- **Prefer editing over rewriting** — targeted edits only; never rewrite a whole file when a diff will do.
- **No fluff** — no sycophantic openers, closing summaries, or filler text.
- **Use `npm`** — not pnpm, yarn, or bun.
- **Never use `router.back()`** on screens that can be deep-linked or refreshed. Use `safeBack(router, fallback)` from `lib/navigation.ts` — it calls `router.replace(fallback)` when `canGoBack()` is false, preventing blank white screens on web.
- **Never use light backgrounds.** All screens use the dark glass aesthetic. Import `Theme` and `GlassEffect` from `constants/theme.ts`. Button primitive: `AnimatedButton` from `components/common/AnimatedButton.tsx` — alias as `TouchableOpacity`.
- **Never modify the database schema directly.** Always write a migration file in `supabase/migrations/` and run it. Direct schema edits will be overwritten on next deploy.
- **Schema source of truth: `SCHEMA.md`** at project root. Read it before writing any query, view, RPC, or skill that touches Supabase. It documents all 50+ public tables, the two parallel billing systems (`subscriptions`/`schools` legacy vs `biz_*` current), foreign keys, and admin-relevant columns. Raw snapshot lives in `supabase/schema-snapshot-YYYY-MM-DD.json`. After any migration that adds/drops/renames tables, regenerate both files.
- **AI prompts belong in `lib/prompts/`**, not inline in logic files. One file per domain (e.g. `livestock-analyzer-prompts.ts`, `ag-skills-prompts.ts`).
- **Every new quiz module that records scores** must add its `PracticeType` to the union in `lib/store/history.ts`.
- **Every new RAG topic** must have an entry in the `TOPIC_QUERIES` map in `lib/ai/rag-quiz.ts`, or quiz generation will silently degrade (no retrieval context).
- **Every new CDE module** needs: a routing `if` block in `app/contest/[id].tsx → startPractice()`, a tier mapping in `lib/tier.ts → FEATURE_TIERS`, and `is_active: true` in `constants/contests.ts` when ready.
- **Never gate Edge Function proxies on JWT shape.** Supabase anon keys rotated to `sb_publishable_...` format — not a JWT. Use `verify_jwt = true` in `config.toml` or check non-empty length only. Hand-rolled `eyJ...` checks will 401 all production requests silently.
- **Sub-agent model routing** — Always set `model` explicitly when spawning agents: Explore → `haiku`, Plan → `opus`, general-purpose → `sonnet`.
- **PostgREST `.upsert(onConflict)` needs a unique CONSTRAINT**, not just a unique INDEX. `create unique index` alone fails silently — Supabase falls back to INSERT and the second call hits a unique violation. Use `alter table ... add constraint ... unique (col)` (or `unique using index`) in the migration.
- **Migration numbering** — two coexisting schemes: legacy `NNN_description.sql` (e.g. `072_*.sql`) and timestamp `YYYYMMDDHHMMSS_description.sql`. New work follows timestamp scheme; numeric scheme is grandfathered through ~073.
- **Gemini structured output** — for any AI call expected to return JSON, build a `Schema` from `@google/generative-ai` and pass `generationConfig: { responseMimeType: 'application/json', responseSchema }`. Parse with `parseAIJson` from `lib/ai/parser.ts`. Always validate/normalize the output (sort, renumber, default missing fields) — the model occasionally returns short or non-contiguous arrays.
- **Gap/report scoping** — `TeacherService.getPerformanceGaps(classroomId?)` is teacher-wide by default. Pass a `classroomId` whenever the result feeds an AI prompt for one specific class, or other classes' weak data leaks into the prompt.
- **Never hardcode CDE contest scores as facts in system prompts.** `lib/prompts/core-prompts.ts → AG_COACH_PRO_SYSTEM_PROMPT` contains fallback score values for disambiguation only. The prompt instructs the model to defer to retrieved RAG rulebook excerpts when present. If scores in that file seem wrong, verify against the official Texas FFA handbook — do not guess.
- **Onboarding v2 entry points — single funnel.** Paid teachers → `app/get-started.tsx` (hardcodes `role=teacher`). Trial teachers → `app/start-trial.tsx` (calls `start-trial` edge fn). Students → `app/(auth)/signup.tsx` (joinCode required). Do not re-introduce a teacher path on `signup.tsx` or role drift returns.
- **Role promotion goes through the outbox** — never call `auth.admin.updateUserById` for role changes in webhook hot paths. Insert into `pending_role_promotions`; the `drain-role-promotions` cron (every 5m) + `stripe-reconcile` (every 15m) handle the admin API call + session invalidation. Keeps webhook critical-path latency low and survives admin API outages.
- **Stripe webhook is idempotent at the gate.** First op after sig verify: `INSERT ... ON CONFLICT DO NOTHING` into `stripe_event_log` keyed on `stripe_event_id`. Duplicate Stripe retries short-circuit 200. On processing failure, the row is DELETED so the next retry re-runs fresh; the catch counts prior failures and tombstones after `MAX_RETRY_ATTEMPTS = 5` to stop Stripe's 72h retry storm.
- **`.catch()` on PostgREST builders is forbidden.** `supabase.from(...).insert(...).catch(...)` throws `TypeError: .catch is not a function` because PostgrestBuilder is thenable, not a Promise. Always use `try { await supabase... } catch {}` for postgrest calls. Only `fetch(...)` and `Promise`-returning helpers (e.g. `notifyOps`) support `.catch()`.
- **Ops notifications via `notifyOps`** in `supabase/functions/_shared/notifyOps.ts`. Resend email + Telegram (Gravity Claw bot). Never throws — fire-and-forget at call sites. Total failure writes `onboarding_alerts (type='notification_failed')`. Env: `RESEND_API_KEY`, `OPS_ALERT_EMAIL`, `GRAVITY_CLAW_BOT_TOKEN`, `OPS_TELEGRAM_CHAT_ID`.
- **CRM/Lead surface is `app/(super-admin)/crm.tsx`** backed by RPC `admin_get_leads_overview()` (SECURITY DEFINER with internal `public.users.role = 'superadmin'` caller gate — EXECUTE is granted to `authenticated` because PostgREST needs it; the real gate is the function body's RAISE). 6 columns: Trial / Trial-ending / Active / Past Due / Canceled / Needs Attention. Orphan cards expose "Heal now" → `manual_heal_orphan(uuid)` RPC.
- **pg_cron URLs use `private.internal_cron_key()` for Bearer auth, NOT `current_setting('app.settings.service_role_key')`.** The latter returns NULL in cron worker sessions (silently 401s). Add a 60s+ `timeout_milliseconds` on every `net.http_post` call — default 5s aborts most reconcile/scan workloads.

---

## Brand System

Voice: **Authoritative Coach + Competitive Motivator**. Expert, direct, metric-focused. Never condescending.

**Tone by audience:**
- Students: metrics-driven, strategy-focused ("Your last 3 tests dropped. Focus on parasite ID first.")
- Teachers: professional peer, outcome-focused ("Your students get 24/7 AI feedback. You get readiness dashboards.")
- Parents: investment confidence, proof-based ("FFA-aligned curriculum. Track competition readiness.")

**Terminology — use:** CDE, placing(s), score, mastery, judge perspective, evaluation criteria, "24/7 AI feedback," "AI-guided practice," "progress dashboard"

**Terminology — avoid:** "fun," "easy," "quick," "gamified," "unlock," "student journey," "learning experience," "skill-building," "personal coach," superlatives without proof

**Colors:** Navy `#001F4D` (authority/UI), Gold `#D4A574` (achievement/progress), White `#FFFFFF`, Dark Gray `#2B2B2B`

**Typography:** Bold serif or sans-serif headings, 16px body, large bold navy metric numbers (32–48px) with gold accents. Strong weight hierarchy — bold is BOLD.

---

## Pricing

Annual site licenses:

| Tier | Price | Seats | Credits |
|------|-------|-------|---------|
| The Greenhand | $495/yr | LDE team + individual quiz logins | 5M |
| The Blue & Gold | $895/yr | Greenhand + 40 CDE logins | 15M |
| The Lone Star Elite | $1,495/yr | Unlimited | 40M |

**Feed Bags:** 1M supplemental credits for $100 — unused credits rollover with active license. Usage alert at 80%. Subscription screen: `app/(admin)/subscription.tsx`.

---

## Commands

```bash
# Development
npm start              # Start Expo dev server (all platforms)
npm run web            # Web only
npm run ios            # iOS simulator (Mac only)
npm run android        # Android emulator

# Build / Deploy
npm run build          # Web export → dist/ (validates bundle contains key content)
npm run export         # Raw web export, no validation
npx tsc --noEmit -p .  # Type-check without emitting; fast pre-commit gate

# Tests
npm test               # Jest
npm test -- creed      # Run a single test file matching "creed"

# Supabase Edge Functions (deploy from project root)
npx supabase functions deploy <function-name>

# RAG knowledge ingest (Python, requires .env loaded)
python3 ingest_knowledge.py
```

## Live infra IDs (for MCP tooling)

- **Supabase project:** `nkoyotdafqllgbpuklva` (Ag Coach Pro, us-west-2, PG17)
- **Vercel project:** `prj_4xPOIb5yS0qzoJFmLstwRURR9KC9` (team `team_n4rQ2jw7YC7ldt5ZAVXaBWK6`)
- **Production URL:** https://www.agcoachpro.com (apex 307→www)

---

## Architecture

### Route groups
`(auth)` → unauthenticated · `(tabs)` → students · `(admin)` → teachers · `(super-admin)` → internal ops.
Auth gating: `app/_layout.tsx → AuthGate`. Role from `session.user.user_metadata.role`.

### Contest routing — the "ID Handshake"

`app/(tabs)/cde.tsx` → `app/contest/[id].tsx` → `resolveContestId()` (`lib/data/identification.ts`) maps UUID or legacy string to a `legacyId` like `cde-livestock` → `startPractice()` chain of `if (legacyId === …)` guards → `router.push` to practice module. **When adding a new CDE module, register a new `if` block in `startPractice()`.**

### Practice module structure

Canonical pattern (forages as reference):

```
app/practice/forages/
  index.tsx      ← Hub screen: Contest Hub + Study + Flashcards
  builder.tsx    ← Topic/count/format pickers → launches quiz
  quiz.tsx       ← Live quiz engine with scoring + results
  flashcards.tsx ← Flip-card mode

lib/forages-quiz.ts  ← generateForagesQuiz() + generateForagesFlashcards()
lib/prompts/forages-prompts.ts  ← all prompt strings
```

### RAG quiz generation

All RAG-backed modules call `generateRAGBatch(topic, type, count, difficulty)` from `lib/ai/rag-quiz.ts`:
1. Hits `match-knowledge` Edge Function → retrieves chunks from `knowledge_documents` (pgvector)
2. Injects chunks as grounding context into Gemini structured-output prompt
3. Returns `QuizQuestion[]`

`TOPIC_QUERIES` in `lib/ai/rag-quiz.ts` holds the semantic retrieval query per topic. Add entries here for every new topic.

### Module variations

**Horse Eval** (`app/practice/horse-eval/`) has a nested `leads/` subdirectory for the Lead Identification drill — deviates from canonical 4-file flat pattern.

**Video generation** — horse leads uses fal-ai / Kling (`fal-ai` client dep) for AI video. Replaced Vertex AI.

### Ag Coach Brain chatbot

`app/study/ai-brain.tsx` — category-filtered Q&A chatbot. UI chips map to `(eventType, category)` pgvector filter params. On send, calls `askBrain(question, '', ragOptions)` from `lib/ai/gemini.ts`, which fetches matching chunks from `knowledge_documents` via `match-knowledge` Edge Function and injects them as grounding context before calling Gemini.

System prompt: `AG_COACH_PRO_SYSTEM_PROMPT` in `lib/prompts/core-prompts.ts`. Hardcoded scores in that file are **fallback defaults only** — retrieved rulebook context takes precedence. Grounded static CDE rules (non-vector): `lib/data/notebooks/cde-rules.ts`.

### CRM & Billing

Super-admin CRM kanban pipeline: `app/(super-admin)/`. Stripe invoice/payment sync pipeline ingests to `biz_*` tables — sync logic in `supabase/functions/`. Token usage tracked on all AI call sites.

---

## Adding a new CDE practice module

1. **`lib/[name]-quiz.ts`** — Wrap `generateRAGBatch`. Define `QUIZ_SOURCES`, `QuizSettings`, `generateXxxQuiz()`, `generateXxxFlashcards()`. Add topic entries to `TOPIC_QUERIES` in `lib/ai/rag-quiz.ts`.
2. **`app/practice/[name]/index.tsx`** — Hub screen (Contest Hub → Study & Practice → Flashcards).
3. **`app/practice/[name]/builder.tsx`** — Topic/count/format pickers.
4. **`app/practice/[name]/quiz.tsx`** — Quiz engine (copy forages pattern, swap import).
5. **`app/practice/[name]/flashcards.tsx`** — Flashcard mode.
6. **`lib/store/history.ts`** — Add new `PracticeType` to the union.
7. **`app/contest/[id].tsx`** — Add `if (legacyId === …)` block in `startPractice()`.
8. **`lib/tier.ts`** — Add feature key → tier mapping in `FEATURE_TIERS`.
9. **`constants/contests.ts`** — Set `is_active: true` when ready.
10. **RAG prerequisite** — Ingest source PDF via `rag-knowledge-ingest` skill first.

---

## Skills Catalog

Stored in `skills/`. Use `/skill-name` to invoke.

| Skill | When to Use |
|---|---|
| `rag-coverage-report` | **Before building any module** — query Supabase to confirm knowledge_documents has chunks for the module's contest_category. Prevents building modules that silently return no questions. |
| `module-status` | **Start of every build session** — scan all 37 practice directories and produce a completeness table (complete / stub / missing). Tells you exactly what needs `scaffold` vs `complete-stub`. |
| `scaffold-cde-module` | **Module directory doesn't exist** — build all 4 screens + lib + 6 integrations from the forages template. |
| `complete-stub-module` | **index.tsx exists but routes to generic `/practice/study` or `/practice/test`** — replace stub routing with RAG-backed screens. |
| `check-site` | **After deploying** — verify agcoachpro.com, check Vercel logs, smoke-test new modules, diagnose blank screens or missing quiz content. |
| `account-health-audit` | **Any "I can't see X" complaint** — Staff tab empty, View-As picker empty, dashboard zeros despite data existing. Diagnoses the 4 silent-empty root causes: missing memberships row, missing EXECUTE on RLS helper, missing EXECUTE on read RPC, public/auth role drift. Includes ready-to-paste SQL diagnostics + fixes. |
| `rag-knowledge-ingest` | Ingest a new PDF/CSV into `knowledge_documents`. Must run before any new module can generate questions. |
| `rag-quiz-generate` | Reference for how `generateRAGBatch` works. |
| `no-blank-pages` | Audit all screens for `router.back()` and replace with `safeBack()`. |
| `3d-animation-creator` | Takes a video file and builds a scroll-driven Apple-style website where scroll position controls video playback. Handles frame extraction, HTML generation, and local deployment. |
| `pinecone-memory` | Search, store, and manage long-term memories in Pinecone vector DB. Use for semantic recall across sessions. CLI: `python3 ~/.claude/pinecone_memory.py query/store/stats/fetch/delete`. |
| `notebooklm` | Full NotebookLM API — create notebooks, add sources, generate audio/study guides. |
| `slides-to-png` | Convert `.pptx`/`.pdf` slide decks to individual PNG files via `pdftoppm`. |
| `sync-slide-bullets` | Reads `lib/data/slide-decks/` and rewrites `bullets[]` arrays in `app/practice/livestock-judging/basics.tsx`. Run after any slide deck change. |
| `wrapup` | **End of every session** — save memories + push session summary to AI Brain notebook. Trigger: `/wrapup`. |

---

## Session Protocol

**End every session with `/wrapup`** → saves memories + pushes summary to AI Brain notebook (ID: `ba26ba14-ac37-4ce8-acea-f00ea2d9dc50`).
