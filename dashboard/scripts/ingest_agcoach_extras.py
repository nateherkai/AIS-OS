#!/usr/bin/env python3
"""ingest_agcoach_extras.py — vectorize ag-coach-app structured data + NotebookLM drops.

Walks two sources:
  1. /Volumes/Samsung PSSD T7/ag-coach-app/lib/data/*.ts  (CDE rules, rubrics, anatomy, formulas, …)
  2. /Volumes/Samsung PSSD T7/ag-coach-app/Notebooklm knowledge/**/*  (anything Bryan drops)

Chunks ~800 chars w/ 100 overlap, embeds via OpenAI text-embedding-3-small (dim=1024),
upserts to the configured Pinecone namespace, defaulting to `knowledge`, with id prefix `agcoach-extra-`.

Incremental: skips files unchanged since last run (mtime-based state in
`dashboard/data/.agcoach_extras_state.json`). Pass --full to force re-embed.

SECURITY: never logs OPENAI_API_KEY or PINECONE_API_KEY.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv

for _env in [
    "/Volumes/Samsung PSSD T7/gravity-claw/.env",
    "/Volumes/Samsung PSSD T7/ag-coach-app/.env",
    "/Volumes/Samsung PSSD T7/AIS-OS/.env",
]:
    if Path(_env).exists():
        load_dotenv(_env)

# ag-coach-app .env may use mixed-case OPENAI key (e.g. OpenAI_API_KEY)
if not os.environ.get("OPENAI_API_KEY"):
    acp_env = Path("/Volumes/Samsung PSSD T7/ag-coach-app/.env")
    if acp_env.exists():
        for line in acp_env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                if k.strip().upper() == "OPENAI_API_KEY":
                    os.environ["OPENAI_API_KEY"] = v.strip().strip('"').strip("'")
                    break

from openai import OpenAI
from pinecone import Pinecone

SOURCES = [
    Path("/Volumes/Samsung PSSD T7/ag-coach-app/lib/data"),
    Path("/Volumes/Samsung PSSD T7/ag-coach-app/Notebooklm knowledge"),
]
ALLOWED_SUFFIXES = {".ts", ".tsx", ".md", ".txt", ".json"}
INDEX_NAME = "gravityclaw-vector"
CONFIG_FILE = Path("/Volumes/Samsung PSSD T7/AIS-OS/dashboard/config.json")
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1024
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
BATCH_SIZE = 50

STATE_FILE = Path("/Volumes/Samsung PSSD T7/AIS-OS/dashboard/data/.agcoach_extras_state.json")
LOG_FILE = Path.home() / ".claude/pinecone_writes.jsonl"


def pinecone_config() -> tuple[str, str]:
    index_name = os.environ.get("PINECONE_INDEX_NAME")
    namespace = os.environ.get("PINECONE_NAMESPACE")
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text())
            pc = (cfg.get("memory") or {}).get("pinecone") or {}
            index_name = index_name or pc.get("index")
            namespace = namespace or pc.get("namespace")
        except Exception:
            pass
    return index_name or INDEX_NAME, namespace or "knowledge"


def walk_sources() -> Iterator[Path]:
    for src in SOURCES:
        if not src.exists():
            continue
        for p in src.rglob("*"):
            if p.is_file() and p.suffix.lower() in ALLOWED_SUFFIXES:
                yield p


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    if len(text) <= size:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += (size - overlap)
    return chunks


def make_id(path: Path, idx: int) -> str:
    rel = str(path).replace("/Volumes/Samsung PSSD T7/", "")
    h = hashlib.sha1(f"{rel}#{idx}".encode()).hexdigest()[:16]
    return f"agcoach-extra-{h}"


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
    _, namespace = pinecone_config()
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "action": "upsert",
            "namespace": namespace,
            "summary": summary,
            "count": count,
        }
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Re-embed all even if unchanged")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    openai_key = os.environ.get("OPENAI_API_KEY")
    pinecone_key = os.environ.get("PINECONE_API_KEY")
    if not openai_key or not pinecone_key:
        print("ERR: missing OPENAI_API_KEY or PINECONE_API_KEY", file=sys.stderr)
        sys.exit(1)

    state = load_state()
    file_state = state.get("files", {})

    files = list(walk_sources())
    print(f"Sources: {len(files)} files total across {sum(1 for s in SOURCES if s.exists())} dirs")

    pending = []
    for p in files:
        mtime = p.stat().st_mtime
        key = str(p)
        if not args.full and file_state.get(key) == mtime:
            continue
        pending.append((p, mtime))
    print(f"Pending embed: {len(pending)} files (changed since last run)")

    if args.dry_run:
        for p, _ in pending[:10]:
            print(f"  would embed: {p.relative_to(p.parents[len(p.parents)-3])}")
        return

    if not pending:
        print("Nothing to do.")
        return

    oai = OpenAI(api_key=openai_key)
    pc = Pinecone(api_key=pinecone_key)
    index_name, namespace = pinecone_config()
    index = pc.Index(index_name)

    total_chunks = 0
    embedded_files = 0
    batch = []

    for path, mtime in pending:
        try:
            text = path.read_text(errors="ignore")
        except Exception as e:
            print(f"  skip (read err): {path.name}")
            continue
        if not text.strip():
            file_state[str(path)] = mtime
            continue
        chunks = chunk_text(text)
        try:
            resp = oai.embeddings.create(
                model=EMBED_MODEL,
                input=chunks,
                dimensions=EMBED_DIM,
            )
        except Exception as e:
            msg = str(e)[:120]
            print(f"  skip (embed err): {path.name} — {msg}")
            continue

        rel_display = str(path).replace("/Volumes/Samsung PSSD T7/", "")
        for i, (chunk, emb) in enumerate(zip(chunks, resp.data)):
            batch.append({
                "id": make_id(path, i),
                "values": emb.embedding,
                "metadata": {
                    "path": rel_display,
                    "filename": path.name,
                    "chunk_idx": i,
                    "source": "agcoach-extras",
                    "category": (
                        "lib-data" if "lib/data" in rel_display
                        else "notebooklm" if "Notebooklm" in rel_display
                        else "other"
                    ),
                    "text": chunk[:1000],
                },
            })
            total_chunks += 1
            if len(batch) >= BATCH_SIZE:
                index.upsert(vectors=batch, namespace=namespace)
                batch = []

        file_state[str(path)] = mtime
        embedded_files += 1

    if batch:
        index.upsert(vectors=batch, namespace=namespace)

    state["files"] = file_state
    save_state(state)
    log_write(f"agcoach-extras: {embedded_files} files, {total_chunks} chunks", total_chunks)
    print(f"Done. Embedded {embedded_files} files / {total_chunks} chunks to {index_name}/{namespace}")


if __name__ == "__main__":
    main()
