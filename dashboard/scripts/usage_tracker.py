"""usage_tracker.py — Live token usage tracking across AI subscriptions.

Parses ~/.claude/projects/**/*.jsonl for last 30 days.
Computes token consumption per subscription and API-equivalent value.

Token fields in .jsonl assistant usage events:
  input_tokens               — non-cached prompt tokens
  cache_read_input_tokens    — prompt tokens served from cache (NOT counted as new usage)
  cache_creation_input_tokens— tokens written to cache (counted as input cost)
  output_tokens              — completion tokens

Claude Pro Max: rate-limited per 5-hour window, no hard monthly ceiling.
  → We show usage in the CURRENT 5-hour window, not a % of plan.
ChatGPT/Gemini: Bryan uses subscriptions (not API), so no raw token events exist.
  → Show "Manual — subscription only" rather than fake 0%.

Budget: ~5s typical. Safe to call on every /api/usage hit.
"""
import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from pathlib import Path as _Path

# Allow import whether running as script or module
_HERE = _Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
from pricing import compute_api_cost

HOME = Path.home()
PROJECTS_ROOT = HOME / ".claude" / "projects"

# ── Subscriptions ───────────────────────────────────────────────
# plan_tokens = None means "no hard ceiling, rate-limited"
SUBSCRIPTIONS = [
    {
        "name": "Claude Pro Max",
        "monthly_usd": 200,
        "model_family": "claude",
        "plan_tokens": None,          # rate-limited per 5h window, not monthly
        "rate_limit_note": "Rate-limited per 5-hour window",
    },
    {
        "name": "ChatGPT Pro",
        "monthly_usd": 200,
        "model_family": "openai",
        "plan_tokens": None,          # subscription, no API events tracked here
        "rate_limit_note": "Subscription — track usage in ChatGPT",
    },
    {
        "name": "Gemini Advanced",
        "monthly_usd": 20,
        "model_family": "gemini",
        "plan_tokens": None,
        "rate_limit_note": "Subscription — track usage in Gemini",
    },
]

# ── API pricing per 1M tokens (in/out) ────────────────────────
API_RATES = {
    "claude-opus":   {"input_per_1m": 15.0,  "output_per_1m": 75.0},
    "claude-sonnet": {"input_per_1m": 3.0,   "output_per_1m": 15.0},
    "claude-haiku":  {"input_per_1m": 1.0,   "output_per_1m": 5.0},
    "gpt-5":         {"input_per_1m": 5.0,   "output_per_1m": 15.0},
    "gpt-4o":        {"input_per_1m": 2.5,   "output_per_1m": 10.0},
    "gemini":        {"input_per_1m": 1.25,  "output_per_1m": 5.0},
}

FAMILY_DEFAULT_RATES = {
    "claude": {"input_per_1m": 3.0,  "output_per_1m": 15.0},
    "openai": {"input_per_1m": 5.0,  "output_per_1m": 15.0},
    "gemini": {"input_per_1m": 1.25, "output_per_1m": 5.0},
}


def _get_rate_for_model(model_str: str, family: str) -> dict:
    m = (model_str or "").lower()
    if "opus" in m:   return API_RATES["claude-opus"]
    if "haiku" in m:  return API_RATES["claude-haiku"]
    if "sonnet" in m: return API_RATES["claude-sonnet"]
    if "gpt-5" in m:  return API_RATES["gpt-5"]
    if "gpt-4" in m:  return API_RATES["gpt-4o"]
    if "gemini" in m: return API_RATES["gemini"]
    return FAMILY_DEFAULT_RATES.get(family, {"input_per_1m": 3.0, "output_per_1m": 15.0})


def _classify_model(model_str: str) -> str:
    m = (model_str or "").lower()
    if any(k in m for k in ("claude", "anthropic")):
        return "claude"
    if any(k in m for k in ("gpt", "openai", "chatgpt", "o1", "o3", "o4")):
        return "openai"
    if "gemini" in m:
        return "gemini"
    return "claude"  # default — Claude Code is the main tool


