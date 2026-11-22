---
name: email-signature-builder
description: Builds a plain HTML email signature and a matching plain-text copy from a JSON file of contact fields, after checking each field and the text color contrast. Use when a user needs an email signature that renders in common email clients with table layout and inline styles, or needs phone, email, website and color values validated before pasting them into a mail client. Do not use for signatures that need images or logos, for sending email, for brand design work, or for editing an existing signature in a mail client.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Email signature builder

Run `scripts/signature.py` on a JSON file of contact fields. It validates the fields, checks the text color against white, and writes two new files: an HTML signature and a plain-text signature. The agent does the intake, reads the exit code, and reports codes and field names. It does not echo the contact values back in chat.

## Inputs

The input is one JSON object. Seven fields are recognized; any other key is an error.

| Field | Required | Rule (working values unless marked spec) |
|---|---|---|
| name | yes | 1 to 80 characters |
| title | no | up to 80 characters |
| company | no | up to 100 characters |
| phone | no | 7 to 15 digits (working value); only digits, spaces, parentheses, dots, hyphens, and an optional leading plus; 7 to 20 characters total |
| email | no | one at-sign, dotted domain, final label of 2+ letters; up to 254 characters (spec: RFC 5321 length limit) |
| website | no | host with a dot, optional http:// or https:// prefix, optional path; up to 200 characters |
| text_color | no | #RRGGBB; default #333333 when absent or empty |

## Workflow

1. Intake. Confirm the path of the user's JSON file (`<input-file>`) and two new output names, `<output-html>` and `<output-txt>`. Required output: one line, "Input: <input-file>; outputs: <output-html>, <output-txt>". If the output names are not given, ask for them. Do not invent them.
2. Pre-check. Read the JSON and confirm it is one object with a non-empty `name`. Required output: the list of keys present, without their values. Stop at the rules in "Refuse / stop when" if a check fails.
3. Run the script with the command in "Script contract". Read the exit code. Required output: the exit code and the one-line JSON from stdout or stderr.
4. Act on the code. Exit 0 goes to step 5. Exit 2 or exit 1 goes to the fix table below. Required output: the code, the field name, and the fix requested from the user.
5. Verify. Open `<output-txt>` and check that line 1 is the name and that a T:, E:, or W: line appears only for fields the user supplied. Open `<output-html>` and check that it contains `max-width:600px` and no `<img` or `<script` tag. Required output: "verified" or the failing check.
6. Report. Required output: the output paths, the contrast ratio from the exit 0 JSON, and the verification result. Do not paste the full HTML into chat unless the user asks.

## Fix table

| Code | Exit | Action |
|---|---|---|
| LOW_CONTRAST | 1 | Ask the user for a darker `text_color`. Do not pick one yourself. Nothing was written. |
| BAD_FIELD | 2 | Ask for the corrected value of the named field. Put it in a new JSON file. Never edit the input file. |
| MISSING_FIELD | 2 | Ask for `name`. |
| UNKNOWN_FIELD | 2 | Ask the user to remove the named key. Do not keep it. |
| OUTPUT_EXISTS | 2 | Ask for new output names. Never delete or replace the existing file. |
| OUTPUT_PATH_INVALID | 2 | Use `.html` for the first output and `.txt` for the second. Use paths different from the input. |
| FILE_MISSING, FILE_TOO_LARGE, BAD_UTF8, BAD_JSON, NOT_OBJECT | 2 | Ask the user to re-export the file as UTF-8 JSON, one object, under 2 MB. |
| BAD_ARGS | 2 | Re-run with exactly three arguments. |
| WRITE_FAILED | 2 | Report the failure. Check the folder exists and is writable. Do not retry more than once. |

Retry limit: three fix rounds in total. After the third failed run, stop and report the last code.

## Output contract

Exit 0, stdout, one line:
`{"status": "ok", "contrast_ratio": <number>, "written": ["<output-html>", "<output-txt>"]}`

Exit 1, stdout, one line:
`{"status": "findings", "findings": [{"code": "LOW_CONTRAST", "field": "text_color", "ratio": <number>, "minimum": 4.5}], "written": []}`

Exit 2, stderr, one line:
`{"status": "error", "code": "<CODE>", "message": "<text>", "field": "<name>"}`. The `field` key is present only when a field is at fault.

The HTML file holds one `role="presentation"` table, `max-width:600px`, inline styles only, no images, no scripts. Links are `mailto:` for email and `https://` for the website; a website given without a scheme gets `https://` added in the link only. The plain-text file has the name, then title and company when present, a blank line, then T:, E:, and W: lines for the fields present. Contrast is the WCAG 2.x ratio against #FFFFFF, rounded to two decimals. The minimum of 4.5 is the WCAG AA value for normal text.

## Refuse / stop when

- `name` is missing or empty. Stop and hand back a numbered list of the questions the user must answer: name, and the two output names.
- The request asks for an image, a logo, a tracking pixel, or raw HTML from the user.
- The request asks to send the signature by email, or to install it into a mail account.
- The request asks to overwrite an existing output file.
- Any field holds a password, a token, an account number, or a government ID. Stop, and ask the user to remove it.
- The contrast check fails and the user asks the tool to choose a color anyway.
- Three fix rounds have run without an exit 0.

## Script contract

Type A. `scripts/signature.py` is Python 3.9+ standard library only. It makes no network calls and runs no subprocesses. It reads the input once, caps it at 2 MB, and never writes to the input path. It writes the two output files with mode "x", so an existing file is never replaced.

Command line:

`python -I "<skill-folder>/scripts/signature.py" "<input-file>" "<output-html>" "<output-txt>"`

Exit codes: 0 means both files were written; 1 means a finding (contrast) and nothing was written; 2 means a usage or input error, and the one-line JSON is on stderr.

## Shipped files

- `scripts/signature.py`: the validator and writer described above.
- `fixtures/valid.json`: a complete valid input. The smoke run writes its outputs into a scratch folder.
- `fixtures/bad-phone.json`: an input with a phone value that fails the phone rule. Expected exit 2, code BAD_FIELD.
- `fixtures/low-contrast.json`: a valid input with a gray text color below 4.5:1. Expected exit 1, code LOW_CONTRAST.
- `LICENSE.txt`: Apache License 2.0.

The fixtures are test inputs. Do not use them as the user's contact data.
