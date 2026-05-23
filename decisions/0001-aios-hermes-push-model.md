# 0001 — AIOS ↔ Hermes: switch to push model

**Date:** 2026-05-22
**Status:** proposed
**Owner:** Bryan

## Context

Current bridge is **pull**: Hermes (Railway, always-on) calls `https://aios.agcoachos.com/api/bridge/query` to fetch live AIOS state.

This is broken in three ways:

1. `aios.agcoachos.com` is fronted by Cloudflare Access → returns 403 to Railway. Plugin never gets a snapshot.
2. AIOS dashboard runs on Bryan's MacBook (`localhost:8080`). Laptop sleeps, Wi-Fi drops, IP changes — Hermes loses the brain every night.
3. Pull means Hermes must know AIOS is reachable. Failure mode is silent: tool returns "AIOS offline", model proceeds without context, answers wrong.

## Decision

Invert direction. AIOS pushes a daily snapshot file into `hermes-claw/hermes/state/`. Hermes reads files (no network call).

### Architecture

```
┌──────────── laptop (intermittent) ───────────┐    ┌── Railway (always-on) ──┐
│  AIOS dashboard                              │    │  Hermes agent            │
│  ↓ 7am cron: snapshot.py                     │    │                          │
│  writes hermes/state/{pipeline,dreams,…}.json│ →  │  reads hermes/state/*    │
│  git commit + push to hermes-claw repo       │    │  on tool call            │
└──────────────────────────────────────────────┘    └──────────────────────────┘
                                                       Railway auto-redeploys
                                                       on git push to main
```

### State files written

- `hermes/state/pipeline.json` — paid/trial counts, goal gap, cold leads (≤10)
- `hermes/state/dreams.json` — today's top-3 dream cards
- `hermes/state/roi.json` — MRR/ARR vs spend, last 30d
- `hermes/state/pillars.json` — Six Pillars status snapshot
- `hermes/state/snapshot.meta.json` — `{generated_at, aios_version, files_written}`

All files token-free (no secrets). Hermes plugin reads at tool-invoke time.

## Why this beats the alternatives

| Option | Cost | Survives laptop offline | Survives ISP/DNS | Net |
|---|---|---|---|---|
| Status quo (Cloudflare 403) | $0 | ❌ | ❌ | dead |
| Cloudflare Access bypass | 30 min | ❌ | ❌ | papers over wrong arch |
| Move AIOS to Railway | $5/mo + port | ✅ | ✅ | overkill — AIOS is a dev tool, not a service |
| **Push model (this)** | **2 hrs build** | **✅** | **✅** | **right shape** |

## Implementation

1. **AIS-OS:** `dashboard/scripts/snapshot_for_hermes.py`
   - Reuses existing `bridge.py:snapshot()` logic
   - Writes to `$HERMES_CLAW/hermes/state/*.json`
   - Single commit per run, message: `state: AIOS snapshot YYYY-MM-DD HH:MM`
2. **macOS launchd** (or existing crontab) — run `snapshot_for_hermes.py` at 07:00 daily + on each `/wrapup`
3. **Hermes plugin:** new `aios_state_tool.py` (replaces `aios_query_tool.py`)
   - Reads `hermes/state/*.json` from local Railway volume
   - Returns same `{snapshot: {...}}` shape so model code unchanged
   - If files older than 24h: warn but return stale snapshot anyway
4. **Deprecate:**
   - `dashboard/scripts/bridge.py` query endpoint stays for ad-hoc curl tests, but no longer the primary path
   - `plugins/hermes_claw/aios.py` — leave as fallback OR delete after 2 weeks of push working
5. **Docs:** already updated `hermes-claw/CLAUDE.md` to reference state files; update `dashboard/bridge/install.md` after ship

## Rollout

- Day 1: build snapshot script, run by hand, verify Hermes reads files
- Day 2: wire launchd schedule
- Day 7: delete pull-tool fallback if no regressions

## Open questions

- Commit-per-snapshot bloats hermes-claw git history. Acceptable? Alternative: separate state branch with `--force` push (no history).
- What happens during week-long laptop offline? Stale snapshot returned with `stale_hours: N` field — Hermes can warn Bryan.
- Should snapshot also include `tasks.json` (in-flight work)? Likely yes — add to v1.
