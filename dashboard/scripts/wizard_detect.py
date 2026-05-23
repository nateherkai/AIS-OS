"""wizard_detect.py — auto-detects models, storage, memory config for onboarding wizard.

SECURITY: Never logs or returns secret values — only presence booleans + key names.
"""

import fcntl
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────
HERMES_ENV = Path("/Volumes/Samsung PSSD T7/hermes-claw/.env")
AIOS_ENV = Path("/Volumes/Samsung PSSD T7/AIS-OS/.env")
ZSHRC = Path.home() / ".zshrc"
ZSHENV = Path.home() / ".zshenv"
CONFIG_DEFAULT = Path(__file__).parent.parent / "config.json"


def _read_env_file(path: Path) -> dict:
    """Read a .env file and return {KEY: True} presence map (no values)."""
    result = {}
    if not path.exists():
        return result
    try:
        text = path.read_text(errors="ignore")
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r'^([A-Z0-9_]+)=.+', line)
            if m:
                result[m.group(1)] = True
    except Exception:
        pass
    return result


def _read_env_value(path: Path, key: str) -> str | None:
    """Read a specific value from a .env file. Used only for non-secret config like INDEX_NAME."""
    if not path.exists():
        return None
    try:
        text = path.read_text(errors="ignore")
        for line in text.splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return None


def _which(cmd: str) -> tuple[bool, str]:
    """Return (found, path) for a command. Also checks ~/.local/bin which shutil.which misses."""
    path = shutil.which(cmd)
    if path:
        return (True, path)
    # Check common user-local install paths not always in PATH
    for extra in [
        Path.home() / ".local/bin" / cmd,
        Path.home() / ".npm-global/bin" / cmd,
        Path("/usr/local/bin") / cmd,
    ]:
        if extra.exists():
            return (True, str(extra))
    return (False, "")


def _all_env_keys() -> dict:
    """Merge key presence from all env sources."""
    keys = {}
    for f in [HERMES_ENV, AIOS_ENV, ZSHRC, ZSHENV]:
        keys.update(_read_env_file(f))
    # Also check os.environ (already-loaded vars)
    for k in os.environ:
        if k.isupper():
            keys[k] = True
    return keys


def _detect_models(env_keys: dict) -> list:
    claude_found, claude_path = _which("claude")
    codex_found, codex_path = _which("codex")
    if not codex_found:
        codex_dir = Path.home() / ".claude/plugins/cache/openai-codex"
        if codex_dir.exists():
            codex_found = True
            codex_path = str(codex_dir)

    gemini_found, gemini_path = _which("gemini")
    if not gemini_found:
        # Check for Anthropic gemini plugin bridge
        gemini_bridge = Path.home() / ".claude/plugins/cache/cc-gemini-plugin"
        if gemini_bridge.exists():
            gemini_found = True
            gemini_path = str(gemini_bridge)

    openrouter_found = "OPENROUTER_API_KEY" in env_keys

    return [
        {
            "name": "claude",
            "label": "Claude Code",
            "detected": claude_found,
            "path": claude_path or "~/.claude",
            "enabled": True,
        },
        {
            "name": "codex",
            "label": "Codex CLI",
            "detected": codex_found,
            "path": codex_path or "not found",
            "enabled": codex_found,
        },
        {
            "name": "gemini",
            "label": "Gemini CLI",
            "detected": gemini_found,
            "path": gemini_path or "not found",
            "enabled": gemini_found,
        },
        {
            "name": "openrouter",
            "label": "OpenRouter",
            "detected": openrouter_found,
            "path": "env" if openrouter_found else "OPENROUTER_API_KEY not found",
            "enabled": openrouter_found,
        },
        {
            "name": "chatgpt",
            "label": "ChatGPT (manual)",
            "detected": False,
            "path": "manual",
            "enabled": False,
        },
    ]


def _detect_storage() -> list:
    bryan_master = "/Users/aaronfamilylivestock/Library/Mobile Documents/com~apple~CloudDocs/Bryan-Aaron-Master"
    paths = [
        (bryan_master, "Bryan-Aaron-Master vault"),
        (str(Path.home() / ".claude"), "Claude config"),
        ("/Volumes/Samsung PSSD T7/hermes-claw", "Hermes"),
        ("/Volumes/Samsung PSSD T7/ag-coach-app", "Ag Coach App"),
    ]
    result = []
    for p, label in paths:
        detected = Path(p).exists()
        result.append({"path": p, "label": label, "detected": detected, "enabled": detected})
    return result


def _detect_memory(env_keys: dict) -> dict:
    # Pinecone index name (not secret)
    index_name = (
        _read_env_value(HERMES_ENV, "PINECONE_INDEX_NAME")
        or _read_env_value(AIOS_ENV, "PINECONE_INDEX_NAME")
        or os.environ.get("PINECONE_INDEX_NAME")
        or "hermes"
    )

    # Supabase project_id — parse from URL (not the key itself)
    supabase_url = (
        _read_env_value(AIOS_ENV, "EXPO_PUBLIC_SUPABASE_URL")
        or _read_env_value(AIOS_ENV, "SUPABASE_URL")
        or os.environ.get("EXPO_PUBLIC_SUPABASE_URL")
        or os.environ.get("SUPABASE_URL")
        or ""
    )
    project_id = ""
    if supabase_url:
        m = re.search(r'https://([^.]+)\.supabase\.co', supabase_url)
        if m:
            project_id = m.group(1)

    obsidian = "/Users/aaronfamilylivestock/Library/Mobile Documents/com~apple~CloudDocs/Bryan-Aaron-Master"

    return {
        "obsidian": obsidian,
        "pinecone": {"index": index_name, "namespace": "knowledge"},
        "supabase": {"project_id": project_id},
    }


def _read_config(config_path: Path) -> dict:
    if config_path.exists():
        try:
            return json.loads(config_path.read_text())
        except Exception:
            pass
    return {}


def detect_all() -> dict:
    """Return full detection payload — never includes secret values."""
    env_keys = _all_env_keys()
    config = _read_config(CONFIG_DEFAULT)

    return {
        "models": _detect_models(env_keys),
        "storage": _detect_storage(),
        "memory": _detect_memory(env_keys),
        "hourly_value": config.get("hourly_value_usd", 100),
        "dream_prefs": config.get("dream_prefs", {
            "web_search": False,
            "image_per_card": False,
            "frequency": "PM",
        }),
    }


def save_wizard(config_update: dict, config_path: Path = CONFIG_DEFAULT) -> dict:
    """Merge wizard config into config.json atomically with exclusive file lock (F8)."""
    # Ensure file exists before attempting r+ open
    if not config_path.exists():
        config_path.write_text("{}")

    with open(config_path, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            try:
                current = json.load(f)
            except Exception:
                current = {}

            # Merge top-level keys from update
            allowed_keys = {"models", "storage", "memory", "hourly_value", "dream_prefs"}
            for key in allowed_keys:
                if key in config_update and config_update[key] is not None:
                    if key == "hourly_value":
                        current["hourly_value_usd"] = config_update[key]
                    else:
                        current[key] = config_update[key]

            # Atomic write via tmp rename
            tmp = config_path.with_suffix(".tmp")
            try:
                tmp.write_text(json.dumps(current, indent=2))
                tmp.replace(config_path)
            except Exception as e:
                if tmp.exists():
                    tmp.unlink()
                raise RuntimeError(f"Failed to write config: {e}")

            return current
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
