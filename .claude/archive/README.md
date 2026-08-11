# Archived agent skills

Superseded local skill copies, kept for reference. Nothing here is loaded by Claude Code —
this folder is deliberately outside `.claude/skills/`.

| File | Was | Retired | Why |
|---|---|---|---|
| `build-input-xlsx-SKILL.md` | `.claude/skills/SKILL.md` | 2026-07-28 | Stale fork of the shared library skill `build-input-xlsx` in the `agentic-age` repo. Line-level diff confirmed it is a strict subset of the library version — the library adds Calculation and Checks tabs to the workbook pattern, the "primary sources only, never derive from computed model values" rule, and three gotchas (text-coerce lookup keys, no array formulas in Checks cells, wildcard criteria colliding on structured labels). Nothing was lost by retiring it. It also sat directly at `skills/SKILL.md` rather than `skills/build-input-xlsx/SKILL.md`, so it was likely never discovered. |

Current version: `agentic-age/skills/build-input-xlsx/`, installed at `~/.claude/skills/build-input-xlsx/`.
