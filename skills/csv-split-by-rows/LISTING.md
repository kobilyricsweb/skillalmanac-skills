# CSV split by rows

## One line

Splits a CSV file into numbered part files of a fixed data-row count, repeats the header in each part, and checks that the parts add up to the original row count.

## What it does

The skill runs a single Python script, `scripts/csv_split.py`, which reads a CSV with the standard csv module. Quoted fields that span several lines remain one record, so a multiline note cell is never cut in half. Records after the header are grouped into chunks of the requested size, and each chunk is written to a new file named with a prefix and a sequence number, such as part_001.csv. Every file starts with the original header.

Output files are created in exclusive mode. If any target name already exists, the script stops with exit code 2 before writing anything. If a write fails part way, the files created in that run are removed. The input file is only read.

After writing, the script reads each part back and compares it with its slice of the original records. It then compares the sum of the part row counts with the input row count. The JSON report lists rows per part, the total, a verified flag, and any ragged rows, meaning rows whose field count differs from the header.

## When to use

- A CSV export is too large for a spreadsheet to open, and the input is at most 2 MB.
- A file must be imported or sent in batches of a set number of rows.
- You need proof that no row was lost or duplicated during the split.
- You want to find rows with the wrong number of fields before the file goes to an import tool.

## When not to use

- The file is larger than 2 MB. The script refuses it.
- The file is an xlsx workbook, JSON, or another non-CSV format.
- You need to merge, filter, sort, or re-encode a CSV. The script only splits.
- The file is not UTF-8. The script refuses it and the user has to re-save the file first.
- You want the parts written over existing files. The script never overwrites.

## Requirements

- Python 3.9 or newer. Only the standard library is used.
- No network access and no subprocesses.
- An existing output folder with no files named like the parts.
- A text editor or viewer to open the part files.

## Example

Command, with the placeholder `<workspace>` standing for the output folder:

```
python -I scripts/csv_split.py fixtures/sample_25_rows.csv --rows 10 --out-dir <workspace>/out
```

Output from the smoke run on the shipped 25-row fixture, which includes one quoted note spanning three lines:

```
{"status": "ok", "input_data_rows": 25, "rows_per_part": 10, "header_columns": 4, "parts": [{"file": "part_001.csv", "data_rows": 10}, {"file": "part_002.csv", "data_rows": 10}, {"file": "part_003.csv", "data_rows": 5}], "parts_data_rows_total": 25, "verified": true, "ragged_row_count": 0, "ragged_rows": []}
```

Exit code 0. The three part files contain 10, 10 and 5 data rows, each with the four-column header.

## Limits

- The 2 MB input cap and the UTF-8 requirement are fixed in the script.
- Verification compares parsed fields, not bytes. Quoting may differ from the source file, and the parts use LF line endings.
- A leading byte order mark is accepted on input and is not copied to the parts.
- Ragged rows are reported but still written as they are. Fixing them is left to the user.
- The script does not check the meaning of any value, duplicate keys, date formats, or encoding of text after decoding.
- The script does not check that a part will open in a particular spreadsheet or import tool.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
