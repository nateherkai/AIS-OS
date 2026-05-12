"""
Parse Apple Card CSV exports and update expenses.json with actual amounts.
Apple Card CSV format:
  Transaction Date,Clearing Date,Description,Merchant,Category,Type,Amount (USD)
"""
import csv
import json
import os
import glob
from datetime import datetime

IMPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "imports")
EXPENSES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "expenses.json")

def find_latest_csv() -> str | None:
    pattern = os.path.join(IMPORTS_DIR, "*.csv")
    files = glob.glob(pattern)
    return max(files, key=os.path.getmtime) if files else None

def match_vendor(description: str, merchant: str, vendor_keywords: list[str]) -> bool:
    text = (description + " " + merchant).upper()
    return any(kw.upper() in text for kw in vendor_keywords)

def parse_and_update():
    csv_path = find_latest_csv()
    if not csv_path:
        return {"updated": False, "reason": "No CSV found in imports/"}

    with open(EXPENSES_FILE) as f:
        data = json.load(f)

    # Accumulate charges per expense by vendor match
    charges: dict[str, float] = {}
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            desc = row.get("Description", "") or row.get("Merchant", "")
            merchant = row.get("Merchant", "")
            try:
                amount = abs(float(row.get("Amount (USD)", 0) or 0))
            except ValueError:
                continue
            for expense in data["expenses"]:
                if match_vendor(desc, merchant, expense["vendor_match"]):
                    charges[expense["name"]] = charges.get(expense["name"], 0) + amount

    # Update amounts where CSV data found
    updated = []
    for expense in data["expenses"]:
        if expense["name"] in charges:
            expense["amount"] = round(charges[expense["name"]], 2)
            updated.append(expense["name"])

    data["last_updated"] = datetime.now().isoformat()

    with open(EXPENSES_FILE, "w") as f:
        json.dump(data, f, indent=2)

    return {"updated": True, "updated_vendors": updated, "csv_file": os.path.basename(csv_path)}

if __name__ == "__main__":
    result = parse_and_update()
    print(result)
