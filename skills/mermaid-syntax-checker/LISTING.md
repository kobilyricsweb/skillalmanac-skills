# Mermaid syntax checker

## One line

Heuristic, stdlib-only checker that scans Mermaid blocks in Markdown or .mmd files and prints line-level findings as JSON.

## What it does

The script pulls each fenced mermaid block out of a Markdown file, or treats a whole .mmd file as one block, and then runs line-level checks. It reads the diagram header and flags unknown types. It counts double quotes and brackets on each line, with quoted text removed first. It checks that every flowchart subgraph has a closing end and that every end belongs to a subgraph. It flags arrows that stop at the end of a line with no target, node ids that are defined twice with different labels, and unquoted flowchart labels that contain characters Mermaid tends to misread. Each finding carries the block number, the file line, a code and a short message. The script does not render anything and does not try to reproduce the official grammar, so the output is a list of suspects for a person to read, not a verdict on the diagram.

## When to use

Use it when a Mermaid block in a document fails to render and you want the likely line before opening a renderer. It also fits a quick pass over several diagrams before a page is published, because it reads every block in one run and reports the block and line for each finding.

## When not to use

Do not use it to decide whether a diagram will render, and do not treat a clean result as proof that it will. It is not a substitute for the official Mermaid parser. It does not create diagrams, and it does not change files.

## Requirements

Python 3.9 or newer, standard library only. No network access and no other packages. The script reads one input path and writes nothing.

## Example

Smoke run on `fixtures/smoke_input.md`, which holds one flowchart with an unclosed subgraph and one flowchart with an unclosed square bracket:

```
{
  "file": "fixtures/smoke_input.md",
  "mode": "heuristic",
  "blocks": 2,
  "finding_count": 3,
  "findings": [
    {
      "block": 1,
      "line": 8,
      "code": "SUBGRAPH_NOT_CLOSED",
      "message": "subgraph has no matching 'end'"
    },
    {
      "block": 2,
      "line": 17,
      "code": "UNBALANCED_BRACKET",
      "message": "unclosed '['"
    },
    {
      "block": 2,
      "line": 17,
      "code": "LABEL_SPECIAL_CHARS",
      "message": "unquoted label of X contains > [; wrap the label in double quotes"
    }
  ]
}
```

## Limits

Multi-line labels are not joined, so a label split across lines can produce a false bracket finding. Tilde fences and four-backtick fences are not read. Curly braces are not counted for class, state and ER blocks because their bodies span lines. Node shapes are recognized by their bracket pairs only, and sequence, gantt and pie blocks get only the header, quote and bracket checks. A finding is a prompt to read the line, not a proof of a fault.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
