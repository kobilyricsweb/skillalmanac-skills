# PDF metadata privacy check

## One line

Reads a PDF's Author, Creator, Producer and XMP fields and flags names, e-mail addresses and local folder paths before the file leaves your hands.

## What it does

The skill runs one read-only Python script on one PDF file. The script reads the file as bytes, up to 2 MB, and pulls the document information entries (Author, Creator, Producer, Title, Subject, Keywords, CreationDate and ModDate) together with four XMP fields. It decodes literal and hex strings, including UTF-16 text with a byte order mark. It then tests each value against three rules: a two-to-three-word capitalized pattern on the Author field, an e-mail shape, and a Windows or Unix home path. Each hit gets a short action from a fixed table, such as clearing the field or re-exporting the file. The script prints JSON, and the skill turns that JSON into a report with fixed sections. The file itself is never changed.

## When to use

Use it when a PDF is about to go to a client, a public download page or an outside uploader, and you want to know whether the file's properties name the author who wrote it or show the folder where it was saved. It also fits a quick check on a file exported from a shared template, where the Author field often keeps the name of whoever built the template.

## When not to use

It does not remove or rewrite metadata, so you still need the source program or a separate tool to clean the file. It does not read text inside scanned pages, so a visible signature or name in an image will not be caught. It does not decompress object streams, so values stored there can be missed; the report says so when that case applies. It is not a check for Word, spreadsheet or image files.

## Requirements

Python 3.9 or newer, standard library only. No network access and no extra packages. The command is `python -I scripts/pdf_meta.py INPUT.pdf`, run from the package folder.

## Example

Run on the bundled test file `fixtures/jane_author.txt`:

```
{
  "file": "jane_author.txt",
  "size_bytes": 325,
  "pdf_version": "1.4",
  "entries": [
    {
      "key": "Author",
      "value": "Jane Doe",
      "source": "info"
    },
    {
      "key": "Creator",
      "value": "<local-path>",
      "source": "info"
    },
    {
      "key": "Producer",
      "value": "Word",
      "source": "info"
    },
    {
      "key": "Title",
      "value": "Quarterly note",
      "source": "info"
    },
    {
      "key": "CreationDate",
      "value": "D:20251103101500+01'00'",
      "source": "info"
    }
  ],
  "flags": [
    {
      "key": "Author",
      "value": "Jane Doe",
      "reason": "possible personal name"
    },
    {
      "key": "Creator",
      "value": "<local-path>",
      "reason": "local file path"
    }
  ],
  "objstm_present": false,
  "notes": [],
  "scrub_advice": [
    "Clear the Author field or replace it with a team or role name.",
    "The value exposes a folder layout. Re-export from the source program with metadata removed."
  ]
}
```

Exit code 1, because two values were flagged.

## Limits

The Title and Subject keys are matched anywhere in the file bytes, so entries from outline or annotation dictionaries can appear next to the Info values; check the source before acting on them. Nesting deeper than 8 levels, or strings longer than 512 characters, are skipped and listed in notes. The name rule is a shape test, so a company name with two capitalized words is flagged as well, and a person with a single given name is not. The input cap is 2 MB. Thresholds such as these are working values chosen for this package, not published standards.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
