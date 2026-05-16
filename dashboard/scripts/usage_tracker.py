"""usage_tracker.py — Live token usage tracking across AI subscriptions.

Parses ~/.claude/projects/**/*.jsonl for last 30 days.
Computes token consumption per subscription and API-equivalent value.

Budget: ~5s typical. Safe to call on every /api/usage hit.
"""
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

HOME = Path.home()
PROJECTS_ROOT = HOME / ".claude" / "projects"

# ── Plan limits ────────────────────────────────────────────────
SUBSCRIPTIONS = [
    {
        "name": "Claude Pro Max",
        "monthly_usd": 200,
        "model_family": "claude",
        "plan_tokens": 5_000_000,  # ~5M tokens/mo rough budget
    },
    {
        "name": "ChatGPT Pro",
        "monthly_usd": 200,
        "model_family": "openai",
        "plan_tokens": 13_000_000,  # $200 / $0.015 per 1K equivalent
    },
    {
        "name": "Gemini Advanced",
        "monthly_usd": 20,
        "model_family": "gemini",
        "plan_tokens": 2_000_000,
    },
]

# ── API pricing per 1M tokens (in/out) ────────────────────────
# Used to compute "what would API cost" for each sub
API_RATES = {
    # Claude rates (using Sonnet as representative for Claude sub)
    "claude-opus": {"input_per_1m": 15.0, "output_per_1m": 75.0},
    "claude-sonnet": {"input_per_1m": 3.0, "output_per_1m": 15.0},
    "claude-haiku": {"input_per_1m": 1.0, "output_per_1m": 5.0},
    # OpenAI
    "gpt-5": {"input_per_1m": 5.0, "output_per_1m": 15.0},
    "gpt-4o": {"input_per_1m": 2.5, "output_per_1m": 10.0},
    # Gemini
    "gemini": {"input_per_1m": 1.25, "output_per_1m": 5.0},
}

# Default rate per family if exact model unknown
FAMILY_DEFAULT_RATES = {
    "claude": {"input_per_1m": 3.0, "output_per_1m": 15.0},   # Sonnet rate
    "openai": {"input_per_1m": 5.0, "output_per_1m": 15.0},
    "gemini": {"input_per_1m": 1.25, "output_per_1m": 5.0},
}


def _get_rate_for_model(model_str: str, family: str) -> dict:
    """Return input/output rates per 1M tokens for a given model string."""
    m = (model_str or "").lower()
    if "opus" in m:
        return API_RATES["claude-opus"]
    if "haiku" in m:
        return API_RATES["claude-haiku"]
    if "sonnet" in m:
        return API_RATES["claude-sonnet"]
    if "gpt-5" in m:
        return API_RATES["gpt-5"]
    if "gpt-4" in m:
        return API_RATES["gpt-4o"]
    if "gemini" in m:
        return API_RATES["gemini"]
    return FAMILY_DEFAULT_RATES.get(family, {"input_per_1m": 3.0, "output_per_1m": 15.0})


def _classify_model(model_str: str) -> str:
    """Map a model string to a subscription family."""
    m = (model_str or "").lower()
    if any(k in m for k in ("claude", "anthropic")):
        return "claude"
    if any(k in m for k in ("gpt", "openai", "chatgpt", "o1", "o3", "o4")):
        return "openai"
    if "gemini" in m:
        return "gemini"
    return "claude"  # default — Claude Code is the main tool


def _days_left_in_cycle() -> int:
    """Days remaining in the current calendar month."""
    now = datetime.now()
    import calendar
    last_day = calendar.monthrange(now.year, now.month)[1]
    return last_day - now.day


def _iter_recent_events(days: int = 30):
    """Yield (file_path, event_dict) for jsonl events within the last N days."""
    if not PROJECTS_ROOT.exists():
        return
    cutoff = time.time() - days * 86400
    for p in PROJECTS_ROOT.rglob("*.jsonl"):
        try:
            if p.stat().st_mtime < cutoff:
                continue
            with open(p) as fh:
                for line in fh:
                    try:
                        ev = json.loads(line)
                        yield p, ev
                    except Exception:
                        continue
        except Exception:
            continue


