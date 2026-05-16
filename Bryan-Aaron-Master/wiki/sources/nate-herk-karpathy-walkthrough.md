---
name: nate-herk-karpathy-walkthrough
type: source
tags: [youtube-transcript, llm-wiki, obsidian, claude-code, karpathy, second-brain]
source_files: [nate-herk-karpathy-walkthrough]
domains: [06-AI-WORKFLOW]
created: 2026-05-16
updated: 2026-05-16
---

# Nate Herk — Karpathy LLM Wiki Walkthrough

YouTube video where Nate Herk demonstrates how to implement Andrej Karpathy's LLM Wiki / second-brain pattern using Claude Code and Obsidian. Recorded April 2026.

## Core Claims

- Karpathy's original tweet on LLM knowledge bases went viral on X. He followed up with a GitHub Gist formalizing the idea, intentionally left vague to encourage customization.
- The system requires no vector database, embedding model, or chunking pipeline — just a folder of markdown files organized by Claude Code.
- One X user turned 383 scattered files + 100+ meeting transcripts into a compact wiki, dropping token usage 95% when querying with Claude.
- Nate ingested 36 YouTube transcripts in batch (~14 min). Claude created 23 wiki pages automatically with zero manual relationship-building.
- The AI 2027 article ingest took ~10 minutes and produced ~25 wiki pages.
- Hot cache (`hot.md`, ~500 chars) reduces token overhead for stateful agents by avoiding full wiki crawls on every turn.
- Wiki linting (health checks) catches orphan pages, inconsistent data, and surfaces article candidates.

## Setup Steps Shown

1. Download Obsidian (free), create a new vault.
2. Open vault folder in VS Code / terminal with Claude Code.
3. Paste Karpathy's Gist prompt + a custom system prompt into Claude Code.
4. Claude creates `raw/`, `wiki/` structure with `index.md`, `log.md`, `CLAUDE.md`.
5. Drop source into `raw/` (use Obsidian Web Clipper extension for web articles — configure destination to `raw/`).
6. Tell Claude to ingest; optionally give domain context first.
7. Claude extracts entities, writes wiki pages, updates index + log.
8. Repeat for each new source.

## Key Entities Mentioned

- **People:** [[../people/andrej-karpathy|Andrej Karpathy]], [[../people/nate-herk|Nate Herk]]
- **Concepts:** [[../concepts/llm-wiki-pattern|LLM Wiki Pattern]], [[../concepts/hot-cache|Hot Cache]], [[../concepts/wiki-linting|Wiki Linting]], [[../concepts/obsidian-web-clipper|Obsidian Web Clipper]]
- **Comparisons:** [[../comparisons/wiki-vs-rag|Wiki vs RAG]]
- **Analysis:** [[../analysis/why-wiki-compounds|Why Wiki Compounds]]

## Related

- [[../people/andrej-karpathy|Andrej Karpathy]]
- [[../people/nate-herk|Nate Herk]]
- [[../concepts/llm-wiki-pattern|LLM Wiki Pattern]]
- [[../comparisons/wiki-vs-rag|Wiki vs RAG]]
