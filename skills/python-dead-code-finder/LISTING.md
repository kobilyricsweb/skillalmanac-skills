# Python Dead Code Finder

## One line

Lists Python functions, classes, methods and modules that no other file in a project folder references.

## What it does

The skill runs `scripts/py_dead.py` against a project folder. The script parses every .py file with Python's ast module and collects the names used anywhere in that folder: plain name loads, attribute loads, import names and module segments, and strings inside an `__all__` list. Each top-level function, class, class method and module whose name never appears in that set is reported with its file and line. Dunder names, functions whose names start with test_, and decorated definitions are left out unless the caller adds `--include-decorated`. Entry-point and test modules are never reported as modules. The scanner never imports or runs the code, so a project with a broken import still scans, provided every file parses.

The output is JSON. It holds the file count, the definition count, a count for each exclusion rule and a sorted list of findings. The skill then sorts each finding into Likely dead or Check first. The triage step searches non-Python files in the same folder for the name, which catches configuration files, templates and route tables that load a name as text. Thresholds on the ratio of findings to definitions decide whether the report is complete or partial. The output is a report a reviewer can read line by line before any deletion happens.

## When to use

- A Python repository has grown over several years and you want a first list of candidates before a cleanup pass.
- You are about to delete a module and want to see whether any file in the folder imports its name.
- You want a repeatable scan you can rerun after each cleanup batch and compare by eye.

## When not to use

- You need proof that code never runs in production. Use runtime coverage tooling for that question.
- The project loads code by string names through getattr, plugin registries or configuration files that you cannot review. The scanner will miss those references or report them as unused.
- You need to judge a public library API that outside users import. The scanner sees only the folder it is given.

## Requirements

Python 3.9 or newer, standard library only. No network access. Run the command from the skill folder so the relative script path resolves, or give the full path to `scripts/py_dead.py`.

## Example

Command: `python -I scripts/py_dead.py fixtures/sample_project` (exit code 1, three findings):

```json
{
  "files_scanned": 3,
  "definitions": 10,
  "excluded": {
    "dunder": 0,
    "test_prefix": 0,
    "decorated": 0,
    "module_entry": 1
  },
  "findings": [
    {
      "file": "models.py",
      "line": 11,
      "kind": "class",
      "name": "LegacyExporter"
    },
    {
      "file": "utils.py",
      "line": 8,
      "kind": "function",
      "name": "old_parser"
    },
    {
      "file": "utils.py",
      "line": 12,
      "kind": "function",
      "name": "unused_helper"
    }
  ]
}
```

## Limits

- Matching is by name only. A name used anywhere in the folder counts as used, even when it belongs to a different class. A recursive function that only calls itself also counts as used.
- Method names such as run or save match any attribute with that name, so a dead method can stay hidden behind a live method of the same name.
- Definitions inside if or try blocks at module level, and functions nested inside other functions, are not checked.
- One file that cannot be read, decoded or parsed stops the whole run with exit code 2. The script does not skip files.
- Each .py file is capped at 2 MB. Larger files stop the run.
- The scanner does not follow string references, getattr calls, entry points declared in packaging metadata or framework routing tables.
- The 30 percent and 40 percent thresholds are working values, not published standards.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
