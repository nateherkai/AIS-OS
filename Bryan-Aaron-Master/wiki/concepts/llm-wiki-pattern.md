---
name: llm-wiki-pattern
type: concept
tags: [knowledge-management, second-brain, claude-code, obsidian, karpathy, markdown, indexing]
source_files: [nate-herk-karpathy-walkthrough]
domains: [06-AI-WORKFLOW]
created: 2026-05-16
updated: 2026-05-16
---

# LLM Wiki Pattern

A knowledge management architecture originated by Andrej Karpathy. Raw sources are dropped into a `raw/` folder; Claude Code reads them, extracts entities, and writes crosslinked markdown wiki pages into a `wiki/` folder. No vector database, embeddings, or chunking pipeline required.

## Structure

```
vault/
├── raw/              ← drop sources here (articles, transcripts, PDFs)
│   └── _ingested/    ← archive after processing
├── wiki/
│   ├── index.md      ← auto-maintained table of contents with [[links]]
│   ├── log.md        ← append-only operation history
│   ├── hot.md        ← 500-char recent-context cache
│   ├── sources/
│   ├── people/
│   ├── organizations/
│   ├── concepts/
│   ├── analysis/
│   └── comparisons/
└── CLAUDE.md         ← schema + ingest rules for the AI
```

## How It Works

1. **Ingest:** Claude reads raw file, classifies it, extracts entities (people, orgs, concepts, claims).
2. **Write:** One wiki page per entity in YAML-frontmatter markdown. Summary only — no verbatim copy.
3. **Crosslink:** Every page has ≥1 outbound link. Index and log updated each run.
4. **Query:** Start at `index.md`, follow `[[links]]`. Read `hot.md` for recent context. Rarely need to touch `raw/`.
5. **Lint:** Periodic health checks find orphan pages, stale entries, missing crosslinks.

## Why It Works at Small Scale

LLMs navigate well-organized markdown faster than RAG retrieval because they can read a whole index in one pass, follow links semantically, and reason about relationships — not just match embeddings. Karpathy noted this works well up to ~100 articles / 500k words. Beyond millions of docs, traditional RAG wins on cost.

## Key Design Choices

- **Flat or subfolder wiki:** Karpathy prefers flat for simplicity; Herk uses subfolders for topic-rich projects (e.g. 36 YouTube transcripts). Both valid.
- **Hot cache:** A `hot.md` file with ≤500 chars of recent context is a token-efficiency trick for stateful agents.
- **CLAUDE.md as schema:** Tells the AI how the vault is organized, what each folder is for, and how to ingest/query.

## Adoption Signal

Karpathy's original tweet on this went viral on X (April 2026). Within days, community implementations appeared. One user: 383 files + 100 meeting transcripts → compact wiki, 95% token reduction for queries.

## Related

- [[../people/andrej-karpathy|Andrej Karpathy]]
- [[../people/nate-herk|Nate Herk]]
- [[../concepts/hot-cache|Hot Cache]]
- [[../concepts/wiki-linting|Wiki Linting]]
- [[../comparisons/wiki-vs-rag|Wiki vs RAG]]
- [[../analysis/why-wiki-compounds|Why Wiki Compounds]]
