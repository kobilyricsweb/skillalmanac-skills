# Source and destination formats

Checked against each tool's documentation on 2026-11-20 (sources at the end).

## Contents

- Cursor
- Windsurf and its successor
- GitHub Copilot
- Claude Code
- Codex
- Activation types across tools
- Where skills are read from
- The skill format in brief
- Sources

## Cursor

- Project rules: `.cursor/rules/`, files with the `.mdc` extension (a plain `.md` there is ignored). Subfolders allowed.
- Frontmatter: `description`, `globs`, `alwaysApply`.

| `alwaysApply` | `globs` | `description` | Type | Loaded |
|---|---|---|---|---|
| true | any | any | Always Apply | every session |
| false | set | any | Apply to Specific Files | when a matching file is in play |
| false | empty | set | Apply Intelligently | when the model judges the description relevant |
| false | empty | empty | Apply Manually | only when mentioned by name |

- Legacy single file `.cursorrules` at the repo root: older projects still have it; treat it as always-on text. Its current status is not stated on the rules page.
- User rules live in the application settings, not on disk; they cannot be inventoried from the repo. Ask the user.
- Cursor reads `AGENTS.md` at the root and in subdirectories, and reads skills from `.agents/skills/`, `.cursor/skills/`, and for compatibility `.claude/skills/` and `.codex/skills/` (plus the same folders in the home directory).
- Built-in migration: a `/migrate-to-skills` command converts Apply Intelligently rules and slash commands into skills. It leaves alone rules with `alwaysApply: true`, rules with `globs`, and user rules. Those are the ones this skill's workflow still has to handle.

## Windsurf and its successor

- Rule files: `.windsurf/rules/*.md`, the legacy root file `.windsurfrules`, and a global rules file. The product documentation now describes the same system under a new name with `.devin/rules/*.md`, and imports the Windsurf locations by default.
- Frontmatter key `trigger`: `always_on`, `glob` (with `globs`), `model_decision` (with `description`), `manual`.
- `AGENTS.md` is read as always-on rules at the workspace root and in directories between the root and the working directory.

## GitHub Copilot

- `.github/copilot-instructions.md`: always-on, plain Markdown, no frontmatter.
- Path-scoped instruction files under `.github/instructions/` may exist; check their frontmatter for a path pattern.
- The Copilot coding agent is listed among the tools that read `AGENTS.md`.

## Claude Code

- `CLAUDE.md` is always-on. Runbooks pasted into it are procedures filed as always-on.
- `.claude/rules/*.md`: always-on unless the file has a `paths` frontmatter list, which scopes it to matching files.
- A `CLAUDE.md` can import the shared file with a line containing `@AGENTS.md`. By default `AGENTS.md` is read directly only when no `CLAUDE.md` exists in the working directory or above.
- Skills: `.claude/skills/<name>/SKILL.md` in the project, `~/.claude/skills/` for the user.

## Codex

- Reads `AGENTS.md` from the project root down to the working directory, one file per directory, concatenated. Combined size is capped (32 KiB by default) and text beyond the cap is dropped without notice, so a root file swollen by migrated rules can lose its tail.
- Reads skills from `.agents/skills/` in the repo, its parents and the home directory.

## Activation types across tools

| Meaning | Cursor | Windsurf | Portable destination |
|---|---|---|---|
| Always loaded | `alwaysApply: true`; `.cursorrules` | `trigger: always_on`; `.windsurfrules` | `AGENTS.md` (if short) |
| By file pattern | `globs` set | `trigger: glob` | nested `AGENTS.md` in the covering directory |
| Model decides from a description | `description` only | `trigger: model_decision` | a skill; the description carries over as a starting point |
| By hand | none of the fields | `trigger: manual` | a skill; a description must be written |

What does not carry over:

- **Exact glob matching.** A nested `AGENTS.md` covers a directory, not a pattern. A rule for `**/*.test.ts` across the whole repo has no exact portable home; put it at the root, or keep the tool-specific rule and accept the duplicate.
- **Manual attach by name.** A skill can be invoked by name in most tools, but it can also trigger on its own from the description. If it must never trigger on its own, say so in the description's boundary and note that some tools offer a private flag for this in their own variant of the file.

## Where skills are read from

| Tool | Project locations |
|---|---|
| Codex, Gemini CLI, Copilot, Cursor | `.agents/skills/<name>/` |
| Claude Code | `.claude/skills/<name>/` |
| Cursor (also) | `.cursor/skills/`, `.claude/skills/`, `.codex/skills/` |

Writing `.agents/skills/` and `.claude/skills/` covers all of these.

## The skill format in brief

```
<skill-name>/
  SKILL.md        frontmatter + instructions
  references/     optional, read on demand
  scripts/        optional, run by the agent
  assets/         optional, templates
```

- `name`: 1 to 64 characters, lowercase letters, digits and single hyphens, equal to the folder name.
- `description`: 1 to 1,024 characters; what the skill does and when to use it.
- Optional: `license`, `compatibility` (up to 500 characters), `metadata` (string values).
- Body under 500 lines; references one level deep.

## Sources

- Cursor documentation: rules page and skills page (cursor.com/docs/context/rules, cursor.com/docs/context/skills)
- Rules documentation formerly at docs.windsurf.com (now served from docs.devin.ai)
- agents.md
- Codex documentation, AGENTS.md guide (learn.chatgpt.com/docs/agent-configuration/agents-md)
- Claude Code documentation, memory and skills pages (code.claude.com/docs)
- Agent Skills specification (agentskills.io/specification)
