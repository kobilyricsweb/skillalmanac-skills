# Listing page content: project-tickets-writer

**One line:** Turns feature descriptions or meeting notes into engineer-ready tickets and validates them with a script.

## What it does

The skill gives an agent a fixed ticket contract (outcome, size, dependencies, non-goals, 1 to 6 Given/When/Then criteria, definition of done), a seven-step workflow and a nine-row decision table for deciding when to split a ticket. For meeting notes it adds a line-tagging procedure that keeps wishes, chatter and unresolved questions out of the tickets. A script, `scripts/tickets_lint.py`, reads a tickets file in JSON or Markdown and prints one JSON report: missing or non-Given/When/Then criteria, too many criteria, vague titles, oversized tickets, duplicate titles and ids, unknown dependencies, dependency cycles, and a build order when the graph is acyclic.

## Capabilities

- Ticket contract with numeric limits (3 engineer-days, 6 criteria, 3 dependencies)
- Splitting decision table; spike rule for criteria that cannot be written yet
- `ASSUMED:` labelling for invented numbers, with a report of what was assumed
- Validator with 16 error rules and 9 warning rules, strict JSON output, exit codes 0, 1, 2
- Markdown template and format reference

## When to use

Write tickets from a spec, PRD, chat thread or meeting notes; break a feature down; split a ticket engineers rejected; check a tickets file before handing it over.

## When not to use

Roadmaps, sprint planning, estimation sessions, writing a PRD, or filing tickets in a tracker (the skill never talks to one). It is not a story-mapping or prioritisation method.

## How it differs from nearby skills

No other skill in this catalogue writes tickets or validates a tickets file. `plan-stress-test` challenges a plan; this skill writes the work items from one. `session-handoff-notes` summarises a coding session; this one does not.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent applies the manual check in step 6.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real script run on the saved fixture `evals/files/t3-repair-tickets/tickets.json` (three refund tickets with a vague title, a free-text criterion and a dependency loop):

```
python scripts/tickets_lint.py evals/files/t3-repair-tickets/tickets.json
```

Output (shortened to the findings), exit code 1:

```
error   vague-title                 R1  title "Handle refunds" names no checkable change
error   criterion-not-gwt           R1  criterion 1 lacks Given, When, Then in that order
warning vague-criterion             R1  criterion 1 uses "properly"
warning missing-non-goals           R1
warning missing-definition-of-done  R1
error   dependency-cycle            R1  cycle: R1 -> R2 -> R3 -> R1
build_order: null
```

Second run, `evals/fixtures/good.md` (three password-reset tickets): `ok` true, 0 errors, 0 warnings, `build_order` `["T1","T2","T3"]`, exit code 0.

No with-skill agent run exists yet, so there is no saved set of tickets written by the agent to show.

## Limits

- The script checks form, not truth: a well-formed criterion can still describe the wrong behaviour.
- Vague-word lists are English only and are heuristics; two-word titles that begin with fix, update, support or make are flagged even when meant well.
- Sizes are the writer's estimate until the team confirms them.
- The script does not read or write any tracker; filing tickets is the user's step.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL and 0 WARN, and 9 of 9 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour, native discovery, cross-tool use, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste meeting notes with decisions, wishes and an open question; the agent tags the lines.
2. The agent splits one oversized item, citing the table row, and marks an invented delivery time `ASSUMED:`.
3. Run `tickets_lint.py`: first run shows two errors; fix; second run `ok: true` with a build order.
4. The closing report lists what was assumed and what was left out.

## FAQ seeds

- Does it need network access? No. The script reads one file and prints JSON.
- Will it create tickets in Jira, Linear or GitHub? No; it writes a file you can import or paste.
- Can I change the limits? Yes: `--max-criteria` and `--max-size-days`; the defaults are working values, not measured optima.
- Do my criteria have to be Given/When/Then? The validator requires it; if your team uses another form, treat `criterion-not-gwt` as the rule to override and say so.
- How is it different from asking an agent to "write user stories"? It adds numeric limits, a split table, an assumption report and a validator. No comparison run has been done.
- Does it estimate? Only as a size label you must confirm; it never replaces team estimation.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures only.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
