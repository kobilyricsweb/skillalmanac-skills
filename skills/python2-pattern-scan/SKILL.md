---
name: python2-pattern-scan
description: Scans one .py file for Python 2 only constructs and lists each with its line and Python 3 replacement. Use when a Python 2 to 3 migration needs an inventory of old print, except X, e, backtick, exec, has_key, xrange, raw_input, unicode, long or octal usage before any edits. Do not use for rewriting or converting files, dependency compatibility checks, whole-repository runs, or Python 3 linting and type checking.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# python2-pattern-scan

Type A skill. The script `scripts/py2_scan.py` does the detection. The agent runs it, checks the flags it returns, verifies the heuristic rows, and writes the inventory. The script reads the input and never edits it.

## Workflow

1. Get the input. Ask the user for the path of one `.py` file. Use the placeholder `<input-file>` in every command shown to the user. Output: the file name, or a stop if the user gave a folder or a non-.py path.
2. Run the scan: `python -I scripts/py2_scan.py <input-file>`. Output: the JSON object from stdout (exit 0 or 1), or the one-line JSON error from stderr (exit 2).
3. Read the two flags `ast_parsed` and `masking`. Output: one line stating both values and the rule from the threshold table that applies.
4. Map each finding to its row in the code table. Output: one table row per finding, in the order the script returns them.
5. Verify the rows that need a source check: every PY2-009 and PY2-011 row, and every row when `masking` is `none`. Open the cited line in the source. Output: a verdict per row, either `confirmed` or `rejected: <reason>`.
6. Write the report in the output contract. Output: the report only. Do not write a converted copy of the file.

## Code table

| Code | Construct | How it is detected | Python 3 replacement |
|---|---|---|---|
| PY2-001 | print statement (`print x`, `print >>f, x`) | masked text | `print(...)` function call |
| PY2-002 | `except X, e:` clause | masked text | `except X as e:` |
| PY2-003 | backtick repr | masked text | `repr(expr)` |
| PY2-004 | exec statement (`exec code in ns`) | masked text | `exec(code, namespace)` |
| PY2-005 | `dict.has_key(k)` call | masked text | `k in mapping` |
| PY2-006 | `xrange` name | ast when parsed, otherwise masked text | `range` |
| PY2-007 | `raw_input` name | ast when parsed, otherwise masked text | `input` |
| PY2-008 | `unicode`, `long`, `basestring` name, or `L` suffix on an integer literal | name: ast or masked text; suffix: masked text | `str`, `int`, `str`; drop the L suffix |
| PY2-009 | integer division risk (working heuristic) | masked text; both operands are integer literals, `len()` or `int()` calls | `//` for floor, or `float(a) / b` for true division |
| PY2-010 | old-style octal literal (`0777`) | masked text | `0o` prefix, for example `0o777` |
| PY2-011 | implicit relative import | import line; module is a `.py` file or a package with `__init__.py` in the input folder; skipped when `from __future__ import absolute_import` is present | `from . import mod` or `from .mod import ...` |

## Decision thresholds

| Condition | Action |
|---|---|
| Exit 0 | Report zero findings. Say the scan has the limits listed below, so zero is not proof of a clean file. |
| Exit 1 | Report every finding. Do not drop a row. |
| Exit 2 | Report the error code and stop. Do not guess findings. |
| Input larger than 2,097,152 bytes | Exit 2 with `too_large`. Ask for a smaller file. Do not split the file yourself. |
| `ast_parsed` is false | Name rows PY2-006 to PY2-008 came from masked text. Check each one in the source (working value). |
| `masking` is `none` | The tokenizer failed. Strings and comments may be reported. Verify every row by hand. |
| PY2-009 row | Keep it only when both operands are integer literals, `len()` or `int()` calls (working value). Check the types before calling it a risk. |
| PY2-011 row | Keep it only when the sibling module exists in the input folder, which the script already checked. Confirm the import is not a stdlib module that shadows it. |

## Output contract

Script stdout, one JSON object with these keys:

- `tool`, `version`, `file` (base name only)
- `ast_parsed` (boolean), `masking` (`tokenize` or `none`)
- `count` (integer), `findings` (list of objects with `line`, `code`, `construct`, `replacement`)

Script stderr on exit 2, one JSON object: `error` (one of `usage`, `file_missing`, `not_python_file`, `file_unreadable`, `too_large`, `not_decodable`) and `message`.

Report, Markdown, with these headings in this order:

1. `## Summary`: a key-value list with File, Ast parsed, Masking, Findings, Exit code.
2. `## Findings`: a table with columns Line, Code, Construct, Python 3 replacement, Verdict. Sort by Line, then Code. One row per finding.
3. `## Open questions`: a numbered list, or the word `None`.

## Refuse / stop when

- The input is a folder, or its name does not end in `.py` (for example `.pyc`, `.pyw`, `.ipynb`). Exit 2 applies; stop.
- The user asks you to rewrite, convert or patch the file. This tool reports only. Say so, and offer the replacement list from the code table.
- The file is over 2,097,152 bytes or cannot be decoded as UTF-8 or as its declared coding.
- The user asks for a repository-wide conversion or a dependency compatibility check. The tool scans one file per run. Say so and stop.
- The user asks for Python 3 linting, type checking or runtime testing. These are outside this skill.
- Do not copy source lines into the report. The script does not echo them, and the report should not either.

## Script contract

- File: `scripts/py2_scan.py`, Python 3.9+ stdlib only.
- Command: `python -I scripts/py2_scan.py <input-file>`
- Arguments: exactly one path to a `.py` file. The file is opened read-only, up to 2 MB.
- Exit 0: no findings. Exit 1: one or more findings, JSON on stdout. Exit 2: usage or input error, one-line JSON on stderr.
- Detection: strings and comments are blanked with `tokenize` before pattern checks. One finding per occurrence. No output file is written.

## What the scan does not verify

- It does not infer types, so PY2-009 is a heuristic over literals and calls only.
- It does not follow imports or read other files except sibling modules for PY2-011.
- It does not check that a replacement keeps behavior, handles bytes versus text, or runs under Python 3.
- It does not see f-string contents on Python 3.12 and later, where tokenize splits them.

## Shipped files

- `scripts/py2_scan.py`: the scanner described above.
- `fixtures/py2_sample.py.txt`: a 25-line Python 2 sample with seven planted constructs, used for the smoke run. Copy it to a file ending in `.py` before scanning, because the script accepts only `.py` input.
- `LICENSE.txt`: Apache-2.0 license text.
