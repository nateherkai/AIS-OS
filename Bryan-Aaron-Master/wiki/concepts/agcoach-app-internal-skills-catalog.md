---
name: agcoach-app-internal-skills-catalog
type: concept
tags: [ag-coach-pro, skills, agent, catalog, development]
source_files: [raw/_ingested/2026-05-16-agcoach-CONSOLIDATED_SKILLS.md, raw/_ingested/2026-05-16-agcoach-CLAUDE.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16 (pass 2 — in-app catalog 10→31)
---

# Ag Coach Pro — App Internal Skills Catalog

Two catalogs exist: the consolidated `.agent/skills/` directory (15 skills for agent use during development) and the in-app `/skills/` directory (operational skills invoked during Claude sessions).

## Development Agent Skills (`/skills/` — from CONSOLIDATED_SKILLS.md)

15 skills stored in `.agent/skills/<name>/SKILL.md`:

| Skill | Purpose |
|---|---|
| `advisor-intelligence` | Analytics, team management, learning gap visualization for FFA Advisors. Principles: Data over Dates, Actionable Insights, Simulation Fidelity |
| `ai-engine` | All AI integrations: Gemini grading, Claude backup, Whisper transcription, prompt engineering, scoring pipeline. Debugging rate limits, malformed responses, timeouts |
| `anatomy-alignment` | Livestock Anatomy module — verifying/correcting anatomical marker alignment. Standardized grid (0-100% coordinates), aspect ratio locking (3:2 container) |
| `auto-commit` | Enforce automatic git add + commit + push after each completed task |
| `backend-data` | Supabase integration: DB schema, migrations, auth, storage, API routes, Zustand state. RLS, pgvector, edge functions |
| `brand-identity` | Single source of truth for brand guidelines, design tokens, tech choices, voice/tone. Resources: `design-tokens.json`, `tech-stack.md`, `voice-tone.md` |
| `contest-builder` | Builds complete FFA contest practice modules end-to-end. Templates: Quiz CDEs, Speech/Presentation LDEs, Role-Play CDEs, Document/Portfolio CDEs, ID/Flashcard modules |
| `csv-question-importer` | Processes CSV question files into the generic practice flow. Guardrail: NO NEW UI — data plumbing only |
| `deployment-qa` | Pre/post-deployment checks. NEVER use Vercel CLI for prod — use GitHub pipeline. Verify on live domain |
| `error-handling-patterns` | Master error handling across languages: exceptions, Result types, Circuit Breakers, Graceful Degradation |
| `id-module-builder` | Creates ID practice modules using AI image generation + categorical mapping. 5-step process: Data Definition → Image Gen → Asset Mapping → UI Scaffolding → Master Config |
| `problem-solving` | Logic Tree approach for complex tasks and debugging death loops. Rule: build logic tree before modifying files |
| `qa-performance` | Testing, perf optimization, bug fixing, bundle auditing. Targets: Launch <3s, Scoring <5s, 60 FPS scrolling. Audit for bundle bloat |
| `reviewing-code` | Code review: architectural compliance, security (hardcoded secrets), performance (re-renders, slow queries) |
| `ui-ux` | Visual UI components, screens, navigation, theming, animations. Constraints: `StyleSheet.create()`, no NativeWind/Tailwind, 44pt minimum hit targets |

## In-App Claude Session Skills (`/skills/` — 31 in repo, 2026-05-16)

Stored in `skills/<name>.md`. Invoked with `/<name>`. Grouped by purpose.

### Module build pipeline

| Skill | Purpose |
|---|---|
| `rag-coverage-report` | Before building any module — confirm knowledge_documents has chunks for contest_category |
| `module-status` | Start of every build session — scan all 37 practice dirs, produce complete / stub / missing table |
| `module-readiness` | Per-module readiness gate (assets, prompts, tier, route) |
| `cde-module-build` | High-level orchestrator for building a new CDE end-to-end |
| `scaffold-cde-module` | Build all 4 screens + lib + 6 integrations from forages template |
| `complete-stub-module` | index.tsx exists but routes to generic screens — replace with RAG-backed screens |
| `tier-feature-register` | Add new feature key → tier mapping in `lib/tier.ts → FEATURE_TIERS` |

### RAG / knowledge

| Skill | Purpose |
|---|---|
| `rag-knowledge-ingest` | Ingest new PDF/CSV into `knowledge_documents` |
| `pdf-to-rag` | PDF-specific ingest pipeline (chunking, OCR if needed) |
| `rag-quiz-generate` | Reference for how `generateRAGBatch` works |
| `prompt-extract` | Pull inline AI prompts out of logic files into `lib/prompts/<domain>-prompts.ts` |
| `brain-v2-citation-check` | Verify Brain v2/v3 returns server-validated UUID citations only (no fabricated) |

### Supabase / infra

| Skill | Purpose |
|---|---|
| `migration-write` | Author a new migration file with correct numbering + safe DDL pattern |
| `rls-policy-audit` | Walk RLS policies + EXECUTE grants on RPCs the client calls |
| `edge-fn-deploy` | Deploy a single edge function with config check |
| `cron-audit` | Verify pg_cron jobs use `private.internal_cron_key()` + `timeout_milliseconds ≥ 60_000` |
| `stripe-webhook-trace` | Trace a Stripe event through the webhook → outbox → role-promote path |
| `view-as-impersonation` | Superadmin "view-as" any user — mint + log impersonation token |
| `account-health-audit` | "I can't see X" complaints — diagnoses 4 silent-empty root causes |
| `feed-bag-credit-sim` | Simulate Feed Bag credit consumption + rollover for tier scenarios |
| `self-healing-workflow` | Compose multi-step reconciliation flow (uses `stripe-reconcile` + `self-heal-check`) |

### UI / web

| Skill | Purpose |
|---|---|
| `no-blank-pages` | Audit all screens for `router.back()` and replace with `safeBack()` |
| `safe-back-audit` | Sub-audit specifically for `safeBack` fallback correctness |
| `brand-voice-lint` | Scan copy for banned terms ("fun", "easy", "gamified", "personal coach") |
| `check-site` | After deploying — verify agcoachpro.com, Vercel logs, smoke-test new modules |
| `3d-animation-creator` | Take a video file → scroll-driven Apple-style website |
| `slides-to-png` | Convert `.pptx`/`.pdf` slide decks to PNGs via `pdftoppm` |
| `sync-slide-bullets` | Sync slide-deck data into `livestock-judging/basics.tsx` after any deck change |

### External / session

| Skill | Purpose |
|---|---|
| `notebooklm` | Full NotebookLM API — create notebooks, add sources, generate audio/study guides |
| `pinecone-memory` | Semantic recall across sessions — CLI `python3 ~/.claude/pinecone_memory.py …` |
| `wrapup` | End of every session — save memories + push summary to AI Brain notebook |

## Related

- [[../sources/agcoach-agent-global-rules|Agent Global Rules]]
- [[../sources/agcoach-agent-master-prompt|B.L.A.S.T. Master Prompt]]
- [[../sources/agcoach-app-working-instructions|App Working Instructions]]
- [[../sources/agcoach-advisor-intelligence-skill|Advisor Intelligence skill detail]]
- [[../concepts/agcoach-rag-architecture|RAG Architecture]]
- [[../concepts/agcoach-edge-functions-architecture|Edge Functions Architecture]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
