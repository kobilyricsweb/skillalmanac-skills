---
name: release-notes-writer
description: Turns a git log, merged-PR list or CHANGELOG draft into user-facing release notes and a proposed version number, using a script that parses conventional-commit lines, groups them, and flags missing scopes, unmarked breaking changes, duplicates, reverts and unstructured logs. Use when the user asks for release notes, a changelog entry, what changed since the last tag, or which version to cut next (major, minor, patch). Do not use for tagging or publishing the release, writing commit messages, running the PR flow, or general documentation.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used and nothing is pushed or tagged. Without Python, follow the manual tables in steps 3 to 5.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Release notes writer

Release notes tell a reader what changed for them. A commit log tells a maintainer what was typed. This skill converts one into the other without inventing anything: every line in the notes must trace to a commit or a changelog bullet the user supplied.

## Hard rules

1. Never add a change that is not in the input. If the log looks incomplete (a gap since the last tag, commits squashed away), say so and ask.
2. Never guess the type of an unprefixed commit. It goes to "Needs a decision" and the user sorts it.
3. Never tag, push, publish or edit a changelog file in place. Output is a draft the user copies.
4. Where the visible effect of a change is unknown, ask one question per change. Do not write a plausible effect.

## Inputs

The log text (`git log` full format, or `git log --oneline --no-merges`), or a PR list, or a CHANGELOG.md draft; plus the previous released version. If the previous version is missing, ask for it. A useful capture command to give the user: `git log <last-tag>..HEAD --no-merges --format=fuller` (the user runs it, not you).

## Workflow

```
- [ ] 1 Save the input to a file and note the current version
- [ ] 2 Run the script
- [ ] 3 Resolve the verdict (ok / needs_review / ask_user)
- [ ] 4 Fix each warning by its rule
- [ ] 5 Rewrite for the audience
- [ ] 6 Re-run on the corrected input and check placeholders are zero
- [ ] 7 Report
```

1. **Save and run.** Put the pasted text in a file (never paraphrase it first), then:

```bash
python scripts/release_notes.py <input-file> --current-version 1.4.2
python scripts/release_notes.py CHANGELOG.md --current-version 1.4.2 --section Unreleased
```

   Add `--audience developers` for notes that also list documentation and internal work. Default is `users`. `--markdown-out notes.md` saves the skeleton; it refuses to write over the input, with or without `--force`.
2. **Read the JSON.** Keys: `proposed_version`, `bump`, `bump_standard`, `bump_reason`, `verdict`, `counts`, `sections{}` (non-breaking entries by section), `breaking[]`, `unsorted[]`, `dropped[]`, `warnings[]` (each with `code`, `severity`, `message`, `refs`), `skeleton`. Exit code 0 is verdict `ok`, 1 is findings, 2 is bad input (the JSON then has an `error` key).
3. **Verdict.** `ask_user`: more than 30 percent of entries have no recognised type. Stop, show the share, and ask whether to sort them together or have the user re-run on a structured log. Do not publish a guess. `needs_review`: work through the warnings. `ok`: go to step 5.
4. **Warnings, by code.**

| Code | What to do |
|---|---|
| `breaking_without_migration_text` | A `!` without a `BREAKING CHANGE:` footer. Ask the user for who is affected and what to do. |
| `possible_unmarked_breaking` | Wording like remove, rename, drop, "no longer", a raised minimum version. Ask whether users must change something. If yes, the entry is breaking and the bump becomes major. |
| `removed_not_marked_breaking` | A CHANGELOG "Removed" entry with no BREAKING marker. Same question. |
| `missing_scope` | Scope is the habit in this log but absent here. Cosmetic; list it, do not invent a scope. |
| `no_leading_verb`, `subject_too_long` | Quality notes for the author. Fix wording only in the notes, never in the history. |
| `internal_wording` | The entry names an implementation. Rewrite per step 5 or ask. |
| `duplicate_subject` | Cherry-picks or repeats. The script kept the first; confirm it is the same change. |
| `revert_pair_dropped` | Change and revert both in this release: left out on purpose. |
| `revert_target_outside` | The revert undoes something already released. Write what users see again; if it removes a released feature it is breaking. |
| `revert_chain` | A revert of a revert. Ask which behaviour ships. |
| `security_disclosure` | A CVE appears. Confirm the fix is released and disclosure timing before it goes in the notes. |
| `zero_major` | Version is 0.x. See the bump table. |
| `prerelease_current`, `input_note` | Decision for the user (final version vs another candidate; check encoding). |

