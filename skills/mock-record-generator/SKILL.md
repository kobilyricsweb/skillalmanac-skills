---
name: mock-record-generator
description: Generates seeded mock records as CSV or JSON from a JSON field list or a simple TypeScript interface. Use when test data must be written by hand today and a repeatable set of rows is needed for a fixture, a seed script, or a UI test, where the same seed and spec must give the same output. Do not use for production or real customer data, real email addresses, load testing at scale, or inserting rows into a live database.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Mock Record Generator

Type A skill. The script [scripts/mock_data.py](scripts/mock_data.py) does the generating. The agent collects the intake, maps each field, runs the script, and reports what was written and what was skipped.

Shipped files: [scripts/mock_data.py](scripts/mock_data.py), [fixtures/spec_fields.json](fixtures/spec_fields.json) (6-field smoke spec), [fixtures/spec_interface.ts](fixtures/spec_interface.ts) (4-field smoke interface), [fixtures/spec_unsupported.ts](fixtures/spec_unsupported.ts) (exit 1 path), [LICENSE.txt](LICENSE.txt).

## Workflow

1. Intake. Confirm four facts: the spec file path, the row count, the output format (`csv` or `json`), and a new output file path. Output: a four-line intake block. If any fact is missing, stop (see the Refuse / stop when list).
2. Pick the spec kind by file extension. `.json` is a field list. `.ts` is an interface. Any other extension exits 2. Output: the spec kind, plus the interface name when a `.ts` file holds several interfaces (passed as `--interface`).
3. Map every field to a type from the tables below. Output: a field map with one row per field (name, type, parameters). Lines the script cannot read are not mapped; they appear in the script report instead.
4. Run the command line below. Use `<spec-file>` and `<new-file>` for the requester's paths. Output: the one-line JSON report from stdout and the exit code.
5. Check the exit code against the exit table. Exit 1 means the file was written but at least one field or line was skipped. Each skipped item goes under Open questions.
6. Write the final report in the output contract. Output: the report block, then the Open questions list.

## JSON field list

The top level is an object with a non-empty `fields` list. Each field has `name` (letters, digits, underscore, at most 64 characters) and `type`. Defaults apply when a parameter is absent.

| type | parameters (default) | shape of a value |
|---|---|---|
| int | min (0), max (100); integers, min at most max | 42 |
| float | min (0.0), max (1.0), decimals (2, range 0 to 6) | 0.37 |
| bool | none | true or false |
| date | from (2000-01-01), to (2030-12-31), both YYYY-MM-DD, inclusive | 2014-06-22 |
| enum | values (required; distinct non-empty strings) | one listed string |
| uuid | none; version 4 layout | 8-4-4-4-12 hex digits |
| name | none; first name and last name from fixed lists of 12 each (working value) | Given Family |
| email | none; always example.com; first.last plus a 3-digit number | first.last123@example.com |
| text | words (5; range 1 to 20, working value) | capitalized words ending in a period |

## TypeScript interface

The header must be one line of the form `interface Name {` or `export interface Name {`. `extends` is not supported. Each field sits on its own line as `name: type;` or `name?: type;`. Without `--interface`, the first matching interface is used.

| TypeScript form | generated value | notes |
|---|---|---|
| string | 8 characters from a-z and 0-9 (8 is a working value) | |
| number | 0.00 to 1000.00, two decimals | |
| boolean | true or false | |
| string literal union (two or more quoted literals) | one of the listed literals | single or double quotes |
| field marked with ? | absent in about half of the rows (working value 0.5) | null in JSON, empty cell in CSV |
| anything else (arrays, Date, nested objects, methods) | skipped and reported | reasons unsupported_type or unsupported_syntax |

## Command line

`python -I scripts/mock_data.py <spec-file> --count <N> --seed <S> --format <csv|json> --out <new-file> [--interface <Name>]`

`--seed` defaults to 0. Same spec, count, and seed give the same rows: the generator draws values only through `random.Random.random()`, and two runs on the smoke fixtures with seed 7 produced identical files.

## Script contract

| argument | rule |
|---|---|
| spec | path ending in .json or .ts; at most 2 MB; UTF-8 (a BOM is accepted) |
| --count | integer, 1 to 10000 (10000 is a working value) |
| --seed | integer, default 0 |
| --format | csv or json (required) |
| --out | new file; must not exist; must not be the spec path; folder must exist |
| --interface | optional interface name |

| exit code | meaning | output file |
|---|---|---|
| 0 | ok; every field and line was supported | written |
| 1 | partial; at least one field or line was skipped | written |
| 2 | usage or input error; one-line JSON on stderr | not written |

Error codes on stderr (exit 2): usage_error, unsupported_spec_file, input_not_found, input_too_large, invalid_utf8, invalid_json, invalid_spec, interface_not_found, no_supported_fields, too_many_fields (more than 100 supported fields; 100 is a working value), output_is_input, output_dir_missing, output_exists, output_not_writable.

Skip reasons in the stdout report: unsupported_type (JSON type not in the list, or TypeScript type not in the table) and unsupported_syntax (a body line that is not a field).

## Output contract

Stdout, one JSON line, keys in this order: `status` (ok or partial), `rows`, `format`, `out`, `fields` (names in spec order), `unsupported` (list of objects with keys `field`, `line`, `type`, `reason`; `field`, `line` and `type` may be null).

The output file: CSV has one header row of field names in spec order, then one row per record, LF line endings. JSON is an array of objects with keys in spec order, two-space indent. Floats are fixed to `decimals` in CSV and written in shortest form in JSON.

Final report to the requester:

```
## Mock data report
- Status: ok | partial | error
- Rows written: <N>
- Output file: <new-file>
- Fields: <name>, <name>, ...
- Skipped: none | one row per skipped item (field, line, type, reason)

## Open questions
1. <question or refused clause>, or "none"
```

## Refuse / stop when

- Intake incomplete: the spec path, row count, format, or output path is missing. Stop and return a numbered question list that asks for each missing fact.
- The output path already exists (exit 2, output_exists). Stop and ask for a new path. Never overwrite and never delete the existing file.
- The row count is above 10000, or the spec has more than 100 supported fields. Stop and ask the requester to lower the count or split the spec.
- The request asks for real personal, customer, or production data, or for real email addresses. Refuse that clause only: generate with the example.com pattern, return status partial, and list the refused clause under Open questions.
- The request asks to insert rows into a live database or to send the output somewhere. This skill does not do either; return the file only.
- The spec uses a type outside the tables. Do not stop: the script skips it (exit 1), and each skipped item goes under Open questions.
- The spec file is over 2 MB, is not UTF-8, is not valid JSON, or has a non-.json and non-.ts extension. The script exits 2; stop and report the error code.
