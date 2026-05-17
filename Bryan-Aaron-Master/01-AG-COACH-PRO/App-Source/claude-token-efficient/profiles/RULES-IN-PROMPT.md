## Copy these rules into your session

Paste this at the start of any chat instead of using CLAUDE.md:

```
Rules for this session:
- Think before acting. Read existing files before writing code.
- Be concise in output but thorough in reasoning.
- Prefer editing over rewriting whole files.
- Do not re-read files already read unless file may have changed.
- Test your code before declaring done.
- No sycophantic openers or closing fluff.
- Keep solutions simple and direct.
- User instructions always override this file.
```

---

## Why two approaches?

**CLAUDE.md file (recommended):**
- Automatic on every message
- Cached efficiently
- Costs 30% less per benchmark
- No copy-paste needed

**Rules in prompt (alternative):**
- Works without project setup
- Clearer what rules apply this session
- Useful for one-off tasks
- Costs ~41% more than CLAUDE.md

---

## Benchmark: both approaches tested on 3 challenges

| Approach | CSV | SQLite | WebSocket | Total | Pass |
|----------|-----|--------|-----------|-------|------|
| Rules in chat | $0.274 | $0.459 | $0.585 | $1.318 | 3/3 |
| **CLAUDE.md (v8)** | **$0.244** | **$0.406** | **$0.285** | **$0.935** | **3/3** |

Both work. CLAUDE.md saves money at scale.
