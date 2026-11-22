# json-to-yaml

## One line

Turns one JSON object or array into block-style YAML, quotes the strings a YAML reader would misread, and re-reads the result before writing it.

## What it does

The script reads one UTF-8 JSON file of at most 2 MiB and writes one new YAML file in 2-space block style. Strings that a YAML 1.1 reader would turn into booleans, nulls, numbers or dates are quoted, so the value `yes` stays text and `2024-01-01` stays text. Strings with a colon or a hash are quoted too. Multi-line strings become literal blocks when the layout allows it, and fall back to a single double-quoted line when it does not. Empty objects and arrays are written as `{}` and `[]`.

Before any file is created, the script parses its own YAML text with a small built-in reader and compares the result with the input, checking types and key order. If the comparison fails, nothing is written and the script reports the first differing path. The output file is created in exclusive mode, so an existing file is never replaced and the input path is never used as the output.

## When to use

Use it when a JSON config, an API payload or a test fixture needs a YAML copy, and a hand-written copy has already produced a quoting error. It is also useful when a reviewer wants proof that the YAML reads back to the same data.

## When not to use

Do not use it for YAML input, for YAML-to-JSON work, or for JSON whose top level is a single value rather than an object or array. It does not handle anchors, aliases, tags or comments, and it does not produce flow style. Do not use it to produce YAML for a parser that reads YAML 1.1 floats such as `1e+16`, since those read as text in that parser.

## Requirements

Python 3.9 or later, standard library only. No network access, no subprocess, no third-party packages. Run it from the skill folder with `python -I scripts/json_to_yaml.py <input-json> <output-yaml>`.

## Example

Output of one run on `fixtures/sample-input.json`, a 15-line JSON file that holds the string `yes`, a string with a colon, a date-like string, an empty list, a two-line string and a nested list. Stdout:

```
{"status": "ok", "written": true, "top_level_entries": 10, "output_lines": 16, "round_trip": "equal"}
```

Written file:

```
flag: "yes"
label: "build: stage #2"
count: 3
ratio: 0.5
empty_list: []
empty_object: {}
nothing: null
date_text: "2024-01-01"
summary: |
  first line
  second line
steps:
  - id: "1"
    note: plain
  - - nested
    - list
```

## Limits

The script checks that its own YAML reads back equal to the input. It does not check that other YAML parsers agree with it, and it does not check the meaning of the data or its fit to any schema. Keys are not sorted. Strings that cannot use a literal block are written double-quoted on one line, which can be long. Comments and anchors are not emitted. The depth limit of 100 levels and the 2 MiB input cap are working values chosen for this tool. Input must be UTF-8, and a file that fails the check writes no output at all, so a user who needs partial output must split the input themselves.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
