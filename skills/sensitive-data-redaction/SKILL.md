---
name: sensitive-data-redaction
description: Redacts personal data and secrets (emails, phones, card numbers, IBANs, API keys, IPs, listed names) in a text, log or JSON file before it goes to an AI tool or another person, with a script that validates card and IBAN checksums and writes a values-free report. Use when the user says redact, scrub, mask, anonymize or remove personal data or secrets from a ticket, log, export or document before sharing it. Can keep a private mapping to restore placeholders in the answer. Do not use for scanning a code repository for leaked secrets, guarding agent actions, legal compliance advice, or true anonymization.
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Sensitive data redaction

Replace sensitive values in a document with consistent placeholders, so the text can go to an AI tool or another person and still read. The original stays on the user's machine.

## What this is and is not

Redaction removes listed and pattern-matched values. It is not anonymization: a text can still identify someone through context (job title, place, event, an unlisted name). It is not a compliance control, and the script's output must not be described as meeting any regulation. The user's organisation policy decides what may leave the machine; this skill only does the mechanical part and reports what it did.

If the text is only in the chat, it has already reached the model. Save it to a file, run the script on the file, and tell the user that redaction protects later sharing, not what was already pasted.

## Workflow

```
- [ ] 1 State the purpose and the audience
- [ ] 2 Choose categories and the keep rule
- [ ] 3 Collect names and terms to list
- [ ] 4 Run redact (dry run first on unknown files)
- [ ] 5 Review the report and the redacted file
- [ ] 6 Work only with the redacted file
- [ ] 7 Restore if wanted, then report
```

1. **Purpose.** Write one line: what the AI or the recipient must do with the text. Keep only what that needs. A summary of a ticket needs the product and the complaint, not the card number.
2. **Choose** from the table below. Default is full replacement; mask partly only when the task needs to tell two items apart.
3. **Lists.** Ask for the names of people, customers, projects and internal hosts that appear. Write them one per line in a private file kept outside the shared folder, with aliases on one line, for example `Dana Reyes | Dana | Ms. Reyes`, so one person gets one placeholder. Aliases under 3 characters are ignored by the script.
4. **Run** (do not open the original file to the chat first):

```bash
python scripts/redact.py redact FILE --names names.txt --terms terms.txt --mapping PRIVATE_DIR/FILE.mapping.private.json --dry-run
python scripts/redact.py redact FILE --names names.txt --terms terms.txt --mapping PRIVATE_DIR/FILE.mapping.private.json
```

   Options: `--keep-last4`, `--keep-private-ips`, `--skip PHONE,IPV4` (categories listed below), `--out-dir`, `--force`. Omit `--mapping` when no restore is needed; then the originals are not stored anywhere. Do not edit the script to change what it detects.
5. **Review.** Read the report (stdout and `<stem>.redaction_report.json`): `counts` per category, `locations` (line numbers `L12` for text, paths like `$.customer.email` for JSON), `samples` (redacted context of the first 3 hits per category), `warnings`. Then read the whole redacted file once. Check for each miss type in the second table. A sample whose context shows a version number, order number or timestamp is a false positive: re-run with `--skip` for that category only if the over-redaction costs the task; otherwise leave it.
6. **Work** only with `<stem>.redacted<ext>`. Never paste the mapping or the original into the AI tool.
7. **Restore** only when the user needs the original values back in the answer: `python scripts/redact.py restore ANSWER_FILE --mapping PRIVATE_DIR/MAPPING.json`. The restored file holds real values; say so and do not share it.

## Decision table: what to redact by document type

| Document | Always | Usually | Keep |
|---|---|---|---|
| Support ticket or email thread | EMAIL, PHONE, CARD, IBAN, NAME of customer | URL_TOKEN, SSN | Product, error text, dates |
| Server or app log | CREDENTIAL, API_KEY, PRIVATE_KEY, URL_TOKEN | EMAIL, IPV4/IPV6 (public) | Timestamps, status codes, request ids, private IPs if topology is not the question (`--keep-private-ips`) |
| Contract or letter | NAME, EMAIL, PHONE, IBAN, TERM (party and project names) | Addresses by hand | Clause text, amounts, dates |
| Meeting notes | NAME, TERM | PHONE, EMAIL | Decisions and action items |
| Spreadsheet export (CSV) | EMAIL, PHONE, CARD, IBAN, SSN | NAME from a list | Column headers, aggregates. Check the first rows by eye: ids that look like numbers can match |
| JSON from an API | CREDENTIAL (keys named password, token, secret), EMAIL, CARD | NAME | Structure and keys; the script keeps the JSON valid |

