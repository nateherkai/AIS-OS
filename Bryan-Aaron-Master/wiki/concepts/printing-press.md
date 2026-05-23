---
name: printing-press
type: concept
tags: [claude-code, cli, tooling, ai-workflow, token-efficiency]
source_files: [raw/_ingested/2026-05-20-printing-press-cli-factory.md]
domains: [06-AI-WORKFLOW]
created: 2026-05-20
updated: 2026-05-20
---

# Printing Press — Agent-Native CLI Factory

CLI factory + 50-CLI library. Turns any service into an agent-native CLI in ~10 minutes inside Claude Code. Built by [@mvanhorn](https://github.com/mvanhorn). Written in Go.

## What It Does

- **Factory**: generate a new custom CLI for any service (even ones with no public API) using a scaffold + Claude Code session
- **Library**: 50+ pre-built CLIs ready to install — covers common SaaS tools
- **Pattern**: replaces MCP servers and direct API calls with lightweight CLI binaries that Claude invokes as shell tools

## Benchmarks (from demo video)

| Metric | CLI | MCP |
|--------|-----|-----|
| Tokens used (same task) | 1× | 35× |
| Reliability (complex tasks) | 100% | 72% |
| Skool demo: upstream tokens | 132,000 | → 2,000 in context |

The 35× token multiplier means MCP servers are bleeding Bryan's AI budget on every tool call.

## Links

- Site + catalog: https://printingpress.dev/
- Factory repo: https://github.com/mvanhorn/cli-printing-press
- CLI library: https://github.com/mvanhorn/printing-press-library
- Video demo: https://youtu.be/YHk45NEpspE
- Go (prereq): https://go.dev/

## How to Use

1. Install Go
2. Clone the library or factory repo
3. For an existing CLI: `go install github.com/mvanhorn/printing-press-library/<cli-name>@latest`
4. For a new CLI: use the factory scaffold + Claude Code session (~10 min)

## Bryan's Application

- **Gravity Claw**: Telegram bot integrations (Supabase, Railway, Stripe) currently using APIs/MCPs — CLI replacements could cut token cost 35×
- **Ag Coach Pro**: any service-to-Claude integration should evaluate CLI first before MCP
- **ROI impact**: direct dollar reduction in Claude API spend; high leverage given current burn rate

## Related

- [[cli-api-mcp-priority]] — the decision framework this tool operationalizes
- [[claude-code-os]] — the environment Printing Press runs inside
- [[../06-AI-WORKFLOW/]] — AI tooling domain
