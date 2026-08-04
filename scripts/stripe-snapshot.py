#!/usr/bin/env python3
"""
Stripe snapshot — pulls active subscriptions, school count, and MRR for Ag Coach Pro.
Usage: python3 scripts/stripe-snapshot.py
Requires: pip install stripe python-dotenv
"""

import os
import stripe
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict

load_dotenv()
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

PLAN_LABELS = {
    "greenhand":        "Greenhand ($495)",
    "blue_and_gold":    "Blue & Gold ($895)",
    "blue-and-gold":    "Blue & Gold ($895)",
    "lone_star_elite":  "Lone Star Elite ($1,495)",
    "lone-star-elite":  "Lone Star Elite ($1,495)",
}

def get_plan_label(sub):
    for item in sub["items"]["data"]:
        name = (item["price"].get("nickname") or item["price"]["id"]).lower()
        for key, label in PLAN_LABELS.items():
            if key in name:
                return label
    return "Unknown"

def main():
    print(f"\n=== Ag Coach Pro — Stripe Snapshot ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===\n")

    subs = stripe.Subscription.list(status="active", limit=100, expand=["data.items.data.price"])
    active = subs["data"]

    by_plan = defaultdict(list)
    total_mrr = 0

    for sub in active:
        label = get_plan_label(sub)
        customer = stripe.Customer.retrieve(sub["customer"])
        name = customer.get("name") or customer.get("email") or sub["customer"]
        mrr = sum(i["price"]["unit_amount"] for i in sub["items"]["data"]) / 100
        by_plan[label].append({"name": name, "mrr": mrr})
        total_mrr += mrr

    total_schools = len(active)
    print(f"Total active schools: {total_schools} / 50 goal")
    print(f"MRR: ${total_mrr:,.2f}  |  ARR: ${total_mrr * 12:,.2f}\n")

    for plan, schools in sorted(by_plan.items()):
        print(f"--- {plan} ({len(schools)} schools) ---")
        for s in schools:
            print(f"  {s['name']}")
        print()

    trials = stripe.Subscription.list(status="trialing", limit=100)
    if trials["data"]:
        print(f"--- Trials ({len(trials['data'])}) ---")
        for sub in trials["data"]:
            customer = stripe.Customer.retrieve(sub["customer"])
            name = customer.get("name") or customer.get("email") or sub["customer"]
            ends = datetime.fromtimestamp(sub["trial_end"]).strftime("%Y-%m-%d")
            print(f"  {name} — trial ends {ends}")
        print()

if __name__ == "__main__":
    main()
