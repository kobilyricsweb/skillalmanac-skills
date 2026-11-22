# PR size and risk scorer

## One line

Turns a saved `git diff --numstat` file into a size band, risk flags and a directory split plan, using a standard-library Python script.

## What it does

The skill takes the plain text that `git diff --numstat` prints, one line per changed file with the added count, the deleted count and the path. A bundled script totals the files and changed lines, places the pull request in a size band from XS to XL, and sorts each file into a class such as lockfile, generated, test, source or other. It then sets five flags: a lockfile changed, a migration changed, CI configuration changed, generated files changed, and source changed without any test changes. When the pull request is L or XL and spans more than one top-level directory, the skill proposes a split with one group per directory, largest first. The script never runs git and never reads anything except the file or stdin it is given.

## When to use

Use this skill when a reviewer receives a large or mixed pull request and wants to know, before reading any code, how big it is and which files carry operational risk. It fits pull requests that touch a dependency lockfile alongside application code, or that combine a database migration with feature changes. A saved numstat file gives the same counts every time, so two reviewers can compare notes against the same numbers.

## When not to use

Do not use this skill to judge whether a change is correct, secure or well designed. It counts lines and matches file names; it does not read the diff content. Do not use it on whitespace-ignoring output, because those counts omit real edits. It does not fetch pull requests and does not run git, so the author or reviewer must produce the numstat text first.

## Requirements

Python 3.9 or newer, standard library only. No network access and no extra packages. The input must be UTF-8 text no larger than 2 MB, with one tab-separated record per line.

## Example

Smoke run on `fixtures/numstat_sample.txt`, a 12-file sample with a migration, a lockfile, a CI workflow and a generated file. Command: `python -I scripts/pr_risk.py fixtures/numstat_sample.txt`. Exit code 1.

```json
{
  "tool": "pr_risk",
  "totals": {
    "files": 12,
    "added": 835,
    "deleted": 163,
    "changed": 998,
    "binary_files": 0
  },
  "band": "L",
  "band_rule": "changed = added + deleted; XS <= 50, S <= 200, M <= 500, L <= 1000, XL above 1000 (working values)",
  "classes": {
    "lockfile": {
      "files": 1,
      "changed": 170
    },
    "generated": {
      "files": 1,
      "changed": 40
    },
    "test": {
      "files": 2,
      "changed": 145
    },
    "source": {
      "files": 4,
      "changed": 560
    },
    "other": {
      "files": 4,
      "changed": 83
    }
  },
  "test_to_source_ratio": 0.26,
  "flags": {
    "lockfile_changed": true,
    "migration_changed": true,
    "ci_config_changed": true,
    "generated_files_changed": true,
    "source_without_tests": false
  },
  "flagged_files": {
    "lockfile": [
      "package-lock.json"
    ],
    "migration": [
      "migrations/0042_add_orders_index.sql"
    ],
    "ci_config": [
      ".github/workflows/ci.yml"
    ],
    "generated": [
      "src/api/generated/schema.py"
    ]
  },
  "split": {
    "suggested": true,
    "reason": "band L with 6 top-level directories",
    "groups": [
      {
        "dir": "src",
        "files": 5,
        "changed": 600
      },
      {
        "dir": "(root)",
        "files": 2,
        "changed": 174
      },
      {
        "dir": "tests",
        "files": 2,
        "changed": 145
      },
      {
        "dir": "docs",
        "files": 1,
        "changed": 33
      },
      {
        "dir": "migrations",
        "files": 1,
        "changed": 30
      },
      {
        "dir": ".github",
        "files": 1,
        "changed": 16
      }
    ]
  },
  "findings": [
    "size_band_L",
    "lockfile_changed",
    "migration_changed",
    "ci_config_changed",
    "generated_files_changed"
  ]
}
```

## Limits

The band limits (50, 200, 500, 1000 changed lines) and the 100-line source threshold are working values chosen for this skill. They are not published standards, and a team may prefer different numbers. The lockfile, generated and CI name lists cover common conventions only; a repository with other names will not flag them. Test detection relies on file names and directory names, so a test written in an unusual location counts as source. Renamed files are reported under their new path. The script does not read file contents, so it cannot tell a large generated change from a large hand-written one unless the path says so.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
