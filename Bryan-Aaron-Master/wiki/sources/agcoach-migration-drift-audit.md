---
name: agcoach-migration-drift-audit
type: source
tags: [ag-coach-pro, supabase, migrations, drift, incident]
source_files: [raw/_ingested/2026-05-16-agcoach-migration-drift.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Migration Drift Audit (2026-05-15)

`docs/migration-drift-2026-05-15.md`. Blocked `npx supabase db push` on `feat/brain-v2`; root cause = past sessions ran `mcp__claude_ai_Supabase__apply_migration` without committing matching SQL files.

## Symptoms

- `npx supabase db push --dry-run` → "Remote migration versions not found in local migrations directory."
- `npx supabase db pull` also fails. Drift is bidirectional.

## Two drift sets

**A. Remote-only (53 versions)** — applied to prod project `nkoyotdafqllgbpuklva`, never saved as files. Spans legacy `050..071` plus timestamped `20260425000200` → `20260515141419`.

**B. Local-only (~50 files)** — in `supabase/migrations/`, never recorded as applied. Schema state unknown — may already exist in prod (silent MCP apply) or genuinely missing.

## Why CLI auto-fix is unsafe

`supabase migration repair --status applied <ver>` writes a row to the tracking table without executing SQL. Safe only when the file's objects already exist in prod with the right shape. Otherwise the DDL is silently skipped forever — e.g., marking the 3 brain-v2 files as applied without running them would leave `match_knowledge_v2` RPC missing and the edge function 500ing.

## Triage path

For each local-only file: read → check if objects exist in prod (`mcp__claude_ai_Supabase__execute_sql`) → repair as `applied` if present, leave for `db push` if absent.

For each remote-only version: pull SQL from `supabase_migrations.schema_migrations.statements`, create matching file, commit. Or accept the loss with `repair --status reverted` (forgets it, no source preserved).

## Recommendation (Bryan to pick)

1. **Quick:** apply brain-v2 files via `apply_migration` MCP (records + runs in one). Ship today; defer cleanup.
2. **Right:** block deploy, walk full triage. Restores `db push` going forward.

## Pinned discipline

- Every applied migration MUST have a matching committed file under `supabase/migrations/`.
- Two numbering schemes coexist — legacy `NNN_*.sql` (grandfathered through ~073) and timestamp `YYYYMMDDHHMMSS_*.sql` (all new).
- CLI repair commands are NOT idempotent against unknown schema state.

## Related

- [[agcoach-schema|Supabase Schema]]
- [[../organizations/supabase|Supabase]]
- [[../concepts/agcoach-rag-architecture|RAG Architecture]]
- [[../concepts/agcoach-billing-systems|Billing Systems]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
