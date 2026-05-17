# Ingest Log

Append-only history of raw/ → wiki/ ingest operations.

Format per entry:
- Timestamp + source filename
- Type (source/transcript/note/meeting/article)
- Pages created (list)
- Domains linked
- Open questions
- Archive path in raw/_ingested/

---

_(first entry appears after first /ingest run)_

---

## 2026-05-16 12:00 — nate-herk-karpathy-walkthrough.txt

- Type: transcript (YouTube)
- Pages created (8):
  - [[wiki/sources/nate-herk-karpathy-walkthrough]]
  - [[wiki/people/andrej-karpathy]]
  - [[wiki/people/nate-herk]]
  - [[wiki/concepts/llm-wiki-pattern]]
  - [[wiki/concepts/hot-cache]]
  - [[wiki/concepts/wiki-linting]]
  - [[wiki/concepts/obsidian-web-clipper]]
  - [[wiki/comparisons/wiki-vs-rag]]
  - [[wiki/analysis/why-wiki-compounds]]
- Domains linked: 06-AI-WORKFLOW
- Open questions: None — transcript was clear and complete.
- Moved to: raw/_ingested/2026-05-16-nate-herk-karpathy-walkthrough.txt

---

## 2026-05-16 12:00 — jack-roberts-cc-os.txt

- Type: transcript (YouTube)
- Pages created (7):
  - [[wiki/sources/jack-roberts-cc-os-walkthrough]]
  - [[wiki/people/jack-roberts]]
  - [[wiki/concepts/claude-code-os]]
  - [[wiki/concepts/dreaming-engine]]
  - [[wiki/concepts/six-pillars-os]]
  - [[wiki/concepts/eight-dim-dream-intelligence]]
  - [[wiki/analysis/visualization-layer-analysis]]
- Domains linked: 06-AI-WORKFLOW
- Open questions: Jack references "Hermes agent" as prior art for auto-skill creation — could warrant its own page if a transcript/source for it surfaces later.
- Moved to: raw/_ingested/2026-05-16-jack-roberts-cc-os.txt

---

## 2026-05-16 12:00 — _Inbox-Home.md

- Type: note (Obsidian landing page — no substantive content)
- Pages created (1): [[wiki/sources/inbox-home]] (placeholder only)
- Domains linked: unassigned
- Open questions: None. Legacy file; Obsidian capture workflow instructions only.
- Moved to: raw/_ingested/2026-05-16-_Inbox-Home.md

---

## 2026-05-16 12:00 — Untitled.md

- Type: note (empty — 1-line blank file)
- Pages created: 0
- Domains linked: none
- Open questions: None. File was empty/stub.
- Moved to: raw/_ingested/2026-05-16-Untitled.md

---

## 2026-05-16 14:00 — agcoach-CLAUDE.md

- Type: source (authoritative app working instructions / architecture rules)
- Pages created (1): [[wiki/sources/agcoach-app-working-instructions]]
- Domains linked: 01-AG-COACH-PRO
- Open questions: None. Dense, highly authoritative file.
- Moved to: raw/_ingested/2026-05-16-agcoach-CLAUDE.md

---

## 2026-05-16 14:00 — agcoach-BUSINESS_BRAIN.md

- Type: source (business-level product/monetization/architecture overview)
- Pages created (1): [[wiki/sources/agcoach-business-brain]]
- Concepts extracted: contributed to agcoach-pricing-tiers, agcoach-contest-modules, agcoach-rag-architecture, agcoach-billing-systems
- Domains linked: 01-AG-COACH-PRO
- Open questions: None.
- Moved to: raw/_ingested/2026-05-16-agcoach-BUSINESS_BRAIN.md

---

## 2026-05-16 14:00 — agcoach-SCHEMA.md

- Type: source (Supabase schema — 47 tables, dual billing, pgvector)
- Pages created (1): [[wiki/sources/agcoach-schema]]
- Concepts extracted: contributed to agcoach-billing-systems, agcoach-rag-architecture, organizations/supabase
- Domains linked: 01-AG-COACH-PRO
- Open questions: Schema captured 2026-04-26 — may be slightly stale re: table counts.
- Moved to: raw/_ingested/2026-05-16-agcoach-SCHEMA.md

---

## 2026-05-16 14:00 — agcoach-CONSOLIDATED_SKILLS.md

- Type: source (15 development agent skills catalog)
- Pages created (1): [[wiki/concepts/agcoach-app-internal-skills-catalog]] (combined with CLAUDE.md skills)
- Domains linked: 01-AG-COACH-PRO
- Open questions: None. Per instructions, not creating individual skill pages — catalog page only.
- Moved to: raw/_ingested/2026-05-16-agcoach-CONSOLIDATED_SKILLS.md

