---
name: problem-solving
description: Enforces a structural "Logic Tree" approach to complex tasks. Use when the user requests a deep refactor, a new feature from scratch, or when the agent is stuck in a debugging loop.
---

# Problem Solving & Logic Trees

## When to use this skill

- Handling complex multi-step refactors
- Building new modules or features from scratch
- Breaking out of "death loops" (hallucinations or repeating errors)
- When the user asks for "efficiency" or "better builds"

## Core Workflow: The Logic Tree

Before modifying any files, you MUST build a logic tree in the chat or a planning artifact.

1. **Plan**: Define the objective, constraints, and the "Mental Model" of the solution.
2. **Validate**: Check the codebase for existing patterns, dependencies, or side effects. Propose the plan to the user.
3. **Branching Logic**: If Task A depends on Task B, define the success criteria for B before starting A.
4. **Execute**: Implement in small, verifiable chunks.
5. **Verify**: Run tests or visual checks after EACH chunk.

## Breaking Loops

If you fail a tool call twice or hit a lint error you can't solve:

- **STOP** all execution.
- **SUMMON** this skill.
- **RESPONSE**: "I'm stuck in a loop. I am resetting my mental model. Here is my new logic tree for resolving this..."

## Rules

- NEVER skip the "Validate" phase for files you haven't read yet.
- ALWAYS use bullet points for planning.
- ALWAYS ask: "What is the simplest way to verify this works?"
