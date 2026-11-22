# crm-web: Cursor rules migration

All paths are under `crm-web/`. The Cursor files (`.cursor/rules/*`, `.cursorrules`) were left untouched so Cursor users keep working; remove them later once everyone has switched, or keep them if Cursor stays in use (note the content is now duplicated).

## What went where

| Source | Destination | Why |
|---|---|---|
| `.cursor/rules/core.mdc` (always on) | `AGENTS.md` | Short, always-applicable conventions. `AGENTS.md` is read by Codex; `CLAUDE.md` imports it. |
| `.cursorrules` (legacy) | `AGENTS.md` | Three of four lines duplicated `core.mdc` and were merged. The only unique rule, "API errors use `toastError`, never `alert()`", was added. |
| `.cursor/rules/react-components.mdc` (glob `src/components/**/*.tsx`) | `src/components/AGENTS.md` + `src/components/CLAUDE.md` (`@AGENTS.md`) | Path-scoped rule; a nested instruction file loads only when working in that folder, in both tools. |
| `.cursor/rules/db-migration.mdc` | skill `db-migration` | Task procedure, only needed when migrating. |
| `.cursor/rules/release-process.mdc` | skill `release-process` | Task procedure. |
| `.cursor/rules/hotfix.mdc` | skill `hotfix` | Task procedure. It was marked always-on in Cursor, which put a long procedure in every session; as a skill it loads only when needed. |
| `.cursor/rules/scratch.mdc` | skill `perf-investigation` | Manual-attach checklist; it had no description, so one was written. |

Skills are in `.claude/skills/<name>/SKILL.md` (Claude Code) and `.agents/skills/<name>/SKILL.md` (Codex), with identical bodies. In the Claude Code copies, `hotfix` and `release-process` have `disable-model-invocation: true`, so they run only when someone invokes them explicitly rather than being triggered automatically. The Codex copies do not have that flag, since it is a Claude Code setting.

## Notes

- `AGENTS.md` is the single source of truth for the always-on rules. Edit it, not `CLAUDE.md`.
- The skill bodies are copies in two places and must be kept in sync by hand.
- Skill descriptions were written by me from each rule's content; review them so they trigger when you want.
- Not migrated, not needed: Cursor frontmatter (`alwaysApply`, `globs`) has no equivalent and was dropped.
