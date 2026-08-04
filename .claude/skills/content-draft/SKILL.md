---
name: content-draft
description: Draft content (email, Facebook post, MailerLite blast, blog) in Bryan's voice for a chosen business. Never sends — writes to drafts/. Trigger on /content-draft, "draft a post", "draft an email", "write content for".
---

# Content Draft

Drafts external content in Bryan's voice. Never sends. Bryan reviews before anything goes live.

## Inputs

- **business:** which avenue (uses `business-router` if not specified).
- **channel:** `email | facebook | mailerlite | blog | sms`
- **topic:** what to write about.
- **audience:** (optional) which segment.

## Logic

1. **Resolve business** — if not given, invoke `business-router` to pick.
2. **Load voice register:**
   - All businesses default to `references/voice.md`.
   - Ranch Dad Strength may have a distinct register — check its context file.
3. **Load relevant context:**
   - `context/businesses/<chosen>.md`
   - `references/voice.md`
   - For ACP: also `context/about-business.md`, `context/priorities.md`
4. **Match channel constraints:**
   - email: subject line + body, ≤300 words unless asked otherwise
   - facebook: 1-3 paragraphs, no em dashes (Bryan's voice rule), conversational hook
   - mailerlite: subject + preheader + body + CTA
   - blog: title + intro hook + body + close, 600-1200 words
   - sms: ≤160 chars
5. **Draft.** Conversational. Direct. Accountability-forward. No corporate tone.
6. **Write to `drafts/`:**
   - Filename: `drafts/YYYY-MM-DD-<business>-<channel>-<slug>.md`
   - Header with metadata: business, channel, audience, topic, status: draft.
7. **Report to Bryan:** print file path + first 200 chars + ask for approval before any send.

## Hard rules

- **NEVER send.** Skill only drafts. Sending is a separate step requiring Bryan's explicit approval.
- **NEVER use em dashes** in external content (Bryan's voice rule from CLAUDE.md).
- For Ag Coach Pro emails to customers, sign as Bryan personally — not "the Ag Coach Pro team."
- If unsure about voice for a stub business, ask Bryan for a voice sample first; don't fabricate.

## Verification

- `/content-draft email ACP "trial follow-up Trinity"` → file appears in `drafts/`, no email actually sent.
- `/content-draft facebook ranch-dad-strength "morning lift recap"` → file matches Ranch Dad register (warns if stub).

## Provenance

Built manually 2026-05-21 as L4 capability. Reuses `references/voice.md` + per-business context files.
