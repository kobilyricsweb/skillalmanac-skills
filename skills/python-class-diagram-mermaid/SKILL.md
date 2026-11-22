---
name: python-class-diagram-mermaid
description: Generates a Mermaid classDiagram from Python source files. Use when a user asks for a UML or class diagram of Python code, wants the inheritance, class attributes, or methods of a Python module mapped out, or needs composition hints taken from type annotations. The script parses each file with the ast module and never imports or runs it. Do not use for other programming languages, runtime introspection of live objects, call-flow or sequence diagrams, or edits to the source files.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Python class diagram in Mermaid

Use this skill to turn one or more `.py` files into a Mermaid `classDiagram`. The script
reads module-level classes only. It never imports, executes, or modifies the inputs.

## Workflow

1. Check intake. You need one or more file paths ending in `.py`, each 2 MB or smaller, saved as UTF-8.
   Output: the list of input paths, with the count of files.
2. Pick the output name. `--out` is optional. If you use it, the name must end in `.mmd` and must not
   already exist. Output: the chosen `<output-file.mmd>` path.
3. Run the script (see the command line below). Output: the Mermaid text on stdout, and the same text in
   `<output-file.mmd>` when `--out` is given.
4. Branch on the exit code. Exit 0: go to step 5. Exit 1: at least one file failed to parse. Each failure
   appears as a `% SYNTAX_ERROR` line. The diagram still contains the other files. Report the file name and
   line, and ask the user to fix the file. A rerun needs a new `--out` name, because exit 1 still writes the
   file. Exit 2: stop and report the error code from the table in the output contract.
5. Verify the counts. Count lines that start with `class ` and compare with `classes=`. Count lines that start
   with four spaces (attributes plus methods) and compare with the sum of `attributes=` and `methods=`. Count
   lines that contain ` *-- `, ` o-- `, or ` <|-- ` and compare with `relations=`. Any mismatch is a script
   defect: stop and report it. Output: "counts verified" or the mismatch.
6. Deliver the diagram in a fenced `mermaid` block, followed by the summary line and any `SYNTAX_ERROR` lines.

## Rules and thresholds

| Item | Rule | Value |
|---|---|---|
| Input size | Largest accepted file | 2 MB (2097152 bytes) |
| Input name | Must end in `.py` | exact, case-insensitive |
| Encoding | UTF-8; a byte order mark is accepted | strict decode |
| Classes read | Module-level `class` statements only | depth 0 |
| Member visibility | Dunder `__x__` gives `+`; mangled `__x` gives `-`; `_x` gives `#`; other names give `+` | fixed |
| Static or class method | `@staticmethod` or `@classmethod` adds `$` after the parentheses | fixed |
| Abstract method | `@abstractmethod` adds `*`; `$` wins when both apply | fixed |
| Method arguments | Drop a first parameter named `self` or `cls`; list positional and keyword-only names; no defaults, no `*args`, no `**kwargs` | fixed |
| Attributes | Class-level annotated or plain name assignments; instance attributes only when annotated as `self.x: T` | fixed |
| Type text | `[` and `]` become `~`; `\|` becomes ` or `; characters outside letters, digits, `_ . ~ ,` and space are removed | fixed |
| Inheritance | `Base <\|-- Child` for each base except `object`; a base not defined in the inputs appears as a stub | fixed |
| Composition | `Owner *-- Target : attr` when the annotation is a local class, or `Optional[Target]` | fixed |
| Aggregation | `Owner o-- Target : attr` when a local class name appears elsewhere in the annotation, such as `List[Target]` or a quoted forward reference | fixed |

## Output contract

Stdout, in this order:

1. Line 1: `classDiagram`
2. Line 2: `% py_classes files=<N> classes=<N> attributes=<N> methods=<N> relations=<N> syntax_errors=<N>`
3. Zero or more lines: `% SYNTAX_ERROR file=<basename> line=<n>` (one per file that failed to parse)
4. One block per class, in input order. A class with members is `class <Name> {`, then indented members, then `}`. A class without members is one line, `class <Name>`.
5. Relation lines, sorted as text.

Errors go to stderr as one JSON line: `{"status": "error", "code": "<CODE>", "message": "<text>"}`.

| Code | Exit | Meaning |
|---|---|---|
| USAGE | 2 | Bad arguments, or `--out` does not end in `.mmd` |
| INPUT_MISSING | 2 | An input path is not a file |
| INPUT_NOT_PY | 2 | An input does not end in `.py` |
| INPUT_TOO_LARGE | 2 | An input is larger than 2 MB |
| INPUT_NOT_UTF8 | 2 | An input is not valid UTF-8 |
| OUTPUT_EXISTS | 2 | The `--out` path already exists; nothing is written |
| OUTPUT_WRITE_FAILED | 2 | The `--out` path cannot be created, for example a missing folder |
| SYNTAX_ERROR | 1 | A file failed to parse; reported as a stdout comment line, not on stderr |

## Script contract

- Script: `scripts/py_classes.py`
- Arguments: one or more `<input-file>` paths, then optional `--out <output-file.mmd>`.
- Exit codes: 0 ok; 1 at least one `SYNTAX_ERROR`; 2 usage or input error.
- Command line:
  `python -I scripts/py_classes.py <input-file> [<input-file> ...] [--out <output-file.mmd>]`
- Shipped with this skill: `fixtures/geometry.py` and `fixtures/circle.py` (text-only smoke inputs),
  `LICENSE.txt`.

## Refuse or stop when

- The user pastes code instead of giving saved `.py` files. Stop and ask for the files, each named and
  saved with a `.py` extension.
- A path is a notebook, a compiled file, an archive, or any other non-`.py` file (INPUT_NOT_PY). Ask for the
  source file.
- The `--out` name already exists. Choose a new name. Never delete or overwrite the existing file.
- The user asks for classes that exist only at runtime, such as classes built inside functions or `if`
  blocks, or classes created by metaclasses. Refuse that clause. The tool does not list them. Deliver the
  module-level diagram, set status partial, and list the refused classes under Open questions.
- The user asks for a diagram of other languages, of live objects, or of call flow. Refuse that clause and
  keep any Python clause that remains.