5. **Rewrite for the audience.** The skeleton carries the commit wording. Replace every `[REWRITE: ...]`, `[SORT]` and `[FILL]` marker. Rules and examples: [references/rewrite-and-exclusions.md](references/rewrite-and-exclusions.md) (read the audience table and the never-include list before the first rewrite). Keep the scope as a bold prefix only when the audience knows the component names.
6. **Re-run.** After the user answers breaking-change questions, correct the input (mark breaking, add the footer, sort the unsorted) and run again. The skeleton still contains markers for what only a person can supply (`counts.placeholders_in_skeleton`); the text you deliver must contain none of `[FILL]`, `[SORT]`, `[REWRITE`. Do not edit the script to silence a warning.
7. **Report** in this shape:

```
Version: <current> -> <proposed> (<bump>; <bump_reason>)
Verdict: <ok / needs_review / ask_user> and what was resolved
Breaking: <count>, each with who is affected and what to do
Left out on purpose: <reverted pairs, duplicates, internal work, merges>
Asked the user: <open questions, or none>
Not checked: <e.g. truth of the commit messages; whether the log is complete>
```

   Deliver the final notes first, then the report.

## Type to section

| Commit type | Section | Bump | In user notes |
|---|---|---|---|
| `feat` | Added | minor | yes |
| `fix` | Fixed | patch | yes |
| `perf` | Performance | patch | yes, only if the effect is visible |
| `docs` | Documentation | none | developers only |
| `chore`, `refactor`, `test`, `build`, `ci`, `style` | Internal | none | developers only |
| `revert` | Reverted (or dropped with its target) | patch | yes |
| no recognised type | Needs a decision | none | never guessed |
| CHANGELOG `Changed` | Changed | minor, confirm breaking | yes |
| CHANGELOG `Deprecated` | Deprecated | minor | yes |
| CHANGELOG `Removed` | Removed | confirm breaking | yes |
| CHANGELOG `Security` | Security | patch | yes, see the CVE rule |

## Breaking-change contract

An entry is breaking when the subject has `!` after the type or scope, a footer line starts with `BREAKING CHANGE:` (capitals, colon), or a CHANGELOG bullet starts with `BREAKING`. A breaking entry is publishable only with all three: what changed, who is affected (which users, which versions or configurations), what to do (the migration step, or "nothing, no workaround"). The script provides the first and any footer text; `Who is affected` and `What to do` stay `[FILL]` until the user supplies them. Never write them from the diff.

## Version bump

Highest rule wins: breaking is major, `feat` and `Deprecated` are minor, `fix` and `perf` are patch, only docs or internal work is no release (the script returns `proposed_version: null`). Version 0.x: the script proposes a minor bump for a breaking change and reports the standard answer in `bump_standard`; tell the user moving to 1.0.0 is their decision. A pre-release current version (1.2.0-rc.1) is flagged, not resolved. Background and sources: [references/versioning-rules.md](references/versioning-rules.md).

## Script

`scripts/release_notes.py`: run it, do not edit it. Reads only the input file. Writes only `--markdown-out` when given, never over the input. Accepts UTF-8, UTF-16 (Windows redirects) and falls back to cp1252 with a warning. Merge commits are skipped and counted, except a GitHub style "Merge pull request" whose body line is the PR title, which is used as the entry. Fixup, squash and WIP subjects are dropped and listed under `dropped`.

## Limits

- The type, breaking and verb checks read text. A commit that says `fix:` but changes an API is not caught; `possible_unmarked_breaking` is a keyword list, not an analysis of the code.
- The verb check uses a fixed list of about 180 verbs and will flag some good subjects. Treat it as a prompt.
- The internal-wording list is English and short. It will miss internal wording not on it.
- Duplicates are matched on scope plus normalised subject; the same change with different wording is not found.
- The 30 percent unstructured limit and the 72-character subject limit are working values, not measured optima.
- Squashed PRs hide the individual changes; the notes can only be as detailed as the PR titles.
- The script cannot check that the log covers everything since the last release.
- No Python: apply the tables above by hand, group by type, and mark every unprefixed commit as undecided.
