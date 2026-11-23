# python2-pattern-scan

## One line

Scans one .py file for Python 2 only syntax and builtins and lists each hit with its line and its Python 3 replacement.

## What it does

The script opens one Python source file read-only and blanks out string literals and comments using the standard tokenizer, so a word such as print inside a docstring is not reported. It then checks each remaining line against eleven construct families, coded PY2-001 through PY2-011: print statements, except clauses with a comma, backticks, exec statements, dict.has_key calls, xrange, raw_input, the unicode, long and basestring names, the L suffix on integer literals, integer division of literal operands, old-style octal literals, and implicit relative imports of sibling modules. When the file parses under the running Python 3, the builtin names are checked through the syntax tree instead of through text. The output is one JSON object with a line, code, construct and replacement for each occurrence. The script never edits or writes files.

## When to use

Use it at the start of a Python 2 to 3 port, when you need a dated inventory of old constructs in one module before any edits. The line numbers tell you where each change must go, which helps split the work by module. Run it once per file, on each module of a package.

## When not to use

Do not use it to convert code, to decide whether a third-party library runs on Python 3, to lint a whole repository, or to certify a file as Python 3 clean. The integer division rule is a heuristic over literal operands and length or int calls only, because the script does not infer types.

## Requirements

Python 3.9 or newer, standard library only. No network access, no third-party packages, and no subprocess calls. The input must be one file whose name ends in .py, no larger than 2 MB, and decodable as UTF-8 or as the coding it declares.

## Example

Command, run on a 25-line Python 2 sample copied to a file ending in .py:

```
python -I scripts/py2_scan.py <input-file>
```

Output, verbatim, exit code 1:

```
{"tool": "py2_scan", "version": "0.1.0", "file": "py2_sample.py", "ast_parsed": false, "masking": "tokenize", "count": 7, "findings": [{"line": 11, "code": "PY2-006", "construct": "xrange", "replacement": "range"}, {"line": 13, "code": "PY2-005", "construct": "dict.has_key() call", "replacement": "key in mapping"}, {"line": 14, "code": "PY2-001", "construct": "print statement", "replacement": "print(...) function call"}, {"line": 16, "code": "PY2-007", "construct": "raw_input", "replacement": "input"}, {"line": 17, "code": "PY2-002", "construct": "except clause with comma", "replacement": "except IOError as err:"}, {"line": 19, "code": "PY2-003", "construct": "backtick repr", "replacement": "repr(value)"}, {"line": 20, "code": "PY2-008", "construct": "unicode type", "replacement": "str"}]}
```

## Limits

Findings list occurrences. They are not a verdict on behavior. The scan does not infer types, does not follow imports beyond sibling modules, does not run the code, and does not check that a replacement keeps the same results. Changes between bytes and text are not detected. On Python 3.12 and later the tokenizer splits f-string contents, so strings inside them may be scanned with less accuracy. When tokenization fails the output reports masking none, and strings or comments may then produce false positives that the reader must check by hand.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
