# Gravity Claw ⇄ Ag Coach Pro AIOS Bridge — Install Prompt

Paste this section verbatim into `/Volumes/Samsung PSSD T7/gravity-claw/CLAUDE.md`
under a new `## AIOS Bridge` heading. Tells Gravity Claw how to reach the
local AIS-OS dashboard for live context.

---

## AIOS Bridge

Bryan runs a local AIOS dashboard at `https://typically-junction-joyce-handle.trycloudflare.com` (FastAPI). It
exposes a bridge endpoint that returns a snapshot of his Ag Coach Pro state:
pipeline (paid / trial / cold), today's "dream" recommendations, recent
memory writes, ROI, and Six Pillars status.

**When to call it:**

- Bryan asks "what's my pipeline today?" / "how many schools?" / "any
  trials going cold?"
- Bryan asks "what dreams did I get?" / "any new recommendations?"
- Bryan asks "what's my ROI?" / "am I spending too much on AI?"
- Bryan asks "what got remembered today?" / "any new memory writes?"
- Cross-platform question that needs AIOS state — pull snapshot before
  answering.

**How to call:**

```bash
curl -s -X POST https://typically-junction-joyce-handle.trycloudflare.com/api/bridge/query \
  -H "X-Bridge-Token: $AIOS_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scope": ["pipeline","dreams","memory","roi","pillars"]}'
```

Response shape:

```json
{
  "ts": "<iso>",
  "version": "0.1.0",
  "pipeline": {"paid": N, "trial": N, "goal": 50, "goal_gap": N, "cold": [...]},
  "dreams":   {"date": "...", "top": [ {...}, {...}, {...} ], "total_recommendations": N},
  "memory":   {"items": [ {source, ts, summary, path}, ... ]},
  "roi":      {"monthly_ai_spend": N, "monthly_value_saved": N, "net_roi": N, "flags": [...]},
  "pillars":  {"pillars": [ {id, name, members, count, active}, ... ]}
}
```

Set `AIOS_BRIDGE_TOKEN` in your `.env` to the same value as the dashboard's
`BRIDGE_TOKEN` env var.

**Handshake (no auth required):** `GET https://typically-junction-joyce-handle.trycloudflare.com/api/bridge/handshake`
returns service identity. Use to verify the bridge is up before relying on it.

**Failure mode:** if curl times out or returns 5xx, tell Bryan "AIOS
dashboard offline — start with `bash dashboard/launch.sh`" rather than
guessing answers from stale state.