---

## 2026-05-16 14:00 — agcoach-PROJECT_SUMMARY.md

- Type: source (early scaffold delivery document; older $450/school pricing model)
- Pages created (1): [[wiki/sources/agcoach-project-summary]]
- Domains linked: 01-AG-COACH-PRO
- Open questions: Pricing in this file ($450 flat) is superseded by current tiered model. Noted in wiki page.
- Moved to: raw/_ingested/2026-05-16-agcoach-PROJECT_SUMMARY.md

---

## 2026-05-16 14:00 — agcoach-PLAN_supabase_admin_data.md

- Type: source (7-phase plan: schema lock → Gravity Claw fix → admin page → views → skills cleanup)
- Pages created (1): [[wiki/sources/agcoach-plan-supabase-admin]]
- Domains linked: 01-AG-COACH-PRO
- Open questions: Unknown which phases are complete vs. pending as of 2026-05-16.
- Moved to: raw/_ingested/2026-05-16-agcoach-PLAN_supabase_admin_data.md

---

## 2026-05-16 14:00 — agcoach-progress.md

- Type: source (short dev journal, 2 entries from 2026-03-10)
- Pages created (1): [[wiki/sources/agcoach-progress-log]]
- Domains linked: 01-AG-COACH-PRO
- Open questions: None. Low-density file; content merged into source record.
- Moved to: raw/_ingested/2026-05-16-agcoach-progress.md

---

## 2026-05-16 14:00 — agcoach-findings.md

- Type: source (architecture discoveries and constraints from B.L.A.S.T. Architect phase)
- Pages created (1): [[wiki/sources/agcoach-findings]]
- Domains linked: 01-AG-COACH-PRO
- Open questions: None.
- Moved to: raw/_ingested/2026-05-16-agcoach-findings.md

---

## 2026-05-16 14:00 — agcoach-README.md

- Type: source (developer quickstart — initial scaffold state, somewhat outdated vs. current)
- Pages created (1): [[wiki/sources/agcoach-readme]]
- Domains linked: 01-AG-COACH-PRO
- Open questions: README reflects early state; current architecture in CLAUDE.md supersedes many details.
- Moved to: raw/_ingested/2026-05-16-agcoach-README.md

---

## 2026-05-16 14:00 — agcoach-agent-master-prompt.md

- Type: source (B.L.A.S.T. protocol system prompt for Antigravity platform agent)
- Pages created (1): [[wiki/sources/agcoach-agent-master-prompt]]
- Domains linked: 01-AG-COACH-PRO
- Open questions: None. B.L.A.S.T. = Blueprint, Link, Architect, Stylize, Trigger.
- Moved to: raw/_ingested/2026-05-16-agcoach-agent-master-prompt.md

---

## 2026-05-16 14:00 — agcoach-agent-global-rules.md

