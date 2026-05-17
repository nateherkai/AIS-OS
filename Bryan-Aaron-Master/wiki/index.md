# Wiki Index

Updated: 2026-05-16 (Pass 5 — Gravity Claw memory cross-vault ingest)

## Tools

- [[concepts/obsidian-web-clipper|Obsidian Web Clipper]] — Chrome extension to clip web articles into vault `raw/`

## Techniques

- [[concepts/wiki-linting|Wiki Linting]] — periodic LLM health checks over the wiki; finds orphans, stale data, article candidates

## Concepts

- [[concepts/llm-wiki-pattern|LLM Wiki Pattern]] — Karpathy's raw/ → wiki/ architecture; no vector DB needed
- [[concepts/hot-cache|Hot Cache]] — ≤500-char `hot.md` for stateful agents; reduces token overhead
- [[concepts/claude-code-os|Claude Code OS]] — visual intelligence dashboard unifying models, memory, skills, knowledge, connections
- [[concepts/dreaming-engine|Dreaming Engine]] — nightly automated analysis → four high-leverage morning recommendations
- [[concepts/six-pillars-os|Six Pillars OS]] — Models, Plans, Memory, Skills, Knowledge, Connections framework
- [[concepts/eight-dim-dream-intelligence|Eight Dimensions of Dream Intelligence]] — eight input streams that feed the Dreaming Engine
- [[concepts/agcoach-pricing-tiers|Ag Coach Pro — Pricing Tiers]] — Greenhand $495 / Blue & Gold $895 / Lone Star Elite $1,495; Feed Bags $100/1M credits
- [[concepts/agcoach-contest-modules|Ag Coach Pro — Contest Modules (40)]] — 29 CDEs + 11 LDEs; 4-screen practice module pattern; 9-step checklist to add new module
- [[concepts/agcoach-rag-architecture|Ag Coach Pro — RAG Architecture]] — pgvector 3072-dim, Gemini Flash, match-knowledge v1/v2/v3, taxonomy classification
- [[concepts/agcoach-billing-systems|Ag Coach Pro — Billing Systems (Dual)]] — legacy schools/subscriptions vs current biz_* chapter-level tables
- [[concepts/agcoach-app-internal-skills-catalog|Ag Coach Pro — App Internal Skills Catalog]] — 15 development agent skills + 31 in-session Claude skills
- [[concepts/agcoach-vet-science-cde|Ag Coach Pro — Veterinary Science CDE]] — contest format, knowledge domains, resources, gaps
- [[concepts/agcoach-livestock-judging-cde|Ag Coach Pro — Livestock Judging CDE]] — Bryan's specialty; format, scoring, phenotype analyzer
- [[concepts/agcoach-meat-science-cde|Ag Coach Pro — Meat Science CDE]] — USDA grading systems, marbling scores, yield grades
- [[concepts/agcoach-creed-speaking-lde|Ag Coach Pro — Creed Speaking LDE]] — 1,000-pt AI video scoring rubric, judging criteria
- [[concepts/agcoach-poultry-judging-cde|Ag Coach Pro — Poultry Judging CDE]] — 6-category contest; 30-MC exam; RAG + NotebookLM pipeline
- [[concepts/agcoach-egg-evaluation-cde|Ag Coach Pro — Egg Evaluation CDE]] — image-based air-cell measurement training (Poultry subdomain)
- [[concepts/agcoach-edge-functions-architecture|Ag Coach Pro — Edge Functions Architecture]] — 26 Deno fns: AI proxies, RAG v1/v2/v3, auth, Stripe, ops
- [[concepts/agcoach-livestock-score-calculator|Ag Coach Pro — Livestock Contest Score Calculator]] — 725-pt blueprint; replaces coach spreadsheet
- [[concepts/agcoach-prompt-catalog|Ag Coach Pro — Prompt Catalog]] — 10 `lib/prompts/` files, per-domain Gemini system prompts + rubrics
- [[concepts/agcoach-farm-business-management-cde|Ag Coach Pro — Farm Business Management CDE]] — 1,200-pt contest format, economics domains, pre-built content pack
- [[concepts/agcoach-brain-rules-accuracy|Ag Coach Pro — Brain Rules Accuracy (v3 Wiring)]] — intent classifier + verification gate; eliminates subcategory retrieval misses

