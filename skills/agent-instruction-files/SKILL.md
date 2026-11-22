---
name: agent-instruction-files
description: Writes, audits and restructures the instruction files coding agents load on every session (AGENTS.md, CLAUDE.md and similar project memory files), keeping only verified, project-specific rules, checking every command and path against the repo with a bundled audit script, and setting up one shared source for several tools. Use when the user asks to write or improve an AGENTS.md or CLAUDE.md, wants best practices or an example applied to their repo, says the agent ignores its instructions or the file is too long or stale, or wants one file to serve several coding tools. Do not use for README or onboarding docs for humans, chatbot system prompts, or converting rule files into skills.
license: Apache-2.0
compatibility: Tool-neutral for AGENTS.md. Loading details for specific tools are in the reference file and were checked against each tool's documentation. The audit script needs Python 3.9 or newer (standard library only). No network access is used.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# Agent instruction files

An instruction file is read in full at the start of every session, by an agent that will act on it literally. Each line costs context every time and competes with every other line for attention. A wrong line is worse than a missing one: the agent runs the command that no longer exists, then spends the session recovering.

Two tests decide whether a line stays:

1. **Would the agent get it wrong without this line?** If a capable agent would do the right thing anyway, or a linter or formatter already enforces it, the line goes.
2. **Is it true today, and can that be checked in the repo?** Every command, path and version must be verified against files, not memory.

## Workflow

### 1. Read the repo before writing a word

Collect facts from their sources and note where each came from:

| Fact | Where to look |
|---|---|
| Package manager and scripts | lockfile name, `packageManager` field, `package.json` scripts, `Makefile`, `justfile`, `pyproject.toml`, task runners |
| What CI really runs, in what order | workflow files under `.github/workflows/` or the CI config |
| Language and tool versions | `go.mod`, `.nvmrc`, `requires-python`, toolchain files |
| Style already enforced by tools | formatter and linter configs |
| Generated code | "DO NOT EDIT" and "GENERATED" headers, generator scripts |
| Traps | comments that mention incidents, ordering, "never", "must"; test setup files; contributing notes |
| Existing instruction files | every `AGENTS.md`, `CLAUDE.md`, rule folders, tool-specific instruction files, at any depth |

When two sources disagree (a doc says tabs, the formatter config says spaces; one file says one version, the manifest another), the file the tools execute wins. Report the disagreement and which source settled it.

### 2. Audit what exists

For each existing instruction file run:

```bash
python scripts/instruction_file_audit.py path/to/AGENTS.md --root path/to/repo
```

Run the script, do not edit it. It reports paths that do not exist, package scripts and make targets that do not exist, a package manager that contradicts the lockfile, imports that point nowhere, lines that look like credentials, vague lines, duplicate lines, emphasis overuse, and size against the limits in the reference. Treat its list as leads: confirm each, then also read the file for what a script cannot see, namely contradictions between two lines and rules that are true but pointless.

Without Python, check every backticked path and command by hand against the repo and count lines.

**A credential in an instruction file** is a leak, not a style problem: remove it, tell the user it must be rotated because it is in version history, and point to where the value should come from. Do not repeat the value in the reply.

### 3. Decide what goes in

Keep, in this order of value:

1. Commands that are not guessable, with the order they must run in and what failure looks like ("tests need the database container; a connection error means it is not running").
2. Things that must never be done, with the consequence ("generated; CI fails if it differs").
3. Conventions that differ from the ecosystem default and are not enforced by a tool.
4. Domain facts that cause real bugs (units, coordinate order, time zones, money as integers).
5. Where things live, only when the layout is surprising.

Cut: personas and pep talk; project history and marketing; anything a linter, formatter or type checker enforces (point to the tool once instead); generic engineering advice; anything already in the README (link to it); repeated statements of one rule; emphasis words on ordinary lines.

Every kept rule that came with a reason keeps the reason, in a clause. Agents follow a rule with a reason more reliably and apply it sensibly at the edges.

Do not add a fact that is not in the repo or supplied by the user. If something important cannot be verified, ask, or leave a visible `TODO(owner): ...` line rather than a guess.

### 4. Place each rule at the right level

- **Root file**: what applies everywhere. Aim for under 100 lines; stop and split before 200.
- **Nested file in a subdirectory**: rules for one package or area. Tools that support nesting load the nearest file for the code being edited.
- **Procedures used occasionally** (release steps, incident runbooks): not in an always-loaded file. Move them to a skill or a linked doc and leave a one-line pointer.
- **Must happen every time, no exceptions**: an instruction is the wrong mechanism; say so and suggest a hook or CI check.

### 5. One source for several tools

When more than one coding tool is in use, keep the shared rules in `AGENTS.md` and make each tool's own file a thin pointer plus that tool's private notes. Read [references/tool-loading.md](references/tool-loading.md) for how each tool finds its files, the import syntax, and the size limits before choosing the layout; do not guess these.

Steps: merge the existing files into `AGENTS.md`, settling every conflict from the repo (step 1); keep tool-only notes (a tool's own subagents, hooks, commands) in that tool's file; reduce duplicates to pointers or remove them; then list for the user how each tool reaches the shared file and what they can run to confirm it.

### 6. Verify and report

Re-run the audit on every file written. It must report no missing path, command or import. Then report:

```
Files: <path> (<lines before> -> <lines after>), ...
Verified against: <manifest, CI file, configs actually read>
Fixed: <wrong commands and paths, each with the source that corrected it>
Conflicts settled: <rule A vs rule B -> winner, by which file>
Removed: <categories and counts, with two or three examples>
Kept: <the rules that survived>
Needs the owner: <secrets to rotate, TODO lines, things not verifiable from the repo>
Audit: <script result, or "not run: checked by hand">
```

## Limits

- The audit script checks that paths and commands exist, not that they do what the file says.
- Loading behaviour in the reference was read from each tool's documentation on the date given there; a tool update can change it. When behaviour matters, have the user ask the tool what it loaded.
- Shorter is not the goal; a missing trap costs more than ten extra lines. The goal is that every line earns its place.
