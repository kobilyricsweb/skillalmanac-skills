# json-records-to-csv

## One line

Turns a JSON array of objects into a CSV file, with nested fields flattened into dot-named columns and arrays joined or expanded into rows.

## What it does

The skill runs a small Python script on a local JSON file whose top level is an array. Each object in the array becomes one CSV row. Nested objects become columns named by their path, so an address stored as `address.city` appears as a column called `address.city`. Arrays can be joined into a single cell with a separator of your choice, which is the default, or expanded so that each array item gets its own row. Columns are the union of every key seen, in the order they first appear. The output is a UTF-8 CSV with a header row, written with exclusive-create mode so an existing file is never overwritten. The script prints a one-line summary with the row count, column count, number of empty cells, and any skipped items.

## When to use

Use it when someone has JSON records from an export, an API response, or a log, and needs them in a spreadsheet. It fits input files of 2 MB or smaller, which is the hard cap on the source file. It is also useful when an agent needs to check how many cells are blank before handing the file over.

## When not to use

Do not use it for JSON whose top level is an object, a string, or a number. Do not use it for CSV to JSON, for Excel workbooks, or for very large exports. It does not fetch data from a URL, and it does not repair malformed JSON.

## Requirements

Python 3.9 or later. The script uses only the standard library and makes no network calls. It needs read access to the input file and write access to the folder that holds the output file.

## Example

Input: a five-record fixture with a nested address, a tags array, an empty tags array, a null postal code, and a record with no address at all. Command: `python -I scripts/json_to_csv.py fixtures/sample_records.json example_join.csv`. Real output from one run:

```
{"status": "ok", "mode": "join", "rows": 5, "columns": 9, "missing_values": 16, "skipped_records": 0, "skipped_indices": [], "column_names": ["id", "name", "address.city", "address.zip", "tags", "active", "address.geo.lat", "address.geo.lon", "score"], "output_file": "example_join.csv"}
```

```
id,name,address.city,address.zip,tags,active,address.geo.lat,address.geo.lon,score
1,Ada Lovelace,London,W1,math; poetry,true,,,
2,"Grace ""Amazing"" Hopper",New York,10001,navy; compilers; cobol,false,,,
3,Alan Turing,Wilmslow,,,true,,,
4,Katherine Johnson,Hampton,23666,orbits,true,37.02,-76.34,
5,"Linus, Torvalds",,,kernel; git,false,,,9.5
```

## Limits

The script does not check that values are correct, only that the JSON parses and has the expected shape. Keys that contain dots are not escaped, so a literal key `a.b` and a nested path `a` then `b` land in the same column. A duplicate key inside one object keeps the last value, as the JSON parser does. Cells that begin with an equals sign, plus sign, minus sign, or at sign are written as they are, so a spreadsheet may read them as formulas. Numbers are written in the form Python prints them, so trailing zeros are dropped. The input cap is 2 MB and deeply nested input is refused. The script does not check how a spreadsheet application will open the file, and it does not verify that the CSV matches any visual layout.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
