"""pinecone_widget.py — read-only Pinecone access for dashboard widget + route.

Uses direct HTTP via curl subprocess (same pattern as ~/.claude/pinecone_memory.py)
so we don't need the pinecone SDK installed.

SECURITY: Never logs API key values.
"""

import json
import os
import re
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv("/Volumes/Samsung PSSD T7/gravity-claw/.env")
load_dotenv("/Volumes/Samsung PSSD T7/AIS-OS/.env")
load_dotenv()

# ── Config pulled from pinecone_memory.py (same creds) ────────
_PINECONE_MEMORY_PY = Path.home() / ".claude/pinecone_memory.py"
_PINECONE_WRITES_LOG = Path.home() / ".claude/pinecone_writes.jsonl"

# Read hardcoded values from pinecone_memory.py as primary source
def _read_pinecone_memory_py() -> dict:
    """Extract API_KEY and INDEX_HOST from ~/.claude/pinecone_memory.py."""
    result = {"api_key": None, "index_host": None}
    if not _PINECONE_MEMORY_PY.exists():
        return result
    try:
        text = _PINECONE_MEMORY_PY.read_text()
        ak = re.search(r'^API_KEY\s*=\s*"([^"]+)"', text, re.MULTILINE)
        ih = re.search(r'^INDEX_HOST\s*=\s*"([^"]+)"', text, re.MULTILINE)
        if ak:
            result["api_key"] = ak.group(1)
        if ih:
            result["index_host"] = ih.group(1)
    except Exception:
        pass
    return result

_PM = _read_pinecone_memory_py()

API_KEY: str = (
    _PM.get("api_key")
    or os.environ.get("PINECONE_API_KEY", "")
)
INDEX_HOST: str = (
    _PM.get("index_host")
    or ""
)
INDEX_NAME: str = (
    os.environ.get("PINECONE_INDEX_NAME", "gravityclaw")
)
NAMESPACE: str = "knowledge"
OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")

_stats_cache: dict | None = None
_stats_cache_ts: float = 0
_STATS_TTL = 60  # seconds


def _curl_pinecone(method: str, path: str, body: dict | None = None) -> dict:
    """Make a Pinecone REST call via curl subprocess. Returns parsed JSON."""
    if not API_KEY:
        return {"error": "PINECONE_API_KEY not configured"}
    if not INDEX_HOST:
        return {"error": "INDEX_HOST not configured — check ~/.claude/pinecone_memory.py"}

    headers = [
        "-H", f"Api-Key: {API_KEY}",
        "-H", "Content-Type: application/json",
    ]
    url = f"{INDEX_HOST}{path}"
    cmd = ["curl", "-s", "-X", method, url] + headers
    if body is not None:
        cmd += ["-d", json.dumps(body)]
    # F2: never surface str(e) — the cmd list contains the API key in argv
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {"error": "Pinecone request timed out"}
    except subprocess.CalledProcessError:
        return {"error": "Pinecone request failed"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON from Pinecone"}
    except Exception:
        return {"error": "Pinecone error"}


def stats() -> dict:
    """Return index stats including per-namespace breakdown. Cached 60s."""
    global _stats_cache, _stats_cache_ts
    now = time.time()
    if _stats_cache and (now - _stats_cache_ts) < _STATS_TTL:
        return _stats_cache

    data = _curl_pinecone("POST", "/describe_index_stats", {})
    if "error" in data:
        return {"index": INDEX_NAME, "namespace": NAMESPACE, "total_vectors": None, "dimension": None, "error": data["error"]}

    namespaces = data.get("namespaces", {})
    ns_data = namespaces.get(NAMESPACE, namespaces.get("", {}))
    total = ns_data.get("vectorCount", data.get("totalVectorCount", 0))
    dim = data.get("dimension", None)

    # Per-namespace breakdown (includes aios-vault)
    ns_breakdown = {
        ns: ns_info.get("vectorCount", 0)
        for ns, ns_info in namespaces.items()
    }

    result = {
        "index": INDEX_NAME,
        "namespace": NAMESPACE,
        "total_vectors": total,
        "dimension": dim,
        "namespaces": ns_breakdown,
        "vault_vectors": ns_breakdown.get("aios-vault", 0),
    }
    _stats_cache = result
    _stats_cache_ts = now
    return result


def recent(limit: int = 50) -> dict:
    """Read ~/.claude/pinecone_writes.jsonl and return last N entries."""
    if not _PINECONE_WRITES_LOG.exists():
        return {
            "items": [],
            "message": "No recent activity logged yet. Vector writes will appear here after next memory store.",
        }
    try:
        lines = _PINECONE_WRITES_LOG.read_text(errors="ignore").splitlines()
        items = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        # Most recent first
        items = items[-limit:][::-1]
        return {"items": items}
    except Exception as e:
        return {"items": [], "error": str(e)}


def query(text: str, top_k: int = 10) -> dict:
    """Embed text (via Pinecone inference API or OpenAI) and query Pinecone."""
    # F7: empty/oversized input guard
    if not text or not text.strip():
        return {"matches": [], "error": "Empty query"}
    text = text.strip()[:8000]

    if not API_KEY:
        return {"matches": [], "error": "PINECONE_API_KEY not configured"}
    if not INDEX_HOST:
        return {"matches": [], "error": "INDEX_HOST not configured"}

    # Use Pinecone's built-in inference embed (same as pinecone_memory.py)
    EMBED_URL = "https://api.pinecone.io/embed"
    MODEL = "multilingual-e5-large"
    embed_payload = json.dumps({
        "model": MODEL,
        "inputs": [{"text": text}],
        "parameters": {"input_type": "query", "truncate": "END"},
    })
    embed_headers = [
        "-H", f"Api-Key: {API_KEY}",
        "-H", "Content-Type: application/json",
        "-H", "X-Pinecone-API-Version: 2025-01",
    ]
    # F2: redact API key from all exception paths — never surface str(e) from secret-bearing subprocesses
    try:
        embed_result = subprocess.run(
            ["curl", "-s", "-X", "POST", EMBED_URL] + embed_headers + ["-d", embed_payload],
            capture_output=True, text=True, timeout=20,
        )
        embed_data = json.loads(embed_result.stdout)
        vector = embed_data["data"][0]["values"]
    except subprocess.TimeoutExpired:
        return {"matches": [], "error": "Embedding timed out"}
    except subprocess.CalledProcessError:
        return {"matches": [], "error": "Embedding subprocess failed"}
    except (KeyError, IndexError, json.JSONDecodeError):
        return {"matches": [], "error": "Embedding response parse error"}
    except Exception:
        return {"matches": [], "error": "Embedding failed"}

    # Query Pinecone
    query_body = {
        "vector": vector,
        "topK": top_k,
        "includeMetadata": True,
        "namespace": NAMESPACE,
    }
    data = _curl_pinecone("POST", "/query", query_body)

    if "error" in data:
        return {"matches": [], "error": data["error"]}

    matches = []
    for m in data.get("matches", []):
        meta = m.get("metadata", {})
        summary = meta.get("text", meta.get("summary", ""))
        if len(summary) > 200:
            summary = summary[:200] + "…"
        matches.append({
            "id": m.get("id", ""),
            "score": round(m.get("score", 0), 4),
            "metadata": meta,
            "summary": summary,
        })

    return {"matches": matches}
