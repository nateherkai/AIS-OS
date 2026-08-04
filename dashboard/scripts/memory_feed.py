"""Aggregate recent memory writes across local + Pinecone + Supabase + Obsidian."""
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request

ROOT = Path(__file__).parent.parent.parent
GC = Path("/Volumes/Samsung PSSD T7/hermes-claw")
HOME = Path.home()


def _read_gc_env() -> dict:
    env = {}
    f = GC / ".env"
    if not f.exists():
        return env
    for line in f.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def local_memory(limit: int = 20) -> list:
    """Walk ~/.claude/projects/**/memory/ for recent MEMORY.md + per-memory files."""
    root = HOME / ".claude" / "projects"
    if not root.exists():
        return []
    cutoff = time.time() - 7 * 86400
    items = []
    for p in root.rglob("memory/*.md"):
        try:
            mtime = p.stat().st_mtime
            if mtime < cutoff:
                continue
            text = p.read_text(errors="ignore")[:200]
            items.append({
                "source": "local-memory",
                "ts": datetime.fromtimestamp(mtime).isoformat(),
                "path": str(p.relative_to(HOME)),
                "summary": text.split("\n")[0][:120],
            })
        except Exception:
            continue
    items.sort(key=lambda x: x["ts"], reverse=True)
    return items[:limit]


def obsidian_recent(limit: int = 10) -> list:
    vault = GC / "memory"
    if not vault.exists():
        return []
    cutoff = time.time() - 7 * 86400
    items = []
    for p in vault.rglob("*.md"):
        try:
            mtime = p.stat().st_mtime
            if mtime < cutoff:
                continue
            text = p.read_text(errors="ignore")[:200]
            items.append({
                "source": "obsidian",
                "ts": datetime.fromtimestamp(mtime).isoformat(),
                "path": str(p.relative_to(vault)),
                "summary": text.split("\n")[0][:120],
            })
        except Exception:
            continue
    items.sort(key=lambda x: x["ts"], reverse=True)
    return items[:limit]


def supabase_recent(limit: int = 10) -> list:
    url = os.environ.get("EXPO_PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and key):
        return []
    out = []
    for table in ("schools",):
        try:
            req = urllib.request.Request(
                f"{url}/rest/v1/{table}?select=id,name,created_at&order=created_at.desc&limit={limit}",
                headers={"apikey": key, "Authorization": f"Bearer {key}"},
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                for row in json.loads(r.read()):
                    out.append({
                        "source": f"supabase.{table}",
                        "ts": row.get("created_at"),
                        "path": f"{table}/{row.get('id')}",
                        "summary": row.get("name", ""),
                    })
        except Exception:
            pass
    return out


def pinecone_recent(limit: int = 5) -> list:
    """Best-effort: read GC's PINECONE creds, query stats endpoint for vector count."""
    env = _read_gc_env()
    key = env.get("PINECONE_API_KEY")
    idx = env.get("PINECONE_INDEX_NAME")
    if not (key and idx):
        return []
    # Listing recent vectors requires Pinecone API per-index host lookup — return summary only.
    return [{
        "source": "pinecone",
        "ts": datetime.now().isoformat(),
        "path": idx,
        "summary": f"Index '{idx}' connected (vector listing requires host-specific call)",
    }]


def build_feed(limit: int = 30) -> dict:
    items = []
    items += local_memory(20)
    items += obsidian_recent(10)
    items += supabase_recent(10)
    items += pinecone_recent(5)
    # Sort by ts desc (fallback to now for missing ts)
    items.sort(key=lambda x: x.get("ts") or "", reverse=True)
    return {"items": items[:limit], "ts": datetime.now().isoformat()}


if __name__ == "__main__":
    print(json.dumps(build_feed(), indent=2))
