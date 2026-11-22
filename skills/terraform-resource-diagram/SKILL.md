---
name: terraform-resource-diagram
description: Draws a Mermaid graph LR diagram of Terraform resource and data blocks and the type.name references between them, listing unresolved references and cycles. Use when a user asks to generate a diagram from Terraform code, map which resources depend on which, or find references to resources that are not declared in the scanned .tf files. Do not use for validating HCL, running terraform plan, reading state, checking provider schemas, or diagramming cloud accounts that have no .tf files.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Terraform resource diagram

This is a script-backed skill. `scripts/tf_graph.py` scans `.tf` text with regular
expressions and prints a Mermaid `graph LR` diagram. The agent runs the script, checks
the findings it prints, and writes the reply. The script does not parse HCL fully and
does not validate Terraform. A reference is any `type.name` or `data.type.name` pattern
inside a block body where the type has at least one underscore.

## Workflow

1. Confirm the input. It must be one `.tf` file, or a directory that directly contains
   `.tf` files (not recursive). Output: the input path and the number of `.tf` files.
2. Check the size. All `.tf` files together must be 2 MB or less. Output: the total
   size in bytes, or a stop.
3. Choose the output mode. Default is stdout only. If the user wants a file, use
   `--out` with a new path that does not exist yet. Output: the mode and the path.
4. Run the command in the Script contract section. Output: the exit code and the
   Mermaid text from stdout, copied unchanged.
5. Sort every `%%` line in the output by its code using the Findings table. Output:
   one row per finding.
6. Count the drawn nodes (`nN["..."]` lines) and drawn edges (`-->` and `-.->` lines).
   Output: the two counts.
7. Write the reply using the Output contract. Output: the reply.

## Thresholds

| Item | Value | Source |
|---|---|---|
| Maximum total input size | 2 MB (2,097,152 bytes), all `.tf` files together | working value |
| Maximum drawn nodes | 150 blocks, in source order; the rest are omitted and reported as L001 | working value |
| Resource node key | `type.name` | fixed by script |
| Data node key | `data.type.name` | fixed by script |
| Reference type rule | at least one underscore in the type, for example `aws_vpc` | fixed by script |
| Exit 0 | no findings | script |
| Exit 1 | one or more findings were printed; the diagram is still printed | script |
| Exit 2 | usage or input error; nothing is printed to stdout | script |

## Findings (printed as `%%` lines under `graph LR`)

| Code | Meaning | Next step |
|---|---|---|
| D001 | The same key is declared twice; the second block is ignored | Ask the user which block is current |
| U001 | A reference points to a key that is not declared in the input; drawn as a dashed node ending in "(unresolved)" | Say the target may live in another module or file not scanned |
| C001 | A reference cycle, printed as `a -> b -> a` | Report it; Terraform rejects real dependency cycles, so check the references |
| L001 | More than 150 blocks; only the first 150 are drawn | Ask for a narrower directory |
| N001 | No resource or data blocks were found | Check the input path and the file contents |

## Errors (exit 2, one line of JSON on stderr)

| Code | Meaning |
|---|---|
| usage | Wrong arguments; `--out` must be followed by a path |
| input_missing | The input path does not exist |
| not_tf_file | The input is a file without a `.tf` extension |
| no_tf_files | The directory holds no `.tf` files |
| input_too_large | Total input is over 2 MB |
| unreadable | A file could not be read |
| invalid_utf8 | A file is not valid UTF-8 |
| unbalanced_braces | A block has no closing brace |
| output_exists | The `--out` path already exists; nothing is overwritten |
| output_is_input | The `--out` path is an input file, or a `.tf` file inside the input directory |
| output_dir_missing | The parent folder of the `--out` path does not exist |
| output_error | The output file could not be created |

## Script contract (type A)

- Command: `python -I scripts/tf_graph.py <input-file-or-dir> [--out <output-file>]`
- Arguments: the first argument is the input (one `.tf` file or a directory). `--out`
  is optional and writes the same text to a new file.
- Stdout: Mermaid text only. Line 1 is `graph LR`, then `%%` finding lines, then node
  lines `  nN["type.name"]`, unresolved node lines `  uN["type.name (unresolved)"]`, and
  edge lines `  nA --> nB` or `  nA -.-> uN`.
- The output holds block keys and finding codes only. Attribute values are never printed.
- Exit codes: 0 no findings, 1 findings printed, 2 usage or input error.
- Writes only to the `--out` path, and only when that path is new.

## Output contract

Reply with these headings in this order:

1. `## Diagram`: the Mermaid text from stdout in one fenced `mermaid` block, unchanged.
2. `## Findings`: a table with the columns Code | Detail | Next step. If there are no
   findings, one row: `none | - | -`.
3. `## Scope`: a table with the columns Input | Files | Nodes drawn | Edges drawn,
   one row.
4. `## Open questions`: a numbered list of anything the user must decide (for example,
   narrowing a directory after L001). Write `none` if there are none.

## Refuse or stop when

- The input is `.tf.json`, `.hcl`, a plan file, a state file, or any other format. Stop.
- The total input is over 2 MB. Stop and ask for a narrower directory.
- The user asks to validate the code, run `terraform plan`, read state, or check
  provider schemas. Refuse that part; this skill reads text only.
- The `--out` path already exists. Never overwrite; ask for a new name.
- The script exits 2. Report the error code and stop. Do not retry with other paths
  that the user did not name.
- The user asks for attribute values or secrets in the diagram. The script does not
  print them; say so.

## Shipped files

- `SKILL.md` (this file)
- `LICENSE.txt` (Apache-2.0)
- `scripts/tf_graph.py` (the script)
- `fixtures/smoke/main.tf.txt` (a five-block smoke input with one unresolved reference;
  copy it to a folder as `main.tf` before running the script, because the script reads
  only `.tf` files)
