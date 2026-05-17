# AGENTS.md

**AgCoachPro** — AI-powered FFA CDE/LDE training platform for Texas FFA students and teachers.
Stack: Expo Router 4 / React Native / Supabase / TypeScript / Gemini AI

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
- **Schema source of truth: `SCHEMA.md`** at project root. Read it before writing any query, view, RPC, or skill that touches Supabase. It documents all 47 public tables, the two parallel billing systems (`subscriptions`/`schools` legacy vs `biz_*` current), foreign keys, and admin-relevant columns. Raw snapshot lives in `supabase/schema-snapshot-YYYY-MM-DD.json`. After any migration that adds/drops/renames tables, regenerate both files.
- **AI prompts belong in `lib/prompts/`**, not inline in logic files. One file per domain (e.g. `livestock-analyzer-prompts.ts`, `ag-skills-prompts.ts`).
- **Every new quiz module that records scores** must add its `PracticeType` to the union in `lib/store/history.ts`.
- **Every new RAG topic** must have an entry in the `TOPIC_QUERIES` map in `lib/ai/rag-quiz.ts`, or quiz generation will silently degrade (no retrieval context).
- **Every new CDE module** needs: a routing `if` block in `app/contest/[id].tsx → startPractice()`, a tier mapping in `lib/tier.ts → FEATURE_TIERS`, and `is_active: true` in `constants/contests.ts` when ready.
- **Never gate Edge Function proxies on JWT shape.** Supabase anon keys rotated to `sb_publishable_...` format — not a JWT. Use `verify_jwt = true` in `config.toml` or check non-empty length only. Hand-rolled `eyJ...` checks will 401 all production requests silently.
- **Sub-agent model routing** — Always set `model` explicitly when spawning agents: Explore → `haiku`, Plan → `opus`, general-purpose → `sonnet`.

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

# Tests
npm test               # Jest
npm test -- creed      # Run a single test file matching "creed"

# Supabase Edge Functions (deploy from project root)
npx supabase functions deploy <function-name>

# RAG knowledge ingest (Python, requires .env loaded)
python3 ingest_knowledge.py
```

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
| `rag-knowledge-ingest` | Ingest a new PDF/CSV into `knowledge_documents`. Must run before any new module can generate questions. |
| `rag-quiz-generate` | Reference for how `generateRAGBatch` works. |
| `no-blank-pages` | Audit all screens for `router.back()` and replace with `safeBack()`. |
| `3d-animation-creator` | Takes a video file and builds a scroll-driven Apple-style website where scroll position controls video playback. Handles frame extraction, HTML generation, and local deployment. |
| `pinecone-memory` | Search, store, and manage long-term memories in Pinecone vector DB. Use for semantic recall across sessions. CLI: `python3 ~/.Codex/pinecone_memory.py query/store/stats/fetch/delete`. |
| `notebooklm` | Full NotebookLM API — create notebooks, add sources, generate audio/study guides. |
| `slides-to-png` | Convert `.pptx`/`.pdf` slide decks to individual PNG files via `pdftoppm`. |
| `sync-slide-bullets` | Reads `lib/data/slide-decks/` and rewrites `bullets[]` arrays in `app/practice/livestock-judging/basics.tsx`. Run after any slide deck change. |
| `wrapup` | **End of every session** — save memories + push session summary to AI Brain notebook. Trigger: `/wrapup`. |

---

## Session Protocol

**End every session with `/wrapup`** → saves memories + pushes summary to AI Brain notebook (ID: `ba26ba14-ac37-4ce8-acea-f00ea2d9dc50`).
