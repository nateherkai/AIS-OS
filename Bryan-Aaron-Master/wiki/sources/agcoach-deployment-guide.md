---
name: agcoach-deployment-guide
type: source
tags: [ag-coach-pro, deploy, vercel, dns, web]
source_files: [raw/_ingested/2026-05-16-agcoach-deployment-guide.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Deployment Guide (Vercel)

Early "pitch-day" deploy walk-through. Largely superseded by the current GitHub→Vercel pipeline ([[../concepts/agcoach-app-internal-skills-catalog|deployment-qa skill]] forbids using Vercel CLI for prod). Kept for the DNS + 404 fallback notes.

## Commands

```bash
npx expo export -p web         # writes dist/
npm i -g vercel                # one-time
vercel login && vercel         # interactive deploy
```

Project settings: name `ag_coach_pro_app`, framework `Other` / `Create React App`, build `npx expo export -p web` (or `npm run build`), output `dist`.

## SPA routing fix

Direct-link / refresh 404s on Vercel solved by checking in `vercel.json` at repo root and redeploying.

## Domain — agcoachpro.com

- A record `@` → Vercel IP.
- CNAME `www` → `cname.vercel-dns.com`.
- DNS propagation 15–30 min; verify with check-host.net.

## Status

Process now: push to `main` → GitHub→Vercel auto-deploy. Do not use `vercel` CLI for production (see `deployment-qa` skill). Domain + 404 fallback still apply.

## Related

- [[../organizations/vercel|Vercel]]
- [[../concepts/agcoach-app-internal-skills-catalog|App Internal Skills Catalog]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
