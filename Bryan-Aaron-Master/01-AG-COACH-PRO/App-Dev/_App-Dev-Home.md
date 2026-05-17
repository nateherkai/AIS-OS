# App-Dev — Ag Coach Pro Technical Overview

> Human-curated technical domain for Ag Coach Pro.
> Full wiki layer → [[../../wiki/sources/agcoach-app-working-instructions|App Working Instructions]]
> Generated 2026-05-16 from ag-coach-app/CLAUDE.md + ag-coach-app/BUSINESS_BRAIN.md

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Expo Router 4 / React Native (iOS, Android, Web) |
| Backend | Supabase (Postgres + pgvector + Edge Functions + Auth) |
| AI — Quiz/RAG | Gemini API (`gemini-embedding-2-preview` 3072d + `gemini-2.0-flash`) |
| AI — Vision | Gemini Vision (livestock phenotype analyzer) |
| AI — Voice | ElevenLabs (Job Interview LDE voice agent) |
| Video Gen | fal-ai / Kling (horse lead identification clips) |
| Payments | Stripe (annual invoice model, PO support) |
| Hosting | Vercel (`prj_4xPOIb5yS0qzoJFmLstwRURR9KC9`, agcoachpro.com) |
| Notifications | Resend + Telegram (Gravity Claw) via `notifyOps` |
| Automation | n8n (cloud, $25.58/mo — note: onboarding v2 killed n8n dependency for signup flow) |

**Supabase Project:** `nkoyotdafqllgbpuklva` (us-west-2, PG17)

---

## Architecture Overview

### Route Groups
- `(auth)` — unauthenticated (login, signup, get-started, start-trial)
- `(tabs)` — student dashboard
- `(admin)` — teacher dashboard
- `(super-admin)` — internal ops (CRM, billing, analytics)

Auth gating via `app/_layout.tsx → AuthGate`. Role from `session.user.user_metadata.role`.

### Contest Routing — The ID Handshake
`cde.tsx` → `contest/[id].tsx` → `resolveContestId()` → `legacyId` → `startPractice()` chain of `if` guards → practice module.

### Practice Module Pattern (4-file flat)
```
app/practice/[name]/
  index.tsx      — Hub (Contest Hub + Study + Flashcards)
  builder.tsx    — Topic/count/format pickers
  quiz.tsx       — Live quiz engine + scoring
  flashcards.tsx — Flip-card mode
lib/[name]-quiz.ts       — generateXxxQuiz() + generateXxxFlashcards()
lib/prompts/[name]-prompts.ts  — all prompt strings
```

### RAG Architecture (v3 current)
1. Query → `match-knowledge-v3` Edge Function
2. Gemini `gemini-embedding-2-preview` (3072d) embeds query
3. pgvector HNSW cosine search in `knowledge_documents`
4. `intent classifier` (Gemini Flash) → taxonomy-aware routing (Brain Accuracy v1, shipped 2026-05-16)
5. Grounding context → `gemini-2.0-flash` structured JSON output → `QuizQuestion[]`

20,987 chunks classified (100% coverage). Top categories: Ag Tech 3,600 / Horse 2,158 / Meats 1,988 / Wildlife 1,240 / Forestry 934 / Livestock 574.

### Billing (Current)
`biz_*` tables are source of truth. Legacy `subscriptions`/`schools` tables grandfathered.

---

## Monthly Operating Costs (Ag Coach Pro)

| Service | Monthly |
|---|---|
| Claude Max | $130 |
| Anthropic API | $47.43 |
| Supabase | $25 |
| Vercel | $20 |
| n8n Cloud | $25.58 |
| OpenRouter | $34.14 |
| Fal.ai | $10.66 |
| ElevenLabs | $5.27 |
| Firecrawl | $19 |
| MailerLite | $15 |
| **Total (tech)** | **~$332** |

Source: `dashboard/data/expenses.json` (2026-05-16)

---

## Key Decisions (Recent)

- **2026-05-16** — Brain Accuracy v1 shipped: intent classifier + verification gate wired to Brain v3 RPC. Slaughter-cattle-grading retrieval miss resolved.
- **2026-05-16** — Brain v3 (taxonomy-aware): `match_knowledge_v3` RPC + all 20,987 chunks classified.
- **2026-05-15** — Brain v2 (Second Brain): unified retrieval across rulebook + Obsidian + app-meta; 6 tool functions; HNSW index fix (14s → 400ms).
- **2026-05-15** — Onboarding v2: n8n killed for signup; Stripe webhook hardened (idempotency, retry tombstone); `start-trial` edge fn.
- **2026-05-09** — `biz_*` billing tables designated current source of truth.

---

## Active Subfolders

- `App-Dev/` ← you are here
- [[../../01-AG-COACH-PRO/Brand/_Brand-Home|Brand]] — voice, colors, logo
- [[../../01-AG-COACH-PRO/Competitor-Intel/_Competitor-Intel-Home|Competitor Intel]]
- [[../../01-AG-COACH-PRO/Content-Modules/_Content-Modules-Home|Content Modules]]
- [[../../01-AG-COACH-PRO/Question-Banks/_Question-Banks-Home|Question Banks]]
- [[../../01-AG-COACH-PRO/Revenue-Model/_Revenue-Model-Home|Revenue Model]]
- [[../../01-AG-COACH-PRO/Sales-Pipeline/_Sales-Pipeline-Home|Sales Pipeline]]

## Related Wiki

- [[../../wiki/sources/agcoach-app-working-instructions|App Working Instructions (CLAUDE.md)]]
- [[../../wiki/sources/agcoach-schema|Supabase Schema]]
- [[../../wiki/concepts/agcoach-rag-architecture|RAG Architecture]]
- [[../../wiki/concepts/agcoach-edge-functions-architecture|Edge Functions Architecture]]
