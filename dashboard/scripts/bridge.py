"""Claude OS Bridge — two-way handshake between AIOS dashboard and Hermes."""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent
DATA = BASE / "data"
DREAMS = DATA / "dreams"

sys.path.insert(0, str(BASE / "scripts"))
from pillars import build_pillars
from memory_feed import build_feed as build_memory_feed
from memory_graph import build as build_memory_graph
from roi import compute as compute_roi
from supabase_client import get_schools, get_pipeline_summary
import notify_hermes

VERSION = "0.1.0"
NAME = "Ag Coach Pro AIOS"


def handshake() -> dict:
    return {
        "name": NAME,
        "version": VERSION,
        "ts": datetime.now().isoformat(),
        "scopes": ["pipeline", "dreams", "memory", "graph", "roi", "pillars"],
        "bridge_endpoints": ["/api/bridge/handshake", "/api/bridge/query", "/api/bridge/push"],
    }


def latest_dream() -> dict:
    if not DREAMS.exists():
        return {}
    files = sorted(DREAMS.glob("*.json"), reverse=True)
    if not files:
        return {}
    return json.loads(files[0].read_text())


def snapshot(scope: list[str] | None = None) -> dict:
    scope = scope or ["pipeline", "dreams", "memory", "graph", "roi", "pillars"]
    out = {"ts": datetime.now().isoformat(), "version": VERSION}

    if "pipeline" in scope:
        try:
            schools = get_schools()
            summ = get_pipeline_summary(schools)
            cold = []
            for s in summ["trials"]:
                created = datetime.fromisoformat(s["created_at"].replace("Z", "+00:00"))
                days = (datetime.now().astimezone() - created).days
                if days >= 14:
                    cold.append({"name": s["name"], "advisor": s.get("advisor_name", ""), "days": days})
            out["pipeline"] = {
                "paid": summ["paid_count"],
                "trial": summ["trial_count"],
                "goal": summ["school_goal"],
                "goal_gap": summ["school_goal"] - summ["paid_count"],
                "cold": cold,
            }
        except Exception as e:
            out["pipeline"] = {"error": str(e)}

    if "dreams" in scope:
        d = latest_dream()
        out["dreams"] = {
            "date": d.get("date"),
            "top": d.get("top_3", []),
            "total_recommendations": len(d.get("recommendations", [])),
        }

    if "memory" in scope:
        try:
            out["memory"] = build_memory_feed(limit=15)
        except Exception as e:
            out["memory"] = {"error": str(e)}

    if "graph" in scope:
        try:
            graph = build_memory_graph()
            out["graph"] = {
                "stats": graph.get("stats", {}),
                "dream_nodes": [n for n in graph.get("nodes", []) if n.get("kind") == "dream"][:12],
                "approval_nodes": [n for n in graph.get("nodes", []) if n.get("kind") == "approval"][:12],
                "agent_nodes": [n for n in graph.get("nodes", []) if n.get("kind") == "agent"][:5],
            }
        except Exception as e:
            out["graph"] = {"error": str(e)}

    if "roi" in scope:
        try:
            out["roi"] = compute_roi()
        except Exception as e:
            out["roi"] = {"error": str(e)}

    if "pillars" in scope:
        try:
            out["pillars"] = build_pillars()
        except Exception as e:
            out["pillars"] = {"error": str(e)}

    return out


def authorize(headers: dict) -> bool:
    expected = os.environ.get("BRIDGE_TOKEN", "")
    if not expected:
        return False
    return headers.get("x-bridge-token") == expected or headers.get("X-Bridge-Token") == expected


# CLI smoke test
def _test():
    print("=== HANDSHAKE ===")
    print(json.dumps(handshake(), indent=2))
    print("\n=== SNAPSHOT (pipeline+dreams only) ===")
    print(json.dumps(snapshot(["pipeline", "dreams"]), indent=2)[:1500])
    print("\n=== TELEGRAM TEST ===")
    res = notify_hermes.post("✅ AIOS bridge online — smoke test " + datetime.now().strftime("%H:%M"))
    print(json.dumps(res, indent=2))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="run smoke test")
    parser.add_argument("--snapshot", action="store_true", help="print full snapshot JSON")
    parser.add_argument("--handshake", action="store_true", help="print handshake")
    args = parser.parse_args()
    if args.test:
        sys.exit(_test())
    if args.snapshot:
        print(json.dumps(snapshot(), indent=2))
    elif args.handshake:
        print(json.dumps(handshake(), indent=2))
    else:
        parser.print_help()
