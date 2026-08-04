# Cadence — Automation Registry

Every scheduled job and event hook running for AIS-OS. Kill switch for each is documented inline.

> **Activation:** the launchd plists in this file are NOT installed automatically. Run `scripts/install_cadence.sh` to load them, or install individually with `launchctl load <plist>`. Crontabs (Linux) shown for portability.

## Schedule overview

| Job | When | Skill / Script | Kill |
|---|---|---|---|
| Nightly dream | every day 02:00 | `dashboard/scripts/dream_machine.py` (existing) | `launchctl unload ~/Library/LaunchAgents/com.agcoachpro.aios.dream.plist` |
| Hot-cache refresh | every day 02:30 | `~/.claude/skills/hot-update` via `claude -p` shell | unload `com.agcoachpro.aios.hot.plist` |
| Revenue snapshot | every day 06:00 | `scripts/revenue_snapshot.py` | unload `com.agcoachpro.aios.revenue.plist` |
| Trial follow-up drafts | Mon 07:00 | `trial-follow-up` skill via `claude -p` | unload `com.agcoachpro.aios.trial.plist` |
| Eval regression | Sun 21:00 | `eval` skill | unload `com.agcoachpro.aios.eval.plist` |
| Vault lint | Fri 18:00 | `wiki-lint` skill | unload `com.agcoachpro.aios.lint.plist` |

## Hook overview (Claude Code events)

Live in `~/.claude/settings.json` (user-global) or `.claude/settings.json` (project). Currently **none installed for this project** — listed as intended:

| Event | Action | Why |
|---|---|---|
| `SessionStart` | (handled by CLAUDE.md instructions) read MEMORY.md + hot.md | Already in place via CLAUDE.md, no hook needed |
| `Stop` | write `dashboard/data/last_session_end.json` (ts + cwd) | Lets dashboard show "last active session". Cheap shell, no LLM. |

Stop hook snippet to add to `.claude/settings.json` when ready:

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "echo \"{\\\"ts\\\":\\\"$(date -Iseconds)\\\",\\\"cwd\\\":\\\"$PWD\\\"}\" > \"/Volumes/Samsung PSSD T7/AIS-OS/dashboard/data/last_session_end.json\""
      }]
    }]
  }
}
```

## Per-job launchd plists

All plists live in `~/Library/LaunchAgents/`. Install via `launchctl load <plist>`. Each writes stdout/stderr to `~/Library/Logs/aios/<job>.log`.

### Revenue snapshot — 06:00 daily

`~/Library/LaunchAgents/com.agcoachpro.aios.revenue.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.agcoachpro.aios.revenue</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/env</string>
    <string>python3</string>
    <string>/Volumes/Samsung PSSD T7/AIS-OS/scripts/revenue_snapshot.py</string>
  </array>
  <key>WorkingDirectory</key><string>/Volumes/Samsung PSSD T7/AIS-OS</string>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>6</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>/Users/aaronfamilylivestock/Library/Logs/aios/revenue.log</string>
  <key>StandardErrorPath</key><string>/Users/aaronfamilylivestock/Library/Logs/aios/revenue.err</string>
</dict></plist>
```

### Trial follow-up — Mon 07:00

Uses headless Claude Code to run the skill. Requires `claude` CLI on PATH and a permission policy that allows the skill's Bash calls.

```xml
<!-- com.agcoachpro.aios.trial.plist -->
<plist version="1.0"><dict>
  <key>Label</key><string>com.agcoachpro.aios.trial</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/env</string>
    <string>bash</string>
    <string>-lc</string>
    <string>cd "/Volumes/Samsung PSSD T7/AIS-OS" && claude -p "/trial-follow-up draft-only" --output-format text</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>/Users/aaronfamilylivestock/Library/Logs/aios/trial.log</string>
  <key>StandardErrorPath</key><string>/Users/aaronfamilylivestock/Library/Logs/aios/trial.err</string>
</dict></plist>
```

### Eval regression — Sun 21:00

```xml
<!-- com.agcoachpro.aios.eval.plist -->
<plist version="1.0"><dict>
  <key>Label</key><string>com.agcoachpro.aios.eval</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/env</string>
    <string>bash</string>
    <string>-lc</string>
    <string>cd "/Volumes/Samsung PSSD T7/AIS-OS" && claude -p "/eval" --output-format text</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict><key>Weekday</key><integer>0</integer><key>Hour</key><integer>21</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>/Users/aaronfamilylivestock/Library/Logs/aios/eval.log</string>
  <key>StandardErrorPath</key><string>/Users/aaronfamilylivestock/Library/Logs/aios/eval.err</string>
</dict></plist>
```

### Hot-cache refresh + Vault lint

Same pattern — `claude -p "/hot"` and `claude -p "/lint"` respectively. Generate via `scripts/install_cadence.sh`.

## Global kill switch

```bash
launchctl list | grep com.agcoachpro.aios | awk '{print $3}' | xargs -I{} launchctl unload ~/Library/LaunchAgents/{}.plist
```

Tears down every AIOS cron in one command. Keep this in muscle memory.

## When something fires unexpectedly

1. Check `~/Library/Logs/aios/<job>.log` for stdout, `<job>.err` for traceback.
2. Disable single job: `launchctl unload ~/Library/LaunchAgents/com.agcoachpro.aios.<job>.plist`.
3. Investigate root cause before re-enabling. Don't `--no-verify` the diagnosis.

## Autonomy posture

Default for this AIOS: **auto for internal, draft for external**. That means:
- Revenue snapshot, eval, lint, dream, hot-update → auto-run.
- Trial follow-up, content drafts → auto-DRAFT to `drafts/`, Bryan approves and sends manually.
- Hermes kill / restart / deploy → never auto. Always Bryan confirms.
