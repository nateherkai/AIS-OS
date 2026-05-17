"""Vectorize Bryan-Aaron-Master vault → Pinecone for Gravity Claw access.

Walks all .md files, chunks ~600-1000 chars w/ 100-char overlap, embeds via
OpenAI text-embedding-3-small (1536 dim) — but gravityclaw-vector is 1024 dim
so use text-embedding-3-small with dimensions=1024 param.

Upserts to namespace 'aios-vault'.

Each vector metadata:
  - path: relative path from vault root
  - title: filename without extension
  - chunk_idx: chunk position
  - source: 'vault'
  - domain: '01-AG-COACH-PRO' | 'wiki' | etc.
  - tags: from YAML frontmatter if present
  - updated_at: file mtime

Idempotent: tracks last-embedded mtime per file in dashboard/data/vault_embed_state.json.
Re-embed only files newer than last run. --full flag forces re-embed all.

CLI:
  python3 vault_to_pinecone.py [--full] [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterator

# Sources
VAULT = Path("/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master")
STATE_FILE = Path("/Volumes/Samsung PSSD T7/AIS-OS/dashboard/data/vault_embed_state.json")
LOG_FILE = Path.home() / ".claude" / "pinecone_writes.jsonl"
INDEX_NAME = "gravityclaw-vector"
NAMESPACE = "aios-vault"
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1024
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# Excludes (don't embed these)
EXCLUDE_DIRS = {"raw/_ingested", ".obsidian", ".git", "node_modules"}
EXCLUDE_FILES = {".gitkeep", ".DS_Store"}


def load_env() -> dict:
    """Load OpenAI + Pinecone keys from known .env files."""
    env = {}
    env_files = [
        Path("/Volumes/Samsung PSSD T7/gravity-claw/.env"),
        Path("/Volumes/Samsung PSSD T7/ag-coach-app/.env"),
        Path("/Volumes/Samsung PSSD T7/AIS-OS/.env"),
    ]
    for env_path in env_files:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    key = k.strip()
                    val = v.strip().strip('"').strip("'")
                    # Normalize OpenAI key (ag-coach-app uses mixed case)
                    if key.upper() == "OPENAI_API_KEY":
                        key = "OPENAI_API_KEY"
                    if key not in env:  # first file wins
                        env[key] = val
    # OS env overrides
    for k in ("OPENAI_API_KEY", "PINECONE_API_KEY", "PINECONE_INDEX_NAME"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def strip_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). Frontmatter parsed via simple YAML-ish regex."""
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    fm_raw = m.group(1)
    body = m.group(2)
    fm = {}
    for line in fm_raw.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('[').strip(']').strip()
    return fm, body


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if len(text) <= size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start:start + size]
        chunks.append(chunk)
        start += (size - overlap)
    return chunks


def walk_vault() -> Iterator[Path]:
    for p in VAULT.rglob("*.md"):
        # Skip excluded dirs
        if any(ex in str(p.relative_to(VAULT)) for ex in EXCLUDE_DIRS):
            continue
        if p.name in EXCLUDE_FILES:
            continue
        yield p


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"files": {}}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def log_write(summary: str, count: int) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "action": "upsert",
            "namespace": NAMESPACE,
            "summary": summary,
            "count": count,
        }
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def make_vector_id(path: Path, chunk_idx: int) -> str:
    rel = str(path.relative_to(VAULT))
    h = hashlib.sha1(f"{rel}#{chunk_idx}".encode()).hexdigest()[:16]
    return f"vault-{h}"


