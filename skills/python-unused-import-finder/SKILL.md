---
name: python-unused-import-finder
description: Finds unused, duplicate, star and shadowed imports in Python files by parsing them with ast, with no linter install and no code execution. Use when a Python file needs a quick import lint, when a change adds imports that may be dead, or when star imports must be listed before a refactor. Do not use for style checks, type checking, formatting, or editing or removing imports automatically.
license: Apache-2.0
compatibility: Requires Python 3.9+ with the standard library only and no network access (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Python unused import finder

Runs `scripts/py_imports.py` on the user's Python files and turns its JSON
findings into a triage table. The script parses each file with `ast`, never
runs it, and writes nothing.

## Workflow

1. **Intake.** Collect the path of each `.py` file the user wants checked.
   Output: a list of file paths. Pass files, not folders; a folder is refused
   with exit 2, so expand a folder into its `.py` files yourself first.
2. **Run the script.** Output: the raw JSON object from stdout.
   ```
   python -I scripts/py_imports.py <input-file.py> [<more-file.py> ...]
   ```
3. **Read the exit code.** Output: one status line.
   - 0: no findings. Report "no unused, duplicate, star or shadowed imports."
   - 1: findings present. Go to step 4.
   - 2: input or usage error. Stop and report the one-line JSON error.
4. **Triage each finding** with the decision table below. Output: one row per
   finding in the triage table of the output contract.
5. **Write the report** in the output contract. Output: the report only, with
   the raw JSON attached in a code block when the user asks for it.

## Decision table

| Code | noqa code | Rule the script applies | Action to recommend |
|---|---|---|---|
| `UNUSED_IMPORT` | F401 | The bound name is never loaded in the file and is not listed in a literal module-level `__all__`. | Delete the line, or list the name in `__all__` if it is a re-export. |
| `DUPLICATE_IMPORT` | F811 | The same module, imported name and alias appear twice in one scope. The later line is reported. | Delete the later line. |
| `SHADOWED_IMPORT` | F811 | The name is rebound later in the same scope and no load falls between the import and the rebinding. | Remove the import, or rename one of the two bindings. |
| `STAR_IMPORT` | F403 | `from <module> import *` appears. | Replace with the explicit names the file uses. |

Working values (not a published spec):

| Item | Value |
|---|---|
| Input size cap per file | 2 MB (2,097,152 bytes), enforced by the script |
| `# noqa` with no code list | Suppresses every code on the statement's lines |
| `# noqa: F401` (or F811, F403) | Suppresses only that mapped code on the statement's lines |
| Duplicate reporting | The first occurrence is kept; each later identical import is reported |

## Output contract

The script prints this JSON object to stdout:

- `tool` (always `py_imports`)
- `files_checked` (integer)
- `finding_count` (integer)
- `suppressed_by_noqa` (integer)
- `findings`: a list of objects with keys `file`, `line`, `code`, `name`,
  `module`, `detail`

The written report uses these headings in this order:

1. **Summary**: files checked, finding count, suppressed count, exit code.
2. **Triage table**: columns `File | Line | Code | Name | Action`, one row per
   finding, sorted as the script sorts them (file, line, code, name).
3. **Not checked**: the limits listed below that apply to this run.
4. **Open questions**: any finding the user should confirm before editing.

## Script contract (type A)

- Arguments: one or more paths to `.py` files. No options.
- Exit 0: the run completed and produced no findings.
- Exit 1: the run completed and produced one or more findings.
- Exit 2: usage error, a missing or non-file path, a path not ending in `.py`,
  a file over 2 MB, invalid UTF-8, or a Python syntax error. The error is one
  line of JSON on stderr, for example `{"error": "file not found: <path>", "exit": 2}`.
- Command line: `python -I scripts/py_imports.py <input-file.py> [<more-file.py> ...]`

## Refuse or stop when

- The path is a folder, not a `.py` file, or does not exist: exit 2, report the error.
- The file is over 2 MB or is not valid UTF-8: stop and ask for a smaller or re-encoded file.
- The file has a syntax error: stop. `ast` parses with the running Python version,
  so Python 2 code and code using a newer grammar than the user's Python fail.
- The user asks you to run the file's own code to check its imports: refuse.
  The script never executes code, and this skill does not run the user's program.
- The user asks you to edit, delete or auto-fix imports: refuse that clause only.
  Report the findings and the recommended action; the user makes the edit.
- The user asks you to install a linter in order to get these results: refuse.
  The point of this skill is that the check needs no install.

## Limits of the check

- A name that appears only inside a string annotation is not seen as a load, so
  its import can be reported as `UNUSED_IMPORT`. Check such names by hand.
- Loads are matched by name across the whole file, not per scope.
- `try: import x` / `except ImportError: x = None` fallbacks can be reported as
  `SHADOWED_IMPORT`. Review these, and add `# noqa: F811` where the fallback is intended.
- `__all__` is read only when it is a literal list or tuple of strings at module level.
- A noqa comment must sit on a line inside the import statement's line span.

## Shipped files

- `scripts/py_imports.py`: the checker described above.
- `fixtures/sample_a.py` and `fixtures/sample_b.py`: smoke inputs for the
  script. They are for checking the tool, not for the user's files. Running
  the script on both gives five findings, one suppressed by noqa, and exit 1.
- `LICENSE.txt`: the Apache-2.0 license text.
