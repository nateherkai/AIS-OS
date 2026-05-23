"""Six Pillars overview — load manifest, probe live status per member."""
import json
import os
import re
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).parent.parent
DATA = BASE / "data"
ROOT = BASE.parent


def _load_manifest() -> dict:
    with open(DATA / "pillars.json") as f:
        return json.load(f)


def _parse_connections() -> list:
    """Read connections.md into pillar members."""
    f = ROOT / "connections.md"
    if not f.exists():
        return []
    members = []
    for line in f.read_text().splitlines():
        m = re.match(r"^\|\s*\d+\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
        if m:
            domain, tool, mech, auth, checked = (s.strip() for s in m.groups())
            if domain == "Domain":
                continue
            status = "active" if "active" in auth.lower() or "live" in tool.lower() else (
                "inactive" if "not yet" in mech.lower() else "unknown"
            )
            members.append({
                "name": tool,
                "domain": domain,
                "mechanism": mech,
                "status": status,
                "last_checked": checked,
            })
    return members


def _probe_supabase() -> str:
    url = os.environ.get("EXPO_PUBLIC_SUPABASE_URL")
    if not url:
        return "unknown"
    try:
        req = urllib.request.Request(f"{url}/rest/v1/", headers={"apikey": os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")})
        with urllib.request.urlopen(req, timeout=3) as r:
            return "active" if r.status < 500 else "degraded"
    except Exception:
        return "inactive"


def _probe_pinecone() -> str:
    # Use GC env file since AIOS may not have key
    gc_env = Path("/Volumes/Samsung PSSD T7/hermes-claw/.env")
    if not gc_env.exists():
        return "unknown"
    return "active"  # presence of key implies connection


def _probe_obsidian() -> str:
    return "active" if Path("/Volumes/Samsung PSSD T7/hermes-claw/memory").exists() else "inactive"


def _probe_local_memory() -> str:
    return "active" if Path.home().joinpath(".claude/projects").exists() else "inactive"


PROBES = {
    "supabase": _probe_supabase,
    "pinecone": _probe_pinecone,
    "obsidian": _probe_obsidian,
    "local-memory": _probe_local_memory,
}


def build_pillars() -> dict:
    manifest = _load_manifest()
    out = []
    for p in manifest["pillars"]:
        pillar = {"id": p["id"], "name": p["name"], "icon": p.get("icon", "")}
        if p.get("from_file") == "connections.md":
            pillar["members"] = _parse_connections()
        else:
            members = []
            for m in p.get("members", []):
                m = dict(m)
                probe = m.pop("probe", None)
                if probe and probe in PROBES:
                    m["status"] = PROBES[probe]()
                m.setdefault("status", "active")
                members.append(m)
            pillar["members"] = members
        active = sum(1 for m in pillar["members"] if m.get("status") == "active")
        pillar["count"] = len(pillar["members"])
        pillar["active"] = active
        out.append(pillar)
    return {"pillars": out, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}


if __name__ == "__main__":
    print(json.dumps(build_pillars(), indent=2))
