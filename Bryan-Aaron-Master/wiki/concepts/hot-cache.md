---
name: hot-cache
type: concept
tags: [token-efficiency, memory, context-management, claude-code, llm-wiki]
source_files: [nate-herk-karpathy-walkthrough]
domains: [06-AI-WORKFLOW]
created: 2026-05-16
updated: 2026-05-16
---

# Hot Cache

A `hot.md` file at the root of the wiki directory that stores a ≤500-character plain-text summary of the most recently ingested material or most recent session context. Designed to be read first by any AI agent before crawling the full wiki.

## Purpose

Reduces token overhead for stateful AI agents. Instead of reading 10+ wiki pages to regain session context, the agent reads one tiny file and gets enough orientation to know whether a deeper wiki read is needed.

## Usage Pattern

- **Written:** Overwritten (not appended) at the end of every ingest or wrapup operation.
- **Read:** First thing an agent reads when opening a vault session.
- **Scope:** Covers what just changed, not a full vault summary.
- **Limit:** 500 chars max — discipline enforced by convention, not by the file system.

## When It Matters

Nate Herk notes that in his executive assistant project ("Herc 2"), adding the hot cache measurably reduced tokens called per session. In a pure research vault (e.g., his YouTube transcript project), the hot cache adds less value because the agent doesn't need recency — it just queries on demand.

## Anti-patterns

- Making `hot.md` too long defeats the purpose — it becomes another wiki page to crawl.
- Not updating `hot.md` after ingest means it reflects stale context.

## Related

- [[../concepts/llm-wiki-pattern|LLM Wiki Pattern]]
- [[../people/nate-herk|Nate Herk]]
- [[../sources/nate-herk-karpathy-walkthrough|Nate Herk Walkthrough]]
