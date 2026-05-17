"""
Parse Apple Card CSV exports and update expenses.json with actual amounts.
Apple Card CSV format:
  Transaction Date,Clearing Date,Description,Merchant,Category,Type,Amount (USD),Purchased By

R3a: Now outputs BOTH curated AI subset AND full card aggregation.
"""
import csv
import json
import os
import glob
import re
from datetime import datetime, date
from collections import defaultdict

IMPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "imports")
EXPENSES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "expenses.json")

_MONTHS = {"january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
           "july":7,"august":8,"september":9,"october":10,"november":11,"december":12}

_MONTH_NAMES = {1:"January",2:"February",3:"March",4:"April",5:"May",6:"June",
                7:"July",8:"August",9:"September",10:"October",11:"November",12:"December"}

# Types to exclude from "real spend" — payments and credits reduce the balance
_EXCLUDE_TYPES = {"payment", "credit", "debit"}  # debit = daily cash adj (tiny)
_INTEREST_TYPES = {"interest"}
_INSTALLMENT_TYPES = {"installment"}

def _filename_date(path: str) -> tuple:
    """Extract (year, month) from 'Apple Card Transactions - April 2026.csv'."""
    name = os.path.basename(path).lower()
    for month, num in _MONTHS.items():
        if month in name:
            m = re.search(r"\b(20\d\d)\b", name)
            year = int(m.group(1)) if m else 0
            return (year, num)
    return (0, 0)

def _month_key(path: str) -> str:
    """Return 'YYYY-MM' for a CSV path."""
    y, m = _filename_date(path)
    return f"{y}-{m:02d}"

def find_all_csvs() -> list[str]:
    """Return all CSVs sorted oldest → newest."""
    pattern = os.path.join(IMPORTS_DIR, "*.csv")
    files = glob.glob(pattern)
    return sorted(files, key=_filename_date)

def find_latest_csv() -> str | None:
    files = find_all_csvs()
    return files[-1] if files else None

def match_vendor(description: str, merchant: str, vendor_keywords: list[str]) -> bool:
    text = (description + " " + merchant).upper()
    return any(kw.upper() in text for kw in vendor_keywords)


def _parse_csv_full(csv_path: str) -> dict:
    """
    Parse one CSV and return a dict with:
      - charges: list of {date, merchant, category, amount, type}
      - full_total: total charges (purchases only, ex interest, ex payments/credits)
      - interest: total interest charged
      - installments: total installment charges
      - txn_count: number of purchase rows
      - by_merchant: {merchant: total}
      - by_category: {category: total}
    """
    charges = []
    interest = 0.0
    installments = 0.0
    full_total = 0.0
    by_merchant: dict[str, float] = defaultdict(float)
    by_category: dict[str, float] = defaultdict(float)

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            merchant = row.get("Merchant", "").strip()
            category = row.get("Category", "").strip()
            txn_type = (row.get("Type", "") or "").strip().lower()
            try:
                amount = float(row.get("Amount (USD)", 0) or 0)
            except ValueError:
                continue
            txn_date = row.get("Transaction Date", "").strip()

            if txn_type in _EXCLUDE_TYPES:
                continue  # payments, credits, debit adj — skip

            if txn_type in _INTEREST_TYPES:
                interest += amount
                continue

            if txn_type in _INSTALLMENT_TYPES:
                installments += amount
                continue

            # It's a purchase
            if amount <= 0:
                continue  # skip returns/credits if they slipped through

            charges.append({
                "date": txn_date,
                "merchant": merchant,
                "category": category,
                "amount": round(amount, 2),
                "type": txn_type,
            })
            full_total += amount
            by_merchant[merchant] += amount
            by_category[category] += amount

    return {
        "charges": charges,
        "full_total": round(full_total, 2),
        "interest": round(interest, 2),
        "installments": round(installments, 2),
        "txn_count": len(charges),
        "by_merchant": {k: round(v, 2) for k, v in sorted(by_merchant.items(), key=lambda x: -x[1])},
        "by_category": {k: round(v, 2) for k, v in sorted(by_category.items(), key=lambda x: -x[1])},
    }