- Type: source (global rules for all app development agents)
- Pages created (1): [[wiki/sources/agcoach-agent-global-rules]]
- Domains linked: 01-AG-COACH-PRO
- Open questions: Brand colors in this file (#004B23 green primary) differ from CLAUDE.md (#001F4D navy). Older doc. Noted.
- Moved to: raw/_ingested/2026-05-16-agcoach-agent-global-rules.md

---

## 2026-05-16 14:00 — agcoach-landing-page-guardrails.md

- Type: source (4-rule protection spec for the premium landing page design)
- Pages created (1): [[wiki/sources/agcoach-landing-page-guardrails]]
- Domains linked: 01-AG-COACH-PRO
- Open questions: None. Very short file; ingest as-is.
- Moved to: raw/_ingested/2026-05-16-agcoach-landing-page-guardrails.md

---

## 2026-05-16 14:00 — agcoach-ffa-prerequisite-materials.md

- Type: source (sourcing guide for Farm Business Management textbooks)
- Pages created (1): [[wiki/sources/agcoach-ffa-prerequisite-materials]]
- Domains linked: 01-AG-COACH-PRO
- Open questions: Content pack referenced in this file may be in a local Claude session folder — not in vault.
- Moved to: raw/_ingested/2026-05-16-agcoach-ffa-prerequisite-materials.md

---

## 2026-05-16 14:00 — agcoach-ffa-resource-audit.md

- Type: source (gap analysis for 5 initial CDE/LDE modules + resource links)
- Pages created (5): [[wiki/sources/agcoach-ffa-resource-audit]], [[wiki/concepts/agcoach-vet-science-cde]], [[wiki/concepts/agcoach-livestock-judging-cde]], [[wiki/concepts/agcoach-meat-science-cde]], [[wiki/concepts/agcoach-creed-speaking-lde]]
- Domains linked: 01-AG-COACH-PRO
- Open questions: None. Dense resource doc.
- Moved to: raw/_ingested/2026-05-16-agcoach-ffa-resource-audit.md

---

## 2026-05-16 14:00 — agcoach-wool-study-guide.md

- Type: source (comprehensive Wool CDE study guide with grading tables, scorecards, glossary)
- Pages created (1): [[wiki/sources/agcoach-wool-study-guide]]
- Domains linked: 01-AG-COACH-PRO
- Open questions: None. High-quality content for RAG ingestion into knowledge_documents.
- Moved to: raw/_ingested/2026-05-16-agcoach-wool-study-guide.md

---

## 2026-05-16 14:00 — CONCEPT PAGES (extracted from above batch)

- Pages created (9 concept + 3 org pages):
  - [[wiki/concepts/agcoach-pricing-tiers]] — Greenhand/Blue & Gold/Lone Star Elite + Feed Bags
  - [[wiki/concepts/agcoach-contest-modules]] — 40 total, 4-screen pattern, 9-step add checklist
  - [[wiki/concepts/agcoach-rag-architecture]] — pgvector v1/v2/v3, taxonomy, Brain Accuracy v1
  - [[wiki/concepts/agcoach-billing-systems]] — dual system, biz_* vs legacy, Stripe webhook rules
  - [[wiki/concepts/agcoach-app-internal-skills-catalog]] — 15 dev agent skills + 10 session skills
  - [[wiki/concepts/agcoach-vet-science-cde]] — contest format, knowledge domains, gaps
  - [[wiki/concepts/agcoach-livestock-judging-cde]] — Bryan's specialty, phenotype analyzer
  - [[wiki/concepts/agcoach-meat-science-cde]] — USDA grading, marbling, yield grades
  - [[wiki/concepts/agcoach-creed-speaking-lde]] — 1000-pt rubric, judging criteria
  - [[wiki/organizations/supabase]] — project nkoyotdafqllgbpuklva, pgvector, Edge Functions
  - [[wiki/organizations/vercel]] — agcoachpro.com, prj_4xPOIb5yS0qzoJFmLstwRURR9KC9
  - [[wiki/organizations/stripe]] — annual invoices, PO support, webhook architecture
- Domains linked: 01-AG-COACH-PRO

---

## 2026-05-16 15:30 — Pass 2 — Ag Coach Pro remaining docs + arch

Batch ingest of 8 staged files (from repo `lucid-galileo-4ea119` worktree) + 4 new concept pages + skills-catalog refresh.

### Source pages created (8)

- [[wiki/sources/agcoach-agents-rules]] — pre-CLAUDE.md rules; mostly stale duplicate, 14-skill catalog & 47-table count both outdated
- [[wiki/sources/agcoach-gemini-schemas]] — InterviewResult + CreedResult JSON contracts (file dormant since 2026-03-10)
- [[wiki/sources/agcoach-task-plan-livestock-calc]] — 7-step 725-pt Livestock Contest Score Calculator blueprint
- [[wiki/sources/agcoach-advisor-intelligence-skill]] — 4 principles + PerformanceGap data model for teacher analytics
- [[wiki/sources/agcoach-deployment-guide]] — early Vercel deploy walkthrough; mostly superseded by GitHub→Vercel pipeline
- [[wiki/sources/agcoach-migration-drift-audit]] — 2026-05-15 incident; 53 remote-only + ~50 local-only migration versions
- [[wiki/sources/agcoach-egg-evaluation-feature]] — image-based air-cell measurement training spec
- [[wiki/sources/agcoach-poultry-judging-feature]] — full Poultry Eval module design + NotebookLM ingest plan

### Concept pages created (4)

- [[wiki/concepts/agcoach-edge-functions-architecture]] — 26 Deno fns grouped: AI proxies (4), RAG v1/v2/v3, auth & role (5), Stripe/billing (7), ops (6)
- [[wiki/concepts/agcoach-livestock-score-calculator]] — replaces coach spreadsheet; 725-pt math + scoring engine + 5 surfaces
- [[wiki/concepts/agcoach-poultry-judging-cde]] — sibling to vet-science/livestock/meat CDE pages; 6 categories, 30-MC contest exam
- [[wiki/concepts/agcoach-egg-evaluation-cde]] — Poultry subdomain; air cell USDA thresholds + 3-phase training design

### Concept pages updated (1)

- [[wiki/concepts/agcoach-app-internal-skills-catalog]] — in-app catalog refreshed 10→31 skills; grouped by purpose (module build / RAG / Supabase / UI / external)

### Skipped (intentional)

- `repomix-output.md` (39k-line snapshot dump, not source-of-truth)
- `EGG_EVAL_QUICK_START.md`, `EGG_EVAL_THIS_WEEK.md` (tactical subsets of egg-evaluation-feature)
- `POULTRY_IMPLEMENTATION_QUICK_START.md` (subset of poultry-judging-feature)
- `CONSOLIDATED_SKILLS.md` (already ingested Pass 1)

### Domains linked

01-AG-COACH-PRO (all pages)

### Open questions

- Should every individual edge function get its own wiki page? Pass-2 user choice was bundled-arch only. Revisit if a fn becomes a hot debug target.
- `AGENTS.md` in repo is now demonstrably stale (14 skills vs 31 real, 47 tables vs 50+, missing brain v2/v3, missing onboarding v2, missing dual billing). Recommend delete-or-rewrite during next dev session.
- 5 unresolved questions in egg-evaluation spec (image source, ground truth, cross-check, feedback timing, exterior grading mode) — Bryan to decide before build.

### Moved (8 files: `raw/_in-progress/` → `raw/_ingested/`)

`2026-05-16-agcoach-AGENTS.md`, `…-gemini.md`, `…-task_plan.md`, `…-advisor-intelligence-skill.md`, `…-deployment-guide.md`, `…-migration-drift.md`, `…-egg-evaluation-feature.md`, `…-poultry-judging-feature.md`

---

## 2026-05-16 16:15 — Pass 3 — Ag Coach Pro superpowers + brand + prompts + PDF inventory

### Sources created (4)

- [[wiki/sources/agcoach-brand-v0-docs]] — combines `docs/brand/{app_description,brand_style_guide}.md`; flags hard conflict with current CLAUDE.md brand (Cyber-Agronomy `#F2A900`/`#00f2ff`/pure black + "gamified" voice vs current Navy `#001F4D` / Gold `#D4A574` / dark glass + "gamified" forbidden)
- [[wiki/sources/agcoach-superpowers-plans]] — catalog of 10 `docs/superpowers/plans/*.md` LLM-executable plans (stripe-fix, cotton-scraper, ag-tech-gauntlet, livestock-phenotype-accuracy, admin-financial-panel, job-interview-voice-agent, teacher-role-bulletproof, brain-second-brain-rebuild, brain-personality, rag-taxonomy)
- [[wiki/sources/agcoach-superpowers-specs]] — catalog of 11 specs + 1 run; flags `livestock-premium-design` + brain v2 trio as awaiting impl; notes brain-v2 spec incorporated Codex adversarial review (C1–C3 / H1–H7 / M1–M5 / L1)
- [[wiki/sources/agcoach-ffa-pdf-inventory]] — index of 7 PDFs + 1 docx + 2 CSVs in `docs/` with suggested RAG categories (`FFA Knowledge`, `FFA Admin`, `Ag Issues`, `Livestock`)

### Concepts created (1)

- [[wiki/concepts/agcoach-prompt-catalog]] — 10 `lib/prompts/` files mapped to domains; missing `poultry-prompts.ts` flagged

### Domains linked

01-AG-COACH-PRO (all 5 pages)

### Skipped (intentional)

- 22 individual superpowers plan/spec files → bundled into two catalog pages (per-file pages would 4× the wiki for marginal lookup benefit)
- 7 PDFs / 2 CSVs in `docs/` → indexed not extracted (bulk text already belongs in pgvector via rag-knowledge-ingest)
- `Texas Livestock CDE Questions.numbers` → Apple Numbers source for the .csv sibling

### Open questions / punch list

- Brand v0 docs need rewrite-or-delete (currently mislead anyone reading them; "gamified" is now a forbidden voice term)
- 4 specs in "Awaiting plan" / "Design (pending impl)" — backlog: livestock-premium, brain-second-brain-rebuild (Codex-revised), brain-personality, rag-taxonomy (note: rag-taxonomy shipped per Decision 2026-05-16, spec may now be stale)
- Missing `lib/prompts/poultry-prompts.ts` blocks Poultry Eval CDE Phase 1

### Moved (2 raw → _ingested)

`2026-05-16-agcoach-brand-app-description.md`, `2026-05-16-agcoach-brand-style-guide.md`. The 22 superpowers files + 9 docs/ PDFs/CSVs were summarized in-place (not copied into raw/) — they remain in the repo, indexed via repo-relative `source_files` paths.

---

## 2026-05-16 — Pass 4 — 37 agcoach-pass2-* raw files (batch complete)

37 files prefixed `agcoach-pass2-*` staged for ingest. Majority were duplicate-prefix versions of files already processed in Pass 2/3 (brand docs, deployment guide, egg eval, poultry, migration drift, superpowers batch 1). New content extracted:

### New pages created (3)

- [[wiki/sources/agcoach-farm-business-management-content-pack]] — 825-line FBM content pack; 12 sections, 50+ questions, 243 economics terms, financial ratios, risk management framework
- [[wiki/concepts/agcoach-farm-business-management-cde]] — 1,200-pt FBM contest format, 7 knowledge domains, build status
- [[wiki/concepts/agcoach-brain-rules-accuracy]] — Brain chatbot → Brain v3 RPC wiring via Gemini Flash intent classifier + verification gate; eliminates subcategory retrieval misses

### Existing pages updated (3)

- [[wiki/sources/agcoach-superpowers-plans]] — added `brain-rules-accuracy` plan (11th plan; 2026-05-16)
- [[wiki/sources/agcoach-superpowers-specs]] — added `brain-rules-accuracy-design` spec (12th spec; 2026-05-16)
- [[wiki/index.md]] — updated to Pass 4; added 3 new concept + 1 new source entry

### Skipped (intentional merges/already-covered)

- `agcoach-pass2-docs-brand-*` (2) — duplicate of Pass 3 `agcoach-brand-v0-docs`
- `agcoach-pass2-docs-deployment_guide.md` — duplicate of Pass 2 `agcoach-deployment-guide`
- `agcoach-pass2-docs-EGG_EVAL_*` (2) + `agcoach-pass2-docs-EGG_EVALUATION_FEATURE.md` — duplicates of Pass 2 egg-evaluation
- `agcoach-pass2-docs-POULTRY_*` (2) — duplicates of Pass 2 poultry
- `agcoach-pass2-docs-migration-drift-2026-05-15.md` — duplicate of Pass 2 migration-drift
- `agcoach-pass2-docs-superpowers-runs-2026-05-15-brain-v2-smoke.md` — run already captured in specs catalog
- `agcoach-pass2-docs-superpowers-plans-*` (9 of 10) — already in Pass 3 plans catalog
- `agcoach-pass2-docs-superpowers-specs-*` (11 of 12) — already in Pass 3 specs catalog (wool-judging-module-design was already listed)
- `agcoach-pass2-ffa-AgCoachPro_Complete_Resource_Audit.md` — source material already captured in `agcoach-ffa-resource-audit` (Pass 1); new detail merged
- `agcoach-pass2-ffa-AgCoachPro_Prerequisite_Materials_Sourcing_Guide.md` — duplicate of Pass 1 `agcoach-ffa-prerequisite-materials`

### Moved (36 files → raw/_ingested/2026-05-16-agcoach-pass2-*)

All 36 pass2 files archived.

### Domains linked

01-AG-COACH-PRO (all new pages)

---

## 2026-05-16 — Step 3 — Gravity Claw cross-vault ingest (00_Core + 01_Bryan + 03_Decisions)

Cross-vault summary ingest from `/Volumes/Samsung PSSD T7/gravity-claw/memory/`. Pages link to originals via path — not copied.

### Pages created (4)

- [[wiki/gravity-claw/gc-memory-core]] — 9 durable truths + 7 Pinecone-indexed YouTube sources; source: `00_Core/MEMORY.md`
- [[wiki/gravity-claw/gc-soul]] — GC identity lock, voice rules, job order, business context; source: `00_Core/SOUL.md`
- [[wiki/gravity-claw/gc-bryan-context]] — Bryan working constraints + voice preference; source: `01_Bryan/bryan.md`
- [[wiki/gravity-claw/gc-decisions]] — 4 architecture decisions, 2026-05-02 log entry, 3 rejected/deferred ideas; source: `03_Decisions/`

### Sections updated (1)

- [[wiki/index.md]] — Added "Gravity Claw Memory" section with 4 entries

### Skipped (per instructions)

- `07_Daily/` — too many session logs, low signal
- `02_Businesses/`, `04_Lessons/`, `05_Projects/`, `06_Sources/` — out of scope for this pass (Core + Bryan + Decisions only)
- `00_Core/HEARTBEAT.md`, `WORKSPACE.md`, `OPENCLAW.md`, `AGENTS.md`, `CLAUDE.md`, `memory-map.md` — minor operational files, content captured in gc-memory-core and gc-decisions

### Domains linked

06-AI-WORKFLOW (all 4 pages)
2026-05-17T04:47:39Z — ingest finance/ — 4 monthly Apple Card statements + finance-overview.md (YTD ,023.65)
