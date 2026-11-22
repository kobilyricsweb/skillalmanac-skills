---
name: control-flow-mermaid-from-code
description: Draws the control flow of one supplied function as a Mermaid flowchart (TD) with numbered nodes, Yes and No decision edges, and a coverage table that maps each source line to its node. Use when a user asks for a flowchart from code, wants to see the if, loop, early return or raise paths of one function, or needs to check which branches a diagram covers. Do not use for whole repositories, files or folders, sources over 80 lines, call graphs across functions, architecture diagrams, or tracing of runtime behavior.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Control flow to Mermaid from code

Draws one function as a Mermaid flowchart, then proves the diagram covers the function with a line-by-line table and a branch count. Run the steps in order. Do not skip step 8.

## Workflow

1. **Intake.** Required facts: (a) the source text of one function, (b) its language. If the language is not stated, infer it only from unambiguous syntax: `def ...:` means Python; `function` or `=>` means JavaScript or TypeScript. If either fact is missing or the language is ambiguous, stop and follow the stop rule below. Output: the language name.
2. **Scope check.** Apply the limits in the table below. Output: pass, partial, or refused.

   | Check | Limit | Result when exceeded |
   |---|---|---|
   | Lines in the function, counting blank and comment lines | 80 | refused |
   | Files or folders supplied | 1 file, 1 function | refused |
   | Top-level functions in the supplied text | 1 | partial; ask which one to draw; draw none |
   | Nested functions and lambdas | not drawn | note under Open questions |

3. **Number the lines.** Use the line numbers of the supplied text, with the first line as 1. Comment and docstring lines keep their numbers but get no node. Output: the numbered source, used in step 7.
4. **List the branch points.** Apply the rules table below to every line. Output: the list of branch points, each with its line number.

   | Source construct | Node drawn | Counts as branch |
   |---|---|---|
   | `if`, `elif`, `else if` header | diamond; Yes into the body, No to the next test or the skip path | yes, one per header |
   | `else` | no node; it is the No edge of its `if` | no |
   | `for`, `while`, loop header | diamond; Yes into the body, No out of the loop | yes, one per header |
   | `try` with `except` or `catch` | diamond "error raised", Yes into the handler, No on the normal path | yes, one per handler |
   | `return`, `raise`, `throw`, `continue`, `break` that is not the last statement of the function | stadium terminal | yes, as an early exit |
   | last `return` of the function | stadium end node | no |
   | assignment, call, expression statement | rectangle; consecutive ones share one node | no |

5. **Assign node ids.** Number nodes N1, N2, and so on, in order of the first source line each node covers. The start node is N1 and covers the function's first line.
6. **Write the diagram.** Use these rules without exception:
   - First line is `flowchart TD`.
   - Start, exit and end nodes use `N1(["text"])`. Decisions use `N2{"text"}`. Processes use `N4["text"]`.
   - Quote every label. Write comparisons in words ("at most 0", "below", "equals", "above"). Never put `<`, `>`, `&`, `#`, `;` or a double quote inside a label.
   - Decision edges carry labels: `N2 -- "Yes" --> N3` and `N2 -- "No" --> N4`.
   - Each loop body end and each `continue` points back to the loop header.
   - Every path ends at a terminal node.
7. **Build the coverage table.** One row per source line that has a node, in line order. Two lines that share a node get two rows with the same node id. Kind is one of `start`, `decision`, `process`, `exit`, `end`. Branch is `yes` for decision and exit rows and `no` for all others.
8. **Count and check.** Branches found is the number of branch points from step 4. Branches drawn is the number of diamonds plus exit terminals in the diagram. The two numbers must be equal, and the number of `yes` rows in the coverage table must equal both. If they differ, fix the diagram once and recount. If they still differ, set Status to `partial` and state both numbers and the gap under Open questions.

## Status values

| Status | When |
|---|---|
| `complete` | All steps finished and the counts match |
| `partial` | A required intake fact is missing, two or more top-level functions are supplied, or the counts still differ after one fix |
| `refused` | The input is a repository, a folder, several files, or a function over 80 lines |

## Stop and refuse rules

- Stop (status `partial`, no diagram, no table) when the source text or the language is missing or ambiguous. Hand back a numbered question list under Open questions, for example: "1. Paste the source of the one function to draw." and "2. Which language is it written in?"
- Refuse (status `refused`) when the input is a repository, a folder, or more than one file.
- Refuse when the function is more than 80 lines. Ask for one function of 80 lines or fewer.
- Refuse requests for call graphs, architecture diagrams, or runtime traces. Say that this skill draws one function's control flow only.
- Partial when two or more top-level functions are supplied. Ask which one to draw.

## Fixing a count mismatch

| Symptom | Usual cause | Fix |
|---|---|---|
| Found is higher than Drawn | An early exit or a loop header was left out of the diagram | Add the missing exit terminal or diamond with its Yes and No edges |
| Drawn is higher than Found | A `continue` or `break` was drawn as a process node | Redraw it as a stadium exit and mark it `yes` in the table |
| Coverage `yes` rows are fewer than Found | A header line has no row in the table | Add a row for the header with its node id |
| Two rows show one node id but different kinds | A process node was merged across a branch point | Split the node at the branch point |

## Output contract

Five level-2 sections, in this order:

1. `## Status` holds one word: `complete`, `partial` or `refused`.
2. `## Diagram` holds one fenced block tagged `mermaid`. Write `None.` when no diagram was drawn.
3. `## Coverage` holds a table with the columns `Line | Node | Kind | Branch`.
4. `## Branch count` holds three lines: `Found: N`, `Drawn: N`, and `Match: yes` or `Match: no`.
5. `## Open questions` holds a numbered list. Write `None.` when there are no questions.

## Files shipped with this skill

- `SKILL.md`: this procedure and output contract.
- `LICENSE.txt`: Apache License 2.0 text.
- [fixtures/ship_status.txt](fixtures/ship_status.txt): a 25-line Python sample with an `if`, a `for` loop and early returns. It is plain text, not runnable as a module, and serves as the smoke input.
