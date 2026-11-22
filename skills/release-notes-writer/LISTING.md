# Listing page content: release-notes-writer

**One line:** Turns a commit log or CHANGELOG draft into user-facing release notes and a proposed version bump, without inventing changes.

## What it does

The agent saves the user's `git log` text, PR list or CHANGELOG draft, then runs a script that parses conventional-commit lines, groups entries by type and scope, and applies a fixed bump rule (breaking is major, feat is minor, fix and perf are patch). The script reports what it dropped (a change and its revert in the same release, duplicates, fixups, merges) and what needs a human: unprefixed commits, a `!` with no migration text, wording that hides a breaking change, internal wording, a CVE mention. It prints a Markdown skeleton with visible markers (`[FILL]`, `[SORT]`, `[REWRITE]`) where only a person can supply the answer. The skill's procedure then covers the audience rewrite, the breaking-change contract (what changed, who is affected, what to do) and a never-include list.

## Capabilities

- `scripts/release_notes.py`: strict JSON with `proposed_version`, `bump`, `bump_reason`, `verdict`, `sections`, `breaking`, `unsorted`, `dropped`, `warnings`, `skeleton`
- Reads full `git log` output, one-line logs and Keep-a-Changelog drafts; handles UTF-16 files made by Windows redirects
- Optional `--markdown-out` that never overwrites its input
- A verdict `ask_user` when more than 30 percent of entries have no type
- 0.x and pre-release version handling
- A fixed report: version, verdict, breaking entries, what was left out, open questions, what was not checked

## When to use

You have commits or a changelog draft and say: write the release notes, what changed since the last tag, which version next, is this a major or a minor.

## When not to use

Tagging, pushing or publishing the release; writing commit messages; the branch and PR workflow (see `git-worktree-and-pr-flow`); product documentation (see `technical-docs-writer`); looking up some other product's changelog.

How it differs from the nearest skills: `git-worktree-and-pr-flow` runs the branch and PR process; `technical-docs-writer` writes documentation from scratch; this skill only derives notes and the bump from commit text, with parsing rules and a script.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent applies the tables in SKILL.md by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real output of `python scripts/release_notes.py evals/fixtures/log_full.txt --current-version 2.3.1` (exit code 1, verdict `needs_review`), abridged:

```
proposed_version: 3.0.0   bump: major
bump_reason: breaking change marked in 9f2b7c1: Remove the v1 orders endpoint
dropped: the fix(ui) commit and its revert (reverted_in_release); a cherry-picked duplicate
warnings: merge_skipped (info), revert_pair_dropped (info), duplicate_subject (warn)

## 3.0.0 - <release date>

### Breaking changes

- **api:** Remove the v1 orders endpoint (#210)
  - Details: GET /v1/orders is gone. Clients must call /v2/orders.
  - Who is affected: [FILL]
  - What to do: [FILL]

### Added

- **ui:** Add dark mode toggle (#215)

### Fixed

- **db:** Handle null values in the migration step

### Needs a decision

- [SORT] update stuff
```

A one-line log with 4 of 5 entries unprefixed (`evals/fixtures/log_unstructured.txt`, version 0.4.0) returns verdict `ask_user`; no type is guessed and the four commits land under "Needs a decision".

## Limits

- Text checks only: a `fix:` commit that changes an API is not caught; the unmarked-breaking check is a keyword list.
- The verb check and internal-wording list are short, English, and will give false alarms and misses.
- Duplicates are found by scope plus normalised subject only.
- The 30 percent and 72-character limits are working values.
- It cannot tell whether the log covers everything since the last release.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL and 0 WARN; 17 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a `git log` and a version; the agent saves it and runs the script.
2. Verdict `needs_review`: the agent walks through the warnings (a revert pair dropped, a duplicate, one breaking change with no "who is affected").
3. The agent asks the user the two breaking-change questions and the one unsorted commit.
4. Final notes with no markers left, then the report listing what was left out and what was not checked.

## FAQ seeds

- Does it tag or push anything? No. It prints a draft; nothing is tagged, pushed or edited in place.
- Does it need network access? No.
- Will it make up what a change means? The rules forbid it: unknown effects and migration steps become questions.
- Does it work without conventional commits? It reports `ask_user` when more than 30 percent of entries have no type and does not guess.
- Can it read my CHANGELOG.md? Yes, the Unreleased section by default, or `--section 1.2.0`.
- What about 0.x versions? A breaking change proposes a minor bump and `bump_standard` shows the plain rule; 1.0.0 is your decision.
- How is it different from asking for "release notes" in a plain prompt? It adds parsing, a fixed bump rule, a breaking-change contract and checks. No comparison run has been done yet.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet; accountable editor: Global Media Holdings.
