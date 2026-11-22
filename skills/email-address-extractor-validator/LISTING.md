# Email address extractor and validator

## One line

Finds email addresses in one text file, flags malformed and repeated entries by line number, and writes a de-duplicated list to a new file.

## What it does

The skill runs a small Python script on a single UTF-8 text file. The script scans each line for candidate tokens that contain an at sign, strips one trailing period, and checks every candidate against a fixed set of syntax rules: a single at sign, a non-empty local part under 64 characters, no consecutive dots, no leading or trailing dot in the local part, a domain with at least one dot, labels made of letters, digits and hyphens, and a final label of two or more letters. The total length limit is 254 characters.

Valid addresses are compared case-insensitively. A repeat of an earlier valid address is reported as a duplicate with the line where it first appeared. Local parts such as sales, support or info are counted separately as role addresses, for information only.

The report is one JSON object. Full addresses never appear in it; duplicates show only a masked local part, and invalid entries show only a line number and a code. When an output path is given, the unique valid addresses are written there in first-seen order, and the script refuses to run if that path already exists.

## When to use

Use it when a contact export, a sign-up list or a pasted set of addresses needs a syntax pass before anyone looks at it by hand. It is most useful when you need line numbers for each problem so a person can open the source file and fix the entry.

## When not to use

Do not use it to decide whether an address is real, whether it accepts mail, or whether a domain exists. It performs no DNS, MX or SMTP work. It does not check spam traps, disposable domains or bounce history. It also does not send anything, import into a mailing tool, or edit the original file.

## Requirements

Python 3.9 or later, standard library only. No network access and no subprocess calls. The input must be a plain text file of 2,097,152 bytes or less, encoded as UTF-8 with or without a byte order mark. Run the command from the skill folder so the relative script path resolves.

## Example

Command, run on the bundled 20-line sample:

```
python -I scripts/email_clean.py fixtures/contacts_sample.txt
```

Output (exit code 1):

```
{
  "status": "findings",
  "lines_scanned": 20,
  "candidates": 10,
  "valid_occurrences": 8,
  "unique_valid": 6,
  "invalid": 2,
  "duplicates": 2,
  "role_addresses": 1,
  "invalid_items": [
    {
      "line": 3,
      "code": "CONSECUTIVE_DOTS"
    },
    {
      "line": 8,
      "code": "MULTIPLE_AT"
    }
  ],
  "duplicate_items": [
    {
      "line": 5,
      "first_line": 1,
      "value_masked": "J***@example.com"
    },
    {
      "line": 11,
      "first_line": 7,
      "value_masked": "b***@example.io"
    }
  ]
}
```

## Limits

The script checks syntax against fixed rules. It does not verify that an address exists, that its domain resolves, or that mail to it would be delivered. The length limits of 254 and 64 characters and the role-name list are working values, not a standard test. The candidate pattern is a practical approximation: unusual quoted local parts, comments and internationalized addresses are not parsed, so they are reported as invalid or missed. Each line is scanned on its own, so an address split across two lines is not joined and is missed. Input larger than 2 MB is refused, and the script does not chunk it.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
