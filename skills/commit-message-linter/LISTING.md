# Commit Message Linter

## One line

Checks a text file of commit messages for Conventional Commits layout, subject length, subject punctuation, imperative wording, blank line before body, body line length and breaking-change footers, and reports each error as JSON.

## What it does

The skill runs one standard-library Python script, `scripts/lint_commits.py`, on a text file that the user saves from their own history. Messages in that file are separated by a line containing only three hyphens. For each message the script checks the subject against a `type(scope)!: description` pattern, checks the type against an allowed list, applies a 72-character subject limit and a 72-character body line limit, flags trailing periods, flags first words that end in `ed` or `ing`, requires a blank second line before any body, and requires a BREAKING CHANGE footer when the exclamation mark is present. Each finding carries a code (E001 to E009), a rule name and a short detail. The script writes a JSON report to standard output and exits 0 for a clean run, 1 when errors exist and 2 for bad input.

The script does not run git, does not write files and does not change the input. The agent that uses the skill turns the JSON into a short report with a summary table and a table of failing messages.

## When to use

- A release is near and someone needs a quick pass or fail list for commit titles.
- A pull request reviewer wants the commit list checked before merge.
- A changelog step needs messages with predictable headers.

## When not to use

- The task is a code review of the diff itself.
- The messages must be rewritten in place. The skill suggests subjects but never edits a file.
- The history must be read from a repository. The user has to export the messages first.

## Requirements

Python 3.9 or newer. No third-party packages, no network access and no git installation are needed for the script itself. The user must provide the input file.

## Example

Output of the smoke run on `fixtures/sample_commits.txt`, which has three passing and three failing messages. Exit code 1.

```json
{
  "tool": "commit-message-linter",
  "version": "0.1.0",
  "input": "sample_commits.txt",
  "types": [
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert"
  ],
  "limits": {
    "max_subject": 72,
    "max_body": 72
  },
  "messages_checked": 6,
  "messages_with_errors": 3,
  "error_count": 7,
  "results": [
    {
      "index": 1,
      "subject": "feat(parser): add trailing comma support",
      "ok": true,
      "errors": []
    },
    {
      "index": 2,
      "subject": "fix(api)!: drop the v1 endpoints",
      "ok": true,
      "errors": []
    },
    {
      "index": 3,
      "subject": "docs: update the install steps",
      "ok": true,
      "errors": []
    },
    {
      "index": 4,
      "subject": "Added a login page.",
      "ok": false,
      "errors": [
        {
          "code": "E001",
          "rule": "header-format",
          "detail": "subject must look like type(scope)!: description"
        },
        {
          "code": "E004",
          "rule": "subject-trailing-period",
          "detail": "subject ends with a period"
        }
      ]
    },
    {
      "index": 5,
      "subject": "feat!: remove the legacy config flag",
      "ok": false,
      "errors": [
        {
          "code": "E006",
          "rule": "missing-blank-line-before-body",
          "detail": "line 2 must be blank before the body"
        },
        {
          "code": "E008",
          "rule": "breaking-change-footer-missing",
          "detail": "'!' is set but no BREAKING CHANGE footer was found"
        }
      ]
    },
    {
      "index": 6,
      "subject": "wibble(core): fixed the crash that happens when the cache is empty during startup",
      "ok": false,
      "errors": [
        {
          "code": "E002",
          "rule": "unknown-type",
          "detail": "type 'wibble' is not in the allowed list"
        },
        {
          "code": "E003",
          "rule": "subject-too-long",
          "detail": "subject is 81 characters, limit is 72"
        },
        {
          "code": "E005",
          "rule": "subject-not-imperative",
          "detail": "first word 'fixed' does not look imperative"
        }
      ]
    }
  ]
}
```

## Limits

- The 72-character limits are working values chosen for this skill, not published thresholds.
- The imperative check is a suffix heuristic. Words such as `need`, `feed` and `bring` are flagged, and a reviewer must confirm E005 results by hand.
- The scope pattern is permissive. It does not compare scopes with a project's component list.
- The input is capped at 2 MB, 1000 messages and 4000 characters per line.
- A line of three hyphens inside a message body is read as a separator.
- Only the commit message text is checked. Diffs, authors and dates are outside the script.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
