---
name: code-risky-pattern-scan
description: Scans a source-code folder read-only for nine risky code patterns (eval or exec, shell=True, string-built SQL, hard-coded keys or passwords, disabled TLS verification, pickle loads, weak hashes) and ranks each hit by file and line with a masked snippet. Use when a reviewer needs a first pass over a code folder before a deeper review, or when asked to scan code for vulnerabilities. Do not use for a security audit, a vulnerability assessment, dependency or CVE checks, live systems, or code that is not in local text files.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Code risky-pattern scan

This skill runs `scripts/risky_scan.py` over one folder and turns its JSON output into a ranked findings report. It is a pattern grep with a fixed list, not an assessment. Every finding is a line that matched a regular expression; a human must decide whether the line is reachable, exploitable, or a false positive.

## Workflow

1. **Confirm the folder.** Required input: the path of one folder that holds the code to scan. Output: the path as the user gave it. Stop if the path does not exist or is a file (see Refuse / stop when).
2. **Run the script once.** Use the exact command in the Script contract section. Output: the raw JSON object and the exit code. Do not edit the script or its patterns for this run.
3. **Branch on the exit code.** Exit 2 means the input was rejected; report the one-line error and stop. Exit 0 or 1 continues to step 4.
4. **Record coverage.** Copy `files_examined`, the three `files_skipped` counts, `truncated`, and `finding_count` into the Scan summary table. Output: the filled summary table, with a Status value of `complete` or `partial` decided by the Status rule under the threshold table.
5. **Build the findings table.** Keep the script's order and its `rank` numbers. Do not re-sort, merge, or drop rows. Mask any snippet you see again; never reconstruct a secret. Output: one row per finding in the Findings table.
6. **Write the next steps.** List the `high` findings first, then `medium`, then `low`. For each, name the file and line for manual review. Output: the Next steps list, one bullet per finding of severity `high`, and one bullet per group of lower findings.
7. **Add the disclaimer and open questions.** Copy the `disclaimer` text from the JSON exactly. List every refused or unanswerable clause under Open questions. Output: the Disclaimer and Open questions sections.

## Pattern and threshold table

| Pattern ID | Severity (working value) | What it matches |
|---|---|---|
| EVAL_EXEC | high | a call to `eval(` or `exec(` not preceded by a word character or a dot |
| SHELL_TRUE | high | `shell=True` with optional spaces around `=` |
| SQL_STRING_BUILD | high | a quoted SQL keyword (select, insert, update, delete) followed by `+`, `%`, or `.format(`, or an f-string starting with one |
| AWS_ACCESS_KEY | high | the shape `AKIA` followed by 16 uppercase letters or digits |
| SECRET_ASSIGNMENT | high | password, passwd, secret, api key, access or auth token, or client secret assigned a quoted value of 8 or more characters that does not start with `<`, `$`, or `{` |
| PRIVATE_KEY_BLOCK | high | a PEM header for an RSA, EC, DSA, OpenSSH, or encrypted private key |
| TLS_VERIFY_OFF | high | `verify=False`, `CERT_NONE`, unverified SSL context, `rejectUnauthorized: false`, or `NODE_TLS_REJECT_UNAUTHORIZED` set to 0 |
| PICKLE_LOAD | medium | `pickle`, `cPickle`, or `dill` `load` or `loads` call |
| WEAK_HASH | low | `hashlib` md5 or sha1 call, or `createHash` with md5 or sha1 |

Severity values are working values chosen by the author; they are not a published standard.

| Limit | Working value | Effect when reached |
|---|---|---|
| Input file size | 2 MB (2097152 bytes) | file counted in `too_large`, not read |
| Files per run | 5000 candidate files | `truncated` is true and later files are not read |
| Characters per line matched | 4000 | longer lines are cut before matching |
| Snippet length | 160 characters | longer snippets are cut |
| Masking | first 2 characters kept, up to 12 asterisks after; values of 4 or fewer characters are fully starred | secret values never appear in full |
| Skipped directories | `.git`, `node_modules`, `__pycache__`, `.venv`, `venv`, `dist`, `build` | not walked |
| Scanned extensions | 25 text extensions listed in `TEXT_EXTS`, plus a file named `.env` | other files are ignored |

