---
name: skill-authoring-and-evals
description: Writes and tests agent skills (SKILL.md folders) for coding agents, starting from what a plain agent gets wrong and ending with a form check, trigger queries and with-versus-without task evals. Use when the user wants to create, improve or debug a SKILL.md or skill folder, asks why a skill never triggers or gets ignored, wants evals or a benchmark for a skill, or is unsure whether something belongs in a skill or an always-on instruction file. Do not use for writing the instruction file itself, subagent definitions, hooks, or MCP servers.
license: Apache-2.0
compatibility: Needs Python 3.9 or newer for the two bundled scripts (standard library only, no network). The authoring rules follow the open SKILL.md layout and apply to any coding agent that loads skills.
metadata:
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.2.0"
  network: none
---

# Skill authoring and evals

A skill is built backwards from a measured failure: no recorded baseline failure, no skill. This skill fixes the order of work, the numbers a skill must meet, and the exact file formats the two bundled scripts read, so the same package gives the same verdict in any tool that loads skills, with no network.

## Workflow

```
- [ ] 1. Gate: baseline failures recorded (3 or more)
- [ ] 2. Choose skill, instruction file or script
- [ ] 3. Write the trigger description from the decision table
- [ ] 4. Write SKILL.md, references, scripts
- [ ] 5. python scripts/skill_check.py <folder>: 0 ERROR, every WARN fixed or justified
- [ ] 6. Trigger test: python scripts/eval_score.py triggers ...
- [ ] 7. Paired task test: python scripts/eval_score.py tasks ...
- [ ] 8. Report in the fixed shape
```

Draft `evals/trigger_queries.json` and `evals/evals.json` before step 4, so the evals are not written to fit the skill.

### 1. Gate: record the baseline

In a fresh session with no skill, run 3 different realistic requests for the job. Fill one row per failure:

| Failure seen | Evidence (quote or file) | Instruction that would close it |
|---|---|---|

Rule: fewer than 3 rows from the 3 requests means the agent mostly gets it right, so answer `DO NOT BUILD`. An instruction with no row is cut. "Be more careful" is not a failure; a failure names an observable wrong output (wrong command, missed file, invented value, wrong order).

### 2. Choose the container

| If the content is | Put it in |
|---|---|
| One line, true for most tasks in the repo (build command, forbidden path) | Always-on instruction file |
| A procedure of more than about 10 lines, needed in fewer than half of sessions | Skill |
| A step that must give the same answer every time (count, parse, validate) | Script, called from a skill |
| Already done right in the baseline | Nothing |

One job per skill; a skill covering two jobs gets a description that fits neither.

### 3. Trigger description: decision table

The description is all the agent reads before choosing. Required shape: concrete verbs, then `Use when` with phrases users really type, then `Do not use for` with the nearest wrong jobs. Size bars are in the table in step 5. Diagnose a failing description from the trigger score, not by feel:

| Observed in the trigger test | Cause | Change |
|---|---|---|
| Should-trigger rate under 90%, missed queries contain a word absent from the description | Missing user vocabulary | Add that exact word to `Use when` |
| Should-trigger rate under 90%, misses use no skill vocabulary at all | Description names the artifact, not the user's goal | Add the goal phrase ("turn a runbook into something loaded on demand") |
| Near-miss false-load rate over 10% | No boundary, or a broad noun | Add `Do not use for <the stealing job>`; replace the broad noun with a specific object |
| Passes on the 60% tuning slice, held-out slice more than 10 points lower | Over-fitted to the tuning queries | Revert the last keyword addition; add new queries only in a new version of the query file |
| A query loads in 1 or 2 of 3 runs | Another installed skill competes | Move the distinguishing words into the first 300 characters |
| Passes here, but the listing shows the description cut short | Over about 700 characters | Cut to 150 to 700, job first |

Any edit to the description invalidates step 6; rerun it.

### 4. Write the body

Keep only what the model would not do unprompted: exact commands, thresholds, a decision table, a required output shape. Detail moves to `references/` (one level deep, each file named in the body with the reason to open it). Say whether the agent runs a script or reads it, forbid editing it to pass a check, and give a manual fallback. Start from [assets/skill-template.md](assets/skill-template.md). Field limits and upload traps: [references/format-rules.md](references/format-rules.md).

### 5. House checks `skill_check.py` enforces

```bash
python scripts/skill_check.py path/to/skill [--json]
```

Exit 0 means no ERROR, 1 at least one ERROR, 2 usage. It only reads. It keeps checking the description even when the frontmatter holds a block scalar (`|` or `>`), so one run shows every problem.

