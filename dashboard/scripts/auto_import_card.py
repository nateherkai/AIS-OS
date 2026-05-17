"""
Watches dashboard/imports/ for new/updated Apple Card CSVs.
Runs parse_apple_card on any file newer than last recorded import.
Writes enriched expenses.json + vault statement pages.

Usage:
    python3 scripts/auto_import_card.py

Idempotent — tracks dashboard/data/.last_import.json per file mtime.
Cron suggestion: 0 9 1,15 * * cd /Volumes/Samsung\\ PSSD\\ T7/AIS-OS/dashboard && python3 scripts/auto_import_card.py
"""
import json
import os
import glob
import sys
from datetime import datetime
from pathlib import Path

SCRIPTS = Path(__file__).parent
BASE = SCRIPTS.parent
IMPORTS_DIR = BASE / "imports"
DATA_DIR = BASE / "data"
LAST_IMPORT_FILE = DATA_DIR / ".last_import.json"
VAULT = BASE.parent / "Bryan-Aaron-Master"
STATEMENTS_DIR = VAULT / "04-FINANCES" / "Statements"

_MONTHS = {"january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
           "july":7,"august":8,"september":9,"october":10,"november":11,"december":12}
_MONTH_NAMES = {1:"January",2:"February",3:"March",4:"April",5:"May",6:"June",
                7:"July",8:"August",9:"September",10:"October",11:"November",12:"December"}

import re

def _filename_date(path) -> tuple:
    name = os.path.basename(str(path)).lower()
    for month, num in _MONTHS.items():
        if month in name:
            m = re.search(r"\b(20\d\d)\b", name)
            year = int(m.group(1)) if m else 0
            return (year, num)
    return (0, 0)

def load_last_import() -> dict:
    if LAST_IMPORT_FILE.exists():
        try:
            return json.loads(LAST_IMPORT_FILE.read_text())
        except Exception:
            pass
    return {}

