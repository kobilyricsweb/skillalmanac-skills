---
name: terraform-module-docs
description: Generates Markdown docs for a Terraform module's variables, outputs, required providers and resource counts from its .tf files. Use when a module's README has gone stale, when a reviewer asks for a variable or output reference, or when undocumented variables and variables without a type need flagging. Do not use for full HCL parsing, expression evaluation, Terraform plans, module calls, or modules written as .tf.json files.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Terraform module docs

This skill runs `scripts/tf_docs.py` on one Terraform module directory and writes a new Markdown reference file. The script reads only the `*.tf` files directly inside the module directory. It uses documented regular expressions and a brace matcher, so it is not a full HCL parser. Check the generated file against the source before you publish it.

## Workflow

1. Collect the intake. You need the module directory path (`<module-dir>`) and a new output file path (`<output-file.md>`). Required output: both paths, written back in the reply. If the output name already exists, pick a new name. Never delete or overwrite an existing file.
2. Confirm the module directory holds at least one `*.tf` file directly inside it. Subfolders are not read. Required output: the count of `.tf` files found.
3. Run the script with the command in the Script contract section. Required output: the single JSON line the script prints.
4. Map the exit code to an action using the decision table below. Required output: the status word (`ok`, `findings`, or `error`).
5. For each finding, list the variable name and file so the module owner can add the missing description or type. Required output: one line per finding under the Findings section of the reply.
6. Deliver the Markdown file path, the counts from the JSON line, and the findings list. Do not paste secret default values; the script already writes them as `(redacted)`.

## Decision and threshold table

| Condition | Value | Action |
| --- | --- | --- |
| Module directory missing | not a directory | Exit 2, error `module directory not found`. Ask for the correct path. |
| No `*.tf` files in module directory | 0 files | Exit 2, error `no .tf files in module directory`. |
| Output path already exists | any existing file | Exit 2, error `output file already exists`. Choose a new name. |
| Input file size | over 2,097,152 bytes (2 MB, working value) | Exit 2, error `input file exceeds 2 MB`. |
| Input file encoding | not valid UTF-8 | Exit 2, error `input file is not valid UTF-8`. |
| Unbalanced braces in a `.tf` file | any | Exit 2, error `unbalanced braces in <file>`. Ask the owner to fix the file first. |
| Wrong number of arguments | not 2 arguments after the script name | Exit 2, error `usage: tf_docs.py <module-dir> <output-file.md>`. Fix the command. |
| `.tf` file cannot be read | OS read error | Exit 2, error `cannot read input file: <name>`. Report it and stop. |
| Output parent folder missing | parent directory does not exist | Exit 2, error `output parent directory not found`. Choose a path in an existing folder. |
| Output file cannot be written | OS write error | Exit 2, error `cannot write output file`. Stop and report it. |
| Variable with no `description` | 1 or more | Exit 1, finding `VAR_NO_DESCRIPTION`. |
| Variable with no `type` | 1 or more | Exit 1, finding `VAR_NO_TYPE`. |
| Variable `default` where the name matches `password`, `passwd`, `secret`, `token`, `api_key`, `apikey`, or `private_key` (case-insensitive) | any | Default shown as `(redacted)`. Working value, chosen to cover common secret names. |
| Variable with no `default` | attribute absent | Shown as `Required` = `yes`. |
| Provider with no `version` | attribute absent | Shown as `-`. No finding is raised. |
| Clean run | 0 findings | Exit 0, status `ok`. |

## Script contract

Command line (run from the skill folder):

```
python -I scripts/tf_docs.py <module-dir> <output-file.md>
```

Arguments: `<module-dir>` is an existing directory. `<output-file.md>` is a path that does not exist yet. The script never writes into an input file.

Exit codes: `0` means the file was written and there are no findings. `1` means the file was written and at least one finding was raised. `2` means a usage or input error; no output file is created.

Stdout on success is one JSON line with these keys: `status` (`ok` or `findings`), `files` (count of `.tf` files read), `variables`, `outputs`, `providers`, `resources` (total resource blocks), `resource_types` (object of type name to count), and `findings` (list of objects with `code`, `name`, and `file`). The finding codes are `VAR_NO_DESCRIPTION` and `VAR_NO_TYPE`.

Stdout on error is one JSON line: `{"status": "error", "error": "<message>"}`.

## Output contract (the generated Markdown)

The file starts with `# Module <directory name>` and a one-line note about regex parsing. It then has five sections in this order:

1. `## Variables`: columns `Name`, `Type`, `Default`, `Required`, `Description`.
2. `## Outputs`: columns `Name`, `Description`.
3. `## Providers`: columns `Name`, `Source`, `Version`.
4. `## Resources`: columns `Type`, `Count`, sorted by type name.
5. `## Findings`: one bullet per finding, in the form `CODE: variable `name` in `file` has no description attribute.`

An empty section prints `None.` in place of the table or list. Missing values print `-`.

## Refuse or stop when

- The module directory does not exist, or it holds no `*.tf` files. Stop and ask for the correct path.
- The output path already exists. Stop and ask for a new name. Never overwrite.
- A `.tf` file is over 2 MB or is not valid UTF-8. Stop; the run writes nothing.
- A `.tf` file has unbalanced braces. Stop and ask the owner to repair the file.
- The request is for `.tf.json` files, full HCL evaluation, resolution of module calls, or a plan. Say these are outside the script and stop.
- The request asks for the real value of a secret-named default. The script has no option for this. Keep `(redacted)` and say so.

## What the script does not read

Heredoc bodies, `data` blocks (not counted in resources), `validation` and `precondition` blocks (not shown), provider version constraints (shown as written, not checked), and comments (removed before parsing, so commented-out resources are not counted).

## Shipped files

- [LICENSE.txt](LICENSE.txt): Apache-2.0 license text.
- [scripts/tf_docs.py](scripts/tf_docs.py): the documentation script.
- [fixtures/build_sample.py](fixtures/build_sample.py): builds the smoke-test module into a new folder from the text fixtures.
- `fixtures/sample_module/variables.txt`: four variables, one without a description. Copied to `variables.tf` by the helper.
- `fixtures/sample_module/main.txt`: one `terraform` block with two providers and three resources, plus one commented-out resource. Copied to `main.tf`.
- `fixtures/sample_module/outputs.txt`: two outputs. Copied to `outputs.tf`.

Smoke run, in two steps:

```
python -I fixtures/build_sample.py <new-dir>
python -I scripts/tf_docs.py <new-dir> <output-file.md>
```

The second command should exit 1 and report one `VAR_NO_DESCRIPTION` finding for `enable_versioning`, four variables, two outputs, two providers, and three resources.
