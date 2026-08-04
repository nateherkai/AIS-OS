# Installation

```bash
git clone https://github.com/Mibayy/token-savior
cd token-savior
python3 -m venv ~/.local/token-savior-venv
~/.local/token-savior-venv/bin/pip install -e ".[mcp]"
```

# Configuration

Add to `.mcp.json`:

```json
{
  "mcpServers": {
    "token-savior": {
      "command": "~/.local/token-savior-venv/bin/token-savior",
      "env": {
        "WORKSPACE_ROOTS": "/path/to/project",
        "TOKEN_SAVIOR_CLIENT": "codex"
      }
    }
  }
}
```

Replace `/path/to/project` with one absolute path or a comma-separated list in `WORKSPACE_ROOTS`. Set `TOKEN_SAVIOR_CLIENT` to the MCP caller name you want to see in the dashboard, for example `codex` or `hermes`.

# Supported languages

Python, TypeScript/JS, Go, Rust, C#, **C/C99/C11**, **GLSL**, Markdown, JSON, YAML, TOML, INI, ENV, XML, HCL/Terraform, Conf, Dockerfile — plus a generic fallback for everything else.

See the full feature matrix in `README.md`.
