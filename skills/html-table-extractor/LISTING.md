# HTML table extractor

## One line

Turns each table in one local HTML file into JSON or CSV files, with merged cells, ragged rows, and missing headers reported as findings.

## What it does

The skill runs a standard-library script that reads one UTF-8 HTML file and collects every top-level table element. For each table it records the caption, a header row, and the data rows. Rowspan and colspan cells are expanded so that each covered position holds the cell text, and every expansion is written to the table's findings with its source row number and expanded column number. Rows shorter than the widest row are padded with empty strings and flagged. Nested tables are flattened into the text of the outer cell and flagged.

In JSON mode the script writes one new file. In CSV mode it writes one file per table plus an index file that carries the findings without the row data. The script refuses to write to any path that already exists, and it never writes to the input path. It reports a summary line on standard output and uses exit code 1 when findings exist, so a caller can branch on the result without parsing the output.

## When to use

Use it when a web page or saved HTML file holds a data table that must be loaded into a spreadsheet, a notebook, or a database. It is a good fit for a local file saved from a browser, a report exported as HTML, or a static documentation page. It also suits a reviewer who needs to know exactly where spans were expanded before the data is trusted.

## When not to use

Do not use it for pages whose tables are inserted by JavaScript after load, because the saved source has no table markup for the script to read. Do not use it for XLSX, DOCX, or PDF tables, for fetching a URL, or for tables inside HTML email that depend on images. It is also the wrong tool when the file is larger than 2 MB, since the script refuses it rather than streaming it.

## Requirements

Python 3.9 or newer. No third-party packages and no network access. The input must be UTF-8 encoded. The output path must be new (JSON mode) or the output directory must exist and be free of the file names the script would create (CSV mode).

## Example

Command, run on the sample fixture shipped with the skill:

```
python -I "<skill-folder>/scripts/html_tables.py" "<input-file>" --format json --out "<output-file>"
```

Real output from the shipped sample (`fixtures/two_tables.html`), stdout first, then the JSON file:

```
{"status": "findings", "tables": 2, "rows": 5, "findings": 2, "outputs": ["listing_run.json"]}
```

```json
{
  "source_name": "two_tables.html",
  "table_count": 2,
  "row_count": 5,
  "findings_count": 2,
  "file_findings": [],
  "tables": [
    {
      "index": 1,
      "caption": "Quarterly orders by region",
      "header": [
        "Region",
        "Q1",
        "Q2"
      ],
      "rows": [
        [
          "North",
          "120",
          "135"
        ],
        [
          "South",
          "98",
          "110"
        ]
      ],
      "row_count": 2,
      "column_count": 3,
      "findings": []
    },
    {
      "index": 2,
      "caption": "Team roster",
      "header": [
        "Name",
        "Name",
        "Role"
      ],
      "rows": [
        [
          "Ana",
          "Lee",
          "Editor"
        ],
        [
          "Ben",
          "Cruz",
          "Writer"
        ],
        [
          "Ben",
          "Dana",
          "Editor"
        ]
      ],
      "row_count": 3,
      "column_count": 3,
      "findings": [
        {
          "code": "MERGED_COLSPAN",
          "row": 1,
          "col": 1,
          "detail": "colspan=2"
        },
        {
          "code": "MERGED_ROWSPAN",
          "row": 3,
          "col": 1,
          "detail": "rowspan=2"
        }
      ]
    }
  ]
}
```

The exit code for this run is 1. The two findings belong to table 2: the header cell with colspan 2 on row 1, and the Ben cell with rowspan 2 on row 3.

## Limits

The script does not check that the expanded values are correct for the page as a viewer sees it. It does not render CSS, so a table hidden with styles is still extracted, and a visually merged cell is only recognized when it uses the colspan or rowspan attributes. It does not decode legacy character sets, and it does not read a charset declaration. Overlapping spans are flagged but not resolved. Cell text is not escaped for spreadsheet formulas, so a value beginning with an equals sign stays as written. A failure midway through CSV mode can leave some table files behind. Span values above 1000 are capped at 1000 (working value). The script does not verify the source, its license, or whether the data may be reused.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
