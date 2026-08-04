"""
Hermes Claw emit_event helper — drop into hermes-claw/src/lib/emit_event.py

Writes typed events to Supabase activity_log so the Live HUD picks them up
in real time. Mirrors the TS helper at
gravity-claw/src/agent/emit-event.ts so both bots use the same schema.

Setup (one-time):
1. supabase-py already in Hermes Dockerfile.railway — no install needed
2. Set Railway env vars pointing at mission-control's Supabase project
   (NOT Ag Coach Pro's — activity_log lives in the MC project):

     railway variable set MC_SUPABASE_URL='https://beorbykrtoeocuqxlhrp.supabase.co'
     railway variable set MC_SUPABASE_KEY='<service-role-key from MC Supabase>'
     railway variable set HERMES_BOT_ID='hermes_claw'

   The helper also falls back to plain SUPABASE_URL/SUPABASE_KEY if MC_* not set,
   and final fallback to AGCOACH_SUPABASE_URL/AGCOACH_SERVICE_KEY for emergencies.
3. Apply schema migration in the MC Supabase project:
     ALTER TABLE activity_log ADD COLUMN IF NOT EXISTS bot_id TEXT DEFAULT 'gravity_claw';
4. Wire emit_event() — for Hermes plugin architecture, wrap ctx.register_tool
   in plugins/hermes_claw/__init__.py register(ctx) (covers all 8 tools at once).
   See docs/superpowers/specs/2026-05-18-hermes-integration-design.md Phase 2a.

Usage:
    from .emit_event import emit_event, make_thought_batcher

    await emit_event(
        type="task_start",
        action="reply to gmail",
        payload={"task_id": task_id, "intent": prompt[:200]},
    )

    batcher = make_thought_batcher()
    async for chunk in stream:
        await batcher.push(chunk.text)
    await batcher.flush()  # at stream end

    await emit_event(
        type="tool_call",
        action=f"tool: {tool_name}",
        payload={"call_id": call_id, "name": tool_name, "args": tool_input},
    )
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
from typing import Any, Awaitable, Callable, Literal

try:
    from supabase import create_client, Client  # type: ignore
except ImportError:
    create_client = None  # type: ignore
    Client = None  # type: ignore


EventType = Literal[
    "task_start",
    "task_end",
    "thought",
    "tool_call",
    "tool_result",
    "memory_write",
    "cost",
]


# ---------------- Supabase client (lazy, fail-soft) ----------------

_client: "Client | None" = None


def _get_client() -> "Client | None":
    global _client
    if _client is not None:
        return _client
    if create_client is None:
        print("[emit_event] supabase-py not installed; events will be no-op", file=sys.stderr)
        return None
    # Try MC project first (where activity_log lives), then generic, then agcoach as last resort
    url = (
        os.environ.get("MC_SUPABASE_URL")
        or os.environ.get("SUPABASE_URL")
        or os.environ.get("AGCOACH_SUPABASE_URL")
    )
    key = (
        os.environ.get("MC_SUPABASE_KEY")
        or os.environ.get("SUPABASE_KEY")
        or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("AGCOACH_SERVICE_KEY")
    )
    if not url or not key:
        print(
            "[emit_event] no Supabase creds (set MC_SUPABASE_URL + MC_SUPABASE_KEY); events will be no-op",
            file=sys.stderr,
        )
        return None
    _client = create_client(url, key)
    return _client


def _bot_id() -> str:
    # Default 'hermes_py' for the Python Hermes deployment.
    # TypeScript Hermes uses 'hermes_ts'. Legacy rows default to 'gravity_claw'.
    return os.environ.get("HERMES_BOT_ID", "hermes_py")


# ---------------- Privacy filter ----------------

_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"sk-[A-Za-z0-9_-]{8,}"), "sk-***"),
    (re.compile(r"Bearer\s+[A-Za-z0-9._-]{8,}", re.IGNORECASE), "Bearer ***"),
    (re.compile(r"password\s*=\s*[^&\s\"']+", re.IGNORECASE), "password=***"),
    (re.compile(r"api[_-]?key\s*=\s*[^&\s\"']+", re.IGNORECASE), "api_key=***"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{20,}"), "eyJ***"),  # JWT (e.g. Supabase keys)
]


def _scrub(value: Any) -> Any:
    """Recursively strip secrets from payload. Strings, lists, dicts."""
    if isinstance(value, str):
        out = value
        for pattern, replacement in _SECRET_PATTERNS:
            out = pattern.sub(replacement, out)
        return out
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    if isinstance(value, dict):
        return {k: _scrub(v) for k, v in value.items()}
    return value


# ---------------- Main emit ----------------

async def emit_event(
    *,
    type: EventType,
    action: str,
    details: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Write one row to activity_log. Fire-and-forget — never raises.

    The Supabase Python client is sync, so we run it in a thread executor to
    keep this awaitable and non-blocking.
    """
    try:
        client = _get_client()
        if client is None:
            return
        clean_payload = _scrub(payload or {})
        row = {
            "action": action,
            "details": details or "",
            "metadata": {"event_type": type, "payload": clean_payload},
            "bot_id": _bot_id(),
        }
        # supabase-py is sync; offload to thread so we don't block the event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: client.table("activity_log").insert(row).execute(),
        )
    except Exception as exc:  # noqa: BLE001 — fire-and-forget by design
        print(f"[emit_event] failed: {exc}", file=sys.stderr)


# ---------------- Thought batcher ----------------

class ThoughtBatcher:
    """Buffer streamed tokens and emit one `thought` event per ~50 tokens or 250ms idle.

    Usage:
        batcher = make_thought_batcher()
        async for chunk in stream:
            await batcher.push(chunk)
        await batcher.flush()  # at end-of-stream
    """

    FLUSH_TOKENS = 50
    FLUSH_IDLE_MS = 250

    def __init__(self) -> None:
        self._buffer: list[str] = []
        self._count = 0
        self._timer_task: asyncio.Task[None] | None = None

    async def push(self, token: str) -> None:
        self._buffer.append(token)
        self._count += 1
        if self._count >= self.FLUSH_TOKENS:
            await self.flush()
            return
        self._reset_timer()

    def _reset_timer(self) -> None:
        if self._timer_task is not None:
            self._timer_task.cancel()
        self._timer_task = asyncio.create_task(self._idle_flush())

    async def _idle_flush(self) -> None:
        try:
            await asyncio.sleep(self.FLUSH_IDLE_MS / 1000)
            await self.flush()
        except asyncio.CancelledError:
            pass

    async def flush(self) -> None:
        if self._count == 0:
            return
        text = "".join(self._buffer)
        self._buffer.clear()
        self._count = 0
        if self._timer_task is not None:
            self._timer_task.cancel()
            self._timer_task = None
        await emit_event(
            type="thought",
            action="reasoning",
            payload={"text": text},
        )


def make_thought_batcher() -> ThoughtBatcher:
    return ThoughtBatcher()


# ---------------- Quick self-check (run as script) ----------------

if __name__ == "__main__":
    async def _demo() -> None:
        print("[emit_event] demo: writing one task_start row")
        await emit_event(
            type="task_start",
            action="demo from CLI",
            details="self-check",
            payload={"task_id": "demo-001", "intent": "verify emit_event works"},
        )
        print("[emit_event] done — check activity_log for bot_id=hermes_claw, action='demo from CLI'")

    asyncio.run(_demo())
