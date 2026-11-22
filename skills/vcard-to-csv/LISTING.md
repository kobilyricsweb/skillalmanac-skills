# vCard to CSV

## One line

Converts a vCard .vcf contact export (versions 2.1, 3.0 and 4.0) into one CSV row per contact, and reports cards without a name and email addresses shared by more than one card.

## What it does

The script reads one vCard text file and writes a new CSV with six columns: name, organization, emails, phones, address and note. Folded lines are unfolded, QUOTED-PRINTABLE values from version 2.1 exports are decoded, and escaped commas and semicolons are restored. Several emails, phones, addresses or notes on one card are joined with semicolons into a single cell, and organization parts are joined with a slash. Every card produces a row, so nothing is merged or dropped. After writing, the script reports which cards have no usable name and which groups of cards share an email address, with email addresses compared without regard to case. The summary gives card numbers rather than addresses, so the printed report carries no contact details. The output file is created exclusively and is never overwritten.

## When to use

Use it when contacts were exported from a phone or mail program as one .vcf file and need to be opened in a spreadsheet, compared, or reviewed by hand. It fits as a first pass before a person decides which of several cards sharing an email address to keep.

## When not to use

Do not use it to edit, delete or merge contacts in place, because it reads the input only and never merges cards. Do not use it to extract photos or other embedded attachments, and do not use it to import contacts into an address book or a mail account.

## Requirements

Python 3.9 or newer with the standard library only. No network access and no packages to install. The input must be UTF-8 text of at most 2,097,152 bytes. The output path must end in .csv, its folder must exist, and the file itself must not exist yet.

## Example

Command, run on the sample file shipped in the fixtures folder:

```
python -I "<skill-folder>/scripts/vcf_to_csv.py" "fixtures/sample.txt" "<output-file>"
```

Summary printed on stdout, exit code 1:

```
{"status": "findings", "cards": 4, "rows_written": 4, "cards_without_name": [], "duplicate_email_groups": 1, "duplicate_card_groups": [[1, 4]], "skipped_lines": 0}
```

CSV written to the output path (byte order mark omitted here):

```
name,organization,emails,phones,address,note
Ada Rivera,Northwind Traders / Accounts,ada.rivera@example.com,+1-555-0101,"12 Harbor Road, Portsmouth, NH, 03801, USA",Prefers email over phone. Met at the spring trade fair in Boston.
Marco Chen,,marco.chen@example.org,+1-555-0142; +1-555-0143,,
Priya Nair,Lakeside Clinic,PRIYA.NAIR@example.com,,,
Ada R.,,ADA.RIVERA@example.com; ada.r@example.net,,,"Call after 5, not before"
```

## Limits

The script does not check whether an email address receives mail, whether a phone number is valid, or whether a name is correct. It does not link cards that describe the same person under different names, such as "Ada Rivera" and "Ada R.", because duplicates are found only by an exact email match after lowercasing. QUOTED-PRINTABLE values that are not valid UTF-8 are decoded with replacement characters. Input that is not valid UTF-8 is refused rather than converted. CSV cells are written as they appear in the card, with no protection against spreadsheet formula injection, so a value beginning with an equals sign could be read as a formula by some programs. PHOTO and other binary properties are ignored.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
