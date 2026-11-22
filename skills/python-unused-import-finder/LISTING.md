# Python unused import finder

## One line

Reports unused, duplicate, star and shadowed imports in Python files using only the standard library and no code execution.

## What it does

The skill runs a small checker over the Python files you name. The checker parses each file with the standard `ast` module, so the file's code is never run and nothing has to be installed. It looks at every import statement, decides whether the bound name is ever loaded in the file, and flags four situations: a name that is never used, the same import written twice in one scope, a name rebound before anyone reads the import, and a star import whose names cannot be checked. Each finding carries the file, the line, a code, the name and a short reason. Lines marked with a matching noqa comment are skipped and counted separately, so the user can see how many findings were silenced. The output is one JSON object, and the skill turns it into a triage table with a recommended action for each row.

## When to use

Use it when a Python file has grown over time and nobody is sure which imports still matter, when a change adds several imports and you want a quick check before review, or when you need to list every star import before a refactor that replaces them. It also works on a folder's worth of files when you pass the paths explicitly, because the script takes any number of file arguments.

## When not to use

Do not use it for style rules, line length, formatting, type checking or auto-fixing. It does not edit files, and it does not check whether a string annotation mentions a name. It is not a replacement for a full linter in a project that already runs one, and it does not understand dynamic imports built with `importlib` or names created with `exec`.

## Requirements

Python 3.9 or newer, with the standard library only. No network access and no installed packages. The input must be a `.py` file of at most 2 MB, encoded as UTF-8, with valid Python syntax for the interpreter that runs the script.

## Example

Command, run from the skill folder against the two smoke fixtures:

```
python -I scripts/py_imports.py fixtures/sample_a.py fixtures/sample_b.py
```

Output, pasted from a real run:

```json
{
  "tool": "py_imports",
  "files_checked": 2,
  "finding_count": 5,
  "suppressed_by_noqa": 1,
  "findings": [
    {
      "file": "fixtures/sample_a.py",
      "line": 4,
      "code": "UNUSED_IMPORT",
      "name": "re",
      "module": "import re",
      "detail": "name never referenced"
    },
    {
      "file": "fixtures/sample_a.py",
      "line": 7,
      "code": "DUPLICATE_IMPORT",
      "name": "json",
      "module": "import json",
      "detail": "same import already at line 3"
    },
    {
      "file": "fixtures/sample_b.py",
      "line": 2,
      "code": "STAR_IMPORT",
      "name": "*",
      "module": "from os.path import *",
      "detail": "names cannot be checked; import the names explicitly"
    },
    {
      "file": "fixtures/sample_b.py",
      "line": 3,
      "code": "UNUSED_IMPORT",
      "name": "sys",
      "module": "import sys",
      "detail": "name never referenced"
    },
    {
      "file": "fixtures/sample_b.py",
      "line": 5,
      "code": "UNUSED_IMPORT",
      "name": "logging",
      "module": "import logging",
      "detail": "name never referenced"
    }
  ]
}
```

The process exits with code 1 because findings were reported.

## Limits

The checker does not verify behavior. It does not confirm that a removed import is safe at runtime, because it never imports or runs the module. It does not follow names through `from module import *`, so star imports are reported but their contents are not checked. It matches loads by name across the whole file rather than per scope, so a name used in one function can hide an unused import of the same name in another. A name used only inside a string annotation is not counted as a use. A `try` import with an `except ImportError` fallback can be reported as shadowed. It also does not check packaging, circular imports, deliverability of any output, or the semantics of the code around the imports.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
