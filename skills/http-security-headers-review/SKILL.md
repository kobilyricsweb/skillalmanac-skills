---
name: http-security-headers-review
description: Checks a pasted HTTP response header block for missing or weak security headers, covering Strict-Transport-Security, Content-Security-Policy, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, X-Frame-Options and Set-Cookie flags. Use when a team needs a header checklist for a web response, wants to know which security headers matter, or asks why a CSP or cookie setting was flagged. Do not use for penetration testing, live scanning of a site, or reviewing application code.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# HTTP security headers review

Use this skill to turn a pasted set of response headers into a severity-ranked checklist. The script `scripts/header_review.py` does the parsing and the checks. You do the triage and the write-up. The script never contacts a server. If the user only has a URL, stop and ask for the header block (see Refuse / stop when).

The output is a header checklist. It is not a penetration test and does not show that a site is exploitable.

## Files in this skill

- `SKILL.md` (this file): workflow, thresholds, output contract.
- `scripts/header_review.py`: the checker. Stdlib only, reads one text file, prints JSON.
- `fixtures/weak_headers.txt`: a small header block with weak CSP and cookie settings, used for the smoke run.
- `LICENSE.txt`: Apache-2.0 license text.

## Workflow

1. **Get the header block as text.** Ask the user to copy the response headers from their browser developer tools network panel, or from their own server configuration, and paste them into a plain text file. Required output: the file path and the number of header lines. Keep the status line if present; the script skips it. Warning: before pasting, redact every cookie value (the text after `=` in each `Set-Cookie` line) and keep only the cookie name and its attributes, because pasted cookies can be live session secrets.
2. **Check the input before running.** Required output: a yes or no for each row. The file must be UTF-8 text, at most 2 MB, at most 2000 lines, with no NUL bytes. It must contain at least one `Name: value` line. If any row fails, stop and report which row failed.
3. **Run the script.** Command line, from the skill folder, with `<file>` set to the user's header text file (the fixture is only for the smoke run, never for a user's request):
   `python -I scripts/header_review.py <file>`
   Required output: the exit code (0, 1 or 2) and the JSON object. Do not edit the JSON before reading it.
4. **Map each finding to a severity row.** Use the threshold table below. Required output: a table with one row per finding. Do not change the severity the script gives. If you think a finding is wrong, say so in a note; do not rewrite it.
5. **Explain the cookie findings without values.** Cookie values are never printed. Report cookie names only. Required output: one line per cookie name with the flags that are missing.
6. **Write the report** using the output contract below. Required output: all headings present, even when a section is empty ("none").
7. **State the scope.** Required output: the sentence "This is a header checklist, not a penetration test." and the list of headers the script does not check (see the output contract).

## Severity and threshold table

| Severity | Meaning in this skill | IDs the script emits |
|---|---|---|
| high | Protection is absent or disabled for a script or cookie context | HSTS-001, CSP-001, CSP-002, CSP-004 (no nonce or hash), CSP-005, CSP-006, COOKIE-001, COOKIE-004 |
| medium | Protection exists but is weak or incomplete | HSTS-002, CSP-003, CSP-007, CSP-008, CSP-012, XCTO-001, XCTO-002, REF-002, XFO-001, XFO-003, COOKIE-002, COOKIE-003 |
| low | Hardening gap with limited direct effect | HSTS-003, HSTS-004, CSP-009, CSP-011, REF-001, REF-003, PP-001, COOKIE-005 |
| info | Recorded for context, does not change the exit code | CSP-004 (with nonce or hash), XFO-002 |

Working values (not published standards):

| Check | Threshold used | Source of value |
|---|---|---|
| HSTS max-age | at least 15552000 seconds (180 days) | working value |
| HSTS includeSubDomains | must be present | working value |
| X-Content-Type-Options | exactly `nosniff` | working value |
| X-Frame-Options accepted values | DENY or SAMEORIGIN | working value |
| Referrer-Policy weak values | unsafe-url, no-referrer-when-downgrade | working value |
| SameSite accepted values | strict, lax, none | working value |

Exit code rule: exit 1 when at least one high, medium or low finding exists. Info-only output exits 0.

## Script contract

- Arguments: exactly one positional argument, the path to the header text file.
- Reads: one file. Writes: nothing. Network: none. Subprocesses: none.
- Output on success: one JSON object on stdout with keys `tool`, `version`, `input_lines`, `headers_parsed`, `lines_skipped`, `counts` (keys high, medium, low, info), `findings` (list of objects with keys `id`, `severity`, `header`, `message`), and `scope`.
- Output on error: one line of JSON on stdout, `{"error": "<reason>"}`, with exit 2.
- Exit codes: 0 no high, medium or low findings; 1 at least one high, medium or low finding; 2 usage or input error.
- Exact command line: `python -I scripts/header_review.py <file>`, where the file path is the only argument.

## Output contract for the report

Use these headings in this order:

1. `## Summary`: one line with the counts, for example `high 4, medium 6, low 4, info 0`, and the exit code.
2. `## Findings`: a table with the columns `ID | Severity | Header | Finding | Remediation`. Sort rows as the script does (high first).
3. `## Cookies`: one row per cookie name with the columns `Name | Missing flags`. Write `none` when the response sets no cookies.
4. `## Not checked`: a bullet list containing at least these items: Cross-Origin-Opener-Policy, Cross-Origin-Resource-Policy, Cache-Control on sensitive pages, and any server-side behavior that a header block cannot show.
5. `## Scope`: the sentence "This is a header checklist, not a penetration test."

## Refuse / stop when

- The user gives a URL or hostname and asks you to fetch or scan it. Stop and ask for the pasted header block.
- The input is a page body, a request header block, or an unrelated text file. Stop and report that the script found no response headers (headers_parsed is 0).
- The input is over 2 MB, has more than 2000 lines, is not UTF-8, or contains NUL bytes. Stop and report the error line from the script.
- The user asks for exploit steps, payloads, or a way to take advantage of a finding. Decline and offer the remediation wording for the finding instead.
- The user asks you to paste cookie values into the report. Decline; names only.
- The user asks whether a site is secure overall. Say the checklist covers headers only and give the findings.

## Remediation wording

For each finding, fill the Remediation column with one short sentence, for example: "Replace unsafe-inline with a nonce or hash in script-src." Keep it to one sentence and name the header the script reported.