## Decision table: full or partial mask, and consistency

| Situation | Choice |
|---|---|
| The AI never needs to tell two cards, IBANs, phones or SSNs apart | Full placeholder |
| Support work where the user says "the card ending 1111" | `--keep-last4` (shows `[CARD_1 ****1111]`; never more than 4 characters) |
| Secrets, keys, passwords, private keys, token values | Always full; never partial |
| Same person or value appears many times | One placeholder per value: the script does this (same normalised value gives the same token, `[EMAIL_1]` stays `[EMAIL_1]`) |
| Two people with similar roles | Different placeholders, so the text still reads: `[PERSON_1]` and `[PERSON_2]` |
| A name list with nicknames | One line with `|` aliases, or the nickname becomes a separate person |
| Output must be re-imported as JSON | Keep the `.json` extension so the file is parsed, not text-scanned |

## What the script detects (priority order)

PRIVATE_KEY (a BEGIN to END block), API_KEY (`AKIA` or `ASIA` plus 16 characters, `sk-` plus 20 or more, GitHub `ghp_` style, Slack `xox` style, three-part JWT), URL_TOKEN (values of secret-named query parameters and the password in `user:pass@`), CREDENTIAL (values after `password`, `secret`, `token`, `api_key` and `Bearer`; in JSON, any string under such a key), EMAIL, IBAN (mod-97 valid), CARD (13 to 19 digits, Luhn valid, first digit 2 to 6), SSN (US pattern), IPV6, IPV4 (loopback and 0.0.0.0 are kept), PHONE (a leading `+`, parentheses or separators, 9 to 15 digits), NAME and TERM (only from your lists). Details and the reasons for each rule: [references/detection-rules.md](references/detection-rules.md); read it only when a sample looks wrong or a value was missed.

## Output contract

`redact` prints one JSON object (and writes the same to the report file):

```json
{"tool": "redact.py", "mode": "text|json", "total_replacements": 0,
 "counts": {"EMAIL": {"matches": 2, "unique": 1}},
 "locations": {"EMAIL": ["L2", "L14"]}, "locations_truncated": [],
 "samples": [{"category": "EMAIL", "location": "L2", "context": "From: [EMAIL_1]"}],
 "warnings": [], "notes": {}, "mapping_written": false, "dry_run": false}
```

No original value appears in it, in the redacted file, or on stdout. The mapping file is written only with `--mapping`, holds the originals, and gets a warning when it sits in the same folder as the redacted output. Existing outputs are never overwritten without `--force`, and an output, report, mapping or restore path that resolves to an input file (or the mapping used for restore) is refused even with `--force`. A card number that fails the Luhn check is left in place and may be a mistyped real card. Exit 0 on success (zero matches included), 2 for a bad argument, unreadable or empty input, or an existing output. `restore` prints counts per category and any `unknown_tokens`.

## What the script misses: check by eye in step 5

| Miss type | Example | Action |
|---|---|---|
| Names not on the list, misspellings, nicknames | "Mr Reyes", "Dan" | Add to the list, re-run |
| Postal addresses, birth dates, usernames, employer names, health or case details | "12 Fern Road", "born 3 March 1980" | Replace by hand in the redacted copy, or list the string as a term |
| Account or customer numbers with no label | `00481516` | List as a term |
| Local phone numbers without a prefix | `555-0100` (7 digits) | List as a term |
| Secrets with no label or known prefix | a bare 40-character hex string | List as a term |
| Identifying combinations | "the only female CFO in Leeds" | Rewrite by hand or do not share |

Report to the user, in this shape, after step 5:

```
Redacted: <categories and counts>
Mapping: <written to where, or not written>
Reviewed by eye: <what you checked in the redacted file>
Possible false positives: <samples that looked wrong, or none>
Not detected by design: <names not listed, addresses, dates of birth, context>
```

## Fallback without Python

Find the values by reading the file against the table above, replace each with `[CATEGORY_n]`, reuse the same token for the same value, and say in the report that the checksum validation was not run. Do not claim the result is complete.

## Limits

- Free-text names are only found when listed. There is no name recognition.
- Phone, IPv4 and card detection are heuristics with known false positives and misses (see notes in the report).
- JSON numbers are scanned as digits; floats and booleans are not.
- A file over 20 MB is refused. Non-UTF-8 text is decoded as cp1252 with a warning.
- Placeholders already present in the input can be confused with new ones on restore; the script warns.
- Variants of one value (different spacing of one card number) share a token, and restore returns the first spelling seen.
- The skill makes no claim of compliance with any law or standard.
