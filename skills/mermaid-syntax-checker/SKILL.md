---
name: mermaid-syntax-checker
description: Checks Mermaid diagram text in Markdown or .mmd files for common syntax errors before rendering, using a stdlib Python heuristic that prints line-level findings as JSON. Use when a Mermaid block in a document fails to render, when a diagram needs a quick pre-publish sanity pass, or when a flowchart, sequence, class, state, ER, gantt or pie block has unclosed brackets, quotes, subgraphs or arrows. Do not use for rendering diagrams, certifying output against the official Mermaid parser, or drawing new diagrams from scratch.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Mermaid syntax checker

This skill runs a line-level heuristic over Mermaid text. It is not the official Mermaid parser and it renders nothing. A clean result does not prove that a diagram renders. A finding can be a false positive, so every finding gets a verdict from you after you read the source line.

## Files

- `scripts/mermaid_check.py`: the checker (type A, stdlib only).
- `fixtures/smoke_input.md`: a two-block Markdown file with a missing `end` and an unclosed bracket. Use it to confirm the script runs on this machine.
- `LICENSE.txt`: Apache-2.0 text.

## Inputs

- One `.md` or `.markdown` file. Only fences that open with a line starting with three backticks and the word `mermaid` are read. Tilde fences and four-backtick fences are not recognized.
- Or one `.mmd` file. The whole file is one block.
- Maximum size 2 MB. UTF-8 only; a byte order mark is accepted.

## Workflow

1. Confirm the input. Output: the path and its extension. Stop if the extension is not `.md`, `.markdown` or `.mmd`.
2. Run the script with the command in the Script contract section. Output: the exit code and the JSON object.
3. For each finding, open the source file at the reported line and decide. Output: one row per finding with a verdict of `real` or `false positive` and a reason of at most 10 words.
4. Fix only the real findings, and change only the diagram block you were asked to check. Output: a list of changed lines, each as line number, old text, new text.
5. Run the script again. Repeat steps 3 and 4 for at most 3 rounds. Output: the final exit code and the round count.
6. Write the report in the Output contract section.

Verdict rules for step 3:

| Situation | Verdict |
|---|---|
| The reported line has an unmatched bracket or quote that renders wrong | real |
| The bracket or quote belongs to a multi-line label or a curly body across lines | false positive |
| The line is inside a tilde or four-backtick fence the script did not read | false positive, and say so in Not checked |

## Check codes and fixes

| Code | Rule (applies to) | Fix |
|---|---|---|
| UNKNOWN_HEADER | First token of the block is not in the script's fixed list of Mermaid diagram headers (for example flowchart, sequenceDiagram, stateDiagram, journey, mindmap, timeline, gitGraph, quadrantChart, sankey-beta; the full list is in the script). A header missing from that list is reported here even if Mermaid accepts it. | Check the header spelling. If the header is valid Mermaid, treat the finding as a false positive and say so. |
| EMPTY_BLOCK | Block has no line that is non-blank and not a comment (all types). | Delete the block. |
| FRONT_MATTER_NOT_CLOSED | Front matter opens with `---` and has no closing `---` (all types). | Add the closing `---`. |
| UNBALANCED_QUOTE | Odd count of double quotes on one line (all types). | Close the label quote. |
| UNBALANCED_BRACKET | Parentheses or square brackets not matched on the same line after quoted text is removed (all types). Curly braces are skipped for classDiagram, stateDiagram, stateDiagram-v2 and erDiagram because their bodies span lines. Depth above 64 is reported with the same code. | Balance the bracket pair. |
| ARROW_NO_TARGET | Line ends with an arrow operator, optionally followed by one `\|label\|` (flowchart, graph, sequenceDiagram, classDiagram, stateDiagram-v2). | Add the target node. |
| SUBGRAPH_NOT_CLOSED | A subgraph line has no later line that is exactly `end` (flowchart, graph). | Add `end` after the subgraph body. |
| END_WITHOUT_SUBGRAPH | An `end` line has no open subgraph (flowchart, graph). | Remove the extra `end`. |
| DUPLICATE_NODE_ID | Same node id defined with a bracket label twice and the label text differs (flowchart, graph). | Rename one id or make the labels equal. |
| LABEL_SPECIAL_CHARS | Unquoted node label contains one of `( ) [ ] { } \| ; # & < > "` (flowchart, graph). | Wrap the label in double quotes. |
| UNCLOSED_FENCE | Markdown mermaid fence reaches end of file with no closing three-backtick line. | Add the closing fence. |

## Thresholds (working values, not industry standards)

| Value | Meaning |
|---|---|
| 2 MB (2097152 bytes) | Input size cap. Larger files are refused with exit 2. |
| 64 | Bracket nesting depth cap per line. |
| 3 | Maximum fix-and-rerun rounds before you stop and report. |
| 0 / 1 / 2 | Exit codes: no findings, findings reported, usage or input error. |

## Script contract

- Command, run from the skill folder: `python -I scripts/mermaid_check.py <path-to-input>`
- Arguments: exactly one positional path. Any other count is a usage error.
- Stdout on success: one JSON object with keys `file`, `mode` (always `heuristic`), `blocks`, `finding_count`, `findings`. Each finding has `block` (1-based), `line` (1-based line in the input file), `code`, `message`.
- Stdout on bad input: one line of JSON with a single key `error`. Examples: input not found, wrong extension, over 2 MB, not UTF-8, no mermaid fence in a Markdown file.
- Exit codes: 0 no findings; 1 one or more findings; 2 usage or input error.
- The script writes no files and reads only the path it is given.

## Output contract

Use these headings in this order.

- `## Result`: one line, `exit N | blocks B | findings F | rounds R`.
- `## Findings`: a table with columns Block | Line | Code | Verdict | Fix applied. Write `none` if there are no findings.
- `## Not checked`: a bullet list that always contains these items: official Mermaid grammar; the header list is fixed and may lag Mermaid releases; rendering; node shape rules beyond bracket pairs; labels that span several lines; directive lines such as init comments; tilde or four-backtick fences.

## Refuse or stop when

- The input is not `.md`, `.markdown` or `.mmd`, is larger than 2 MB, or is not valid UTF-8. Report the error line and stop.
- A Markdown file contains no mermaid fence. Report that and stop.
- The user asks whether a diagram will render, or asks for an official parser verdict. Say that this skill cannot provide it and offer the heuristic result instead.
- The user asks you to certify that a diagram is correct. Refuse, and state that a clean result only means no heuristic finding was triggered.
- A requested fix would change anything outside the named diagram block. Stop and ask first.
- Three fix rounds have run and findings remain. Stop, list the remaining findings with their verdicts, and do not start a fourth round.
