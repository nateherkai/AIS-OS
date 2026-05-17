---
name: agcoach-superpowers-specs
type: source
tags: [ag-coach-pro, specs, superpowers, design, catalog]
source_files: [repo:/docs/superpowers/specs/, repo:/docs/superpowers/runs/, raw/_ingested/2026-05-16-agcoach-pass2-docs-superpowers-specs-2026-05-16-brain-rules-accuracy-design.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Superpowers Specs + Runs Catalog

`docs/superpowers/specs/` = 11 design specs; `docs/superpowers/runs/` = 1 run record. Each spec is the **why + decisions** counterpart to a plan in [[agcoach-superpowers-plans|Plans catalog]]. Runs capture smoke / verification outputs.

## Specs (11)

| Date | Spec | Status | Focus |
|---|---|---|---|
| 2026-05-04 | `cotton-image-scraper-design` | Approved | Image acquisition pipeline + Supabase Storage layout for cotton grades |
| 2026-05-06 | `wool-judging-module-design` | Approved | Full Wool CDE module (Expo Router / React Native / Supabase / Gemini AI) |
| 2026-05-08 | `ag-tech-gauntlet-design` | (n/a) | Replace `app/practice/ag-tech/math-drill.tsx` with adaptive Formula Gauntlet |
| 2026-05-08 | `livestock-premium-design` | Awaiting plan | Premium upgrade to Livestock module (no impl plan yet) |
| 2026-05-10 | `livestock-phenotype-accuracy-design` | Approved (pending plan) | Phase 1 of 3: accuracy foundation (P2 = visual overlays, P3 = 3D/video scan) |
| 2026-05-12 | `admin-financial-panel-design` | Approved | Superadmin financial KPIs |
| 2026-05-12 | `job-interview-rag-voice-agent-design` | Approved | RAG-based question generation + ElevenLabs voice |
| 2026-05-13 | `teacher-role-bulletproof-design` | Approved | Driven by Trinity / Athens ISD incident — three role-integrity guarantees |
| 2026-05-15 | `ai-brain-second-brain-rebuild-design` | Awaiting plan; **revision v2 — incorporates Codex adversarial review findings (C1–C3, H1–H7, M1–M5, L1)** | Hardened Brain v2 architecture |
| 2026-05-15 | `brain-personality-design` | Design (pending impl) | Ag-teacher voice + concision rules |
| 2026-05-15 | `rag-taxonomy-design` | Design (pending impl) | Subcategory backfill + retrieval boost |
| 2026-05-16 | `brain-rules-accuracy-design` | Design — pending user review | Brain chatbot → v3 RPC wiring via intent classifier + verification gate; eliminates slaughter-cattle-grading-style retrieval miss |

## Runs (1)

- **2026-05-15 `brain-v2-smoke`** — Branch `feat/brain-v2`. Harness `scripts/smoke-brain-v2.ts` (server-side CLI, bypasses edge-fn JWT via service-role client). Pipeline: embed (Gemini RETRIEVAL_QUERY, 3072d) → `match_knowledge_v2` RPC → `wrapChunk` → Gemini 2.0 Flash w/ 6 brain tools → strip confidence tail → validate citations.

## Pattern observations

- All recent specs (May 2026) follow `Date / Status / Owner` header.
- Specs that hit "Approved" usually spawn matching plan within 1–7 days; "Awaiting plan" specs are the build backlog.
- `ai-brain-second-brain-rebuild-design` is the only spec to call out external adversarial review (Codex C1–C3 etc.) — Brain v2 hardening pattern.

## Related

- [[agcoach-superpowers-plans|Superpowers Plans catalog]]
- [[../concepts/agcoach-rag-architecture|RAG Architecture]] (brain v2/v3 lineage)
- [[../sources/agcoach-app-working-instructions|App Working Instructions]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
