---
name: gc-decisions
type: source
tags: [gravity-claw, operator-brain, decisions, architecture, accuracy, memory]
source_files: [/Volumes/Samsung PSSD T7/gravity-claw/memory/03_Decisions/DECISION_CONTEXT.md, /Volumes/Samsung PSSD T7/gravity-claw/memory/03_Decisions/log.md, /Volumes/Samsung PSSD T7/gravity-claw/memory/03_Decisions/REJECTED_IDEAS.md]
domains: [06-AI-WORKFLOW]
created: 2026-05-16
updated: 2026-05-16
---

# Gravity Claw — Decisions

Summary wiki mirror of GC decision files under `/Volumes/Samsung PSSD T7/gravity-claw/memory/03_Decisions/`.

## Architecture Decisions

### Pinecone First For RAG
- **Decision:** Pinecone = primary RAG store for video transcripts + semantic source memory
- **Reason:** Already powers GC vector memory. Supabase tables for YouTube metadata were absent; dashboard is secondary.
- **Result:** YouTube RAG → Pinecone namespace `knowledge`; local artifacts under `data/youtube/<videoId>/`

### OpenClaw as Pattern Source
- **Decision:** OpenClaw = lineage + pattern inspiration, NOT upstream dependency to blindly copy
- **Reason:** GC has business-specific tools, voice, ACP workflows. Cherry-pick what improves security, memory, model routing, operator quality.

### Accuracy Stack
- **Decision:** Improve accuracy via durable daily logs, accuracy report, stricter factuality rules
- **Reason:** Agent drift pattern — identity/operating rules/lessons/decisions not written down, searchable, or protected from compaction
- **Result:** `/accuracy` reports current stack; daily logs in `memory/07_Daily/`; final replies pass QA gate for unsupported numbers, dates, contacts, customer/business facts

### Red-Line Guardrails
- **Decision:** Andrew's 10 OpenClaw red lines in `AGENTS.md`; highest-risk lines enforced in runtime tool loop
- **Reason:** Agent mistakes become expensive at live systems, permissions, deletions, deployments, or outside people
- **Result:** `src/agent/red-lines.ts` blocks live execution, permanent deletion, access-control changes, client-facing sends

### Obsidian + Pinecone Memory
- **Decision:** Durable context in readable Markdown + local Markdown indexing path into Pinecone
- **Reason:** Jack Roberts' Obsidian pattern — human-editable reasoning + scalable recall. GC already had files + Pinecone; needed bridge for inspectable AND searchable memory
- **Result:** `memory/00_Core/memory-map.md` maps layers; `/rag_docs` previews/indexes local Markdown into `knowledge` namespace

## Decisions Log (2026-05-02)

- Adopted AIS-OS useful parts as GC operating discipline, not as replacement framework
- Reason: GC has real business integrations; missing leverage = auditability, repeatable capabilities, cadence
- Follow-up: Add `/audit`, preserve `ops/` layer, then add weekly `/level-up`

## Rejected / Deferred Ideas

| Idea | Status | Reason |
|---|---|---|
| Supabase as required YouTube RAG storage | Rejected | Pinecone is the correct source memory store |
| Replace GC wholesale with OpenClaw upstream | Rejected | Cherry-pick patterns instead |
| Mission Control dashboard views for RAG sources | Deferred | Useful later, not required for current retrieval |

## Related

- [[gc-memory-core|Core Memory]]
- [[gc-soul|Identity Core]]
- [[../../06-AI-WORKFLOW/_AI-Workflow-Home|AI Workflow domain home]]
- [[../../wiki/concepts/agcoach-rag-architecture|Ag Coach Pro RAG Architecture]] (different Pinecone index — ACP uses Supabase pgvector, not this Pinecone)