Status rule: `complete` when `truncated` is false, all three `files_skipped` counts are 0, and `files_examined` is 1 or more. Otherwise `partial`. A run with `files_examined` of 0 is `partial` even with exit 0, because nothing was checked.

## Output contract

The final report has these sections, in this order, with these headings.

**Scan summary** (table, columns: Field | Value)
- Files examined
- Files skipped: too large | not UTF-8 | unreadable (three values in one cell, separated by slashes)
- Scan truncated (yes or no)
- Findings (the `finding_count` value)
- Status (`complete` or `partial`)

**Findings** (table, columns: Rank | Severity | Pattern ID | File | Line | Snippet)
One row per entry in the script's `findings` array, in script order. Use the masked snippet exactly as printed. If there are no findings, write one row reading "No findings" with dashes in the other cells.

**Next steps** (bulleted list): one bullet per `high` finding, citing file and line; one bullet for all `medium` findings together; one bullet for all `low` findings together.

**Disclaimer** (one paragraph): the exact `disclaimer` value from the JSON, followed by the sentence "Clean output does not mean the code is secure."

**Open questions** (bulleted list, or "None"). Required when any clause was refused or any file was skipped.

## Script contract

Command (the placeholder is the user's folder, never a fixture):

```
python -I scripts/risky_scan.py <code-folder>
```

- Arguments: exactly one positional argument, a path to an existing folder. Anything else is a usage error.
- Output on stdout: one JSON object with the keys `tool`, `tool_version`, `disclaimer`, `limits`, `files_examined`, `files_skipped` (keys `too_large`, `not_utf8`, `unreadable`), `truncated`, `finding_count`, and `findings`. Each finding has `rank`, `severity`, `pattern_id`, `file` (relative, forward slashes), `line`, and `snippet`.
- Output files: none. The script never writes.
- Exit codes: 0 means the scan ran and found nothing; 1 means the scan ran and found one or more findings; 2 means a usage or input error, with a one-line JSON object `{"error": "..."}` on stderr.

## Refuse / stop when

- The path is missing, is a file, or is not given. Stop with exit 2 text and ask for the folder path.
- The path is a URL, a repository address, or a remote location. Stop: the script does not fetch anything. Ask the user to clone the code locally first.
- The request asks you to print full secret values, or to recover a masked value. Refuse that clause only; keep the scan and mark the status `partial`, listing the clause under Open questions.
- The request asks for a verdict that the code is secure, an audit sign-off, or a compliance statement. Refuse that clause only; the scan report stays, with the Disclaimer in place, and the clause goes under Open questions.
- The request asks you to fix findings automatically or edit the scanned code. Out of scope. Report the findings and the file and line for each, and stop there.
- The folder holds no scanned extensions (`files_examined` is 0). Do not call the folder clean. Report the zero count and stop.

## Files shipped with this skill

- `LICENSE.txt` (Apache-2.0 text)
- `scripts/risky_scan.py` (the scanner, stdlib only)
- `fixtures/make_sample.py` (smoke helper: writes a new code folder from the text sources, stdlib only)
- `fixtures/sample-source/app/runner.py.txt` (fixture: `shell=True` and `eval`)
- `fixtures/sample-source/db/users.py.txt` (fixture: string-built SQL)
- `fixtures/sample-source/config/settings.py.txt` (fixture: fake AWS-shaped key)
- `fixtures/sample-source/net/client.py.txt` (fixture: `verify=False`)

The smoke run uses the helper to write a four-file folder outside the skill, then scans it:

```
python -I fixtures/make_sample.py <new-folder>
python -I scripts/risky_scan.py <new-folder>
```

The fixtures exist for a smoke run only. Never point the workflow command at the fixture folders for a real user.
