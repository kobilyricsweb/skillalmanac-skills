# json-validate-format-repair

## One line

Checks a JSON file, pins the first syntax error to a line and column, pretty-prints valid JSON, and repairs six listed mistakes with a log of each repair.

## What it does

The skill wraps one Python script that uses only the standard library. It reads a single file of at most 2 MB, confirms the bytes are UTF-8, and tries to parse the text. A failing parse is reported with the line and column that Python's own JSON parser gives for the first error. Duplicate object keys and NaN or Infinity values are also rejected, because the default parser would accept them silently.

With the repair switch on, the script walks the text once and handles six patterns: single-quoted strings, line and block comments, trailing commas, unquoted keys, Python literals (True, False, None), and closing brackets missing at the end of the file. Each change is logged with its line number and fix code. Anything the rules cannot map, such as a bare word used as a value or a closing bracket that does not match, stops the run and is reported with its line. The repaired text is parsed again before anything is written.

When a valid result exists and an output name is given, the script writes a new file with two-space indentation. It never overwrites a file and never writes over the input.

## When to use

Use it when a pipeline or a developer has a JSON file that will not parse and the mistakes are the common, mechanical kind: a trailing comma left after the last item, a single-quoted string copied from a Python dictionary, a comment left in a config, or a missing closing brace at the end of a truncated export. It also fits a request to format a small test payload so a person can read it.

## When not to use

Do not use it to check data against a schema, to change values, or to keep comments in an output file. Do not use it on JSON5 or JSONC files where comments are meant to stay, on files above 2 MB, or on anything with a repair that depends on intent, such as a value that could be a string or a number.

## Requirements

Python 3.9 or later on the local machine. No packages, no network access, and no write permission needed outside the output path chosen by the user.

## Example

Input (the fixture shipped with the skill, 12 lines):

```
{
  "name": 'demo-app',
  "version": "1.0",   // semantic version
  "tags": ["json", "format"],
  "limits": {
    "max_items": 50,
    "pages": [1, 2, 3]
  },
  "active": true,
  "notes": "plain text value",
  "empty": null,
}
```

Command, run from a scratch folder with a relative output name:

```
python -I "<skill-folder>/scripts/json_fix.py" "<skill-folder>/fixtures/broken_12_lines.json" --repair --output repaired.json
```

Report on stdout, verbatim:

```
{"status": "repaired", "first_error": {"line": 2, "column": 11, "message": "Expecting value"}, "repairs": [{"line": 2, "fix": "single_quotes", "detail": "single-quoted string converted to double quotes"}, {"line": 3, "fix": "comment", "detail": "line comment removed"}, {"line": 11, "fix": "trailing_comma", "detail": "trailing comma removed"}], "refused": null, "output": "repaired.json"}
```

Contents of `repaired.json`, verbatim:

```
{
  "name": "demo-app",
  "version": "1.0",
  "tags": [
    "json",
    "format"
  ],
  "limits": {
    "max_items": 50,
    "pages": [
      1,
      2,
      3
    ]
  },
  "active": true,
  "notes": "plain text value",
  "empty": null
}
```

The exit code was 1, because the input needed repair.

## Limits

- It checks syntax only. It does not check that the output matches any schema, field meaning, or what the owner intended.
- Only the six listed fixes run. Anything else is refused, and the script does not guess.
- Output is rebuilt from parsed values, so number text can change (for example, 1.10 is written as 1.1), and comments and original spacing are lost.
- Duplicate keys are reported as invalid with no line number, because the parser does not report positions for them.
- If a write fails after the file is created, a partial file can remain at the output path.
- Error reports can echo up to 40 characters of a key or bare word, so a file holding secrets should not be pasted into a report.
- Visual equality, deliverability, semantics, and security of the data are not verified.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
