"""Revenue snapshot — pulls Stripe active subs + trials, writes JSON for dashboard.

Output: dashboard/data/revenue.json
{
  "ts": "2026-05-21T...",
  "total_schools": 12,
  "school_goal": 50,
  "mrr": 1234.56,
  "arr": 14814.72,
  "by_plan": {"Greenhand ($495)": [{"name":"...","mrr":41.25}, ...]},
  "trials": [{"name":"...", "trial_end":"2026-06-01"}, ...],
  "stale": false
}

Reuses plan-label mapping from `scripts/stripe-snapshot.py` (kept independent to avoid hyphen-in-name import gymnastics).
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    import stripe
    from dotenv import load_dotenv
except ImportError as e:
    print(f"missing dependency: {e}. install with: pip install stripe python-dotenv", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "dashboard" / "data" / "revenue.json"

PLAN_LABELS = {
    "greenhand": "Greenhand ($495)",
    "blue_and_gold": "Blue & Gold ($895)",
    "blue-and-gold": "Blue & Gold ($895)",
    "lone_star_elite": "Lone Star Elite ($1,495)",
    "lone-star-elite": "Lone Star Elite ($1,495)",
}
SCHOOL_GOAL = 50


def get_plan_label(sub) -> str:
    for item in sub["items"]["data"]:
        name = (item["price"].get("nickname") or item["price"]["id"]).lower()
        for key, label in PLAN_LABELS.items():
            if key in name:
                return label
    return "Unknown"


def collect() -> dict:
    load_dotenv(ROOT / ".env")
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        return {
            "ts": datetime.now(timezone.utc).isoformat(),
            "stale": True,
            "error": "STRIPE_SECRET_KEY missing from .env",
        }

    subs = stripe.Subscription.list(status="active", limit=100, expand=["data.items.data.price"])
    active = subs["data"]
    by_plan: dict[str, list[dict]] = defaultdict(list)
    total_mrr = 0.0
    for sub in active:
        label = get_plan_label(sub)
        customer = stripe.Customer.retrieve(sub["customer"])
        name = customer.get("name") or customer.get("email") or sub["customer"]
        mrr = sum(i["price"]["unit_amount"] for i in sub["items"]["data"]) / 100.0
        by_plan[label].append({"name": name, "mrr": mrr})
        total_mrr += mrr

    trials_raw = stripe.Subscription.list(status="trialing", limit=100)["data"]
    trials = []
    for sub in trials_raw:
        customer = stripe.Customer.retrieve(sub["customer"])
        name = customer.get("name") or customer.get("email") or sub["customer"]
        trials.append({
            "name": name,
            "trial_end": datetime.fromtimestamp(sub["trial_end"]).strftime("%Y-%m-%d"),
        })

    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "stale": False,
        "total_schools": len(active),
        "school_goal": SCHOOL_GOAL,
        "mrr": round(total_mrr, 2),
        "arr": round(total_mrr * 12, 2),
        "by_plan": dict(by_plan),
        "trials": trials,
    }


def main() -> int:
    snap = collect()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(snap, indent=2))
    if snap.get("stale"):
        print(f"stale snapshot written to {OUT_PATH}: {snap.get('error')}", file=sys.stderr)
        return 1
    print(f"revenue snapshot ok: {snap['total_schools']}/{SCHOOL_GOAL} schools, MRR ${snap['mrr']}, ARR ${snap['arr']}, {len(snap['trials'])} trials → {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
