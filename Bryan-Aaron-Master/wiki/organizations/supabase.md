---
name: supabase
type: organization
tags: [supabase, database, pgvector, auth, storage, edge-functions, infrastructure]
source_files: [raw/_ingested/2026-05-16-agcoach-BUSINESS_BRAIN.md, raw/_ingested/2026-05-16-agcoach-SCHEMA.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Supabase

PostgreSQL-based Backend-as-a-Service. Primary data store for Ag Coach Pro.

## Role in Ag Coach Pro

- **PostgreSQL** — all app data (47 public tables)
- **Auth** — email/password, Google OAuth, Clever OAuth (school district SSO)
- **Storage** — media assets
- **pgvector** — `knowledge_documents` table (3072-dim HNSW index, 20,987 chunks, ~390 MB) for RAG
- **Edge Functions** — 9 Deno functions handling AI proxying, Stripe webhooks, onboarding, notifications
- **pg_cron** — scheduled jobs (drain-role-promotions every 5m, stripe-reconcile every 15m, trial-reminder daily 14:00 UTC)

## Project Details

- **Project ID**: `nkoyotdafqllgbpuklva`
- **Region**: us-west-2
- **Postgres version**: 17.6.1
- **MCP available**: Yes (nkoyotdafqllgbpuklva)

## Key Edge Functions

match-knowledge (RAG search), gemini-proxy, anthropic-proxy, clever-auth, create-payment-intent, stripe-webhook, generate-annual-invoices, notify-assignment, process-support-email.

## Publishable Key Format

Supabase rotated from JWT anon keys to `sb_publishable_...` format. Never gate proxies on JWT shape — use `verify_jwt = true` in `config.toml` or non-empty length check only.

## pg_net Timeout Note

Default pg_net timeout is 5s, which aborts most reconcile/scan workloads. Must set `timeout_milliseconds` ≥ 60s on every `net.http_post` call.

## Related

- [[../sources/agcoach-schema|Database Schema]]
- [[../sources/agcoach-plan-supabase-admin|Supabase Admin Plan]]
- [[../concepts/agcoach-rag-architecture|RAG Architecture]]
- [[../concepts/agcoach-billing-systems|Billing Systems]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
