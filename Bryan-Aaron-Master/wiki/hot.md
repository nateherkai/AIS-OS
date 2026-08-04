# Hot Cache

Updated: 2026-05-20 (Pass 6 — Printing Press CLI factory)

Printing Press (mvanhorn): CLI factory + 50-CLI library for Claude Code. Turns any service into agent-native CLI in ~10 min. Key benchmark: MCP uses 35× more tokens than equivalent CLI; reliability drops 100%→72% at complexity. Decision order: CLI first → direct API → MCP last resort. Go required. Links: https://printingpress.dev/ / https://github.com/mvanhorn/cli-printing-press. Bryan's MCP-heavy stack (Supabase, Railway, Stripe) all have existing CLIs — switching = direct ROI gain.