## Sources

- [[sources/nate-herk-karpathy-walkthrough|Nate Herk — Karpathy LLM Wiki Walkthrough]] — YT transcript, April 2026
- [[sources/jack-roberts-cc-os-walkthrough|Jack Roberts — Claude Code OS Walkthrough]] — YT transcript, 2026
- [[sources/inbox-home|00-INBOX Home]] — legacy Obsidian landing page, archived
- [[sources/agcoach-app-working-instructions|Ag Coach Pro — App Working Instructions (CLAUDE.md)]] — authoritative dev rules, architecture, decisions
- [[sources/agcoach-business-brain|Ag Coach Pro — Business Brain]] — product, monetization, users, features, architecture
- [[sources/agcoach-schema|Ag Coach Pro — Supabase Schema]] — 47 tables, dual billing systems, pgvector RAG
- [[sources/agcoach-project-summary|Ag Coach Pro — Project Summary]] — initial scaffold delivery, early financial projections
- [[sources/agcoach-plan-supabase-admin|Ag Coach Pro — Supabase + Admin + Gravity Claw Plan]] — 7-phase plan to connect real data
- [[sources/agcoach-progress-log|Ag Coach Pro — Dev Progress Log]] — B.L.A.S.T. initialization journal
- [[sources/agcoach-findings|Ag Coach Pro — Findings Notes]] — architecture discoveries and constraints
- [[sources/agcoach-readme|Ag Coach Pro — README]] — developer quickstart, project structure
- [[sources/agcoach-agent-master-prompt|Ag Coach Pro — B.L.A.S.T. Master Prompt]] — System Pilot identity, 5-phase build protocol
- [[sources/agcoach-agent-global-rules|Ag Coach Pro — Agent Global Rules]] — global rules for all app agents
- [[sources/agcoach-landing-page-guardrails|Ag Coach Pro — Landing Page Guardrails]] — protect premium landing page design
- [[sources/agcoach-ffa-resource-audit|Ag Coach Pro — FFA Resource Audit]] — gap analysis for 5 initial CDE/LDE modules
- [[sources/agcoach-ffa-prerequisite-materials|Ag Coach Pro — Prerequisite Materials Sourcing Guide]] — Farm Business Management textbook sourcing
- [[sources/agcoach-wool-study-guide|Ag Coach Pro — Wool & Mohair Study Guide]] — comprehensive Wool CDE content with grading systems + scorecards
- [[sources/agcoach-agents-rules|Ag Coach Pro — AGENTS.md (Coding Conventions)]] — pre-CLAUDE.md rules file; mostly stale duplicate
- [[sources/agcoach-gemini-schemas|Ag Coach Pro — Gemini Data Schemas]] — InterviewResult + CreedResult JSON contracts
- [[sources/agcoach-task-plan-livestock-calc|Ag Coach Pro — Task Plan: Livestock Score Calculator]] — 7-step 725-pt blueprint
- [[sources/agcoach-advisor-intelligence-skill|Ag Coach Pro — Advisor Intelligence Skill]] — 4 principles + PerformanceGap data model
- [[sources/agcoach-deployment-guide|Ag Coach Pro — Deployment Guide (Vercel)]] — early pitch-day deploy; mostly superseded
- [[sources/agcoach-migration-drift-audit|Ag Coach Pro — Migration Drift Audit (2026-05-15)]] — 53 remote-only + ~50 local-only versions blocking `db push`
- [[sources/agcoach-egg-evaluation-feature|Ag Coach Pro — Egg Evaluation Feature]] — image-based air-cell measurement design spec
- [[sources/agcoach-poultry-judging-feature|Ag Coach Pro — Poultry Judging Feature]] — full module-design + NotebookLM integration plan
- [[sources/agcoach-brand-v0-docs|Ag Coach Pro — Brand v0 docs]] — pre-rebrand "Cyber-Agronomy" style guide; flagged conflicts with CLAUDE.md
- [[sources/agcoach-superpowers-plans|Ag Coach Pro — Superpowers Plans Catalog]] — 11 LLM-executable implementation plans
- [[sources/agcoach-superpowers-specs|Ag Coach Pro — Superpowers Specs Catalog]] — 12 design specs + 1 run record
- [[sources/agcoach-ffa-pdf-inventory|Ag Coach Pro — FFA Source PDF Inventory]] — 7 PDFs + DOCX + CSVs in `docs/`; RAG ingest map
- [[sources/agcoach-farm-business-management-content-pack|Ag Coach Pro — Farm Business Management Content Pack]] — 12 sections, 50+ questions, 243 economics terms
- [[../01-AG-COACH-PRO/App-Source/_INDEX|Ag Coach Pro App Source Mirror]] (182 files)

