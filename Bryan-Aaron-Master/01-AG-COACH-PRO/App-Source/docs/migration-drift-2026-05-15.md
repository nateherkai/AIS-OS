# Migration Drift Audit — 2026-05-15

**Status:** BLOCKING brain-v2 deploy. Repo-hygiene problem, predates current branch.

## Symptom

`npx supabase db push --dry-run` fails on `feat/brain-v2`:

> Remote migration versions not found in local migrations directory.

`npx supabase db pull` also fails — drift is bidirectional.

## Root cause

Supabase tracking table (`supabase_migrations.schema_migrations` on prod project `nkoyotdafqllgbpuklva`) and local `supabase/migrations/` directory have diverged on **both sides**:

### A. Remote-only versions (53) — applied to prod, never saved as files

Likely cause: prior sessions called `mcp__claude_ai_Supabase__apply_migration` (or used Studio SQL editor) without committing the corresponding file to git. Schema change is live; repo has no record.

Versions:

```
050 051 052 053 054 055 056 057 058 059 060
062 063 064 065 066 067 068 069 070 071
20260425000200 20260428024804
20260503213555 20260503214427 20260503220049
20260506184234 20260506190300 20260506192833 20260506194830
20260509061624 20260509061631
20260510213824 20260511152447
20260512170853 20260512170917 20260512173353
20260513202943 20260513202947 20260513203006 20260513203010
20260514003059 20260514010837 20260514013345 20260514014447 20260514014840 20260514022652
20260515023133 20260515025727 20260515025806 20260515034609 20260515034913 20260515141419
```

### B. Local-only files (~50) — in repo, never recorded as applied

Files sit in `supabase/migrations/` but tracking table has no row. Schema state of each is unknown — may already exist in prod (applied via MCP without recording) or may genuinely be missing.

CLI-suggested versions to mark `applied`:

```
0500 050..074 (numbered legacy)
20260506120000 ... 20260513220000 (timestamped pre-brain-v2)
20260515014446 20260515020000 20260515030000  ← onboarding-v2
20260515030500 20260515031000 20260515141349  ← THIS BRANCH (brain-v2 + health-watch)
```

**Trap:** CLI's auto-fix would mark `20260515030500`, `20260515031000`, `20260515141349` as `applied` — they have NOT actually run. Brain-v2 RPC + tables would never be created, edge function `match-knowledge-v2` would 500.

## Why CLI auto-fix is unsafe

`supabase migration repair --status applied <ver>` writes a row to the tracking table without executing the SQL. For files where the SQL is already in prod schema (applied via MCP), this is correct. For files where it isn't, this silently skips a real DDL change forever.

Cannot trust CLI to know the difference. Requires human judgment per-file.

## Triage path (when ready to fix)

For each local-only migration file:

1. Read the file, identify what objects it creates/alters.
2. Query prod (`mcp__claude_ai_Supabase__execute_sql` or psql) to check if those objects exist with the right shape.
3. If present → `supabase migration repair --status applied <ver>`.
4. If absent → leave unrepaired so `db push` runs it. (Or run manually + then repair.)

For each remote-only version (53):

1. Pull SQL of that version from `supabase_migrations.schema_migrations.statements` column (Supabase stores executed SQL).
2. Create matching file under `supabase/migrations/<version>_<inferred_name>.sql`.
3. Commit. Tracking now matches repo.

OR accept the loss:

- `supabase migration repair --status reverted <ver>` for all 53. Tracking forgets them. Repo never gains the source. Future `db pull` would regenerate as schema snapshot. Acceptable if you don't care about migration provenance going forward.

## Recommendation

Before brain-v2 ships:

1. **Quick path:** Apply just the 3 brain-v2 SQL files directly via `mcp__claude_ai_Supabase__apply_migration` (which both runs SQL and records the version). Skip `db push` entirely until drift is cleaned. Brain-v2 ships today; drift cleanup deferred.

2. **Right path:** Block brain-v2 deploy. Spend a focused session walking the triage above. Resolves drift, makes `db push` work again going forward.

Bryan to pick.

## Pinned facts (so future Claude sessions don't repeat)

- Prod project ref: `nkoyotdafqllgbpuklva`.
- Past sessions used `apply_migration` MCP without committing files. Stop doing this. Every applied migration MUST have a matching committed file under `supabase/migrations/`.
- Two parallel migration numbering schemes in repo (legacy `NNN_*.sql` and timestamp `YYYYMMDDHHMMSS_*.sql`) — both shown in tracking table, both must be reconciled.
- CLI repair commands are NOT idempotent against unknown schema state. Don't run them on autopilot.
