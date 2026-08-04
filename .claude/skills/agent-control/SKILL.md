---
name: agent-control
description: Inspect and control Hermes agent on Railway. Show status, last messages, plugin health, push commands, deploy plugin updates, kill switch. Trigger on /agent, /hermes, "check agent", "deploy hermes", "kill hermes".
---

# Agent Control (Hermes)

Hermes is Bryan's personal AI agent, running on Railway. Replaced Gravity Claw (deprecated 2026-05-21). This skill is the control surface from inside the AIOS.

## Inputs

- One of these intents:
  - `status` — show Hermes service state, last deploy, log tail.
  - `logs [n]` — last n log lines (default 50).
  - `plugin <name> deploy` — push plugin update (delegates to `hermes-plugin-deploy` skill).
  - `command <text>` — send a Telegram-style command to Hermes (if API surface available).
  - `kill` — stop Hermes service (requires explicit confirmation).
  - `restart` — restart Hermes service.

## Logic

1. **Resolve project** — use Railway MCP `list_projects` + `list_services` to find Hermes service.
2. **Branch on intent:**
   - `status`: call `environment_status` + `service_metrics` + `list_deployments` (last 1). Show: state, last deploy ts, error rate, request count.
   - `logs`: call `get_logs` with tail=n.
   - `plugin <name> deploy`: invoke `hermes-plugin-deploy` skill — it knows the schema-wrap bug, toolset registration, OAuth refresh-token flow.
   - `command`: TODO — wire to Hermes API endpoint (write to `references/hermes-api.md` when wired).
   - `kill`: **require explicit "yes kill hermes" confirmation**. Then call Railway MCP to stop service. Never auto-confirm.
   - `restart`: call `deploy` on current commit.
3. **Write status snapshot** to `dashboard/data/hermes_status.json` for dashboard L7 to render.

## Hard rules

- **`kill` and `restart` are destructive** — require Bryan to type confirmation explicitly. No auto-kill from cron.
- **Never deploy plugin without `hermes-plugin-deploy`** — that skill has the schema-wrap fix and OAuth flow needed.
- **Never target Gravity Claw paths** (`/Volumes/Samsung PSSD T7/gravity-claw/`) for live agent action — those are archival.

## Output

For `status`:
```
Hermes — Railway service <service-id>
State: ACTIVE | last deploy 2026-05-21T14:02 (3m ago)
Error rate (1h): 0.2%
Requests (1h): 47
Last log line: <tail>
```

Also writes JSON to `dashboard/data/hermes_status.json`:
```json
{
  "ts": "...",
  "state": "ACTIVE",
  "last_deploy_ts": "...",
  "error_rate_1h": 0.002,
  "requests_1h": 47,
  "log_tail": ["..."]
}
```

## Verification

- `/agent status` → returns live Railway state + writes status JSON.
- `/agent logs 10` → returns 10 log lines.
- `/agent kill` → asks for confirmation, does NOT kill without it.

## Provenance

Built manually 2026-05-21 as L4 capability. Reuses `use-railway` + `hermes-plugin-deploy` skills.
