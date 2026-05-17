# Token Savior — recommended config for Claude Code

This file is auto-discovered by Claude Code. It tells the agent how to use
Token Savior efficiently. Drop this CLAUDE.md (or its contents) at the root
of your own project to reproduce the 100% / −77% active-tokens result on
[tsbench](https://github.com/Mibayy/tsbench).

## Defaults the bench uses

```bash
TOKEN_SAVIOR_PROFILE=tiny_plus            # 15 tools, ~2.5 KT manifest
TS_CAPTURE_DISABLED=1           # skip read-side capture sandboxing
```

`tiny_plus` is the Pareto-optimal profile. It exposes exactly the 15 tools
agents reach for after the first turn — locate, read, edit, audit, graph,
git, and config — and hides the rest behind `ts_search` (Nomic embeddings
on tool descriptions). Manifest math: tiny_plus ~2.5 KT vs lean ~7 KT vs
full ~10 KT.

## Tool routing (use these, not natives)

| Goal | Tool | Replaces |
|---|---|---|
| Locate a symbol | `find_symbol(name)` | `grep -rn` |
| Read a function / class | `get_function_source(name)` / `get_class_source(name)` | `cat` + scroll |
| One-shot context (loc + source + callers + deps) | `get_full_context(name)` | the whole chain |
| Search across project | `search_codebase(pattern)` | `grep` / `rg` |
| Discover any other tool | `ts_search(query)` | reading docs |
| Edit code (`.py`/`.ts`/`.tsx`/`.js`/`.jsx`) | `replace_symbol_source` / `insert_near_symbol` | `Edit` / `Write` |
| Add a model field (`.prisma`/`.py`/`.ts`) | `add_field_to_model` | hand edits |
| Move a symbol with import fixup | `move_symbol(name, target_file)` | copy-paste |
| Detect import cycles | `find_import_cycles` | manual reasoning |
| Detect duplicates | `find_semantic_duplicates(max_groups=30)` | manual review |
| Diff between refs | `detect_breaking_changes(ref="v1")` | `git diff` reading |
| Find dead code | `find_dead_code` | manual hunting |
| Audit config (orphans / secrets) | `analyze_config(checks=["orphans"])` | manual checks |
| Git status (structured) | `get_git_status` | `git status` parsing |

`Edit` / `Write` / `Read` / `Grep` stay allowed for `.env`, `.yml`, `.json`
config and `.md` docs. They are **forbidden on source code** in the
benchmark — the model that uses them on `.py`/`.ts` files loses points.

## Hard rules from the v2 system prompt

These rules earn the last 4 points (192/192 vs 188/192) on Opus tiny+v2:

- **Never spawn `Agent`** (sub-agent delegation). It runs without MCP
  context, can't see the project, and abandons the task. The harness
  also bans it via `--disallowedTools Agent`.
- **Code-generation tasks**: the response must contain (1) `import`
  statements at the top of the code block and (2) the explicit target
  file path (e.g. a `### packages/utils/foo.py` heading). The grader
  searches for both.
- **Rename tasks**: `replace_symbol_source` on the function definition
  + `search_codebase` for callers in the same module. Never touch
  same-named symbols in other modules.
- **Add-field tasks** (`.prisma` + `.ts`/`.py`): one `add_field_to_model`
  call per file. Don't insert by hand on `.prisma`.
- **Citations**: every symbol mentioned needs a `file::symbol` path.
  Never abbreviate to "...and N more".

## Reproduce the bench

```bash
git clone https://github.com/Mibayy/tsbench && cd tsbench
python3 generate.py --seed 42
git tag v1
python3 breaking_changes.py
git tag v2
TOKEN_SAVIOR_PROFILE=tiny_plus TS_CAPTURE_DISABLED=1 python3 bench.py --tasks all --run B
```

Score: 192 / 192 (100%) on Claude Opus 4.7 — wall 26.6 s/task, active
3 929 tokens/task. See [BENCHMARK-SUMMARY.md](https://github.com/Mibayy/tsbench/blob/main/BENCHMARK-SUMMARY.md).