def _days_left_in_cycle() -> int:
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


def _iter_events_since_ts(since_ts: float):
    """Yield (file_path, event_dict, event_timestamp) for events after since_ts."""
    if not PROJECTS_ROOT.exists():
        return
    cutoff_day = time.time() - 1 * 86400  # only scan files modified in last 24h for 5h window
    for p in PROJECTS_ROOT.rglob("*.jsonl"):
        try:
            if p.stat().st_mtime < cutoff_day:
                continue
            with open(p) as fh:
                for line in fh:
                    try:
                        ev = json.loads(line)
                        ts_str = ev.get("timestamp") or ""
                        if not ts_str:
                            continue
                        # Parse ISO timestamp
                        try:
                            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            ts = dt.timestamp()
                        except Exception:
                            continue
                        if ts >= since_ts:
                            yield p, ev, ts
                    except Exception:
                        continue
        except Exception:
            continue


def _build_daily_burn(daily_tokens: dict, days: int = 14) -> list:
    result = []
    for i in range(days - 1, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        result.append({"date": d, "tokens": daily_tokens.get(d, 0)})
    return result


def _per_session_top(session_tokens: dict, top_n: int = 10) -> list:
    sorted_sessions = sorted(session_tokens.items(), key=lambda x: x[1], reverse=True)
    return [{"session_id": sid[:12], "tokens": tok} for sid, tok in sorted_sessions[:top_n]]


def _five_hour_window_stats() -> dict:
    """Compute Claude token usage in the current 5-hour window."""
    now = time.time()
    window_start = now - 5 * 3600
    inp = 0
    out = 0
    cache_read = 0
    cache_create = 0
    events = 0
    for _, ev, _ in _iter_events_since_ts(window_start):
        msg = ev.get("message") or {}
        if msg.get("role") != "assistant":
            continue
        usage = msg.get("usage") or {}
        if not usage:
            continue
        family = _classify_model(msg.get("model", "") or "")
        if family != "claude":
            continue
        inp += usage.get("input_tokens", 0) or 0
        out += usage.get("output_tokens", 0) or 0
        cache_read += usage.get("cache_read_input_tokens", 0) or 0
        cache_create += usage.get("cache_creation_input_tokens", 0) or 0
        events += 1
    return {
        "input_tokens": inp,
        "output_tokens": out,
        "cache_read_tokens": cache_read,
        "cache_creation_tokens": cache_create,
        "total_tokens": inp + out + cache_create,  # cache_read is free re-reads
        "events": events,
        "window_hours": 5,
    }


def _per_model_breakdown(family_model_tokens: dict) -> dict:
    """Return {model_key: {input, output, cache_read, cache_create}} per model."""
    out = {}
    for model_key, tok in family_model_tokens.items():
        out[model_key] = tok
    return out


def usage_stats() -> dict:
    """Returns usage data for all subscriptions plus detailed breakdown.

    Key changes from v1:
    - input_tokens = non-cached prompt tokens ONLY (not added to cache_read)
    - cache_read_input_tokens tracked separately (informational — Claude caches these, no extra billing cost)
    - cache_creation_input_tokens tracked separately (these ARE billed as input)
    - Claude Pro Max: no % of plan, shows 5h window instead
    - ChatGPT/Gemini: shows "Manual entry" note, no fake 0% bars
    - Per-model breakdown (opus/sonnet/haiku)
    """
    # Accumulators
    family_input = defaultdict(int)         # family -> non-cached input tokens
    family_output = defaultdict(int)        # family -> output tokens
    family_cache_read = defaultdict(int)    # family -> cache read tokens (informational)
    family_cache_create = defaultdict(int)  # family -> cache creation tokens (billed as input)
    family_models = defaultdict(set)        # family -> set of model strings seen
    model_tokens = defaultdict(lambda: {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0})
    daily_tokens = defaultdict(int)         # "YYYY-MM-DD" -> tokens (input+output+cache_create)
    session_tokens = defaultdict(int)
    sessions_seen = set()

    for fpath, ev in _iter_recent_events(days=30):
        msg = ev.get("message") or {}
        role = msg.get("role", "")
        model = msg.get("model", "") or ""
        usage = msg.get("usage") or {}

        sid = ev.get("sessionId") or str(fpath)
        sessions_seen.add(sid)

        if role == "assistant" and usage:
            inp = usage.get("input_tokens", 0) or 0
            out = usage.get("output_tokens", 0) or 0
            cr = usage.get("cache_read_input_tokens", 0) or 0
            cc = usage.get("cache_creation_input_tokens", 0) or 0
            family = _classify_model(model)
            family_input[family] += inp
            family_output[family] += out
            family_cache_read[family] += cr
            family_cache_create[family] += cc
            if model:
                family_models[family].add(model)
                # Per-model breakdown key
                mk = model.split("-")[0:2]
                model_key = "-".join(mk)[:20] if mk else model[:20]
                model_tokens[model_key]["input"] += inp
                model_tokens[model_key]["output"] += out
                model_tokens[model_key]["cache_read"] += cr
                model_tokens[model_key]["cache_create"] += cc

            # Billable tokens for burn tracking: input + output + cache_creation
            # (cache_read is served from cache at reduced cost, not a new ingest)
            billable = inp + out + cc
            if billable > 0:
                ts_str = ev.get("timestamp") or ""
                if ts_str:
                    try:
                        day = ts_str[:10]
                        daily_tokens[day] += billable
                    except Exception:
                        pass
                session_tokens[sid] += billable

    days_left = _days_left_in_cycle()
    days_elapsed = max(1, 30 - days_left)

    # Five-hour window for Claude Pro Max
    five_h = _five_hour_window_stats()

    subs_out = []
    total_api_equiv = 0.0
    total_sub_usd = 0.0

    for sub in SUBSCRIPTIONS:
        family = sub["model_family"]
        inp = family_input[family]
        out = family_output[family]
        cr = family_cache_read[family]
        cc = family_cache_create[family]
        # Billable usage = input (non-cached) + output + cache_creation (billed as input)
        used_billable = inp + out + cc

        # API equivalent cost — per-model accurate pricing
        # Sum across every model bucket that belongs to this subscription family
        api_cost = 0.0
        sub_model_breakdown = []
        for model_key, tok in model_tokens.items():
            # Only count models that belong to this subscription's family
            model_family = _classify_model(model_key)
            if model_family != family:
                continue
            model_cost = compute_api_cost(
                input_tokens=tok["input"],
                output_tokens=tok["output"],
                cache_creation_tokens=tok["cache_create"],
                cache_read_tokens=tok["cache_read"],
                model_str=model_key,
            )
            api_cost += model_cost
            sub_model_breakdown.append({
                "model": model_key,
                "input_tokens": tok["input"],
                "output_tokens": tok["output"],
                "cache_read_tokens": tok["cache_read"],
                "cache_creation_tokens": tok["cache_create"],
                "equiv_usd": round(model_cost, 2),
            })
        # Sort breakdown by cost descending
        sub_model_breakdown.sort(key=lambda x: x["equiv_usd"], reverse=True)

        # If no per-model data for this family (e.g. openai/gemini with no jsonl events),
        # fall back to family-level totals with default rates
        if api_cost == 0.0 and used_billable > 0:
            models_seen = family_models.get(family, set())
            best_model = next(iter(sorted(models_seen, key=lambda m: "opus" in m, reverse=True)), "")
            rate = _get_rate_for_model(best_model, family)
            api_cost = (
                (inp / 1_000_000) * rate["input_per_1m"] +
                (out / 1_000_000) * rate["output_per_1m"] +
                (cc / 1_000_000) * rate["input_per_1m"] +
                (cr / 1_000_000) * rate["input_per_1m"] * 0.1
            )
        api_cost = round(api_cost, 2)
        total_api_equiv += api_cost

        sub_usd = sub["monthly_usd"]
        total_sub_usd += sub_usd

        plan = sub["plan_tokens"]
        if plan is not None and plan > 0:
            pct = round(min((used_billable / plan) * 100, 100), 1)
        else:
            pct = None  # No plan ceiling — rate-limited

        daily_rate = used_billable / days_elapsed if days_elapsed > 0 else 0

        entry = {
            "name": sub["name"],
            "model_family": family,
            "monthly_usd": sub_usd,
            "plan_tokens": plan,
            "rate_limit_note": sub.get("rate_limit_note", ""),
            "used_tokens": used_billable,
            "input_tokens": inp,
            "output_tokens": out,
            "cache_read_tokens": cr,
            "cache_creation_tokens": cc,
            "pct": pct,
            "days_left": days_left,
            "daily_burn": round(daily_rate),
            "api_equivalent_usd": api_cost,
            "net_savings_usd": round(sub_usd - api_cost, 2),
            "model_breakdown": sub_model_breakdown,
        }

        # Claude Pro Max: attach 5h window stats
        if family == "claude":
            entry["window_5h"] = five_h

        # Non-Claude: mark as manual
        if family in ("openai", "gemini") and used_billable == 0:
            entry["manual_tracking"] = True

        subs_out.append(entry)

    total_tokens = sum(
        family_input[f["model_family"]] + family_output[f["model_family"]] + family_cache_create[f["model_family"]]
        for f in SUBSCRIPTIONS
    )
    total_api_equiv = round(total_api_equiv, 2)
    total_sub_usd = round(total_sub_usd, 2)

    # Per-model breakdown (top 10 by output)
    model_summary = sorted(
        [{"model": k, **v} for k, v in model_tokens.items()],
        key=lambda x: x["output"],
        reverse=True,
    )[:10]

    return {
        "subscriptions": subs_out,
        "total_tokens_30d": total_tokens,
        "total_sessions_30d": len(sessions_seen),
        "total_subscription_usd": total_sub_usd,
        "total_api_equivalent_usd": total_api_equiv,
        "net_savings_usd": round(total_sub_usd - total_api_equiv, 2),
        "daily_burn_14d": _build_daily_burn(daily_tokens, days=14),
        "top_sessions": _per_session_top(session_tokens, top_n=10),
        "per_model_breakdown": model_summary,
        "generated_at": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import sys
    print("Running usage_stats() dry-run...")
    try:
        result = usage_stats()
        print(f"OK — {result['total_sessions_30d']} sessions, {result['total_tokens_30d']:,} billable tokens (30d)")
        for s in result["subscriptions"]:
            pct_str = f"{s['pct']}%" if s['pct'] is not None else "rate-limited"
            note = f" [{s.get('rate_limit_note','')}]" if s.get('rate_limit_note') else ""
            print(f"  {s['name']}: {s['used_tokens']:,} billable tokens ({pct_str}){note}")
            print(f"    in={s['input_tokens']:,}  out={s['output_tokens']:,}  cache_read={s['cache_read_tokens']:,}  cache_create={s['cache_creation_tokens']:,}")
            if s.get('window_5h'):
                w = s['window_5h']
                print(f"    5h window: {w['total_tokens']:,} tokens ({w['events']} events)")
            print(f"    API equiv: ${s['api_equivalent_usd']}")
        print(f"Total sub: ${result['total_subscription_usd']} | API equiv: ${result['total_api_equivalent_usd']} | savings: ${result['net_savings_usd']}")
        print("\nPer-model breakdown:")
        for m in result['per_model_breakdown'][:5]:
            print(f"  {m['model']}: in={m['input']:,} out={m['output']:,} cache_read={m['cache_read']:,}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        sys.exit(1)
