## Contents

- Trigger queries
- Reading trigger results
- Task assertions
- Check types for eval_score.py
- Blind grading
- Common ways evals lie

# Eval design for skills

## Trigger queries

Twenty queries as a floor: ten should load the skill, ten are near-misses.

Writing rules:

1. Write as the user types: lowercase, casual, partial. "my skill never fires, here's the file" beats "Diagnose a skill activation failure".
2. Near-misses share nouns or verbs with the skill but need another tool. For a skill about writing skills: "write an AGENTS.md for my repo", "make a hook that runs prettier", "what does SKILL.md stand for in this tutorial". A near-miss that no skill could plausibly want teaches nothing.
3. Include some should-trigger queries that never use the word "skill": "turn this runbook into something the agent loads on demand".
4. Vary length, politeness and the amount of context pasted in.
5. Have someone other than the description's author write at least half; an author writes the queries the description already matches.
6. Fix the file once tuning starts; add queries only in a new version of the set.

File format, `evals/trigger_queries.json`:

```json
[
  {"query": "my skill never loads on its own, fix the description", "should_trigger": true},
  {"query": "write an AGENTS.md for this repo", "should_trigger": false}
]
```

Results, `evals/trigger_results.json`, one entry per query with one boolean per fresh-session run:

```json
[
  {"query": "my skill never loads on its own, fix the description", "loaded": [true, true, false]}
]
```

## Reading trigger results

The scorer prints the rate over all runs for each kind and again for a held-out 40% selected by hash of the query text, so the split does not move when queries are added in a different order. Tune the description while looking only at the other 60%; the held-out figure is the honest one. A query that misses in one of three runs is flaky routing, not a pass: look at the other installed skills that compete for it.

Typical fixes, in order of cost: add the missing user word; move the trigger clause earlier; add a boundary phrase for the near-miss that stole the load; shorten the description if the listing shortens it away.

## Task assertions

Each task is a realistic prompt plus input files. Write 4 to 7 assertions per task.

- Prefer scripted checks over judged ones; they are repeatable.
- Make at least one assertion fail for a lazy run. If the baseline passes every assertion, the task does not measure the skill; make it harder or the assertion more specific.
- Assert outcomes, not the path taken. "The report lists the unchecked areas" can be tested; "the agent thought carefully" cannot.
- Assertions written by the skill's author tend to be too kind. Have a second person read them against the baseline output before the runs.
- Mark judged assertions in the label (`[judge]`) and keep them out of the scripted list.

## Check types for eval_score.py

In `evals/evals.json`:

```json
{"evals": [{"id": "task-1", "prompt": "...", "checks": [
  {"type": "file_exists", "path": "out/SKILL.md", "label": "skill file written"},
  {"type": "file_contains", "path": "out/SKILL.md", "pattern": "use when", "label": "trigger clause"},
  {"type": "file_not_contains", "path": "out/SKILL.md", "pattern": "<[a-z]+>", "label": "no tags"},
  {"type": "max_lines", "path": "out/SKILL.md", "max": 200},
  {"type": "frontmatter_key", "path": "out/SKILL.md", "key": "license"}
]}]}
```

| Type | Passes when |
|---|---|
| `file_exists` | at least one file matches `path` (glob allowed) |
| `file_contains` | the regular expression (case-insensitive, multi-line) matches in any matched file |
| `file_not_contains` | the file exists and the expression matches nowhere |
| `max_lines` | every matched file has at most `max` lines |
| `frontmatter_key` | a matched file has the key in its `---` block |

A missing file fails every type, including `file_not_contains`, so an empty output cannot pass. Paths are relative to the folder passed on the command line and may not leave it.

## Blind grading

For judged assertions, give a grader the two outputs labelled A and B in random order, the assertion text and nothing that reveals which used the skill. Require a quoted line as evidence for each verdict and a preference with a reason. Keep the A/B key in a separate file. Replies that mention "the skill" or "the checker" leak the configuration; strip such remarks before grading when possible. A human reads every disagreement.

## Common ways evals lie

- The queries or assertions were written after seeing the skill's text.
- One run per cell: a single flip changes the verdict.
- The skill's own script is also the only measure of success.
- The grader and the executor share a model and a taste for the same style.
- The catalogue in the trigger test is small, so competition for the load is missing.
- Tokens and time were not recorded, so a skill that doubles the cost looks free.