def parse_and_update():
    """
    Main entry point. Reads ALL CSVs in imports/, computes full aggregation,
    updates curated expense amounts from latest CSV, and writes enriched
    expenses.json with both curated and full-card data.
    """
    all_csvs = find_all_csvs()
    if not all_csvs:
        return {"updated": False, "reason": "No CSV found in imports/"}

    with open(EXPENSES_FILE) as f:
        data = json.load(f)

    # --- Parse all CSVs ---
    period_data: list[dict] = []
    all_charges_30d: list[dict] = []

    for csv_path in all_csvs:
        y, m = _filename_date(csv_path)
        month_key = f"{y}-{m:02d}"
        month_name = _MONTH_NAMES.get(m, str(m))
        parsed = _parse_csv_full(csv_path)
        period_data.append({
            "month": month_key,
            "month_name": f"{month_name} {y}",
            "full": parsed["full_total"],
            "interest": parsed["interest"],
            "installments": parsed["installments"],
            "txn_count": parsed["txn_count"],
            "by_merchant": parsed["by_merchant"],
            "by_category": parsed["by_category"],
            "charges": parsed["charges"],
            "csv_file": os.path.basename(csv_path),
        })

    # Most recent month = latest CSV
    latest_period = period_data[-1]
    latest_csv = all_csvs[-1]

    # --- 30-day top vendors / category = latest month ---
    top_vendors_30d = [
        {"merchant": k, "amount": v}
        for k, v in list(latest_period["by_merchant"].items())[:15]
    ]
    by_category_30d = latest_period["by_category"]

    # --- Rolling avg of full charges across all periods ---
    all_totals = [p["full"] for p in period_data]
    monthly_avg_full = round(sum(all_totals) / len(all_totals), 2) if all_totals else 0.0

    # --- Period summaries (for trend chart) ---
    period_summaries = []
    for p in period_data[-4:]:  # last 4 months
        period_summaries.append({
            "month": p["month"],
            "month_name": p["month_name"],
            "full": p["full"],
            "interest": p["interest"],
            "installments": p["installments"],
            "txn_count": p["txn_count"],
        })

    # --- Update curated expense amounts from latest CSV ---
    curated_charges: dict[str, float] = {}
    for row in latest_period["charges"]:
        merchant = row["merchant"]
        amount = row["amount"]
        for expense in data["expenses"]:
            if match_vendor("", merchant, expense["vendor_match"]):
                curated_charges[expense["name"]] = curated_charges.get(expense["name"], 0) + amount

    updated_vendors = []
    for expense in data["expenses"]:
        if expense["name"] in curated_charges:
            expense["amount"] = round(curated_charges[expense["name"]], 2)
            updated_vendors.append(expense["name"])

    monthly_charges_curated = round(sum(e["amount"] for e in data["expenses"]), 2)

    # --- Write enriched expenses.json ---
    data["monthly_charges_full"] = latest_period["full"]
    data["monthly_charges_curated"] = monthly_charges_curated
    data["monthly_interest"] = latest_period["interest"]
    data["monthly_avg_full"] = monthly_avg_full
    data["top_vendors_30d"] = top_vendors_30d
    data["by_category_30d"] = by_category_30d
    data["period_summaries"] = period_summaries
    data["expenses_full"] = latest_period["charges"]
    data["last_csv_date"] = latest_period["month"]
    data["last_updated"] = datetime.now().isoformat()

    with open(EXPENSES_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return {
        "updated": True,
        "updated_vendors": updated_vendors,
        "csv_file": os.path.basename(latest_csv),
        "monthly_charges_full": latest_period["full"],
        "monthly_charges_curated": monthly_charges_curated,
        "monthly_avg_full": monthly_avg_full,
        "monthly_interest": latest_period["interest"],
        "periods_parsed": len(period_data),
    }


def parse_all_periods() -> list[dict]:
    """Return full parsed data for all CSVs (used by auto_import_card.py)."""
    return [
        {**{"csv_path": csv_path, "month_key": _month_key(csv_path)}, **_parse_csv_full(csv_path)}
        for csv_path in find_all_csvs()
    ]


if __name__ == "__main__":
    result = parse_and_update()
    print(result)
