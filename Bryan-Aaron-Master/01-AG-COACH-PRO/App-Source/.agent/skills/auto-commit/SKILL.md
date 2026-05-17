---
name: auto-commit
description: Enforces that every time a task is completed, changes are automatically added to version control, committed with a descriptive message, and pushed to the remote repository. Use this skill whenever a change has been finalized and verified.
---

# Auto-Commit Skill

## Overview
This skill implements the rule: **Always commit and push to source control when a task is finished.** 

## When to use this skill
- Whenever a user requests a change, feature, bug fix, or image update, and the work has been completed and verified.
- Immediately before ending a task or notifying the user that a step is complete.

## Workflow

1. **Verify Completion**: Ensure the task meets all requirements and tests/builds successfully (if applicable).
2. **Review Changes**: Check `git status` to see what files were generated or modified. 
3. **Commit**: 
   - Add all relevant modified or untracked files to git (`git add <files>`).
   - Create a clear, concise commit message explaining what was fixed, added, or changed (`git commit -m "Description of changes"`).
4. **Push**:
   - Push the changes to the remote repository (`git push`).
5. **Report**:
   - Inform the user that the code was pushed successfully and the task is complete.
