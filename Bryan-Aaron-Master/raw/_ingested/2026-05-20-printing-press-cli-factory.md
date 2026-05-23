# Printing Press — CLI Factory Just 10x'd Everyone's Claude Code

Source: Google Drive share (Bryan Aaron, 2026-05-20)
Video: https://youtu.be/YHk45NEpspE

## Summary

Printing Press is a CLI factory + 50-CLI library that turns any service into an agent-native CLI in ~10 minutes inside Claude Code. The video walks through install, demos a Skool CLI built in 10 minutes (no public API), and lays out the CLI > API > MCP priority framework.

## Links

- Printing Press site (catalog + docs): https://printingpress.dev/
- CLI factory repo: https://github.com/mvanhorn/cli-printing-press
- Public CLI library: https://github.com/mvanhorn/printing-press-library
- Go (prereq): https://go.dev/

## Benchmarks

- 35× more tokens used by MCP vs equivalent CLI on same task
- Reliability: 100% (CLI) → 72% (MCP) as task complexity scales
- 132,000 upstream tokens → ~2,000 entered Claude's context in Skool demo

## Decision Framework

1. CLI first (use Printing Press library or factory)
2. Direct API if no CLI exists
3. MCP only as last resort
