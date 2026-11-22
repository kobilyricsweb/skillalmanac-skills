# How coding tools load instruction files

Read on 2026-11-20 from each tool's own documentation (sources at the end). Recheck when behaviour matters.

## Contents

- AGENTS.md (the shared format)
- Claude Code
- Codex
- Cursor
- Other tools
- Layouts that work
- Confirming what was loaded
- Sources

## AGENTS.md (the shared format)

Plain Markdown, no required fields or headings. Suggested content: project overview, build and test commands, code style, testing, security notes, commit and pull request rules. With nested files, the file closest to the code being edited takes precedence, and an explicit instruction in the chat overrides the files.

## Claude Code

- Its own file is `CLAUDE.md`. Locations, broadest first: organisation policy file; `~/.claude/CLAUDE.md` (user); `./CLAUDE.md` or `./.claude/CLAUDE.md` (project); `./CLAUDE.local.md` (personal, not committed). Files in parent directories of the working directory load at start. Files in subdirectories load on demand when a file there is read or edited. All loaded files are concatenated; nothing is overridden.
- **Imports**: a line containing `@path/to/file` pulls that file in, relative to the importing file, up to 4 levels deep. Imports inside code spans and fenced code blocks are not evaluated.
- **AGENTS.md**: by default it is read only when no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists in the working directory or above. A project that has a `CLAUDE.md` therefore needs the import. The documented way to share is a `CLAUDE.md` whose content is `@AGENTS.md` followed by any Claude-only notes. A symlink also works but is fragile on Windows.
- **Path-scoped rules**: `.claude/rules/*.md` load at start; a rule with a `paths` frontmatter list loads only when a matching file is read or edited.
- **Size**: target under 200 lines per `CLAUDE.md`. Nested and path-scoped files have a per-file character cap (40,000 characters on a 200K-token context).

## Codex

- Global: `~/.codex/AGENTS.override.md` if present and not empty, otherwise `~/.codex/AGENTS.md`.
- Project: from the project root (normally the git root) down to the working directory, one file per directory, checked in the order `AGENTS.override.md`, `AGENTS.md`, then any names in `project_doc_fallback_filenames`.
- Files are concatenated root first, so closer files come later and take precedence.
- **Size limit**: `project_doc_max_bytes`, default 32 KiB (32,768 bytes) across the combined files. Loading stops at the limit, so text past it is silently missing. Keep the root file small and push detail down into nested files.
- `CLAUDE.md` is not among the names it looks for by default; `project_doc_fallback_filenames` can add other names.

## Cursor

- Reads `AGENTS.md` in the project root and in subdirectories; nested files combine with their parents and the more specific one takes precedence.
- Its own project rules are `.cursor/rules/*.mdc` files (a plain `.md` file there is ignored) with frontmatter `description`, `globs`, `alwaysApply`. A rule with `alwaysApply: true` is loaded into every session, so it duplicates anything also in `AGENTS.md`.
- User rules are set in the application, not in files.
- Keep each rule under 500 lines.

## Other tools

The AGENTS.md site lists many tools as supporting the format, including GitHub Copilot's coding agent, Gemini CLI, Windsurf, Zed, Aider, Jules, goose, opencode, RooCode and Amp. Several also have their own file (for Copilot, `.github/copilot-instructions.md`). When the user names a tool that is not covered above, say that its loading rules were not verified here and check its documentation.

## Layouts that work

**Small repo, several tools**

```
AGENTS.md                 shared rules (the only place they are edited)
CLAUDE.md                 "@AGENTS.md" + Claude-only notes
```

Remove or shrink always-on Cursor rules that repeat the shared file. Keep a Cursor rule only for something Cursor-specific or scoped by glob.

**Monorepo**

```
AGENTS.md                 what applies everywhere, short
CLAUDE.md                 "@AGENTS.md"
packages/api/AGENTS.md    API-only rules
packages/api/CLAUDE.md    "@AGENTS.md"
packages/web/AGENTS.md    web-only rules
packages/web/CLAUDE.md    "@AGENTS.md"
```

Each nested `CLAUDE.md` imports the `AGENTS.md` beside it: Claude Code loads nested `CLAUDE.md` files on demand, and by its documented default it reads an `AGENTS.md` only when no `CLAUDE.md` exists in the working directory or above.

**Personal preferences** go in the user-level file of each tool, never in the shared file.

## Confirming what was loaded

Ask each tool, in a fresh session at the repo root and again inside a package: "List the instruction files you loaded and quote the first line of each." In Claude Code the `/memory` command shows the loaded files. For Codex, compare the combined byte size of the files on the path with the limit.

## Sources

- agents.md
- Claude Code documentation, memory page (code.claude.com/docs/en/memory)
- Codex documentation, AGENTS.md guide (learn.chatgpt.com/docs/agent-configuration/agents-md)
- Cursor documentation, rules page (cursor.com/docs/context/rules)