| Check code | Level | Threshold or rule |
|---|---|---|
| `name`, `name-folder` | ERROR | `a-z0-9` and single hyphens, at most 64 chars, equals the folder name |
| `name-reserved` | ERROR | name contains `anthropic` or `claude` |
| `description` | ERROR | missing or empty |
| `description-length` | ERROR over 1,024; WARN under 150 or over 700 | characters |
| `description-when` | ERROR | no `Use when ...` or `Use for ...` clause |
| `description-frontload` | WARN | `Use when` starts after character 300 |
| `description-boundary` | WARN | no `Do not use` or `not for` clause |
| `description-person` | ERROR | starts with "I ", "You can", "Use this to" |
| `description-tag`, `description-vague` | ERROR, WARN | an XML or HTML tag; "helps with", "and more", "etc." |
| `frontmatter-keys` | WARN | key outside name, description, license, compatibility, metadata, allowed-tools |
| `frontmatter` | ERROR | unparseable line; block-scalar value |
| `body-size` | ERROR over 500 lines; WARN over 200 | body lines |
| `body-tokens` | WARN | over 5,000 tokens (chars / 4) |
| `limits`, `workflow` | WARN | no `Limits` heading; no numbered `1.` step |
| `time-sensitive` | WARN | "currently", "as of 2026", "latest version" |
| `hidden-comment`, `paths` | ERROR | HTML comment; backslash path |
| `link-missing`, `orphan` | ERROR, WARN | link to a missing file; file in references, assets or scripts never named in the body |
| `reference-toc`, `reference-chain` | WARN, ERROR | reference over 100 lines without `## Contents`; reference linking another `.md` |
| `script-docstring`, `script-syntax` | WARN, ERROR | no module docstring; does not parse |

### 6. Trigger test

Exact file shapes (the scorer rejects anything else with exit 2):

```
evals/trigger_queries.json  [{"query": "string", "should_trigger": true}]
evals/trigger_results.json  [{"query": "same string", "loaded": [true, true, false]}]
```

Rules: at least 20 queries, 10 should-trigger and 10 near-misses; at least 3 `loaded` booleans per query, each from a fresh session with 20 or more other skills installed; half the queries written by someone who did not write the description; some positives never contain the word "skill". Command:

```bash
python scripts/eval_score.py triggers evals/trigger_queries.json evals/trigger_results.json
```

Pass: should-trigger rate at least 90% and near-miss false rate at most 10%, on all queries and again on the held-out slice (queries whose SHA-1 value mod 5 is 3 or 4, about 40%). Tune only against the other 60%. Writing rules and examples: [references/eval-design.md](references/eval-design.md) ("Trigger queries").

### 7. Task test and the evals.json contract

`evals/evals.json`:

| Field | Type | Rule |
|---|---|---|
| `skill_name` | string | equals the folder name |
| `evals` | array | at least 3 tasks (house rule) |
| `evals[].id` | string | unique; the id passed on the command line |
| `evals[].prompt` | string | a realistic user message |
| `evals[].files` | array of string | optional; input paths relative to the skill root |
| `evals[].checks` | array | scripted checks; 4 to 7 per task (house rule); at least one must be able to fail for a lazy run |
| `evals[].judge` | array of string | optional; judged assertions, graded blind, never scored by the script |
| `checks[].type` | string | `file_exists`, `file_contains`, `file_not_contains`, `max_lines`, `frontmatter_key` |
| `checks[].path` | string | relative to the output folder, glob allowed, no `..`, not absolute |
| `checks[].pattern` | string | regex (case-insensitive, multi-line) for the two `contains` types |
| `checks[].max` | integer | for `max_lines` |
| `checks[].key` | string | for `frontmatter_key` |
| `checks[].label` | string | optional, shown in the report |

A missing file fails every check, including `file_not_contains`. Run each task twice (same model, same prompt, fresh context), once with the skill and once without, then:

```bash
python scripts/eval_score.py tasks evals/evals.json <task-id> out/with out/baseline
```

Exit 0 only if every check passes in the with-skill folder. Read the output for: `separating` checks (pass with, fail without: the only evidence the skill works); `NOT-MEASURING` (same result in both runs: replace the check); baseline equal to with-skill on all checks (cut that task's instructions); with-skill worse than baseline (release blocked). Blind grading of judged assertions: [references/eval-design.md](references/eval-design.md) ("Blind grading").

### 8. Report shape

```
Verdict: READY | NEEDS WORK | DO NOT BUILD (baseline already passes)
Form check: <errors> errors, <warns> warns, <what was fixed>
Triggers: all <x>% / <y>% false; held-out <x>% / <y>% false; misses: <queries>
Tasks: <id>: with <n>/<m>, baseline <n>/<m>, separating <k>, not-measuring <k>
Cost: <tokens or seconds per run, or "not recorded">
Not tested: <agents, models, runs per cell, native discovery>
```

## How this differs from a general skill-creator tool

It is tool-neutral and offline: two standard-library scripts, no network, no model calls, no browser viewer. It does not run the agent for you; you record which sessions loaded the skill and save the outputs, and the scripts score the files. Its measurable additions are the fixed 60/40 held-out split, the `NOT-MEASURING` detector and the numeric bars above.

## Limits

- The scripts judge form and counts, not whether the skill helps; only paired task runs show that.
- The 3-task minimum and 4-to-7 checks per task are house rules the scorer does not enforce.
- Trigger behaviour depends on the agent, model and the other installed skills; a pass in one setup is not a pass in another.
- The layout rules follow the open SKILL.md format; tool-specific extras break strict upload surfaces.
- Python 3.9 or newer. Without it, walk the table in step 5 by hand and tally results in a table.