def domain_for(path: Path) -> str:
    rel = path.relative_to(VAULT)
    parts = rel.parts
    if parts and (parts[0].startswith(("01-", "02-", "03-", "04-", "05-", "06-", "07-")) or parts[0] == "wiki"):
        return parts[0]
    return "root"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Re-embed all files even if unchanged")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be embedded; no API calls")
    parser.add_argument("--limit", type=int, default=0, help="Cap number of files (testing)")
    args = parser.parse_args()

    env = load_env()
    if not args.dry_run:
        if not env.get("OPENAI_API_KEY"):
            print("ERR: OPENAI_API_KEY not found", file=sys.stderr)
            return 1
        if not env.get("PINECONE_API_KEY"):
            print("ERR: PINECONE_API_KEY not found", file=sys.stderr)
            return 1

    state = load_state()
    if args.full:
        state["files"] = {}

    # Walk + filter
    pending = []
    for p in walk_vault():
        rel = str(p.relative_to(VAULT))
        mtime = p.stat().st_mtime
        prev = state["files"].get(rel, {}).get("mtime", 0)
        if mtime > prev or args.full:
            pending.append((p, mtime))
        if args.limit and len(pending) >= args.limit:
            break

    print(f"Vault: {sum(1 for _ in walk_vault())} files total")
    print(f"Pending embed: {len(pending)} files (changed since last run)")

    if args.dry_run:
        for p, _ in pending[:20]:
            print(f"  - {p.relative_to(VAULT)}")
        if len(pending) > 20:
            print(f"  ... and {len(pending) - 20} more")
        return 0

    if not pending:
        print("Nothing to embed.")
        return 0

    # Lazy imports
    try:
        from openai import OpenAI
        from pinecone import Pinecone
    except ImportError as e:
        print(f"ERR: missing dep: {e}", file=sys.stderr)
        return 1

    oa = OpenAI(api_key=env["OPENAI_API_KEY"])
    pc = Pinecone(api_key=env["PINECONE_API_KEY"])
    index_name = env.get("PINECONE_INDEX_NAME", INDEX_NAME)
    index = pc.Index(index_name)

    total_chunks = 0
    total_files = 0
    batch_vectors = []
    BATCH_SIZE = 96

    def flush():
        nonlocal batch_vectors
        if not batch_vectors:
            return
        try:
            index.upsert(vectors=batch_vectors, namespace=NAMESPACE)
        except Exception as e:
            print(f"WARN: upsert failed: {e}", file=sys.stderr)
        batch_vectors = []

    for path, mtime in pending:
        try:
            text = path.read_text()
        except Exception as e:
            print(f"  skip (read err): {path.relative_to(VAULT)} — {e}", file=sys.stderr)
            continue

        if not text.strip():
            state["files"][str(path.relative_to(VAULT))] = {"mtime": mtime, "chunks": 0}
            continue

        fm, body = strip_frontmatter(text)
        chunks = chunk_text(body)

        # Embed all chunks for this file in one OpenAI call
        chunk_texts = chunks
        try:
            embed_resp = oa.embeddings.create(
                model=EMBED_MODEL,
                input=chunk_texts,
                dimensions=EMBED_DIM,
            )
            embeddings = [e.embedding for e in embed_resp.data]
        except Exception as e:
            print(f"  skip (embed err): {path.relative_to(VAULT)} — {e}", file=sys.stderr)
            continue

        rel_path = str(path.relative_to(VAULT))
        title = path.stem
        domain = domain_for(path)
        tags = fm.get("tags", "") if isinstance(fm.get("tags"), str) else ""

        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            vec_id = make_vector_id(path, idx)
            meta = {
                "path": rel_path,
                "title": title,
                "chunk_idx": idx,
                "source": "vault",
                "domain": domain,
                "tags": tags,
                "text": chunk[:500],  # store snippet for quick recall
                "updated_at": datetime.fromtimestamp(mtime).isoformat(),
            }
            batch_vectors.append({"id": vec_id, "values": emb, "metadata": meta})
            total_chunks += 1
            if len(batch_vectors) >= BATCH_SIZE:
                flush()

        total_files += 1
        state["files"][rel_path] = {"mtime": mtime, "chunks": len(chunks)}
        if total_files % 25 == 0:
            print(f"  ...embedded {total_files} files / {total_chunks} chunks")
            save_state(state)

    flush()
    save_state(state)
    log_write(f"Vault embed: {total_files} files, {total_chunks} chunks", total_chunks)

    print(f"Done. Embedded {total_files} files / {total_chunks} chunks to {index_name}/{NAMESPACE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
