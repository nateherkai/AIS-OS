"""Dream Machine — overnight analyzer of Claude Code transcripts.

Reads ~/.claude/projects/**/*.jsonl from last 24h, scores 8 dimensions,
emits dashboard/data/dreams/YYYY-MM-DD.json with ranked recommendations.

Budget: <30s on typical day. Skips files older than 24h.
"""
import hashlib
import json
import re
import sys
import time
import urllib.request
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path


def _redact_prompt(text: str) -> str:
    """Return a non-reversible 8-char content hash. Never persist raw user text."""
    if not isinstance(text, str):
        return ""
    return "hash:" + hashlib.sha1(text.encode()).hexdigest()[:8]


def _sanitize_detail(detail: dict) -> dict:
    """Strip raw user text from a recommendation detail. Keep aggregates."""
    if not isinstance(detail, dict):
        return detail
    out = dict(detail)
    if "prompt" in out:
        out["prompt_hash"] = _redact_prompt(out["prompt"])
        del out["prompt"]
    return out


def _redact_priority_minutes(priority: str) -> int:
    return {"high": 30, "medium": 15, "low": 5}.get(priority, 10)


def _build_cards(top_recs: list) -> list:
    """Project top recommendations into the dashboard's expected `cards` schema."""
    cards = []
    for i, r in enumerate(top_recs):
        cards.append({
            "id": f"d{i+1}",
            "dim": r.get("dimension", "unknown"),
            "title": (r.get("headline") or "")[:80],
            "insight": r.get("headline", ""),
            "action": ("Promote to skill or memory" if r.get("priority") == "high"
                       else "Review and decide"),
            "estimated_value_minutes": _redact_priority_minutes(r.get("priority", "low")),
            "status": "open",
        })
    return cards

HOME = Path.home()
BASE = Path(__file__).parent.parent
DREAMS_DIR = BASE / "data" / "dreams"
SKILLS_FILE = BASE / "data" / "skills.json"

CUTOFF_HOURS = 24
MAX_FILES = 200  # safety cap


def _recent_jsonl() -> list:
    """Return list of jsonl files mtime'd within CUTOFF_HOURS."""
    root = HOME / ".claude" / "projects"
    if not root.exists():
        return []
    cutoff = time.time() - CUTOFF_HOURS * 3600
    files = []
    for p in root.rglob("*.jsonl"):
        try:
            if p.stat().st_mtime >= cutoff:
                files.append(p)
        except Exception:
            continue
    return files[:MAX_FILES]


def _iter_events(files: list):
    for f in files:
        try:
            with open(f) as fh:
                for line in fh:
                    try:
                        yield f, json.loads(line)
                    except Exception:
                        continue
        except Exception:
            continue


def _extract_user_text(ev: dict) -> str:
    """Pull user text from message events. Returns '' if not a user msg."""
    msg = ev.get("message") or {}
    if msg.get("role") != "user":
        return ""
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def _extract_tool_calls(ev: dict) -> list:
    msg = ev.get("message") or {}
    if msg.get("role") != "assistant":
        return []
    content = msg.get("content") or []
    if not isinstance(content, list):
        return []
    return [b.get("name") for b in content if isinstance(b, dict) and b.get("type") == "tool_use"]


def _model_used(ev: dict) -> str:
    return (ev.get("message") or {}).get("model", "") or ""


def _load_config() -> dict:
    """Load dashboard config.json. Returns {} on failure."""
    cfg = BASE / "config.json"
    try:
        return json.loads(cfg.read_text())
    except Exception:
        return {}


def _ddg_search(query: str, max_results: int = 3) -> list:
    """Fetch DuckDuckGo HTML results for query. Returns [{title, url}] best-effort."""
    try:
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(query)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible)"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        # Extract result titles and URLs via regex (no beautiful soup needed)
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)
        links = re.findall(r'class="result__url"[^>]*>(.*?)</span>', html, re.DOTALL)
        results = []
        for i, title in enumerate(titles[:max_results]):
            clean_title = re.sub(r"<[^>]+>", "", title).strip()
            url_text = links[i].strip() if i < len(links) else ""
            if clean_title:
                results.append({"title": clean_title[:120], "url": url_text[:200]})
        return results
    except Exception:
        return []


