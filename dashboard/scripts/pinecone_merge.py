#!/usr/bin/env python3
"""Migrate orphan Pinecone index `gravityclaw` -> active index `gravityclaw-vector`.

Background: Gravity Claw's remember_fact / extraction pipeline historically wrote
to the `gravityclaw` index (1,070 vecs in `knowledge`, 48 in `conversations`).
Current agent code reads from `gravityclaw-vector`. The two never connected.
This script copies every vector + metadata from the orphan into the active
index, preserving IDs and namespaces. Then prints a stats summary so a human
can verify before deleting the orphan index out-of-band.

Idempotent: re-upserting same ID overwrites with same values. Safe to re-run.

Usage:
    python3 pinecone_merge.py --dry-run
    python3 pinecone_merge.py
"""

import argparse
import json
import sys
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path

API_KEY = "pcsk_47Zipr_2jtBTcdZEPwKjVNWYCcGFyYws4NZDt7zR2X6AKYq81Artjo9BEC6vhv2gBLgW52"
SRC_HOST = "https://gravityclaw-7macm39.svc.aped-4627-b74a.pinecone.io"
DST_HOST = "https://gravityclaw-vector-7macm39.svc.aped-4627-b74a.pinecone.io"

WRITES_LOG = Path.home() / ".claude" / "pinecone_writes.jsonl"

HEADERS = [
    "-H", f"Api-Key: {API_KEY}",
    "-H", "Content-Type: application/json",
    "-H", "X-Pinecone-API-Version: 2025-01",
]

PAGE_SIZE = 100


def _log_write(action: str, summary: str, count: int, namespace: str):
    try:
        entry = {
            "ts": datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z"),
            "action": action,
            "summary": summary,
            "count": count,
            "namespace": namespace,
            "source": "pinecone_merge.py",
        }
        with open(WRITES_LOG, "a") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[merge] _log_write failed: {e}", file=sys.stderr)


def post(host: str, path: str, payload: dict) -> dict:
    body = json.dumps(payload)
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{host}{path}"] + HEADERS + ["--data-binary", "@-"],
        input=body, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed: {result.stderr}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"non-json response from {host}{path}: {result.stdout[:200]}")


def get_stats(host: str) -> dict:
    return post(host, "/describe_index_stats", {})


def list_ids(host: str, namespace: str) -> list:
    """Page through all IDs in a namespace using Pinecone list endpoint."""
    ids = []
    pagination_token = None
    while True:
        url = f"{host}/vectors/list?namespace={namespace}&limit={PAGE_SIZE}"
        if pagination_token:
            url += f"&paginationToken={pagination_token}"
        result = subprocess.run(
            ["curl", "-s", "-X", "GET", url] + HEADERS,
            capture_output=True, text=True
        )
        data = json.loads(result.stdout)
        page = [v["id"] for v in data.get("vectors", [])]
        ids.extend(page)
        pagination_token = data.get("pagination", {}).get("next")
        if not pagination_token:
            break
        time.sleep(0.05)
    return ids


def fetch_vectors(host: str, ids: list, namespace: str) -> dict:
    """Fetch up to 100 vectors by ID at a time."""
    fetched = {}
    for i in range(0, len(ids), PAGE_SIZE):
        batch = ids[i:i + PAGE_SIZE]
        # Pinecone fetch uses repeated `ids=` query params
        ids_q = "&".join(f"ids={vid}" for vid in batch)
        url = f"{host}/vectors/fetch?{ids_q}&namespace={namespace}"
        result = subprocess.run(
            ["curl", "-s", "-X", "GET", url] + HEADERS,
            capture_output=True, text=True
        )
        data = json.loads(result.stdout)
        fetched.update(data.get("vectors", {}))
        time.sleep(0.05)
    return fetched


