# Decision Context

Standing constraints and values that shape decisions in this AIOS.

## Hard Constraints

- Revenue target: $120K/yr from Ag Coach Pro (threshold to leave teaching)
- School target: 50 schools on Blue & Gold or Lone Star Elite by August 2026
- Debt payoff: all non-mortgage debt by end of 2026
- Never send email/messages without Bryan's explicit approval
- Never auto-deploy to production without Bryan's review

## Decision Principles

- Ag Coach Pro work > all other business avenues (highest leverage)
- Prefer automation that compounds (skills, crons) over one-shot fixes
- Minimum viable autonomy: draft, don't act. Increase autonomy only with validation history.
- Push model > pull model for cross-system bridges (laptop sleep breaks pull)
- Real DB in tests, not mocks (burned by mock/prod divergence 2026-Q1)

## Approved Patterns

- Dream engine → promote → skill pipeline for surfacing automation candidates
- File-based push for AIOS→Hermes state sync (decision 2026-05-22)
- Stripe webhook processing with synthetic row filtering
- CLI fallback when MCP tools break (temporary, fix root cause)
