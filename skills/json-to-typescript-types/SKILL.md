---
name: json-to-typescript-types
description: Infers exported TypeScript interfaces from a JSON sample that is one object or an array of objects. Use when typing an API response or config file by hand is slow and you hold a representative sample, or when optional fields, nullable values, empty arrays and mixed-type unions must be flagged for review. Do not use for JSON Schema generation, runtime validation code, or samples you have not checked against the live source.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# JSON to TypeScript types

This skill runs `scripts/json_to_ts.py` on a JSON sample and returns a `.ts` file of exported interfaces plus a list of findings. The script does the inference. You check the findings against the real source and decide what each one means.

## Workflow

1. Check the intake. The input must be one JSON file, UTF-8, at most 2 MB. Its root must be a JSON object, or a non-empty array in which every item is an object. Choose an output name that ends in `.ts` and does not exist yet. Required output: the input path, the output path and the root name (default `Root`).
2. Run the script with the command in the Script contract below. Required output: the raw one-line JSON summary and the exit code.
3. Branch on the exit code. Exit 2 means stop: report the error code from the stderr line and do not retry with a changed output path unless the user agrees. Exit 0 or 1 means the `.ts` file exists. Open it and read it.
4. Triage each finding with the decision table below. Required output: one row per finding in the Findings table, with the action you recommend.
5. Deliver the result in the Output contract. List every item you could not confirm under Open questions.

## Decision and threshold table

| Code or threshold | Meaning in the output | Action |
|---|---|---|
| NULL_ONLY | Field or array item is `null` in every sample item. Emitted as `null`. | Get a sample with a real value. Keep `null` and flag it if none exists. |
| EMPTY_ARRAY | Array is empty in every sample item. Emitted as `unknown[]`. | Replace `unknown[]` with the element type from the API docs. Do not guess an element type. |
| MIXED_TYPES | A position holds more than one non-null kind (string, number, boolean, object, array). Emitted as a union. | Check each kind against the live source. If one kind is a sample error, fix the sample and rerun. |
| NAME_COLLISION | Two positions produce the same interface name. The second gets a numeric suffix (`Address2`). | Rename one interface by hand and update every reference to it. |
| Optional marker (not a finding) | A property is `?` when at least one object at its parent lacks the key. A key present with `null` is not optional. | Accept the marker only when the sample has at least 5 items (working value). Below 5 items, list every optional marker under Open questions. |
| Sample size (working value) | Below 5 items, every optional marker is unreliable. | Note the sample size in Open questions. |

## Output contract

The reply has these headings, in this order:

- `## Result`: a table with the columns `Field | Value`. Rows: `Status` (script `status`, `ok` or `findings`), `Interfaces` (script `interfaces`), `Optional properties` (script `optional_properties`), `Output file` (the path given), `Exit code`.
- `## Findings`: a table with the columns `Code | Path | Action`. Use one row per entry in the script `findings` list. Write `none` when the list is empty.
- `## Command`: the exact command line run, in a code block.
- `## Open questions`: a numbered list. Write `none` when empty.

## Script contract (type A)

Command line:

```
python -I scripts/json_to_ts.py <input-file> <output-file.ts> [--root-name Root]
```

Arguments:

- `input-file`: the JSON sample. Read only. Must exist, be at most 2 MB, and be valid UTF-8 JSON.
- `output-file.ts`: a new file. The name must end in `.ts`. The script opens it in exclusive-create mode and refuses an existing path.
- `--root-name`: optional identifier for the root interface. Default `Root`. Applied through PascalCase.

Stdout, one line of JSON on success: `status` (`ok` or `findings`), `interfaces`, `optional_properties`, `findings` (a list of `{"code", "path"}` objects; `path` uses `$` for root, `.key` for a property, and `[]` for an array item).

Exit codes:

- 0: `status` is `ok`. No findings. The `.ts` file is written.
- 1: `status` is `findings`. The `.ts` file is written. Triage every finding.
- 2: usage or input error. Stderr carries one JSON line `{"error", "message"}`. No file is written.

Finding codes: `NULL_ONLY`, `EMPTY_ARRAY`, `MIXED_TYPES`, `NAME_COLLISION`.

Error codes (exit 2): `USAGE`, `INPUT_NOT_FOUND`, `INPUT_UNREADABLE`, `INPUT_TOO_LARGE`, `INVALID_UTF8`, `INVALID_JSON`, `TOO_DEEP`, `ROOT_NOT_OBJECT`, `EMPTY_ROOT_ARRAY`, `ROOT_NOT_OBJECTS`, `OUTPUT_EXTENSION`, `OUTPUT_EXISTS`, `OUTPUT_DIR_MISSING`, `OUTPUT_WRITE_FAILED`.

Shipped files: `scripts/json_to_ts.py` (the script), `fixtures/sample_records.json` (a 5-item text fixture for a smoke run), `LICENSE.txt`.

## Mapping rules the script applies

- Object keys become property names. Keys that are not plain identifiers are quoted.
- Interface names are PascalCase from the key. Array item interfaces use the singular of the key (suffix rule: `ies` becomes `y`, a trailing `s` is dropped unless the word ends in `ss`, `us` or `is`).
- A property is optional when any parent object lacks it.
- `null` is added as `| null` when the field also has a value.
- Integers and floats both map to `number`.
- An array with no items at a position emits `unknown[]`.
- An empty object emits an interface with no properties (`export interface X {}`).
- Properties appear in the order they are first seen across all items, so the field order in the output is not the order of the last item.
- Nested objects at the same key path are merged across all items before any name is chosen.
- Root arrays also emit `export type <Root>List = <Root>[];`.
- Values are never copied into the output or the summary. Only keys, types and paths appear.

## Refuse or stop when

- The root is a primitive, or an array with no items, or an array with any non-object item. Stop with the matching error code.
- The input is larger than 2 MB, is not UTF-8, or is not JSON.
- The output path exists, does not end in `.ts`, or sits in a missing folder. Never overwrite it and never write to the input path.
- The user asks for runtime validators, JSON Schema or a type for data you have not seen. This skill infers types from the sample only.
- The user asks for the output to be applied to live code without a finding review. Report the findings first.
