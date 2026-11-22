---
name: pr-size-risk-scorer
description: Scores a pull request's size and risk from git diff --numstat text by totaling changed lines, assigning a size band, flagging lockfiles, migrations, CI config, generated files and untested source, and suggesting a directory split. Use when a reviewer gets a large or mixed pull request and needs a size band and risk flags before reading the diff. Do not use for judging code correctness, running git, or fetching pull requests.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# PR size and risk scorer

This skill turns the output of `git diff --numstat` into a size band, a set of risk flags and a split suggestion. The script does the counting. You do the reading and the reporting. The thresholds below are working values chosen for this skill. They are not published standards.

## Inputs

- A text file holding `git diff --numstat` output, one line per file: added count, deleted count and path, separated by tab characters. Binary files show `-` in both count fields.
- The author or reviewer runs git and saves the output. This skill never runs git and never fetches a pull request.

## Workflow

1. Confirm the input. Required output: the input path, or the word stdin, and the number of non-blank lines you expect. Stop if the file does not exist.
2. Check that the input is UTF-8 and at most 2 MB. Required output: none. A failure ends the run with exit code 2.
3. Run the script with the command in the script contract below. Required output: the JSON object on stdout and the exit code.
4. Read `totals` and `band`. Required output: the band, then files, added, deleted, changed and binary files.
5. Read `classes` and `test_to_source_ratio`. Required output: the ratio to two decimals, or "n/a" when the script returns null.
6. Read `flags` and `flagged_files`. Required output: one row per flag that is true, with its files.
7. Read `split`. Required output: the groups in the order the script gives them, or the reason no split is suggested.
8. Write the summary using the output contract. Do not add a verdict on code quality.

## Size band (changed = added + deleted)

| Band | Changed lines | Reviewer action |
|---|---|---|
| XS | 0 to 50 | Review in one pass |
| S | 51 to 200 | Review in one pass |
| M | 201 to 500 | Review in one pass and check every flag |
| L | 501 to 1000 | Suggest a split; finding `size_band_L` |
| XL | 1001 and above | Ask for a split before review; finding `size_band_XL` |

Upper limits are inclusive: 500 changed lines is M, and 501 is L.

## Classification (first match wins)

| Order | Class | Rule |
|---|---|---|
| 1 | lockfile | basename is in the lockfile list below |
| 2 | generated | a directory named `generated` or `__generated__`, or a name ending in `.min.js`, `.min.css`, `.pb.go`, `_pb2.py`, `.generated.ts` or `.generated.js` |
| 3 | other | migration or CI file (these stay flagged, see below) |
| 4 | test | a directory named `test`, `tests`, `__tests__`, `spec` or `specs`, or a name like `test_*.py`, `*_test.py`, `*_test.go`, `*.test.js`, `*.spec.ts`, `*Test.java` |
| 5 | source | extension is one of py, js, jsx, ts, tsx, go, rb, java, kt, cs, rs, php, swift, c, h, cc, cpp, hpp, scala |
| 6 | other | everything else |

Lockfile list: package-lock.json, npm-shrinkwrap.json, yarn.lock, pnpm-lock.yaml, poetry.lock, Pipfile.lock, uv.lock, Cargo.lock, Gemfile.lock, composer.lock, go.sum, mix.lock, pubspec.lock.

## Risk flags (working values)

| Flag | Rule | Files listed under |
|---|---|---|
| `lockfile_changed` | any file in the lockfile list | `lockfile` |
| `migration_changed` | any directory named `migrations` or `migrate` | `migration` |
| `ci_config_changed` | basename is .gitlab-ci.yml, .travis.yml, .drone.yml, azure-pipelines.yml, bitbucket-pipelines.yml or Jenkinsfile, or path starts with .github/workflows/ or .circleci/ | `ci_config` |
| `generated_files_changed` | any file that matches the generated rule in the classification table | `generated` |
| `source_without_tests` | source changed lines are at least 100 and test changed lines are 0 | none (report "n/a") |

Each flag can be true at the same time as the others. A flagged file also keeps its class in `classes`.

## Split suggestion

- Groups are the first path segment. Files at the repository root form the group `(root)`.
- A split is suggested only when the band is L or XL and there are at least 2 groups.
- Groups are sorted by changed lines, highest first, then by name. Suggest one pull request per group, starting with the largest.
- For bands XS, S and M, report "no split suggested" and the band as the reason.

## Output contract

Write the summary with these headings, in this order:

```
## Size
Band: BAND. Files: N. Added: N. Deleted: N. Changed: N. Binary files: N.

## Classes
| Class | Files | Changed |
|---|---|---|
(rows for lockfile, generated, test, source, other)

Test to source ratio: VALUE or n/a

## Flags
| Flag | Value | Files |
|---|---|---|
(one row per flag, in the order of the flags table above)

## Split
Suggested: yes or no. Reason: REASON. Groups: DIR (N lines), ...

## Findings
FINDING_NAMES or none
Exit code: 0, 1 or 2
```

## Script contract

- Path: `scripts/pr_risk.py`
- Command: `python -I scripts/pr_risk.py INPUT`
- Arguments: one positional argument, the path to the numstat text. Pass `-` to read stdin. There are no options and no output-file option. The script writes only to stdout and stderr.
- Stdout on success: one JSON object with the keys `tool`, `totals`, `band`, `band_rule`, `classes`, `test_to_source_ratio`, `flags`, `flagged_files`, `split` and `findings`.
- Stderr on error: one line of JSON with the keys `error` and `line`. `line` is the 1-based numstat line, or null when the error is not tied to a line.
- Exit 0: no findings. Exit 1: findings present (band L or XL, or any flag true). Exit 2: usage or input error, including a missing file, input over 2 MB, invalid UTF-8, empty input, a line that is not three tab-separated fields, or counts that are not digits or a dash.
- The input is plain text. The script parses no JSON, so nesting limits do not apply.
- Renames such as `dir/{old => new}/file` or `old => new` are counted under their new path.

Smoke command, run from the package folder: `python -I scripts/pr_risk.py fixtures/numstat_sample.txt`. Expected result: band L, four flags true, exit 1.

## Refuse or stop when

- The input is missing, empty, over 2 MB, not UTF-8, or has a malformed line. Report the stderr line and stop. Do not estimate counts.
- The user asks you to run git, check out a branch or fetch a pull request. Ask for the saved numstat text instead.
- The numstat text was made with whitespace-ignoring options such as `-w` or `-b`. Those counts miss real changes. Ask for a plain numstat before scoring.
- The user asks whether the code is correct, secure or well designed. This skill measures size and risk flags only. Say so and stop.
- The user asks for an approve or merge decision. The skill gives a band and flags, not a decision.

## Package files

- `SKILL.md` (this file)
- `scripts/pr_risk.py` (the scorer)
- `fixtures/numstat_sample.txt` (the 12-file smoke input)
- `LICENSE.txt` (Apache-2.0)
