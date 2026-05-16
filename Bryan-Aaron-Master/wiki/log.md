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
