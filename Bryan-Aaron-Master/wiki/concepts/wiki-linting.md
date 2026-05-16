---
name: wiki-linting
type: concept
tags: [health-check, maintenance, orphan-detection, llm-wiki, quality-control]
source_files: [nate-herk-karpathy-walkthrough]
domains: [06-AI-WORKFLOW]
created: 2026-05-16
updated: 2026-05-16
---

# Wiki Linting

Periodic LLM-driven health checks run over a wiki to maintain structure quality and surface improvement opportunities. Karpathy mentions this as a key maintenance step for LLM wiki vaults.

## What Linting Checks

- **Orphan pages:** Pages with no inbound or outbound links — violates the no-orphan rule.
- **Inconsistent data:** Conflicting claims across pages that reference the same entity.
- **Missing data:** Fields present in some pages but absent in similar pages (e.g., missing `domains` tag).
- **Stale entries:** Pages referencing outdated information that newer sources have superseded.
- **Broken crosslinks:** `[[links]]` pointing to pages that don't exist.
- **Unprocessed raw files:** Files in `raw/` not yet in the log.

## What Linting Can Trigger

- Web searches to fill in missing data on a page.
- Suggestions for new article candidates to fill relationship gaps.
- Merge proposals for duplicate entity pages.
- Questions back to the user for ambiguous classifications.

## Frequency

Run on demand (e.g., `/lint` command), daily, or weekly. Karpathy mentions running it periodically; Herk treats it as an optional maintenance step. This vault runs lint via `scripts/lint.py` and writes results to `dashboard/lint-report.md`.

## Related

- [[../concepts/llm-wiki-pattern|LLM Wiki Pattern]]
- [[../people/andrej-karpathy|Andrej Karpathy]]
- [[../sources/nate-herk-karpathy-walkthrough|Nate Herk Walkthrough]]
