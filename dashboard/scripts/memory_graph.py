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
    MAX_WORKSPACES = 16
    MAX_FILES_PER_WORKSPACE = 12

    # Center
    nodes.append({"id": "aios", "label": "AIOS", "kind": "core", "size": 14})

    # Workspaces — top-level dirs in .claude/projects
    projects_root = HOME / ".claude" / "projects"
    if projects_root.exists():
        workspaces = sorted(
            [d for d in projects_root.iterdir() if d.is_dir()],
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )
        for ws in workspaces[:MAX_WORKSPACES]:
            # Clean up label: take last meaningful segment of path-encoded name
            raw = ws.name.replace("-Users-aaronfamilylivestock-", "")
            raw = raw.replace("-Volumes-Samsung-PSSD-T7-", "")
            raw = raw.replace("--", "/").replace("-", " ").strip()
            label = raw.split()[-1] if raw else ws.name[:18]
            nid = f"ws:{ws.name}"
            nodes.append({"id": nid, "label": label[:18], "kind": "workspace", "size": 6})
            edges.append({"source": "aios", "target": nid})
            # Memory files inside
            mem = ws / "memory"
            if mem.exists():
                files = sorted(mem.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
                for f in files[:MAX_FILES_PER_WORKSPACE]:
                    fid = f"file:{f}"
                    age = now - f.stat().st_mtime
                    kind = "stale" if age > STALE_AGE else "file"
                    nodes.append({"id": fid, "label": f.stem[:20], "kind": kind, "size": 4})
                    edges.append({"source": nid, "target": fid})

    # Skills — under .claude/skills and AIS-OS .claude/skills
    for skills_root in [HOME / ".claude" / "skills", Path("/Volumes/Samsung PSSD T7/AIS-OS/.claude/skills")]:
        if not skills_root.exists():
            continue
        for s in [d for d in skills_root.iterdir() if d.is_dir()][:10]:
            sid = f"skill:{s.name}"
            nodes.append({"id": sid, "label": "/" + s.name, "kind": "skill", "size": 5})
            edges.append({"source": "aios", "target": sid})

    # Obsidian decisions — Gravity Claw vault under memory/06_Decisions or memory/02_Decisions or anywhere
    obsidian = GC / "memory"
    if obsidian.exists():
        decision_files = []
        for pattern in ("**/Decisions/*.md", "**/decisions/*.md", "**/decision*.md"):
            decision_files.extend(obsidian.glob(pattern))
        for f in decision_files[:10]:
            did = f"dec:{f.name}"
            nodes.append({"id": did, "label": f.stem[:24], "kind": "decision", "size": 5})
            edges.append({"source": "aios", "target": did})
        # Workspace-tagged daily notes (sessions)
        daily = obsidian / "07_Daily"
        if daily.exists():
            for f in sorted(daily.glob("*.md"))[-6:]:
                sid = f"sess:{f.name}"
                age = now - f.stat().st_mtime
                kind = "stale" if age > STALE_AGE else "session"
                nodes.append({"id": sid, "label": f.stem, "kind": kind, "size": 4})
                edges.append({"source": "aios", "target": sid})

    # Vector indexes
    env = _gc_env_keys()
    if env.get("PINECONE_INDEX_NAME"):
        vid = f"vec:{env['PINECONE_INDEX_NAME']}"
        nodes.append({"id": vid, "label": env["PINECONE_INDEX_NAME"], "kind": "vector", "size": 8})
        edges.append({"source": "aios", "target": vid})

    # Domain hubs — big anchor nodes representing each 01-07 vault domain folder
    # These give the graph clear central structures (like Obsidian's hub-and-spoke)
    domain_hubs = [
        ("01-AG-COACH-PRO",          "Ag Coach Pro",          "domain", 22),
        ("02-AARON-FAMILY-LIVESTOCK","Aaron Family Livestock","domain", 20),
        ("03-TEACHING",              "Teaching",              "domain", 16),
        ("04-FINANCES",              "Finances",              "domain", 14),
        ("05-PERSONAL",              "Personal",              "domain", 14),
        ("06-AI-WORKFLOW",           "AI Workflow",           "domain", 18),
        ("07-RESOURCES",             "Resources",             "domain", 14),
    ]
    vault_root_check = Path("/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master")
    for slug, label, kind, size in domain_hubs:
        if (vault_root_check / slug).exists():
            did = f"domain:{slug}"
            nodes.append({"id": did, "label": label, "kind": kind, "size": size})
            edges.append({"source": "aios", "target": did})
    # Special anchors — Business Brain + CLAUDE.md as big standalone hubs
    bb = vault_root_check / "Business_Brain.md"
    if bb.exists():
        nodes.append({"id": "anchor:business-brain", "label": "Business Brain", "kind": "anchor", "size": 20})
        edges.append({"source": "aios", "target": "anchor:business-brain"})
    cmd = vault_root_check / "CLAUDE.md"
    if cmd.exists():
        nodes.append({"id": "anchor:claude-md", "label": "CLAUDE", "kind": "anchor", "size": 18})
        edges.append({"source": "aios", "target": "anchor:claude-md"})

    # Vault wiki nodes — Karpathy LLM Wiki, subkinded for visual layer + cross-linked
    wiki_palette = {
        "sources": "wiki-source",
        "people": "wiki-person",
        "organizations": "wiki-org",
        "concepts": "wiki-concept",
        "comparisons": "wiki-comparison",
        "analysis": "wiki-analysis",
    }
    wiki_size = {
        "sources": 5,
        "people": 6,
        "organizations": 6,
        "concepts": 5,
        "comparisons": 4,
        "analysis": 4,
    }
    vault_root = Path("/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master")
    wiki_nodes_raw = load_vault_wiki_nodes(vault_root)
    existing_ids = {n["id"] for n in nodes}
    wiki_ids = {f"wiki:{wn['id']}" for wn in wiki_nodes_raw}
    for wn in wiki_nodes_raw:
        nid = f"wiki:{wn['id']}"
        if nid in existing_ids:
            continue
        nodes.append({
            "id": nid,
            "label": wn["id"][:24],
            "kind": wiki_palette.get(wn["type"], "wiki"),
            "size": wiki_size.get(wn["type"], 7),
            "path": wn["path"],
        })
        # Connect to domain hub(s) instead of just AIOS — gives graph structure
        connected_to_domain = False
        for slug, label, kind, size in [
            ("01-AG-COACH-PRO",          "Ag Coach Pro",          "domain", 22),
            ("02-AARON-FAMILY-LIVESTOCK","Aaron Family Livestock","domain", 20),
            ("03-TEACHING",              "Teaching",              "domain", 16),
            ("04-FINANCES",              "Finances",              "domain", 14),
            ("05-PERSONAL",              "Personal",              "domain", 14),
            ("06-AI-WORKFLOW",           "AI Workflow",           "domain", 18),
            ("07-RESOURCES",             "Resources",             "domain", 14),
        ]:
            label_lower = wn["id"].lower()
            slug_key = slug.lower().replace("0", "").replace("-", "")
            # Heuristic: agcoach-* → ag-coach-pro, etc.
            if (
                ("agcoach" in label_lower and "01" in slug) or
                ("livestock" in label_lower and "02" in slug) or
                ("teaching" in label_lower and "03" in slug) or
                ("finance" in label_lower and "04" in slug) or
                ("nate-herk" in label_lower and "06" in slug) or
                ("jack-roberts" in label_lower and "06" in slug) or
                ("karpathy" in label_lower and "06" in slug) or
                ("wiki" in label_lower and "06" in slug) or
                ("dream" in label_lower and "06" in slug) or
                ("hot-cache" in label_lower and "06" in slug) or
                ("obsidian" in label_lower and "06" in slug) or
                ("os" in label_lower and "06" in slug)
            ):
                did = f"domain:{slug}"
                if did in existing_ids:
                    edges.append({"source": did, "target": nid})
                    connected_to_domain = True
                    break
        if not connected_to_domain:
            edges.append({"source": "aios", "target": nid})
        existing_ids.add(nid)
    # Crosslinks BETWEEN wiki nodes — fires the neural map
    for wn in wiki_nodes_raw:
        src = f"wiki:{wn['id']}"
        for tgt_stem in wn["edges"]:
            tgt_clean = tgt_stem.replace(".md", "").strip()
            tgt = f"wiki:{tgt_clean}"
            if tgt in wiki_ids and tgt != src:
                edges.append({"source": src, "target": tgt})

    # ── Gravity Claw cluster ─────────────────────────────────────
    # Hub node connecting GC vault memory files to AIOS
    gc_hub_id = "gc:gravity-claw"
    if GC.exists():
        nodes.append({"id": gc_hub_id, "label": "Gravity Claw", "kind": "gc-hub", "size": 12})
        edges.append({"source": "aios", "target": gc_hub_id})
        existing_ids.add(gc_hub_id)

        # Key memory files from GC vault
        gc_priority_files = [
            GC / "memory" / "00_Core" / "MEMORY.md",
            GC / "memory" / "00_Core" / "SOUL.md",
            GC / "memory" / "00_Core" / "CLAUDE.md",
            GC / "memory" / "01_Bryan" / "bryan.md",
        ]
        for gf in gc_priority_files:
            if gf.exists():
                gfid = f"gc-file:{gf.name}"
                age = now - gf.stat().st_mtime
                kind = "stale" if age > STALE_AGE else "gc-file"
                nodes.append({"id": gfid, "label": gf.name, "kind": kind, "size": 4})
                edges.append({"source": gc_hub_id, "target": gfid})
                existing_ids.add(gfid)

        # Walk all GC memory sub-folders for additional files (cap 20)
        gc_extra_count = 0
        for sub in sorted((GC / "memory").iterdir()):
            if not sub.is_dir() or gc_extra_count >= 20:
                break
            for gf in sorted(sub.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)[:3]:
                gfid = f"gc-file:{sub.name}-{gf.name}"
                if gfid in existing_ids:
                    continue
                age = now - gf.stat().st_mtime
                kind = "stale" if age > STALE_AGE else "gc-file"
                nodes.append({"id": gfid, "label": f"{sub.name}/{gf.stem}", "kind": kind, "size": 3})
                edges.append({"source": gc_hub_id, "target": gfid})
                existing_ids.add(gfid)
                gc_extra_count += 1

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
        "wiki": counts.get("wiki", 0),
        "gc_files": counts.get("gc-file", 0),
        "nodes_total": len(nodes),
        "edges_total": len(edges),
    }

    return {"nodes": nodes, "edges": edges, "stats": stats}


def load_vault_wiki_nodes(vault_root):
    """Walk vault wiki, return nodes with type + edges from [[links]]."""
    from pathlib import Path
    import re
    vault_root = Path(vault_root)
    wiki = vault_root / "wiki"
    if not wiki.exists():
        return []
    link_re = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
    nodes = []
    for md in wiki.rglob("*.md"):
        if md.name in {"index.md", "log.md", "hot.md"}:
            continue
        try:
            text = md.read_text()
        except Exception:
            continue
        links = [m.group(1).strip().split("/")[-1] for m in link_re.finditer(text)]
        nodes.append({
            "id": md.stem,
            "type": md.parent.name,  # sources/people/concepts/...
            "edges": links,
            "path": str(md.relative_to(vault_root)),
        })
    return nodes


if __name__ == "__main__":
    result = build()
    wiki_nodes = load_vault_wiki_nodes("/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master")
    print(f"# Vault wiki nodes: {len(wiki_nodes)}", flush=True)
    for n in wiki_nodes:
        print(f"  [{n['type']}] {n['id']}  edges={n['edges'][:3]}", flush=True)
    print(json.dumps(result, indent=2))
