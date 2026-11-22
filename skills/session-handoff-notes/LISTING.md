# Listing page content: session-handoff-notes

**One line:** A handoff note the next coding-agent session can act on, checked for evidence, paths and vague items.

## How it differs from handover-readiness-check

`handover-readiness-check` audits a handover package that someone supplies, to decide whether another person can take the work over (acceptance criteria, reproducible state, ownership). This skill writes the note a coding-agent session leaves about its own work, from a fixed template, and mechanically validates that note (evidence per claim, real paths, decisions as questions, no credentials). Use this one at the end of your own session; use the other to assess a package before accepting it.

## What it does

The skill has the agent collect the real repository state (status, diff, commit), fill a fixed eight-section template, and then run a checker script on the note. The checker flags missing sections, changes that name no file, paths that do not exist, success claims with no command and result, vague lines such as "fixed stuff", decisions that are not questions, and credential-like strings. The agent fixes every finding, re-runs two or three key commands itself, and reports what was and was not verified. The same skill covers resuming from a note: compare the stated repository state with the real one before acting.

## Capabilities

- `assets/handoff-template.md`: header, goal, current state, changes, verification, open decisions, next steps, commands, not verified
- `scripts/handoff_note_check.py`: strict JSON findings (PROBLEM and NOTE), exit code 0, 1 or 2
- `references/section-guide.md`: the rule, a weak line and its repair for each section
- A fixed closing report that lists what was not verified

## When to use

Long sessions that end with a full context window, a pause until tomorrow, a hand-over to another agent or person, or a request to resume from an existing note.

## When not to use

Commit messages, pull request descriptions, changelogs, meeting notes and project documentation.

## Requirements

Python 3.9+ for the checker. No network. Tested tools: see Evidence (none beyond script runs).

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples (from saved script runs; no agent run has been saved yet)

1. Command: `python scripts/handoff_note_check.py evals/fixtures/bad_note.md --root evals/fixtures/repo`. Saved output: `evals/fixtures/expected_bad.json`: 14 PROBLEM and 5 NOTE findings, including `change_without_path` for "Fixed stuff in the cart module", `path_missing` for `src/missing_cart.py`, `verification_no_result` for "Ran `make test`." and `credential_like` for a pasted key (the value is not echoed).
2. Command: `python scripts/handoff_note_check.py evals/fixtures/good_note.md --root evals/fixtures/repo`. Saved output: `evals/fixtures/expected_good.json`: `"ok": true`, no findings.

Agent-written examples will replace these once the task evals in `evals/evals.json` have been run.

## Limits

- The script checks form and evidence, not truth; a note can pass and still be wrong.
- It never runs the commands in the note.
- Notes go stale; the resume procedure compares the stated state with the real one.
- Do not put secrets or personal data in a note.

## Evidence

See `VERIFICATION.md`. In short: static lint passes with 0 FAIL and 0 WARN; the script passes 4 recorded fixture cases. Not tested: any agent run with or without the skill, trigger behaviour, other tools, human review.

## Demo script (60 to 90 seconds)

To be recorded from a saved real run. Planned beats: (1) a session ends with half-finished work; (2) the agent runs `git status` and `git diff --stat`; (3) the checker returns PROBLEMs for an unproven "tests pass"; (4) the agent runs the test command, rewrites the line with its result, and the checker returns `"ok": true`.

## FAQ seeds

- Does it need network? No.
- What does the script send anywhere? Nothing; it reads the note and the paths it names.
- Does it run my commands? No; the agent must run them, the script only checks that results are shown.
- How is it different from asking the agent to summarize? It demands evidence per claim and checks it mechanically.
- Where is the note saved? Where you say, by default a dated file in the repository root; it is not committed unless you ask.
- How do I uninstall? Delete the skill folder.

## Changelog

- 0.2.0 (2026-11-21): fix round: scope narrowed against handover-readiness-check, case-insensitive credential patterns, `schema_version` in the JSON.
- 0.1.0 (2026-11-21): first version; script fixtures ran on this version; no agent evals yet.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Author: Skill Almanac Editorial. Accountable editor: Global Media Holdings. Drafted by an AI model (claude-sonnet-5-5). No independent human review yet.
