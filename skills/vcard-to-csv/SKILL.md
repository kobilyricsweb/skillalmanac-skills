---
name: vcard-to-csv
description: Converts vCard (.vcf) contact files in versions 2.1, 3.0 and 4.0 into one CSV row per contact with name, organization, emails, phones, address and note columns. Use when contacts are locked in .vcf exports and must be merged into a spreadsheet, or when cards without a name or with a repeated email address must be found. Do not use for editing or deleting contacts, merging cards into one contact, extracting photos or attachments, or importing into a phone or email account.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A)
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# vCard to CSV

Script-backed skill (type A). The script reads one .vcf file and writes one new .csv file. It uses only the Python standard library.

## Workflow

1. Intake. Confirm the input is a text vCard file (BEGIN:VCARD blocks, version 2.1, 3.0 or 4.0). Confirm the output path ends in .csv and does not exist yet. Output: input path, output path, input size in bytes.
2. Size check. The input must be at most 2,097,152 bytes. Above that, stop (see Refuse / stop when). Output: "Size: OK" or "Size: STOP".
3. Run the script with the command line in the Script contract section. Output: the one-line JSON summary from stdout, or the one-line error from stderr, plus the exit code.
4. Branch on the exit code. Exit 0: go to step 5. Exit 1: go to step 5 and carry the findings forward. Exit 2: stop and report the error code from the Error codes table.
5. Integrity check. rows_written must equal cards. Output: "Integrity: pass" or "Integrity: fail" with both numbers. On fail, stop.
6. Findings. Map each finding to an action with the Decision thresholds table. Output: one row per finding in the Findings table (Output contract).
7. Final report. Output: the Summary table and the status value from the Output contract. Do not print email addresses or phone numbers in the report; point the user to the CSV.

## Decision thresholds

| Condition | Value | Action |
|---|---|---|
| Input size | up to 2,097,152 bytes (2 MB, working value) | Run the script. Above this, exit 2 with input_too_large |
| Exit 0 (status ok) | no cards without a name, no duplicate emails | Deliver the CSV. Findings table says "None" |
| Cards without a name | one or more card numbers in cards_without_name | Deliver the CSV. Those rows keep a blank name. Do not invent a name |
| Duplicate email group, 2 to 5 cards | duplicate_card_groups entry of length 2 to 5 (working value) | Deliver the CSV with every card kept. List the card numbers |
| Duplicate email group, 6 or more cards | duplicate_card_groups entry of length 6 or more (working value) | Same as above, and add "likely a shared mailbox" to the note |
| Integrity | rows_written equals cards | Pass. Otherwise stop and report both numbers |
| Duplicate removal | any request to delete or merge cards | Refused for the script. Every card stays in the CSV |
| Output name | ends in .csv and does not exist | Otherwise exit 2 (output_not_csv or output_exists) |

## Output contract

The CSV file, written by the script:

- Header row, exactly: `name,organization,emails,phones,address,note`
- One row per card, in file order. No card is dropped or merged.
- UTF-8 with a byte order mark, so spreadsheet programs show non-ASCII names correctly. Line endings are CRLF (csv module default).
- emails, phones and note: values joined with "; ". Organization: ORG components joined with " / ". Address: non-empty ADR parts joined with ", ".
- name: the FN value. When FN is missing, built from N as prefix, given, additional, family, suffix (non-empty parts only).

The one-line JSON summary on stdout has these keys, in this order: status, cards, rows_written, cards_without_name, duplicate_email_groups, duplicate_card_groups, skipped_lines.

Summary table in the report to the user:

| Field | Value |
|---|---|
| Status | ok, findings, partial or stopped |
| Cards | value of cards |
| Rows written | value of rows_written |
| Cards without a name | card numbers, or "None" |
| Duplicate email groups | value of duplicate_email_groups, with card numbers |
| Skipped lines | value of skipped_lines (lines inside cards that had no colon) |

Findings table, one row per finding:

| Finding | Card numbers | Count | Action |
|---|---|---|---|

Status values: ok (exit 0), findings (exit 1), partial (the CSV was delivered but one requested clause was refused), stopped (exit 2 or failed integrity check).

## Script contract

Script: `scripts/vcf_to_csv.py`

Arguments, in order:

1. input-file: an existing .vcf file of at most 2,097,152 bytes, UTF-8 (a byte order mark is allowed).
2. output-file: a path ending in .csv, in an existing folder, that does not exist yet.

Command line:

```
python -I "<skill-folder>/scripts/vcf_to_csv.py" "<input-file>" "<output-file>"
```

Exit codes: 0 converted with no findings; 1 converted with findings; 2 usage, input or output error.

Error codes (stderr, one line, form `{"error": "<code>"}`), all exit 2:

| Code | Meaning |
|---|---|
| usage | not exactly two arguments |
| input_missing | input path is not a file |
| input_too_large | input is over 2,097,152 bytes |
| io_error | a file could not be read or written |
| invalid_utf8 | input is not valid UTF-8 |
| no_cards | no BEGIN:VCARD block was found |
| unterminated_card | a BEGIN:VCARD has no END:VCARD, or a card starts inside another card |
| output_not_csv | output path does not end in .csv |
| output_is_input | output path is the same file as the input |
| output_dir_missing | output folder does not exist |
| output_exists | output file already exists; the script never overwrites |

Output checks run before the input is read, so a refused output never leaves a partial file behind.

## Refuse / stop when

- The input has no BEGIN:VCARD block (no_cards). Stop and ask the user for a vCard export.
- The input is over 2,097,152 bytes. Stop and ask the user to split the export into smaller .vcf files. Do not split or truncate the file yourself.
- The input is not UTF-8, for example a Windows-1252 export. Stop and ask the user to export again as UTF-8. Do not transcode silently.
- The output path already exists. Stop and ask for a new name. Never overwrite it and never write to the input path.
- A card is unterminated (unterminated_card). Stop and ask for a fresh export.
- The request asks to delete, merge or de-duplicate cards: refuse that clause only. Keep every card in the CSV, set status to partial, and list "Delete or merge duplicate cards: refused, the script keeps every card" under Open questions. Deliver the rest.
- The request asks to edit the source .vcf: refuse that clause only, set status to partial, and list it under Open questions. The script never writes to the input.
- The request asks for PHOTO or other binary attachments: not handled, because the script ignores PHOTO. Set status to partial and list it under Open questions.
- A card has no name: do not invent one. The row keeps a blank name.

## Shipped files

- [scripts/vcf_to_csv.py](scripts/vcf_to_csv.py): the converter described in the Script contract.
- [fixtures/sample.txt](fixtures/sample.txt): a four-card version 3.0 vCard sample saved with a .txt extension, with one folded line and one email address shared by two cards, for checking the script.
- [LICENSE.txt](LICENSE.txt): the Apache-2.0 license text.

The script does not verify that email addresses are deliverable, that phone numbers are well formed, or that names are correct. It does not decode attachments and does not read version 2.1 files encoded other than UTF-8.
