---
name: agcoach-app-internal-skills-catalog
type: concept
tags: [ag-coach-pro, skills, agent, catalog, development]
source_files: [raw/_ingested/2026-05-16-agcoach-CONSOLIDATED_SKILLS.md, raw/_ingested/2026-05-16-agcoach-CLAUDE.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
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

## In-App Claude Session Skills (from CLAUDE.md Skills Catalog)

| Skill | When to Use |
|---|---|
| `rag-coverage-report` | Before building any module — confirm knowledge_documents has chunks for contest_category |
| `module-status` | Start of every build session — scan 37 practice dirs, produce completeness table |
| `scaffold-cde-module` | Module directory doesn't exist — build all 4 screens + lib + 6 integrations |
| `complete-stub-module` | index.tsx exists but routes to generic screens — replace with RAG-backed screens |
| `check-site` | After deploying — verify agcoachpro.com, Vercel logs, smoke-test new modules |
| `account-health-audit` | "I can't see X" complaints — diagnoses 4 silent-empty root causes |
| `rag-knowledge-ingest` | Ingest new PDF/CSV into knowledge_documents |
| `rag-quiz-generate` | Reference for how generateRAGBatch works |
| `no-blank-pages` | Audit all screens for router.back() and replace with safeBack() |
| `wrapup` | End of every session — save memories + push to AI Brain notebook |

## Related

- [[../sources/agcoach-agent-global-rules|Agent Global Rules]]
- [[../sources/agcoach-agent-master-prompt|B.L.A.S.T. Master Prompt]]
- [[../sources/agcoach-app-working-instructions|App Working Instructions]]
- [[../concepts/agcoach-rag-architecture|RAG Architecture]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