## People

- [[people/andrej-karpathy|Andrej Karpathy]] — AI researcher; originator of the LLM Wiki pattern
- [[people/nate-herk|Nate Herk]] — YouTuber / AI educator; Up-to-AI; implemented Karpathy's pattern
- [[people/jack-roberts|Jack Roberts]] — AI builder / YouTuber; built Claude Code OS + Dreaming Engine

## Organizations

- [[organizations/supabase|Supabase]] — PostgreSQL + pgvector + Auth + Edge Functions; Ag Coach Pro project `nkoyotdafqllgbpuklva`
- [[organizations/vercel|Vercel]] — Web hosting for agcoachpro.com; project `prj_4xPOIb5yS0qzoJFmLstwRURR9KC9`
- [[organizations/stripe|Stripe]] — Payment processing for annual site licenses; annual invoice model, PO support

## Comparisons

- [[comparisons/wiki-vs-rag|Wiki vs RAG]] — LLM Wiki vs semantic search RAG; when each applies

## Analysis

- [[analysis/why-wiki-compounds|Why Wiki Compounds]] — why this pattern creates compounding knowledge vs ephemeral AI chat
- [[analysis/visualization-layer-analysis|Visualization Layer Analysis]] — why visual AI dashboards are the next major trend

## Gravity Claw Memory

Mirror summaries of Bryan's separate operator AI vault (`/Volumes/Samsung PSSD T7/gravity-claw/memory/`). These are summary pages — not copies. Links back to original files via path.

- [[gravity-claw/gc-memory-core|Gravity Claw — Core Memory (MEMORY.md)]] — 9 durable truths, 7 indexed YouTube sources in Pinecone
- [[gravity-claw/gc-soul|Gravity Claw — Identity Core (SOUL.md)]] — persona lock, voice rules, primary job order, business context
- [[gravity-claw/gc-bryan-context|Gravity Claw — Bryan Operating Context]] — constraints, working schedule, voice preference
- [[gravity-claw/gc-decisions|Gravity Claw — Decisions]] — architecture decisions (Pinecone RAG, OpenClaw pattern, accuracy stack, red-line guardrails, Obsidian+Pinecone memory); decisions log; rejected ideas

## Domain Map

- Ag Coach Pro → [[../01-AG-COACH-PRO/]]
- AFL → [[../02-AARON-FAMILY-LIVESTOCK/]]
- Teaching → [[../03-TEACHING/]]
- Finances → [[../04-FINANCES/]]
- Personal → [[../05-PERSONAL/]]
- AI Workflow → [[../06-AI-WORKFLOW/]]
- Resources → [[../07-RESOURCES/]]
