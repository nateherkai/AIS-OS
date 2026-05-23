# Upstream Kit Snapshot

Source: AIS-OS starter kit by Nate Herk (MIT). https://github.com/ — pristine template, placeholders.

## Snapshots

| Date | Path | Notes |
|------|------|-------|
| 2026-05-21 | `aios-main-snapshot-2026-05-21/` | Copy of upstream `AIS-OS-main/` as dropped into repo. Contains pristine `onboard`, `audit`, `level-up`, `3ms-framework.md`, intake template, placeholder `CLAUDE.md`. |

## Purpose

Kit-canonical reference. Read-only. Use for:
- Re-sync: diff against project root to spot template improvements upstream added.
- Re-onboard: rerun `/onboard` from clean intake if context goes stale.
- Provenance: prove which kit version this AIOS forked from.

## Do NOT

- Edit files inside snapshots. They are frozen.
- Run skills from snapshot paths. Skills live in `.claude/skills/` or `~/.claude/skills/`.
- Treat snapshot `CLAUDE.md` as live config — live config is at repo root.

## Re-sync workflow

```
diff -rq archives/aios-main-snapshot-2026-05-21 . | grep -v "Only in \."
```

Anything `Only in archives/...` = upstream file you might be missing.
Anything `differ` = your intentional drift; verify still intentional.
