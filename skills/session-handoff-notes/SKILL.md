---
name: session-handoff-notes
description: "Use when the user says handoff, hand off, wrap up, new agent, switching sessions, context is getting full, save progress for tomorrow, continue tomorrow, or asks to resume from a note. Writes the note a coding agent leaves for its next session, sized to the job: nothing to hand off gets a plain sentence, a small job gets a short Done / Left / Not run note, a long messy session gets the full template. A checker script counts words, flags credentials and unproven success claims. Do not use for commit messages, pull request descriptions, changelogs, meeting notes, project docs, or auditing someone else's handover package (use handover-readiness-check)."
license: Apache-2.0
compatibility: Tool-neutral. The checker script needs Python 3.9 or newer (standard library only). No network access is used.
metadata:
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.3.0"
  network: none
---

# Session handoff notes

A handoff note is read cold. Its worth is what the reader can act on. The most common failures are padding, invented detail and ignoring the user's length limit, so the main skill is deciding how little to write.

## 1. Pick the size first

| Situation | Write |
|---|---|
| No work was done, or the input shows nothing to carry over | One or two plain sentences saying there is nothing to hand off, plus any open question. No template, no invented goal. |
| Small job (a rename, one fix, under about 10 log lines) or the user gave a word limit | Short note, see step 2. |
| Long or messy session (many files, failed attempts, unfinished state) | Full template, see step 3. |
| Two sessions in one request | One short block per session, each with its own goal. Never merge goals. |

The user's word limit always wins. Aim for 80% of it. Count words by whitespace split, as the checker does.

## 2. Short note

Use only these labels, in this order, and nothing else:

```
Done: <what changed, with file names>
Left: <what remains, most important first>
Not run: <checks nobody ran, or "none">
```

Add `Decision:` only if the input shows a real open question. Use only facts present in the transcript, log or diff. Do not add decisions, owners, aliases, commands or exit codes the input does not contain. If something is unknown, write "not recorded". Check it with `python scripts/handoff_note_check.py note.md --short --max-words N` (omit `--max-words` if there is no limit).

## 3. Full note (long or messy sessions only)

Collect facts from the repository, not memory: `git status --short`, `git diff --stat`, `git rev-parse --short HEAD`, `git branch --show-current`. Outside git, list files from your tool history and say so.

Copy [assets/handoff-template.md](assets/handoff-template.md) to `HANDOFF-YYYY-MM-DD.md` (or the place the user names). Fill every section that has content. Write "none" for a section with nothing, rather than inventing text. Rules:

1. Every change names a file in backticks and one line on what changed.
2. Every success claim carries its command and result on the same line. A skipped check is "not run" with the reason, and a command whose exit code was never captured is listed under Not verified.
3. Open decisions are questions with options, a recommended default and who must answer.
4. Next steps are numbered; step 1 re-establishes the baseline with a command, and each step names a file or a command.
5. Never write a secret. Name where it lives and say it should be rotated if it was exposed in the log.
6. Not verified lists what was only read, assumed or untested.

Verify: `python scripts/handoff_note_check.py HANDOFF-YYYY-MM-DD.md --root .` (add `--max-words N` if limited). It prints JSON; exit 0 means no PROBLEM, 1 at least one, 2 unreadable. Fix every PROBLEM and re-run until `"ok": true`; judge each NOTE. It checks form, not truth, so re-run the two or three key commands yourself. Without Python, check the same rules by hand.

Section guidance is in [references/section-guide.md](references/section-guide.md); read only the section you are unsure about. Keep the full note under 200 lines.

## 4. Report to the user

Keep it to a few lines: the note path, checker result (or "checked by hand"), open decisions waiting on the user, and what is not verified. If the user set a word limit, the reply itself should be the note.

## Resuming from a note

Read the whole note, then run step 1 of Next steps before anything else. If the repo differs from the Repo state line, tell the user and reconcile first. Treat every claim as a lead until a command confirms it.
