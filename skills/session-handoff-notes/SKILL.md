---
name: session-handoff-notes
description: "Writes the session-continuation note that a coding agent leaves for its own next session, or another agent, when long work stops, from a fixed eight-section template, and validates it with a checker script: every success claim shows its command and result, every changed file exists, decisions are questions, no credential is pasted. Use when the user says handoff, hand off, wrap up the session, context is getting full, save progress for tomorrow, or asks to resume from a note. Do not use to audit a handover package for readiness (the handover-readiness-check skill does that), or for commit messages, pull request descriptions, changelogs, meeting notes or project documentation."
license: Apache-2.0
compatibility: Tool-neutral. The checker script needs Python 3.9 or newer (standard library only). No network access is used.
metadata:
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.2.0"
  network: none
---

# Session handoff notes

A handoff note is read cold by a reader with none of this session's memory. It is worth only what that reader can act on: a vague line forces them to rediscover the fact, and an unproven "it works" sends them down a path that may be broken. Write every line so it can be checked.

## Scope

This skill produces and validates the note itself: the note a session writes about its own work. It does not judge a handover package someone else supplies (acceptance criteria, ownership, readiness for a person to take over); for that use `handover-readiness-check`. If the user hands over an existing package and asks whether it is ready, stop and say so.

## Workflow

### 1. Collect facts from the repository, not from memory

Run these and keep the output at hand:

```bash
git status --short
git diff --stat
git rev-parse --short HEAD
git branch --show-current
```

Outside git, list the files you touched from your own tool history and say so in the note. Also gather what the diff cannot show: database or remote changes, environment variables set, services started, files outside the repository.

### 2. Fill the template

Copy [assets/handoff-template.md](assets/handoff-template.md) to the place the next session will look first (repository root, named `HANDOFF-YYYY-MM-DD.md`, unless the user names a place). Fill every section; delete none. Read [references/section-guide.md](references/section-guide.md) only for the section you are unsure about: it gives the rule, a weak line and its repair.

Rules that decide quality:

1. **Every change names a file** in backticks, with one line on what changed.
2. **Every success claim carries evidence on the same line**: the command in backticks and its result (exit code, counts or key output). A check you skipped is written as "not run" with the reason.
3. **Open decisions are questions** with options, a recommended default and who must answer.
4. **Next steps are numbered**, step 1 re-establishes the baseline with a command, and each step names a file or a command.
5. **Commands are literal and copyable**, with real values. Never include a secret; name where it lives instead.
6. **Not verified is honest**: list what was only read, assumed, or untested.

### 3. Verify the note

```bash
python scripts/handoff_note_check.py HANDOFF-YYYY-MM-DD.md --root .
```

Run the script, do not edit it. It prints one JSON object (`schema_version` 1, `file`, `ok`, `counts`, `findings` with `level`, `code`, `line`, `message`). Exit 0 means no PROBLEM, 1 at least one, 2 unreadable input. Credential patterns are case-insensitive and include `password = value`, `API_TOKEN: value`, AWS key ids, `sk-` and `ghp_` tokens and private key headers. Rule 4 is enforced as a NOTE (`first_step_not_concrete`): step 1 with no command or file in backticks. Fix every `PROBLEM` finding and re-run until `"ok": true`. Judge each `NOTE` finding and fix it unless it is a deliberate choice. The script checks that evidence is shown, paths exist and sections are filled; it cannot tell whether a stated result is true, so re-run the two or three most important commands yourself before you finish and correct the note if the output differs.

Without Python, check by hand: both header lines present, all eight sections filled, every change names an existing file, every success claim has command plus result, every decision ends in a question, step 1 is a command.

### 4. Report to the user

```
Note: <path> (<lines>)
Checker: <ok true/false, PROBLEM and NOTE counts, or "not run: checked by hand">
Re-run by me before finishing: <commands and results>
Open decisions waiting on the user: <list, or none>
Not verified: <list>
```

## Resuming from a note

Read the whole note, then run the commands in step 1 of Next steps before doing anything else. If the repository state differs from the Repo state line (other commit, other modified files), say so to the user and reconcile before continuing. Treat every claim in the note as a lead until a command confirms it.

## Limits

- The script checks form and evidence, not truth; a note can pass and still be wrong.
- It reads only the note and the paths the note names under `--root`; it never runs the commands in the note.
- Notes go stale. A note older than the last commit, or written before other people pushed, needs the Repo state check above.
- Do not paste secrets, tokens or personal data into a note; notes are often committed or shared.
- The template is for notes that are filled in; the unfilled template fails the check by design.
