---
name: email-address-extractor-validator
description: Extracts email addresses from a plain text file or pasted contact list, checks each one for syntax errors, flags repeated addresses, and writes a de-duplicated list to a new file. Use when a user asks to validate an email list, clean a contact export, find malformed or repeated addresses, or count valid addresses in text. Do not use for checking whether an address receives mail, DNS or MX lookups, deliverability scoring, or sending messages.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Email address extractor and validator

This skill runs `scripts/email_clean.py` on one plain text file. The script finds candidate addresses, applies fixed syntax rules, reports invalid entries and repeats by line number, and can write the unique valid addresses to a new file. It performs no DNS lookup and makes no claim that any address can receive mail.

## Workflow

1. **Confirm the input.** Need one UTF-8 text file, 2,097,152 bytes or less. Output: the input path. If the user only pasted text, save it to a new `.txt` file in the user's workspace and use that path. Stop if neither is possible.
2. **Confirm the output.** Output: either a NEW file path for the de-duplicated list, or `none`. Never reuse a path that already exists.
3. **Run the script** with the exact command below. Output: the JSON report on stdout and the exit code. Record the exit code.
4. **Apply the decision table** to the exit code (next section). Output: the status word used in the report.
5. **Map each finding.** For every entry in `invalid_items`, record its line and code. For every entry in `duplicate_items`, record its line, first line and masked value. Output: the two tables in the output contract.
6. **Write the report** using the output contract. Do not print full addresses from the report in chat; the masked values are the only address text you show. Full unique addresses exist only in the `--out` file.

Command (Windows or POSIX shell, run from the skill folder):

```
python -I scripts/email_clean.py <input-file> [--out <output-file>]
```

## Decision table

| Exit code | `status` value | Meaning | Action |
|---|---|---|---|
| 0 | `ok` | No invalid addresses and no duplicates | Report the counts. Write `--out` if requested. |
| 1 | `findings` | At least one invalid address or duplicate | Report every item in both finding tables. Write `--out` if requested. |
| 2 | `error` | Usage or input error; JSON error on stderr | Quote the `error` key, ask for a fixed input or path, and re-run once. Do not invent counts. |

Thresholds used by the rules (the script's fixed values):

| Rule | Value | Basis |
|---|---|---|
| Maximum address length | 254 characters | Common SMTP path limit; a working value, not a deliverability test |
| Maximum local-part length | 64 characters | Common SMTP local-part limit; a working value |
| Maximum domain label length | 63 characters | DNS label limit |
| Maximum input size | 2,097,152 bytes (2 MB) | Working value |
| Trailing period stripped before checks | 1 period | Working value; handles "...at dana@example.com." |
| Role local parts (informational only) | 15 names: abuse, admin, billing, contact, help, hello, hostmaster, info, noreply, no-reply, postmaster, sales, support, team, webmaster | Working list; role addresses never change `status` |
| Duplicate test | Lowercased full address equals an earlier valid address | Case-insensitive |

## Invalid codes

Every code the script emits appears here. Codes are checked in this order; the first failing rule is reported.

| Code | Rule that failed |
|---|---|
| `TOO_LONG` | Address is longer than 254 characters |
| `MULTIPLE_AT` | More than one `@` |
| `EMPTY_LOCAL` | Nothing before the `@` |
| `EMPTY_DOMAIN` | Nothing after the `@` |
| `LOCAL_TOO_LONG` | Local part is longer than 64 characters |
| `CONSECUTIVE_DOTS` | Two dots in a row anywhere in the address |
| `LOCAL_EDGE_DOT` | Local part starts or ends with a dot |
| `LOCAL_BAD_CHAR` | Local part has a character outside letters, digits, dots and these symbols: ! # $ % & ' * + - / = ? ^ _ { } ~, plus backtick and vertical bar |
| `DOMAIN_NO_DOT` | Domain has no dot |
| `DOMAIN_BAD_LABEL` | A domain label has a character outside letters, digits and hyphen, starts or ends with a hyphen, or is longer than 63 characters |
| `TLD_INVALID` | Final domain label is not two or more letters |

Duplicates are not invalid. They never appear in `invalid_items`; they appear only in `duplicate_items`.

## Output contract

Use these headings in this order. Omit "Output file" only when `--out` was not used.

**Summary** (table, two columns: `Metric`, `Count`). Rows, in this order, copied from the JSON keys: `lines_scanned`, `candidates`, `valid_occurrences`, `unique_valid`, `invalid`, `duplicates`, `role_addresses`, and `written_unique` when present.

**Invalid addresses** (table: `Line`, `Code`). One row per `invalid_items` entry. Write "None" in one row when empty.

**Duplicates** (table: `Line`, `First seen on line`, `Masked value`). One row per `duplicate_items` entry. Write "None" in one row when empty.

**Role addresses** (one sentence): the value of `role_addresses`, stated as informational.

**Output file** (one line): the output path and `written_unique` count, or "not requested".

**Status** (one line): `ok`, `findings` or `error`, exactly as in the decision table.

## Refuse or stop when

- The user asks whether an address exists, receives mail, or is deliverable. This skill does no DNS, MX or SMTP checks. Say so and stop that clause only; keep the syntax report.
- The user asks you to send mail to these addresses or import them into a mailing tool. Stop; this skill only cleans lists.
- Exit 2 with `input_too_large`: ask the user to split the file into parts of 2 MB or less. Do not split it yourself.
- Exit 2 with `invalid_utf8`: ask the user to re-save the file as UTF-8 text.
- Exit 2 with `output_exists`: ask for a new output name. Never delete, rename or overwrite the existing file.
- The user asks you to print full unmasked addresses in chat. Refuse that part; the full list is available only in the `--out` file.

## Script contract (type A)

- **Command:** `python -I scripts/email_clean.py <input-file> [--out <output-file>]`
- **Arguments:** one positional input file (required). `--out` followed by a new file path (optional). Any other argument is a usage error.
- **Inputs:** one UTF-8 text file (a BOM is accepted), 2,097,152 bytes or less. The input is read only.
- **Output file:** written only with `--out`, opened in exclusive-create mode. It holds unique valid addresses, one per line, first-seen order, original casing of the first occurrence.
- **Stdout JSON keys:** `status`, `lines_scanned`, `candidates`, `valid_occurrences`, `unique_valid`, `invalid`, `duplicates`, `role_addresses`, `invalid_items` (each with `line`, `code`), `duplicate_items` (each with `line`, `first_line`, `value_masked`), and `written_unique` (only with `--out`).
- **Stderr on exit 2:** one JSON line with keys `error` and `detail`. Error codes: `usage`, `file_not_found`, `not_a_file`, `read_failed`, `input_too_large`, `invalid_utf8`, `output_exists`, `output_write_failed`.
- **Exit codes:** 0 = `ok`; 1 = `findings`; 2 = usage or input error (`error`).
- **Network, subprocess, eval:** none.

## Shipped files

- [scripts/email_clean.py](scripts/email_clean.py): the extractor, validator and writer described above.
- [fixtures/contacts_sample.txt](fixtures/contacts_sample.txt): a 20-line sample used to check the script's behavior. It is not the user's data.
- [LICENSE.txt](LICENSE.txt): Apache License 2.0.
