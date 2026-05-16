"""Build nodes + edges for the Memory Graph visualization.

Categories (color-mapped client-side):
  core      — AIS-OS center
  workspace — .claude/projects directories
  file      — memory .md files
  decision  — Obsidian decision notes
  session   — Pinecone vector index references
  skill     — installed skills
  stale     — files unchanged > 30 days
"""
import json
import os
import time
from pathlib import Path
from collections import defaultdict

HOME = Path.home()
GC = Path("/Volumes/Samsung PSSD T7/gravity-claw")
GC_ENV = GC / ".env"


def _gc_env_keys():
    if not GC_ENV.exists():
        return {}
    out = {}
    for line in GC_ENV.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def build():
    nodes = []
    edges = []
    now = time.time()
    STALE_AGE = 30 * 86400

    # Center
    nodes.append({"id": "aios", "label": "AIOS", "kind": "core", "size": 22})

    # Workspaces — top-level dirs in .claude/projects
    projects_root = HOME / ".claude" / "projects"
    if projects_root.exists():
        for ws in [d for d in projects_root.iterdir() if d.is_dir()][:8]:
            nid = f"ws:{ws.name}"
            nodes.append({"id": nid, "label": ws.name[:24], "kind": "workspace", "size": 12})
            edges.append({"source": "aios", "target": nid})
            # Memory files inside
            mem = ws / "memory"
            if mem.exists():
                for f in list(mem.glob("*.md"))[:6]:
                    fid = f"file:{f}"
                    age = now - f.stat().st_mtime
                    kind = "stale" if age > STALE_AGE else "file"
                    nodes.append({"id": fid, "label": f.stem[:20], "kind": kind, "size": 7})
                    edges.append({"source": nid, "target": fid})

    # Skills — under .claude/skills and AIS-OS .claude/skills
    for skills_root in [HOME / ".claude" / "skills", Path("/Volumes/Samsung PSSD T7/AIS-OS/.claude/skills")]:
        if not skills_root.exists():
            continue
        for s in [d for d in skills_root.iterdir() if d.is_dir()][:10]:
            sid = f"skill:{s.name}"
            nodes.append({"id": sid, "label": "/" + s.name, "kind": "skill", "size": 8})
            edges.append({"source": "aios", "target": sid})

    # Obsidian decisions — Gravity Claw vault under memory/06_Decisions or memory/02_Decisions or anywhere
    obsidian = GC / "memory"
    if obsidian.exists():
        decision_files = []
        for pattern in ("**/Decisions/*.md", "**/decisions/*.md", "**/decision*.md"):
            decision_files.extend(obsidian.glob(pattern))
        for f in decision_files[:10]:
            did = f"dec:{f.name}"
            nodes.append({"id": did, "label": f.stem[:24], "kind": "decision", "size": 9})
            edges.append({"source": "aios", "target": did})
        # Workspace-tagged daily notes (sessions)
        daily = obsidian / "07_Daily"
        if daily.exists():
            for f in sorted(daily.glob("*.md"))[-6:]:
                sid = f"sess:{f.name}"
                age = now - f.stat().st_mtime
                kind = "stale" if age > STALE_AGE else "session"
                nodes.append({"id": sid, "label": f.stem, "kind": kind, "size": 7})
                edges.append({"source": "aios", "target": sid})

    # Vector indexes
    env = _gc_env_keys()
    if env.get("PINECONE_INDEX_NAME"):
        vid = f"vec:{env['PINECONE_INDEX_NAME']}"
        nodes.append({"id": vid, "label": env["PINECONE_INDEX_NAME"], "kind": "vector", "size": 14})
        edges.append({"source": "aios", "target": vid})

    counts = defaultdict(int)
    for n in nodes:
        counts[n["kind"]] += 1

    stats = {
        "workspaces": counts.get("workspace", 0),
        "memory_files": counts.get("file", 0) + counts.get("stale", 0),
        "vector_indexes": counts.get("vector", 0),
        "skills": counts.get("skill", 0),
        "decisions": counts.get("decision", 0),
        "sessions": counts.get("session", 0),
        "stale": counts.get("stale", 0),
        "nodes_total": len(nodes),
        "edges_total": len(edges),
    }

    return {"nodes": nodes, "edges": edges, "stats": stats}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