def _build_daily_burn(daily_tokens: dict, days: int = 14) -> list:
    """Return last N days of token totals as [{date, tokens}]."""
    result = []
    for i in range(days - 1, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        result.append({"date": d, "tokens": daily_tokens.get(d, 0)})
    return result


def _per_session_top(session_tokens: dict, top_n: int = 10) -> list:
    """Return top sessions by token count."""
    sorted_sessions = sorted(session_tokens.items(), key=lambda x: x[1], reverse=True)
    return [{"session_id": sid[:12], "tokens": tok} for sid, tok in sorted_sessions[:top_n]]


def usage_stats() -> dict:
    """Returns usage data for all subscriptions plus detailed breakdown.

    Schema:
    {
        subscriptions: [{
            name, model_family, monthly_usd, plan_tokens,
            used_tokens, input_tokens, output_tokens,
            pct, days_left, daily_burn,
            api_equivalent_usd, net_savings_usd
        }],
        total_tokens_30d,
        total_sessions_30d,
        total_subscription_usd,
        total_api_equivalent_usd,
        net_savings_usd,
        daily_burn_14d: [{date, tokens}],
        top_sessions: [{session_id, tokens}],
    }
    """
    # Accumulators
    family_input = defaultdict(int)   # family -> total input tokens
    family_output = defaultdict(int)  # family -> total output tokens
    family_models = defaultdict(set)  # family -> set of model strings seen
    daily_tokens = defaultdict(int)   # "YYYY-MM-DD" -> tokens
    session_tokens = defaultdict(int) # session_id -> tokens
    sessions_seen = set()

    for fpath, ev in _iter_recent_events(days=30):
        msg = ev.get("message") or {}
        role = msg.get("role", "")
        model = msg.get("model", "") or ""
        usage = msg.get("usage") or {}

        # Get session id
        sid = ev.get("sessionId") or str(fpath)
        sessions_seen.add(sid)

        # Token usage is on assistant messages
        if role == "assistant" and usage:
            inp = usage.get("input_tokens", 0) or 0
            out = usage.get("output_tokens", 0) or 0
            family = _classify_model(model)
            family_input[family] += inp
            family_output[family] += out
            if model:
                family_models[family].add(model)

            total_ev = inp + out
            if total_ev > 0:
                # Try to get timestamp
                ts_str = ev.get("timestamp") or ""
                if ts_str:
                    try:
                        day = ts_str[:10]
                        daily_tokens[day] += total_ev
                    except Exception:
                        pass
                session_tokens[sid] += total_ev

    days_left = _days_left_in_cycle()
    days_elapsed = max(1, 30 - days_left)

    subs_out = []
    total_api_equiv = 0.0
    total_sub_usd = 0.0

    for sub in SUBSCRIPTIONS:
        family = sub["model_family"]
        inp = family_input[family]
        out = family_output[family]
        used = inp + out
        plan = sub["plan_tokens"]
        pct = round(min((used / plan) * 100, 100), 1) if plan > 0 else 0

        # Daily burn
        daily_rate = used / days_elapsed if days_elapsed > 0 else 0

        # API equivalent cost
        # Use the most common (or most expensive) model seen
        models_seen = family_models.get(family, set())
        best_model = next(iter(sorted(models_seen, key=lambda m: "opus" in m, reverse=True)), "")
        rate = _get_rate_for_model(best_model, family)
        api_cost = (inp / 1_000_000) * rate["input_per_1m"] + (out / 1_000_000) * rate["output_per_1m"]
        api_cost = round(api_cost, 2)
        total_api_equiv += api_cost

        sub_usd = sub["monthly_usd"]
        total_sub_usd += sub_usd
        savings = round(sub_usd - api_cost, 2)  # positive = sub is cheaper

        subs_out.append({
            "name": sub["name"],
            "model_family": family,
            "monthly_usd": sub_usd,
            "plan_tokens": plan,
            "used_tokens": used,
            "input_tokens": inp,
            "output_tokens": out,
            "pct": pct,
            "days_left": days_left,
            "daily_burn": round(daily_rate),
            "api_equivalent_usd": api_cost,
            "net_savings_usd": savings,
        })

    total_tokens = sum(family_input[f["model_family"]] + family_output[f["model_family"]] for f in SUBSCRIPTIONS)
    total_api_equiv = round(total_api_equiv, 2)
    total_sub_usd = round(total_sub_usd, 2)
    net_savings = round(total_sub_usd - total_api_equiv, 2)

    return {
        "subscriptions": subs_out,
        "total_tokens_30d": total_tokens,
        "total_sessions_30d": len(sessions_seen),
        "total_subscription_usd": total_sub_usd,
        "total_api_equivalent_usd": total_api_equiv,
        "net_savings_usd": net_savings,
        "daily_burn_14d": _build_daily_burn(daily_tokens, days=14),
        "top_sessions": _per_session_top(session_tokens, top_n=10),
        "generated_at": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    # Dry-run / smoke test
    import sys
    print("Running usage_stats() dry-run...")
    try:
        result = usage_stats()
        print(f"OK — {result['total_sessions_30d']} sessions, {result['total_tokens_30d']:,} tokens")
        for s in result["subscriptions"]:
            print(f"  {s['name']}: {s['used_tokens']:,} / {s['plan_tokens']:,} ({s['pct']}%) — API equiv ${s['api_equivalent_usd']}")
        print(f"Total sub: ${result['total_subscription_usd']} | API equiv: ${result['total_api_equivalent_usd']} | savings: ${result['net_savings_usd']}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
