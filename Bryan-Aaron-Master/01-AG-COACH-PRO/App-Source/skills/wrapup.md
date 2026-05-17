---
name: wrapup
description: End-of-session wrap-up — summarizes the session, saves key memories, and pushes a session log to the user's AI Brain NotebookLM notebook. Trigger on "/wrapup" or when user says "wrap up", "save this session", "end of session", "session summary".
---

# Session Wrap-Up

Run this at the end of every session to capture what happened and commit it to long-term memory.

## Step 0: Ensure AI Brain Notebook Exists

Before doing anything else, check if the user already has a Brain notebook set up.

**Check for saved notebook ID:**
Look for a memory file or config that stores the Brain notebook ID. Check the memory index for a reference like `brain_notebook_id`.

**If no notebook ID is saved:**

1. List existing notebooks: `notebooklm list --json`
2. Look for one titled "AI Brain" or similar (e.g. "[Name]'s AI Brain")
3. **If found:** Use that notebook's ID going forward
4. **If NOT found:** Tell the user:
   > "You don't have an AI Brain notebook yet. This is where I'll save a summary of every session so you can search, query, or generate reports from your history over time. Want me to create it now?"
5. If the user agrees, create it: `notebooklm create "[Name]'s AI Brain" --json`
6. Save the notebook ID to a memory file so future sessions find it automatically:
   ```
   Memory file: reference_brain_notebook.md
   Content: Brain notebook ID, title, and when it was created
   ```
   Also update the MEMORY.md index.

**If notebook ID IS saved:** Verify it still exists with `notebooklm list --json`. If it's been deleted, repeat the creation flow above.

## Step 1: Review the Session

Look back through the entire conversation and identify:

- **Decisions made** — what was decided and why
- **Work completed** — what was built, fixed, configured, or shipped
- **Key learnings** — anything surprising or non-obvious that came up
- **Open threads** — anything left unfinished or to revisit next time
- **User preferences revealed** — any new feedback about how the user likes to work

## Step 2: Save Memories

Check the existing memory index and save or update memories as needed:

- **feedback** — any corrections or confirmed approaches from this session
- **project** — ongoing work, goals, deadlines, or context that future sessions need
- **user** — anything new learned about the user's role, preferences, or knowledge
- **reference** — any external resources, tools, or systems referenced

Rules:
- Don't duplicate existing memories — update them instead
- Don't save things derivable from code or git history
- Convert relative dates to absolute dates
- Include **Why:** and **How to apply:** for feedback and project memories

## Step 3: Write Session Summary

Create a markdown session summary with today's date. Keep it concise but complete.

Format:
```markdown
# Session Summary — YYYY-MM-DD

## What We Did
- Bullet points of key work completed

## Decisions Made
- Key decisions and their reasoning

## Key Learnings
- Non-obvious insights or discoveries

## Open Threads
- Anything to pick up next time

## Tools & Systems Touched
- List of tools, repos, services involved
```

Save this to a temp file at `/tmp/session-summary-YYYY-MM-DD.md`.

If there are multiple sessions in the same day, append a counter: `/tmp/session-summary-YYYY-MM-DD-2.md`

## Step 4: Push to NotebookLM Brain

Add the session summary as a source to the Brain notebook:

```bash
notebooklm source add /tmp/session-summary-YYYY-MM-DD.md --notebook <BRAIN_NOTEBOOK_ID>
```

If the CLI is not on PATH, use the full path: `~/.notebooklm-venv/bin/notebooklm`

If auth fails, warn the user and skip this step — the memories are still saved locally.

## Step 5: Confirm

Tell the user:
- How many memories were saved/updated
- That the session summary was added to the Brain notebook (or skipped if auth failed)
- Any open threads to pick up next time

Keep it brief. No need to read back the full summary — just confirm it's done.

## Error Handling

- If NotebookLM auth fails: save memories locally, skip the notebook push, tell the user
- If the Brain notebook was deleted: re-create it and update the saved ID
- If there's nothing meaningful to save: just say so, don't force empty memories
- If `notebooklm` CLI not found: try `~/.notebooklm-venv/bin/notebooklm`, if that fails tell user to install with `pip install notebooklm-py`

## Prerequisites

This skill requires the NotebookLM CLI. See the NotebookLMSkill for setup instructions:
1. Install: `pip install "notebooklm-py[browser]"` and `playwright install chromium`
2. Authenticate: `notebooklm login`
3. The skill handles everything else automatically on first run
