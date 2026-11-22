---
name: utm-link-audit
description: Audits a file of campaign links for UTM parameter consistency and reports each problem with its line number. Use when a marketing team has a list of tracked links to check before a launch, or when campaign reports split into duplicate rows because utm_source, utm_medium or utm_campaign differ by case, spaces or separator characters. Do not use for building UTM links, for fetching or checking live pages over the network, or for attribution analysis of analytics data.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# UTM Link Audit

This skill runs a read-only script over a list of campaign URLs and turns its JSON report into a fix list. The script does the checks. You classify the findings, write the fix list, and stop when the input is outside the contract below.

Files in this package: `scripts/utm_audit.py` (the checker), `fixtures/campaign_urls.txt` (8-line smoke input with 4 planted problems), `LICENSE.txt` (Apache-2.0).

## Inputs

- INPUT_FILE: a UTF-8 text file with one URL per line. A UTF-8 byte order mark is accepted.
- Size limits (working values, not industry standards): file 2 MB or less; each line 4096 characters or less.
- Blank lines and lines starting with `#` are skipped and counted in `lines_read` only.
- ALLOWED_MEDIUMS: comma-separated list. Default: `cpc,email,social,referral,display,affiliate,organic`. This default is a team working list. Change it only when the owner supplies the new values.

## Workflow

1. Confirm INPUT_FILE exists and that the report path, if any, differs from it.
   Required output: the input path and the count of non-blank lines you expect to check.
2. Run the script with the command in the Script contract section. Keep the exit code.
   Required output: the exit code (0, 1 or 2) and the `summary` object.
3. If the exit code is 2, stop. Report the one-line JSON error from stderr. Do not guess a fix.
4. For each entry in `findings`, pick the fix from the decision table below.
   Required output: one table row per finding.
5. Build the corrected list only if the owner asked for one. Write it to a new file, never over INPUT_FILE.
   Required output: the new file path and the number of lines changed.

## Decision table: finding codes and fixes

| Code | Trigger in the script | Fix to propose |
|---|---|---|
| BAD_URL | no scheme or no host | Replace the line with a full URL, or delete it. |
| MISSING_PARAM | utm_source, utm_medium or utm_campaign absent | Add the parameter. The detail field names which one. |
| UPPERCASE | a utm_ key or value contains an uppercase letter | Lowercase the key or value. |
| SPACE | a utm value contains a space, `%20` or `+` | Replace the space with a hyphen, then apply the MIXED_SEPARATOR rule to the result. |
| BAD_MEDIUM | utm_medium (lowercased) not in ALLOWED_MEDIUMS | Map to an allowed value, or ask the owner to extend the list. |
| MIXED_SEPARATOR | campaign has both `_` and `-`, or equals an earlier campaign except for the separator character | Use one separator. Keep the spelling that appears first in the file unless the owner says otherwise. |
| DUPLICATE | same scheme, host, path and query pairs after lowercasing and sorting | Remove the later line. The detail field names the first line. |

Checks are applied in this order for each URL: BAD_URL, then DUPLICATE, then key case, then required keys, then value case and spaces, then BAD_MEDIUM, then MIXED_SEPARATOR. A line with a space in a value is reported as SPACE only, not also as UPPERCASE.

## Exit code table

| Exit | Meaning | Action |
|---|---|---|
| 0 | No findings | Report "no findings" with the counts. |
| 1 | One or more findings | Continue at workflow step 4. |
| 2 | Usage or input error | Stop. Report the stderr line. |

## Script contract

- Path: `scripts/utm_audit.py`
- Arguments: `INPUT_FILE` (positional, required); `--output REPORT_FILE` (optional, refused with exit 2 if it resolves to INPUT_FILE); `--allowed-mediums LIST` (optional, default above).
- Read only on the input. No network, no subprocess, no eval.
- Output: JSON on stdout, or in REPORT_FILE when `--output` is given. Keys: `input`, `lines_read`, `urls_checked`, `allowed_mediums`, `summary` (count per code), `findings` (list of objects with `line`, `code`, `detail`, `url`).
- Errors: one JSON line on stderr, such as `{"error": "input file not found"}`, then exit 2. Covered errors: missing file, file over 2 MB, line over 4096 characters, invalid UTF-8, empty allowed list, output path equal to input path.
- Exit codes: 0 no findings, 1 findings, 2 usage or input error.

Command line:

```
python -I scripts/utm_audit.py INPUT_FILE --output REPORT_FILE --allowed-mediums cpc,email,social,referral,display,affiliate,organic
```

Omit `--output` to print the report to stdout. Omit `--allowed-mediums` to use the default list.

## Output contract

Reply with these four sections, in this order.

### Summary
- Input: the path
- Lines read / URLs checked: two integers
- Findings: total count, then one line per code with a non-zero count

### Findings
A table with the columns: `Line | Code | Detail | Fix`. One row per finding, sorted by line number, then by code name.

### Corrected file (only if requested)
- Path of the new file and the number of lines changed.

### Not checked
- Count of skipped blank and comment lines.
- Any BAD_URL lines, repeated here so they are not missed.

## Refuse / stop when

- The request is to check whether a URL is live, to follow redirects, or to fetch a page. This skill has no network access.
- The request is to write over INPUT_FILE. Refuse and offer a new file path instead.
- The script exits with 2. Stop and report the error line. Do not work around the size or line limits.
- The input is not a list of URLs, for example a spreadsheet export with many columns or a JSON document. Ask for a one-URL-per-line file.
- The request is to create new UTM links for a campaign. That is a different task.
- The owner asks to change the medium list but gives no values. Keep the default and ask.
- A fix would change the meaning of a link, such as altering the path or host. Report it and leave the line unchanged.
