---
name: draft-reply
description: Paste an incoming email or message, get a draft reply in Bryan's voice. Classifies intent, picks the right response angle, drafts. L2 — Bryan reviews and sends. Trigger: /draft-reply, "draft a reply", "help me respond to this", "write a response to this email".
bike-method-phase: 1  # Phase 1 — Training wheels. Run manually first. Paste email, review draft, send yourself.
three-ms-attribution: |
  Adapted from The Three Ms of AI™ © 2026 Nate Herk.
---

## What this skill does

Bryan pastes an incoming email or message. Skill classifies intent, selects response strategy, drafts a reply in Bryan's voice. Bryan edits if needed and sends manually.

**L2 autonomy — AI drafts, Bryan sends. Never autonomous.**

## Execution

### Step 1: Read the incoming message

Bryan pastes the message. Extract:
- Sender name (first name if available)
- Intent category (see below)
- Key question or concern raised

### Step 2: Classify intent

| Category | Signals | Response angle |
|----------|---------|----------------|
| Support issue | "not working", "can't access", "error", "broken" | Acknowledge, ask clarifying question, promise fix |
| Feedback | "love it", "suggestion", "would be great if", "missing" | Thank them, confirm you're noting it, set expectation |
| Billing | "charge", "invoice", "subscription", "cancel", "price" | Direct, factual, reassuring |
| Trial interest | "trying it out", "just signed up", "testing" | Warm welcome, point to best first drill, invite feedback |
| Upgrade question | "how do I", "what's included", "difference between" | Clear answer, soft pitch for right tier |
| General / other | Anything else | Friendly, direct, invite next question |

### Step 3: Draft reply

Match Bryan's voice register from `references/voice.md`:
- Warm, direct, unpretentious
- Short sentences, no corporate tone
- Accountability-forward ("I'll get that fixed", "I'm adding it to the list")
- Genuine sign-off, not performative

Format:
```
Subject: Re: [original subject if known]

Hey [First Name],

[2-4 sentences max. Answer their question or acknowledge their issue. One concrete next step.]

[Optional: soft ask — feedback, upgrade, referral — only if natural]

Thanks,
Bryan
```

### Step 4: Show the draft

Print the draft clearly. Then ask:
> "Edit anything? Or ready to copy and send?"

If they say edit: take their instruction and redraft once.
If they say ready: print final version formatted for easy copy.

### Step 5: Log if contacted a trial or paid school

If sender is a trial or paid school, ask:
> "Want me to log this in the decisions log?"

If yes, append to `decisions/log.md`:
```
## YYYY-MM-DD — Replied to [Name] at [School]
**Decision:** Responded to [intent category] inquiry.
**Owner:** Bryan
```

## Notes

- Never send email directly. Draft only.
- If message is hostile or a refund demand: flag it — "This one needs your personal touch. Here's a draft but review carefully before sending."
- Keep drafts under 100 words. Bryan's style is short.
