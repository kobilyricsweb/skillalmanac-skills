---
name: rules-to-skills-migration
description: Migrates editor and agent rule files (.cursor/rules .mdc files, .cursorrules, Windsurf rules, Copilot instructions, long runbooks inside CLAUDE.md) into a portable setup of AGENTS.md for always-on rules and agent skills for on-demand procedures, using an inventory script that classifies every rule by how it is activated. Use when the user asks to convert, migrate, port or consolidate cursor rules or other rule files, turn a rule into a SKILL.md, make rules work across several coding tools, or decide which rules should be always-on and which on-demand. Do not use to write a new skill or instruction file from scratch, or to explain how one tool's rules work.
license: Apache-2.0
compatibility: Produces open-standard skill folders and AGENTS.md. Source formats covered are listed in the reference file with the date they were checked. The inventory script needs Python 3.9 or newer (standard library only). No network access is used.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# Rules to skills migration

A rule file has two parts: the text, and the way it is switched on (always, by file pattern, by the model's choice, by hand). A migration that copies the text and ignores the switch produces a setup that loads the wrong things at the wrong time. Classify by activation first, then move the text.

## Workflow

### 1. Inventory

```bash
python scripts/rules_inventory.py path/to/repo
```

Run the script, do not edit it. It finds rule and instruction files of the known formats, reads their frontmatter, and prints one row per file: activation, size, and a suggested destination. It also flags procedures filed as always-on, short always-on rules filed as on-demand, and lines that appear in more than one source. Without Python, list the files by hand using the locations in [references/source-formats.md](references/source-formats.md); read that file in any case for what each frontmatter field means, because the same word means different things in different tools.

### 2. Decide the destination of each rule by what it is, not where it was

| The rule is | Destination |
|---|---|
| A convention that applies to all work in the repo, a few lines | root `AGENTS.md` |
| A convention for one area or file pattern | an `AGENTS.md` in the directory that best covers the pattern |
| A multi-step procedure used now and then (release, hotfix, migration, incident triage, a checklist) | a skill |
| Reference material consulted during a task | a skill, with the bulk in `references/` |
| A personal preference | the user-level file of that person's tool; not the repo |
| Something a linter, formatter or CI job enforces | drop it; name the tool once in `AGENTS.md` |

The source's activation is evidence, not a verdict. Correct it when it is wrong:

- A long procedure marked always-on costs every session its full length. It becomes a skill, with at most a one-line pointer in `AGENTS.md`.
- A two-line convention marked "model decides" or "manual" that should always hold goes into `AGENTS.md`.
- A manual rule with no description needs one written before it can be a skill: nothing can trigger a skill that has no description.

### 3. Settle duplicates and conflicts before writing

The same rule often lives in several sources, sometimes with different wording or different facts. Merge duplicates into one line. For a conflict, find the fact in the repo (lockfile, manifest, config, CI file), keep the version the repo supports, and report the conflict and the evidence. If the repo cannot settle it, ask; do not pick silently and do not keep both.

### 4. Write AGENTS.md

Short, always-on, verified. Every command and path checked against the repo. Rules keep their reasons. Stay well under 100 lines at the root. Tools that have their own always-loaded file get a thin pointer to it; the loading rules of each tool are in the reference.

### 5. Write each skill

Start from [assets/skill-skeleton.md](assets/skill-skeleton.md). A rule is prose aimed at an editor assistant; a skill is a procedure an agent loads when a description matches. Converting means rewriting, not renaming:

1. **Name**: lowercase words and hyphens, equal to the folder name, states the job, no tool or vendor names.
2. **Description** (this decides whether the skill ever loads): third person; what it does; `Use when` followed by the words a user would type and the situations that should trigger it; `Do not use for` the nearest wrong job. Write it from the user's vocabulary, not the rule's title. Between 150 and 700 characters.
3. **Frontmatter**: only `name`, `description`, and optionally `license`, `compatibility`, `metadata`. Source-tool keys (`globs`, `alwaysApply`, `trigger`) and tool-specific extras are left out, because strict loaders reject unknown keys.
4. **Body**: a numbered workflow in the order the work is done. Hard rules next to the step they govern. A check at the end that proves the work is right (keep any query, command or checklist the rule had for this).
5. **Cut or move**: history, incident stories and rationale longer than a clause go to `references/` or are cut; tables and long lists consulted mid-task go to `references/` with a line in the body saying when to read them.
6. **Keep every fact**: identifiers, formats, thresholds, error codes, commands, exact strings. After writing, compare against the source and list anything dropped.

### 6. Install where each tool looks

Skills go in `.agents/skills/<name>/` (read by most coding tools) and `.claude/skills/<name>/` (the documented location for Claude Code). Write both and say that the two copies must stay identical; name one as the source and the other as the copy. A file-pattern rule keeps its precision only in tools that scope by path; in the others the nested `AGENTS.md` is the replacement. State this loss.

### 7. Old files

Do not delete the source files in the same step unless the user asked. Say what should happen to each: remove after the team confirms the new setup, or keep as the tool-specific version with the risk that two copies drift. If always-on source rules stay, the tool that reads them now loads the content twice; say so.

### 8. Verify and report

- Run the inventory again and confirm nothing is still filed as a misplaced procedure.
- For each created skill: name equals folder, description has trigger and boundary, only allowed frontmatter keys.
- Compare facts: every identifier, command and number in the sources appears somewhere in the result, or is listed as dropped with the reason.
- Give the user a check to run in each tool: ask it which instruction files and skills it loaded.

Report as a table, one row per source file:

```
| Source | Activation there | Destination | Why | Changed or dropped |
```

then: conflicts settled and the evidence; what is lost or weakened (path scoping, manual attach); what to do with the old files; the per-tool check.

**Plan-only requests** ("don't change anything yet", "what would go where"): do steps 1 to 3, write nothing in the repo, and deliver the same table plus the losses and the conflicts.

## Limits

- The script classifies by frontmatter and size. Whether a rule is a convention or a procedure is a judgement; check each suggestion.
- Whether a migrated skill triggers in a given tool depends on that tool and on the other skills installed; test with real requests.
- Some tools have a built-in migration command for part of this job (see the reference); it converts only some rule types and leaves the rest. Tell the user it exists and what it skips.
- Formats change between tool releases; the reference states the date it was checked.
