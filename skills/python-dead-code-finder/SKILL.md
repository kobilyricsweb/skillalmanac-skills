---
name: python-dead-code-finder
description: Lists Python functions, classes, methods and modules that no other file in a project folder references, using an ast scan that never runs the code. Use when a Python project has grown and unreferenced definitions need listing before a cleanup, or when you need to know whether a module is imported anywhere in the folder. Do not use for proving code is unused at runtime, for non-Python projects, or for judging public APIs that outside callers import.
license: Apache-2.0
compatibility: Python 3.9+ standard library only, no network access (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Python Dead Code Finder

This skill lists definitions whose names no file in a project folder uses. The scanner is [scripts/py_dead.py](scripts/py_dead.py). It parses each .py file with `ast` and never imports or runs project code. It reads names only, so every finding is a candidate for review, not a verdict.

## Workflow

1. **Check the input.** Confirm `<project-dir>` is an existing folder that holds .py files outside the skipped folders listed in the script contract. Output: one line, `input: <project-dir>, <N> .py files`. If the folder is missing or holds no .py files, stop (see Refuse / stop when).
2. **Run the scan.** Command: `python -I scripts/py_dead.py <project-dir>`. Add `--include-decorated` only when the user asks to see decorated functions and classes. Output: the raw JSON from stdout, plus the exit code (0, 1 or 2).
3. **Copy the exclusion counts.** Copy the four values under `excluded` into the Excluded table. Do not change them.
4. **Triage each finding.** Apply the triage table to every entry in `findings`, top row first; the first matching row decides. Output: one row per finding in the Findings table, with its Triage and Evidence.
5. **Apply the thresholds.** Compute the ratios in the threshold table. Set the status from the table. Output: the Status value and, when partial, one Open questions item for each threshold that tripped.
6. **Write the report.** Use the output contract below, in the heading order given. Output: the full report.

## Triage table

| Condition (first matching row applies) | Triage | Evidence to record |
|---|---|---|
| The name appears as a whole word in a non-.py file under `<project-dir>` (search with `grep -rwl --exclude=*.py "<name>" <project-dir>`) | Check first | File path of the first match |
| Kind is `method` and the name is one of: get, post, put, patch, delete, handle, clean, save, setUp, tearDown, dispatch, run, main (working value list) | Check first | "framework hook name" |
| Kind is `module` and the file is cli.py, app.py, wsgi.py, asgi.py, tasks.py or manage.py (working value list) | Check first | "possible launch target" |
| Anything else | Likely dead | "no textual match" |

Check-first rows are not removal approvals. Likely dead rows still need a second look before anything is deleted, because the scanner cannot see getattr calls or string-based loading in .py code.

## Threshold table

| Measure | Threshold | Result |
|---|---|---|
| findings / definitions | 30% or less | Status follows step 5 |
| findings / definitions | above 30% (working value) | Status partial; Open questions item: "name-based dispatch may hide references" |
| (dunder + test_prefix + decorated) / definitions | above 40% (working value) | Status partial; Open questions item: "most definitions were excluded by rule" |
| exit code | 0 or 1 | The scan ran; read the findings |
| exit code | 2 | Status stopped; report the error code |

Status values: `complete` when the scan ran, every finding has a triage value, and no threshold tripped (zero findings is complete); `partial` when any threshold tripped; `stopped` when exit code is 2.

## Output contract

The report uses these headings, in this order:

- `# Dead code report: <project-dir>`
- `## Summary`: table with columns `Key | Value`. Rows: Status, Files scanned, Definitions, Findings, Exit code.
- `## Findings`: table with columns `File | Line | Kind | Name | Triage | Evidence`. Kind is one of `module`, `function`, `class`, `method`. Triage is `Likely dead` or `Check first`. With no findings, one row reads `none` in the File column and dashes elsewhere.
- `## Excluded`: table with columns `Rule | Count`. Rows, in this order: `dunder`, `test_prefix`, `decorated`, `module_entry`.
- `## Open questions`: numbered list, or the word `None`.

## Script contract

- Command: `python -I scripts/py_dead.py <project-dir> [--include-decorated]`
- Arguments: one positional folder path. The optional flag `--include-decorated` also reports decorated functions and classes. Any other argument is a usage error.
- Definitions checked: module-level functions and classes, and functions directly inside a class body. Nested functions are not checked.
- A definition is used when its name appears in the scanned folder as a Load-context name, a Load-context attribute, an import name or module segment, or a string in an `__all__` list.
- Skipped folders: names starting with a dot, plus `__pycache__`, `venv`, `node_modules`, `build`, `dist` and `site-packages`.
- Module exclusions (counted under `module_entry`): `__init__.py`, `__main__.py`, `main.py`, `conftest.py`, `setup.py`, and files named `test_*.py` or `*_test.py`.
- Excluded definitions: dunder names (`__name__`-style), functions and methods whose name starts with `test_`, and decorated definitions unless `--include-decorated` is set.
- Stdout keys: `files_scanned` (integer), `definitions` (integer, counted before exclusions; includes one module entry per scanned .py file), `excluded` (object with `dunder`, `test_prefix`, `decorated`, `module_entry`), `findings` (list of objects with `file`, `line`, `kind`, `name`). Paths are relative to `<project-dir>` with forward slashes.
- Exit codes: `0` no findings; `1` one or more findings; `2` usage or input error.
- Error output: one line of JSON on stderr, `{"error": "<code>", "detail": "<text>"}`, with exit code 2. Codes:

| Code | Meaning |
|---|---|
| usage | Wrong arguments |
| not_a_directory | The argument is not a folder |
| no_python_files | No .py file outside the skipped folders |
| read_error | A .py file could not be read |
| file_too_large | A .py file is over 2 MB (2,097,152 bytes) |
| invalid_utf8 | A .py file is not valid UTF-8 |
| syntax_error | A .py file does not parse as Python, or contains a null byte |

One bad file stops the whole run with exit 2. The script does not skip files.

## Refuse / stop when

- The argument is missing, is not a folder, or holds no .py files. Stop and return the error code. Do not substitute a different scan.
- The script returns `file_too_large`, `invalid_utf8`, `syntax_error` or `read_error`. Stop, name the file from the detail text, and ask the user to fix or move it. Do not remove files or edit them to get a clean run.
- The user asks you to delete, move or edit flagged code. Refuse that request only. Keep the rest of the report, set Status to partial, and list the request under Open questions.
- The user asks whether code is unused at runtime, or asks for coverage data. Out of scope: say the scanner reads names in source only.
- The project is not Python. Stop; this scanner reads .py files only.

## Shipped files

- [scripts/py_dead.py](scripts/py_dead.py): the scanner described in the script contract.
- `fixtures/sample_project/main.py`, `fixtures/sample_project/utils.py` and `fixtures/sample_project/models.py`: a three-file smoke project with two unused functions and one unused class. Run the scanner on `fixtures/sample_project` to see the expected findings.
- [LICENSE.txt](LICENSE.txt): Apache-2.0 license text.
