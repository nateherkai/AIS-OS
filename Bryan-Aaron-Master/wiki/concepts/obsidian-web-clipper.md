---
name: obsidian-web-clipper
type: concept
tags: [obsidian, browser-extension, ingest, web-article, capture-tool]
source_files: [nate-herk-karpathy-walkthrough]
domains: [06-AI-WORKFLOW]
created: 2026-05-16
updated: 2026-05-16
---

# Obsidian Web Clipper

A Chrome browser extension that captures web articles directly into an Obsidian vault folder. Used as a frictionless front-end for the LLM Wiki ingest pipeline.

## Setup for LLM Wiki

1. Install "Obsidian Web Clipper" from Chrome Web Store.
2. Open extension options → Location → change from default `clippings/` to `raw/`.
3. When on any article, click the extension → "Add to Obsidian" → "Open Obsidian."
4. The raw article file lands in `raw/` with title, source URL, and partial content.
5. Tell Claude Code to ingest the new file.

## Notes

- The file that lands in `raw/` is not fully populated — just the metadata + raw HTML capture. Claude Code does the classification and extraction.
- Obsidian itself is not strictly necessary for the LLM Wiki pattern — it's just a visual interface for the markdown files. The vault works with any text editor.
- Karpathy himself uses Claude Code directly; Obsidian is Herk's UI preference.

## Related

- [[../concepts/llm-wiki-pattern|LLM Wiki Pattern]]
- [[../people/nate-herk|Nate Herk]]
- [[../sources/nate-herk-karpathy-walkthrough|Nate Herk Walkthrough]]
