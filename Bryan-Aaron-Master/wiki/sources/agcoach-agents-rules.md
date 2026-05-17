---
name: agcoach-agents-rules
type: source
tags: [ag-coach-pro, rules, agents, conventions]
source_files: [raw/_ingested/2026-05-16-agcoach-AGENTS.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — AGENTS.md (Coding Conventions)

Pre-CLAUDE.md rules file consumed by any agent touching the codebase. Mostly merged into the canonical [[agcoach-app-working-instructions|App Working Instructions]] page; this entry captures the few facts unique to `AGENTS.md`.

## Distinct vs CLAUDE.md

- Skills catalog lists only **14** in-app session skills (vs 31 in repo today and 10 in current CLAUDE.md catalog) — `AGENTS.md` is stale.
- References `47` Supabase public tables (CLAUDE.md says `50+` — schema grew).
- Pinecone CLI path written as `~/.Codex/pinecone_memory.py` (likely copy-paste typo for `~/.claude/`).
- No mention of Brain v2/v3, onboarding v2, dual billing systems, or cron auth — predates 2026-05-15 work.

## Status

Outdated companion to [[agcoach-app-working-instructions|CLAUDE.md]]. Either delete from repo or keep as the lowest-common-denominator rules set for non-Claude agents.

## Related

- [[agcoach-app-working-instructions|App Working Instructions (CLAUDE.md)]]
- [[../concepts/agcoach-app-internal-skills-catalog|App Internal Skills Catalog]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
