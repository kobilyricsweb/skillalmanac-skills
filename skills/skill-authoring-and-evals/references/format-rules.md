## Contents

- Folder layout
- Frontmatter fields
- Name rules
- Description rules
- Loading and budgets
- Where each tool looks
- Pre-flight checklist
- Sources

# Format rules for a portable skill

Facts below were read from the sources at the end of this file; wording is ours. Re-read the sources when a tool ships a new release.

## Folder layout

```
my-skill/
  SKILL.md        required
  references/     optional, Markdown opened on demand
  scripts/        optional, code the agent runs
  assets/         optional, templates the agent copies or fills
```

The folder name is the skill name. Keep every file referenced from `SKILL.md`; a file the body never names will not be found. Keep references one level deep: `SKILL.md` links to them, they link to nothing, because an agent that follows a chain of links may read only the top of the deeper files.

## Frontmatter fields

| Field | Status | Rule |
|---|---|---|
| `name` | required | See name rules |
| `description` | required | 1 to 1,024 characters; see description rules |
| `license` | optional | Short identifier or a file name |
| `compatibility` | optional | Up to 500 characters; only a real requirement such as an interpreter version or network use |
| `metadata` | optional | Map of string keys to string values; put author and version here |
| `allowed-tools` | optional, experimental | Tool names differ between agents; skip it in a portable skill |

Keys outside this list are the main cause of rejected uploads on strict surfaces. Per-tool extras belong in a generated variant, not in the canonical file. Use single-line values: block scalars (`|` or `>`) and anchors break simple parsers.

## Name rules

1 to 64 characters; lowercase letters, digits and single hyphens; no leading, trailing or doubled hyphen; equal to the folder name. Some upload surfaces reject names containing the vendor words "anthropic" or "claude". Prefer a gerund or noun phrase that states the job (`reviewing-pull-requests`); avoid `helper`, `utils`, `tools`.

## Description rules

- Third person: "Writes ...", not "I can write ..." or "You can ...". The description is injected into the agent's own context, and a shifting point of view confuses selection.
- No angle-bracket tags.
- Say what, when and what not. The trigger clause is the part that decides loading.
- The skill list shown to the agent has a shared budget in some tools, and descriptions are shortened first; the start of the description therefore matters most.

## Loading and budgets

Three levels. Level 1: name and description of every installed skill, always in context. Level 2: the body of `SKILL.md`, read when the skill is chosen; keep under 500 lines and about 5,000 tokens. Level 3: references, scripts and assets, opened or run only when the body says so; script source need not enter context when the agent only runs the script and reads its output.

Long reference files (over about 100 lines) start with a contents list so a partial read still shows what exists.

## Where each tool looks

Project-level skills live in a skills folder under the repository root; user-level ones under the home directory. The Claude family reads `.claude/skills/<name>/`; several other coding agents read `.agents/skills/<name>/`, and some also read the Claude folder. Installing the same folder to both locations covers the common tools. Locations change between releases: check the tool's own documentation before telling a user a path.

## Pre-flight checklist

Use when Python is not available. Every line should be yes.

- Folder name equals `name`; name matches the name rules
- Only spec keys in the frontmatter; values on one line
- Description: third person, has `Use when`, has `Do not use for`, 150 to 700 characters, trigger words in the first 200
- Body under 200 lines, numbered workflow, `Limits` section
- Every file in `references/`, `scripts/`, `assets/` is named in the body, with the reason to open it
- No file links to another reference file
- Paths use forward slashes
- Each script has a documented fallback
- No time-sensitive wording outside a dated note

## Sources

- Open format specification, folder layout, field limits and validator: https://agentskills.io/specification
- Vendor authoring guidance (naming, descriptions, evaluation-first method, budget advice): https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Reference skill-creation method (paired runs, trigger query sets): https://github.com/anthropics/skills/tree/main/skills/skill-creator
- Another vendor's skill documentation (scan locations, description budget): https://learn.chatgpt.com/docs/build-skills
