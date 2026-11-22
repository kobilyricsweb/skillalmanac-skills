---
name: markdown-frontmatter-lint
description: Lints the YAML front matter of a folder of Markdown notes and reports each problem with its file and line number. Use when a note vault has drifted, or before a sync or publish step, to find duplicate keys, missing required keys, invalid ISO dates, empty values, or tags with spaces or capitals. Do not use for rewriting or fixing front matter, for Markdown body style, or for YAML files that are not Markdown notes.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Markdown front matter lint

This skill runs `scripts/frontmatter_lint.py` over one folder of Markdown notes. The script reads files only, parses each front matter block with the standard library, and reports every finding with its file and line. It never edits a note.

## Inputs

- `<notes-folder>`: the folder to scan. Required.
- Required keys: default `title,date,tags` (working value). Change them with `--required`.

## Workflow

1. Confirm the folder exists and holds `.md` files by listing it. Output: the folder path and the count of `.md` files. Stop if the folder is missing or has none (see the Refuse list).
2. Run the script with the command line in the Script contract section. Output: the JSON report on stdout and the exit code.
3. Branch on the exit code using the Exit codes table. Output: one line naming the exit code and its action.
4. For exit 1, take the findings in report order and map each `code` to the Rule table. Output: the findings table.
5. Write the report in the Output contract. Output: the summary block and the findings table, with every finding listed.

## Exit codes

| Exit | Meaning | Next action |
|---|---|---|
| 0 | No findings | Report status `clean` and the files-scanned count. |
| 1 | One or more findings | Continue at step 4. |
| 2 | Usage or input error; one line of JSON on stderr | Stop. Report the error text and exit 2. Do not retry with a different path. |

## Rule table

Trigger values marked "working value" are chosen for this skill, not published specifications.

| Code | Rule | Trigger | Fix |
|---|---|---|---|
| FM001 | no_front_matter | First line is not `---`. Reported at line 1. | Add a front matter block at the top of the file. |
| FM002 | unclosed_front_matter | No later line equals `---`. Reported at line 1. | Add the closing `---` line. |
| FM003 | duplicate_key | A key appears a second time. The first value is kept. Reported at the second occurrence. | Delete the later line. |
| FM004 | missing_required_key | A key from `--required` is absent. Reported at the closing `---` line. | Add the key. |
| FM005 | bad_date | Key is `date` or `updated` (working value) and the value is not a real calendar date in `YYYY-MM-DD` form. | Rewrite as `2026-03-14`. |
| FM006 | bad_tag | A tag item contains whitespace or any uppercase letter (working value). | Use a lowercase tag with hyphens instead of spaces. |
| FM007 | empty_value | Key has no value, an inline list is `[]`, or an item is empty. | Give the key a value or delete the key. |
| FM008 | invalid_line | Line is not a top-level key, list item, or comment. Also covers indented keys and list items under a key that has a value. | Check for nested maps or multi-line text. This parser does not read them. |
| FM009 | file_too_large | File is larger than 2 MB (working value). Skipped. | Split the note or review it by hand. |
| FM010 | invalid_utf8 | File does not decode as UTF-8. Skipped. | Re-save the file as UTF-8. |
| FM011 | unreadable_file | The operating system refuses to open the file. Skipped. | Check file permissions. |

## Scan rules

- Only files ending in `.md` (any letter case) are scanned.
- Directories whose names start with a dot are skipped, for example `.obsidian` or `.trash`.
- Symbolic links are skipped, both files and folders.
- A leading UTF-8 byte-order mark is ignored.
- Parser subset: `key: value` lines, block lists written as `- item` under a key with an empty value, inline lists written as `[a, b]`, quoted scalars, and lines starting with `#` as comments.

## Output contract

The summary block uses these exact labels, in this order:

```
## Summary
- Files scanned: <n>
- Files with findings: <n>
- Findings: <n>
- Status: clean | findings
```

The findings table uses these exact columns: `| File | Line | Code | Rule | Key | Message |`. Show `-` where the JSON `key` is null. List every finding in JSON order and drop none.

## Script contract

Command line:

```
python -I scripts/frontmatter_lint.py "<notes-folder>" --required title,date,tags
```

- Arguments: one positional `<notes-folder>`; optional `--required KEYS` (comma-separated plain key names; default `title,date,tags`).
- stdout on exit 0 or 1: a JSON object with keys `tool`, `version`, `required_keys`, `files_scanned`, `files_with_findings`, `findings_count`, `status`, `findings`. Each finding has `file`, `line`, `code`, `rule`, `key`, `message`.
- stderr on exit 2: one line, `{"error": "<text>", "exit": 2}`.
- Exit codes: 0 no findings; 1 findings; 2 usage or input error.
- Read-only. The script writes no file and makes no network call.

Shipped files, relative to this folder:

- [scripts/frontmatter_lint.py](scripts/frontmatter_lint.py): the linter.
- `fixtures/vault/`: six small notes used as a smoke set (`alpha.md`, `beta.md`, `gamma.md`, `delta.md`, `epsilon.md`, `zeta.md`). Running the script on that folder must exit 1 with four findings: `beta.md` line 4 FM003, `gamma.md` line 3 FM005, `delta.md` line 5 FM006, `epsilon.md` line 4 FM004.
- [LICENSE.txt](LICENSE.txt): Apache License 2.0.

## Refuse / stop when

- The folder does not exist or is not a directory: exit 2, stop.
- The folder holds no `.md` files: exit 2, stop. Do not create sample notes to make the run work.
- A `--required` name contains spaces or punctuation: exit 2, stop.
- The user asks you to fix, rewrite, or delete front matter, or to save the report to a file: refuse. This skill only reports, and the script writes nothing.
- The user asks for a YAML validity verdict on anchors, nested maps, or multi-line strings: say the parser does not read them. Their lines appear as FM008 "not read", not as YAML errors.