def _search_external_opportunities(repeated_tasks: list) -> list:
    """Search DuckDuckGo for top-3 repeated task patterns. Returns aggregated results.

    Only called when config.json dream_prefs.web_search is True.
    Returns [] if disabled or all fetches fail.
    """
    cfg = _load_config()
    if not cfg.get("dream_prefs", {}).get("web_search", False):
        return []
    if not repeated_tasks:
        return []
    results = []
    for task in repeated_tasks[:3]:
        snippet = task.get("snippet", "")
        if not snippet or len(snippet) < 5:
            continue
        query = f"AI skill for {snippet}"
        hits = _ddg_search(query, max_results=3)
        results.extend(hits)
    return results[:9]  # cap at 9 total results


def analyze() -> dict:
    files = _recent_jsonl()
    user_texts = []
    tool_calls = []
    model_per_session = defaultdict(set)
    session_tools = defaultdict(list)
    session_text_lens = defaultdict(int)

    for f, ev in _iter_events(files):
        sid = ev.get("sessionId") or str(f)
        ut = _extract_user_text(ev)
        if ut:
            user_texts.append(ut)
            session_text_lens[sid] += len(ut)
        tcs = _extract_tool_calls(ev)
        tool_calls.extend(tcs)
        session_tools[sid].extend(tcs)
        m = _model_used(ev)
        if m:
            model_per_session[sid].add(m)

    # Dimension 1: Repeated manual tasks — user typed similar request 3+ times
    norm = lambda s: re.sub(r"\s+", " ", s.lower().strip())[:120]
    user_counter = Counter(norm(t) for t in user_texts if len(t) > 20)
    # Store hashes only — never raw user text. Keep a short non-identifying snippet
    # of 30 chars (truncated and lowercased) for headlines.
    repeated = [
        {"prompt_hash": _redact_prompt(k), "snippet": k[:30], "count": v}
        for k, v in user_counter.most_common(5) if v >= 3
    ]

    # Dimension 2: Slow workflows — sessions w/ >40 tool calls
    slow_sessions = [{"session": s[:8], "tool_calls": len(tools)}
                     for s, tools in session_tools.items() if len(tools) > 40][:5]

    # Dimension 3: Token waste — opus used on short sessions (<500 chars user text)
    waste = []
    for sid, models in model_per_session.items():
        if any("opus" in m.lower() for m in models) and session_text_lens.get(sid, 0) < 500:
            waste.append({"session": sid[:8], "user_chars": session_text_lens[sid]})
    waste = waste[:5]

    # Dimension 4: Memory gaps — same question phrased 2+ times across sessions
    memory_gaps = [
        {"prompt_hash": _redact_prompt(k), "snippet": k[:30], "count": v}
        for k, v in user_counter.most_common(10)
        if 2 <= v < 3 and any(q in k for q in ("what is", "where is", "how do i", "remind me"))
    ][:5]

    # Dimension 5: Skill underuse
    skills_doc = json.loads(SKILLS_FILE.read_text())
    underused = [{"skill": s["name"], "reason": "never invoked"}
                 for s in skills_doc["skills"] if s["run_count"] == 0][:5]

    # Dimension 6: Skill overuse — manual tool repetition (Bash >100 calls)
    tool_counter = Counter(tool_calls)
    overused = [{"tool": t, "calls": c, "suggest": "wrap in skill or hook"}
                for t, c in tool_counter.most_common(3) if c >= 50]

    # Dimension 7: Cross-tool friction — sessions w/ Read followed by Write of similar path repeatedly
    friction = []
    for sid, tools in session_tools.items():
        rw = sum(1 for i in range(len(tools) - 1) if tools[i] == "Read" and tools[i + 1] == "Edit")
        if rw >= 10:
            friction.append({"session": sid[:8], "read_then_edit": rw})
    friction = friction[:3]

    # Dimension 8: Knowledge silos — queries about Pinecone/Supabase data without using the tools
    silo_terms = ("pinecone", "supabase", "gravity claw", "obsidian")
    silos = []
    for t in user_texts:
        tl = t.lower()
        if any(term in tl for term in silo_terms) and len(t) > 30:
            # Persist only the matched term, not the full prompt
            matched = next((term for term in silo_terms if term in tl), "")
            silos.append({"term": matched, "prompt_hash": _redact_prompt(tl)})
        if len(silos) >= 5:
            break

    # Rank recommendations
    recs = []
    for r in repeated:
        recs.append({"dimension": "repeated-task", "priority": "high",
                     "headline": f'Saw similar prompt {r["count"]}x ({r["prompt_hash"]}) — promote to skill',
                     "detail": _sanitize_detail(r)})
    for s in slow_sessions:
        recs.append({"dimension": "slow-workflow", "priority": "medium",
                     "headline": f'Session {s["session"]} ran {s["tool_calls"]} tool calls — review for batching',
                     "detail": s})
    for w in waste:
        recs.append({"dimension": "token-waste", "priority": "high",
                     "headline": f'Opus on tiny session {w["session"]} ({w["user_chars"]} chars) — try Haiku',
                     "detail": w})
    for g in memory_gaps:
        recs.append({"dimension": "memory-gap", "priority": "medium",
                     "headline": f'Asked similar question {g["count"]}x ({g["prompt_hash"]}) — write a memory',
                     "detail": _sanitize_detail(g)})
    for u in underused:
        recs.append({"dimension": "skill-underuse", "priority": "low",
                     "headline": f'{u["skill"]} never invoked',
                     "detail": u})
    for o in overused:
        recs.append({"dimension": "tool-overuse", "priority": "medium",
                     "headline": f'{o["tool"]} called {o["calls"]}x — {o["suggest"]}',
                     "detail": o})
    for fr in friction:
        recs.append({"dimension": "cross-tool-friction", "priority": "medium",
                     "headline": f'Session {fr["session"]} did Read→Edit {fr["read_then_edit"]}x — pattern candidate',
                     "detail": fr})
    for si in silos:
        recs.append({"dimension": "knowledge-silo", "priority": "low",
                     "headline": f'Asked about external store ({si["term"]})',
                     "detail": _sanitize_detail(si)})

    # Dimension 9: External opportunities — DuckDuckGo search for top repeated tasks
    # Only runs if config.json dream_prefs.web_search is True
    external_opps = _search_external_opportunities(repeated)
    if external_opps:
        recs.append({
            "dimension": "external-opportunities",
            "priority": "medium",
            "headline": f"Found {len(external_opps)} tools matching your repeated work patterns",
            "detail": {"results": external_opps, "query_count": len(external_opps)},
        })

    out = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "generated_at": datetime.now().isoformat(),
        "files_analyzed": len(files),
        "events_total": len(user_texts) + len(tool_calls),
        "dimensions": {
            "repeated_tasks": repeated,
            "slow_workflows": slow_sessions,
            "token_waste": waste,
            "memory_gaps": memory_gaps,
            "skill_underuse": underused,
            "tool_overuse": overused,
            "cross_tool_friction": friction,
            "knowledge_silos": silos,
            "external_opportunities": external_opps,
        },
        "recommendations": recs[:20],
        "top_3": recs[:3],
        # Backwards-compat with dashboard JS (loadVaultCards reads dream.cards).
        "cards": _build_cards(recs[:3]),
    }
    return out


def main():
    DREAMS_DIR.mkdir(parents=True, exist_ok=True)
    result = analyze()
    out_path = DREAMS_DIR / f"{result['date']}.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Dream written: {out_path}")
    print(f"Recommendations: {len(result['recommendations'])}")
    return result


if __name__ == "__main__":
    main()