def upsert_vectors(host: str, vectors: list, namespace: str, dry_run: bool = False) -> int:
    """Upsert in batches of 100. Returns count actually written."""
    if dry_run:
        return len(vectors)
    written = 0
    for i in range(0, len(vectors), PAGE_SIZE):
        batch = vectors[i:i + PAGE_SIZE]
        resp = post(host, "/vectors/upsert", {"vectors": batch, "namespace": namespace})
        written += resp.get("upsertedCount", len(batch))
        time.sleep(0.1)
    return written


def migrate_namespace(ns: str, dry_run: bool) -> dict:
    print(f"\n=== namespace: {ns} ===", flush=True)

    src_stats = get_stats(SRC_HOST)
    src_count = src_stats.get("namespaces", {}).get(ns, {}).get("vectorCount", 0)
    print(f"  src vectors:  {src_count}")
    if src_count == 0:
        print("  empty, skipping")
        return {"namespace": ns, "src_count": 0, "fetched": 0, "written": 0}

    dst_stats = get_stats(DST_HOST)
    dst_before = dst_stats.get("namespaces", {}).get(ns, {}).get("vectorCount", 0)
    print(f"  dst before:   {dst_before}")

    print("  listing IDs from src...")
    ids = list_ids(SRC_HOST, ns)
    print(f"  ids listed:   {len(ids)}")

    if len(ids) != src_count:
        print(f"  WARNING: id count {len(ids)} != stats count {src_count}; proceeding with listed ids", flush=True)

    print("  fetching vectors + metadata...")
    fetched = fetch_vectors(SRC_HOST, ids, ns)
    print(f"  fetched:      {len(fetched)}")

    payload = []
    for vid, v in fetched.items():
        values = v.get("values")
        if not values or len(values) != 1024:
            print(f"  skip {vid}: invalid dim ({len(values) if values else 'none'})", flush=True)
            continue
        payload.append({
            "id": vid,
            "values": values,
            "metadata": v.get("metadata", {}),
        })

    print(f"  upserting:    {len(payload)} {'(DRY RUN)' if dry_run else ''}")
    written = upsert_vectors(DST_HOST, payload, ns, dry_run=dry_run)
    print(f"  written:      {written}")

    if not dry_run:
        time.sleep(1.5)
        dst_stats_after = get_stats(DST_HOST)
        dst_after = dst_stats_after.get("namespaces", {}).get(ns, {}).get("vectorCount", 0)
        delta = dst_after - dst_before
        print(f"  dst after:    {dst_after}  (Δ {delta:+d})")
        _log_write(
            action="merge_orphan",
            summary=f"migrated gravityclaw/{ns} -> gravityclaw-vector/{ns}: src={src_count} fetched={len(fetched)} written={written}",
            count=written,
            namespace=ns,
        )

    return {
        "namespace": ns,
        "src_count": src_count,
        "fetched": len(fetched),
        "written": written,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="fetch + report, no writes")
    parser.add_argument("--namespaces", nargs="+", default=["knowledge", "conversations"])
    args = parser.parse_args()

    print(f"[merge] {'DRY RUN' if args.dry_run else 'LIVE'}", flush=True)
    print(f"  src: {SRC_HOST}")
    print(f"  dst: {DST_HOST}")

    results = []
    for ns in args.namespaces:
        try:
            results.append(migrate_namespace(ns, args.dry_run))
        except Exception as e:
            print(f"  ERROR in {ns}: {e}", flush=True)
            results.append({"namespace": ns, "error": str(e)})

    print("\n=== summary ===")
    for r in results:
        if "error" in r:
            print(f"  {r['namespace']}: ERROR {r['error']}")
        else:
            print(f"  {r['namespace']}: src={r['src_count']} fetched={r['fetched']} written={r['written']}")

    if args.dry_run:
        print("\n[merge] dry run complete. Re-run without --dry-run to commit.")
    else:
        print("\n[merge] migration complete. Verify gravityclaw-vector counts, then delete orphan index:")
        print("  curl -X DELETE 'https://api.pinecone.io/indexes/gravityclaw' \\")
        print("    -H 'Api-Key: $PINECONE_API_KEY' -H 'X-Pinecone-API-Version: 2025-01'")


if __name__ == "__main__":
    main()
