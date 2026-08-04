---
name: cli-api-mcp-priority
type: concept
tags: [claude-code, decision-framework, cli, mcp, api, ai-workflow, token-efficiency]
source_files: [raw/_ingested/2026-05-20-printing-press-cli-factory.md]
domains: [06-AI-WORKFLOW]
created: 2026-05-20
updated: 2026-05-20
---

# CLI > API > MCP Priority Framework

Decision framework for connecting Claude Code (or any LLM agent) to external services. Introduced alongside [[printing-press]] by @mvanhorn.

## The Rule

```
1. CLI first       — use or build a CLI binary
2. Direct API      — if no CLI exists, call the API directly
3. MCP last resort — only when CLI + API are genuinely insufficient
```

## Why This Order

MCP servers add a protocol translation layer that bloats token usage 35× vs an equivalent CLI on the same task. As task complexity grows, reliability also degrades (100% CLI → 72% MCP).

CLIs are:
- Leaner (shell invocations, not JSON-RPC round-trips)
- More reliable at scale
- Faster to build with [[printing-press]] (~10 min per service)

## When MCP Is Still OK

- Service has no CLI and no usable public API
- Task genuinely requires streaming tool introspection
- Integration complexity too high to justify a custom CLI

## Application to Bryan's Stack

| Integration | Current | Should Be |
|-------------|---------|-----------|
| Supabase queries | Supabase MCP | `supabase` CLI (already exists) |
| Railway deploys | Railway MCP | `railway` CLI (already exists) |
| Custom SaaS (e.g. Skool) | manual API | Printing Press factory CLI |
| Stripe | Stripe MCP | `stripe` CLI (already exists) |

Most of Bryan's current MCP usage has CLI equivalents — switching would cut token spend significantly.

## Related

- [[printing-press]] — tool that makes "CLI first" practical for any service
- [[claude-code-os]] — the platform where this framework applies
- [[../06-AI-WORKFLOW/]] — AI tooling domain