def save_last_import(record: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LAST_IMPORT_FILE.write_text(json.dumps(record, indent=2))

def find_new_csvs(last_import: dict) -> list[Path]:
    """Return CSVs that are new or have been modified since last import."""
    pattern = str(IMPORTS_DIR / "*.csv")
    all_files = sorted(glob.glob(pattern), key=lambda p: _filename_date(p))
    new = []
    for f in all_files:
        mtime = os.path.getmtime(f)
        key = os.path.basename(f)
        if key not in last_import or last_import[key]["mtime"] < mtime:
            new.append(Path(f))
    return new


def write_vault_statement(csv_path: Path, parsed: dict, month_key: str):
    """Write/overwrite a vault statement page for one month."""
    STATEMENTS_DIR.mkdir(parents=True, exist_ok=True)
    y, m = _filename_date(csv_path)
    month_name = _MONTH_NAMES.get(m, str(m))
    slug = f"{y}-{m:02d}-{month_name.lower()}"
    out_path = STATEMENTS_DIR / f"{slug}.md"

    total_charges = parsed["full_total"]
    interest = parsed["interest"]
    installments = parsed["installments"]
    txn_count = parsed["txn_count"]
    by_category = parsed["by_category"]
    by_merchant = parsed["by_merchant"]
    by_business = parsed.get("by_business", {})
    charges = parsed["charges"]

    lines = [
        f"# {y}-{m:02d} — {month_name} Statement",
        "",
        f"> Apple Card transactions for {month_name} {y}",
        f"> Generated {datetime.now().strftime('%Y-%m-%d')} from `dashboard/imports/{csv_path.name}`",
        f"> Total charges: ${total_charges:,.2f} · Interest: ${interest:,.2f} · Transactions: {txn_count}",
        "",
        "## Summary by Category",
        "",
        "| Category | Amount |",
        "|---|---|",
    ]
    for cat, amt in by_category.items():
        lines.append(f"| {cat} | ${amt:,.2f} |")

    # By-Business section
    if by_business:
        lines += [
            "",
            "## By Business",
            "",
            "| Business | Amount |",
            "|---|---|",
        ]
        for biz, amt in sorted(by_business.items(), key=lambda x: -x[1]):
            lines.append(f"| {biz} | ${amt:,.2f} |")

    lines += [
        "",
        "## Top Vendors",
        "",
        "| Vendor | Amount | Category | Business |",
        "|---|---|---|---|",
    ]
    # Top 15 by amount
    top_vendors = sorted(by_merchant.items(), key=lambda x: -x[1])[:15]
    # Build merchant→category and merchant→business lookup from charges
    merch_cat: dict[str, str] = {}
    merch_biz: dict[str, str] = {}
    for c in charges:
        merch_cat.setdefault(c["merchant"], c["category"])
        merch_biz.setdefault(c["merchant"], c.get("business", ""))
    for vendor, amt in top_vendors:
        cat = merch_cat.get(vendor, "")
        biz = merch_biz.get(vendor, "")
        lines.append(f"| {vendor} | ${amt:,.2f} | {cat} | {biz} |")

    lines += [
        "",
        "## All Transactions",
        "",
        "| Date | Merchant | Category | Business | Amount |",
        "|---|---|---|---|---|",
    ]
    if interest > 0:
        lines.append(f"| Interest | Interest Charge | Interest | personal | ${interest:,.2f} |")
    if installments > 0:
        lines.append(f"| Installment | Monthly Installment | Installment | | ${installments:,.2f} |")
    for c in sorted(charges, key=lambda x: x["date"], reverse=True):
        lines.append(f"| {c['date']} | {c['merchant']} | {c['category']} | {c.get('business','')} | ${c['amount']:,.2f} |")

    lines += [
        "",
        "## Related",
        "- [[../_Finances-Home]]",
        "- [[../../wiki/concepts/usage-tracker]]",
    ]

    out_path.write_text("\n".join(lines))
    return out_path


def update_finances_home(period_summaries: list[dict]):
    """Update _Finances-Home.md with 4-month statement links and summary."""
    home_path = VAULT / "04-FINANCES" / "_Finances-Home.md"
    if not home_path.exists():
        return

    # Build statement block
    stmt_lines = [
        "",
        "---",
        "",
        "## Apple Card Statements",
        "",
        "> Auto-ingested from `dashboard/imports/`. Last updated " + datetime.now().strftime("%Y-%m-%d") + ".",
        "",
        "### 4-Month Summary",
        "",
        "| Month | Charges | Interest | Transactions |",
        "|---|---|---|---|",
    ]
    for p in reversed(period_summaries):
        y, m = p["month"].split("-")
        month_name = _MONTH_NAMES.get(int(m), m)
        slug = f"{p['month']}-{month_name.lower()}"
        stmt_lines.append(
            f"| [[Statements/{slug}|{month_name} {y}]] | ${p['full']:,.2f} | ${p['interest']:,.2f} | {p['txn_count']} |"
        )

    if period_summaries:
        totals = sum(p["full"] for p in period_summaries)
        avg = totals / len(period_summaries)
        stmt_lines += [
            "",
            f"**4-month avg real burn:** ${avg:,.2f}/mo (ex interest, ex payments)",
        ]

        # By-business 4-month summary
        from collections import defaultdict
        biz_totals: dict = defaultdict(float)
        for p in period_summaries:
            for biz, amt in p.get("by_business", {}).items():
                biz_totals[biz] += amt
        n = len(period_summaries)
        if biz_totals:
            stmt_lines += [
                "",
                "### By Business (4-Month Avg/Mo)",
                "",
                "| Business | 4-Mo Avg/Mo |",
                "|---|---|",
            ]
            for biz, total in sorted(biz_totals.items(), key=lambda x: -x[1]):
                stmt_lines.append(f"| {biz} | ${total/n:,.2f} |")

        stmt_lines += [
            "",
            "### Statements Folder",
            "",
            "[[Statements/]] — one page per month, full transaction list.",
        ]

    marker = "## Apple Card Statements"
    content = home_path.read_text()

    if marker in content:
        # Replace from marker to end
        idx = content.index(marker)
        # Find the preceding separator or just cut
        sep_idx = content.rfind("\n---\n", 0, idx)
        if sep_idx >= 0:
            content = content[:sep_idx]
        else:
            content = content[:idx]

    home_path.write_text(content.rstrip() + "\n" + "\n".join(stmt_lines) + "\n")


def run():
    sys.path.insert(0, str(SCRIPTS))
    from parse_apple_card import parse_and_update, find_all_csvs, _parse_csv_full, _filename_date as _fd, _month_key

    last_import = load_last_import()
    new_csvs = find_new_csvs(last_import)

    if not new_csvs:
        print("auto_import: no new or updated CSVs — nothing to do.")
        return {"updated": False, "new_files": []}

    print(f"auto_import: found {len(new_csvs)} new/updated CSV(s): {[f.name for f in new_csvs]}")

    # Parse all for full aggregation (parse_and_update handles this)
    result = parse_and_update()
    print(f"auto_import: expenses.json updated — full burn ${result.get('monthly_charges_full',0):.2f}, avg ${result.get('monthly_avg_full',0):.2f}")

    # Write vault statement pages for each new CSV
    all_csvs = find_all_csvs()
    new_csv_names = {f.name for f in new_csvs}
    period_summaries_full = []
    for csv_path in all_csvs:
        csv_path_obj = Path(csv_path)
        parsed = _parse_csv_full(csv_path)
        y, m = _fd(csv_path)
        month_key = f"{y}-{m:02d}"
        period_summaries_full.append({
            "month": month_key,
            "full": parsed["full_total"],
            "interest": parsed["interest"],
            "txn_count": parsed["txn_count"],
            "by_business": parsed.get("by_business", {}),
        })
        if csv_path_obj.name in new_csv_names:
            out_path = write_vault_statement(csv_path_obj, parsed, month_key)
            print(f"auto_import: wrote vault page → {out_path}")

    # Update _Finances-Home.md
    update_finances_home(period_summaries_full[-4:])
    print(f"auto_import: updated _Finances-Home.md")

    # Update last_import tracker
    new_record = dict(last_import)
    for f in new_csvs:
        new_record[f.name] = {"mtime": os.path.getmtime(str(f)), "ts": datetime.now().isoformat()}
    save_last_import(new_record)

    return {
        "updated": True,
        "new_files": [f.name for f in new_csvs],
        "result": result,
    }


if __name__ == "__main__":
    outcome = run()
    print(json.dumps(outcome, indent=2))
