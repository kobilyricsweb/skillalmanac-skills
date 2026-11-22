---
name: env-file-exposure-check
description: Checks a project folder for committed environment files and secret-shaped values, reporting file, line and a masked value without printing full secrets. Use when auditing a repository before a push or release, when a .env, .pem, id_rsa or credentials file may be tracked, or when asking whether the folder's .gitignore covers its secret files. Do not use for scanning git history, live cloud accounts, dependency vulnerabilities or code logic bugs.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Environment file exposure check

Run `scripts/env_exposure.py` on one local folder, then turn its JSON into a status, a findings table and a remediation list. The script never prints a full secret. Each match shows a line number. A token-shaped match (AWS key ID, GitHub token) shows its first 4 characters followed by `***`. A key=value match shows only the value's length, for example `*** (20 chars)`, so no part of a password or key is printed.

## Workflow

1. **Confirm the target.** Required output: the absolute path of the folder and whether a `.git` folder exists at its root. If the path is not a directory, stop (see the refusal list).
2. **Run the scanner once** with the command in the Command section. Required output: the exit code and the full JSON object. Do not re-run with other flags to "see more".
3. **Classify each finding** with the threshold table. Required output: one class per finding.
4. **Set the status** with the rule below. Required output: one word.
5. **Write the report** in the output contract. Required output: the four headings, in order.

## Threshold table

| Signal in the JSON | Rule | Class | Action |
|---|---|---|---|
| `sensitive_filename` only, `ignored_by_gitignore` true | Name matches, no content match | Note | None; the file is kept out of git |
| `sensitive_filename` only, `ignored_by_gitignore` false | Name matches, not ignored | Exposure | Add a rule to `.gitignore`, untrack the file |
| `aws_access_key_id` | `AKIA` followed by 16 uppercase letters or digits | Exposure | Rotate the key in the provider console |
| `private_key_block` | A `-----BEGIN ... PRIVATE KEY-----` line | Exposure | Replace the key pair |
| `github_token` | `ghp_` followed by 20 or more letters or digits | Exposure | Revoke the token |
| `key_value_secret` | Keyword such as secret, token, password or api_key, then a value of 16 or more characters (working value) | Review | May be a placeholder; confirm with the owner |
| `files_skipped` above 0 | File over 2 MB, contains a NUL byte, or is not valid UTF-8 | Gap | Check that file by hand |
| `truncated` true | 5000 files listed or depth 12 reached | Gap | Re-run on each subfolder |

A file that is not ignored and was committed to a shared remote must be treated as leaked, even after it is deleted. Say so in the remediation list.

## Status rule

- `EXPOSED`: `exposure_count` is 1 or more.
- `PARTIAL`: `exposure_count` is 0 and (`truncated` is true or `files_skipped` is 1 or more).
- `CLEAN`: `exposure_count` is 0, `truncated` is false and `files_skipped` is 0.

## Output contract

Use exactly these headings, in this order.

```
## Status
EXPOSED | PARTIAL | CLEAN. exposures: N, files flagged: M, files skipped: K

## Findings
| File | Ignored by .gitignore | Reasons | Line | Masked value | Class |

## Remediation
1. One numbered item per exposure, using the Action column.

## Gaps
- One bullet per skipped or truncated item, or the word none.
```

One table row per match. A file with a sensitive name and no content match gets one row with `-` in the Line and Masked columns.

## Command

```
python -I scripts/env_exposure.py DIR
```

Replace `DIR` with the folder path. Run from the skill folder, or give the full path to the script.

## Script contract (scripts/env_exposure.py)

- **Arguments:** exactly one positional argument, `DIR`, an existing directory.
- **Reads:** files under `DIR` and the root `.gitignore` only. Never writes. Symbolic links are not followed or read. The folders `.git` and `node_modules` are skipped.
- **Caps:** 5000 files, depth 12, 2 MB per file, 20 matches per file in the output.
- **Stdout JSON keys:** `tool`, `root`, `gitignore_present`, `files_visited`, `files_content_scanned`, `files_skipped`, `truncated`, `exposure_count`, `findings`. Each finding has `file`, `ignored_by_gitignore`, `reasons`, `matches`. Each match has `line`, `pattern`, `masked`.
- **Exit 0:** `exposure_count` is 0.
- **Exit 1:** `exposure_count` is 1 or more.
- **Exit 2:** usage error or `DIR` is not a directory. Stderr holds one line: `{"error": "..."}`. Stdout is empty.

Gitignore rules as implemented: a pattern with no slash matches any path component; a pattern with a slash is anchored at the root; trailing slashes are dropped; a leading `!` re-includes a path only when a later rule matches it. Git's rule that an excluded parent directory cannot be re-included is not modelled. Only the root `.gitignore` is read.

## Refuse / stop when

- The user asks for the full value of a matched secret, or for the scanner to print one. Give the masked output only and say the value must be read in the file by its owner.
- `DIR` is a drive root or a user's home folder. Ask for a project folder, because the 5000-file cap would make the result partial.
- The user asks to scan a git remote, a URL or a live account. This skill scans local folders only.
- The user asks you to delete files, rewrite git history or edit `.gitignore`. Report the findings only; those changes need the user's explicit approval.
- Exit code 2. Report the error line and stop. Do not guess a different path.

## Files in this skill

- `scripts/env_exposure.py`: the scanner described above.
- `fixtures/build_fixture.py`: builds a three-file smoke folder in the system temp directory. The fake key is assembled at run time and is never stored in the package.
- `LICENSE.txt`: Apache-2.0 text.
