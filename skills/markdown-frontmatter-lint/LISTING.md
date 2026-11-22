# Markdown front matter lint

## One line

Reads the YAML front matter of every Markdown note in a folder and reports each duplicate key, missing required key, bad date, bad tag, and empty value with its file and line.

## What it does

The skill runs a standard-library Python script over one folder of notes. It walks the folder for `.md` files, skips hidden directories and symbolic links, and reads each file as UTF-8. For each file it finds the block between the opening and closing `---` lines and parses the subset a note vault normally uses: top-level `key: value` lines, block lists written with dashes, inline lists in square brackets, and quoted values.

It then checks the block. A repeated key is flagged at its second occurrence, and the first value is treated as the real one. Keys named `date` or `updated` must be real calendar dates in `YYYY-MM-DD` form. Tags must not contain whitespace or capital letters. Required keys, which default to `title`, `date`, and `tags`, must be present. Empty values are flagged, and lines the parser cannot read are reported as invalid rather than guessed at.

The output is a JSON report on standard output. The exit code says whether the folder is clean (0), has findings (1), or could not be scanned (2). The script writes nothing to disk, so a note vault can be checked before a sync without any risk to the notes.

## When to use

- Before a sync, publish, or static-site build step, to catch front matter that a later tool would reject or misread.
- After a bulk import or a batch edit, when several authors or scripts have touched the same notes.
- When a folder of notes has drifted and you need a list of exact file and line locations, not a general opinion.

## When not to use

- When you want the front matter rewritten or fixed. The script only reports.
- When the notes use nested maps, anchors, or multi-line strings. The parser does not read them, and those lines appear as invalid.
- For Markdown body style, link checks, or spelling.

## Requirements

Python 3.9 or later. No third-party packages and no network access. Run it from any shell with the notes folder as the single argument.

## Example

Run on the six-note smoke set, with the default required keys:

```
python -I scripts/frontmatter_lint.py fixtures/vault
```

Output, verbatim from the run:

```json
{
  "tool": "frontmatter_lint",
  "version": "0.1.0",
  "required_keys": [
    "title",
    "date",
    "tags"
  ],
  "files_scanned": 6,
  "files_with_findings": 4,
  "findings_count": 4,
  "status": "findings",
  "findings": [
    {
      "file": "beta.md",
      "line": 4,
      "code": "FM003",
      "rule": "duplicate_key",
      "key": "date",
      "message": "key repeats; first seen on line 3"
    },
    {
      "file": "delta.md",
      "line": 5,
      "code": "FM006",
      "rule": "bad_tag",
      "key": "tags",
      "message": "tag contains whitespace; tag is not lowercase"
    },
    {
      "file": "epsilon.md",
      "line": 4,
      "code": "FM004",
      "rule": "missing_required_key",
      "key": "tags",
      "message": "required key is missing"
    },
    {
      "file": "gamma.md",
      "line": 3,
      "code": "FM005",
      "rule": "bad_date",
      "key": "date",
      "message": "value is not a valid YYYY-MM-DD date"
    }
  ]
}
```

The exit code is 1. Each finding points at the line a note author would open.

## Limits

- Parses only the simple front matter subset described above. Anchors, nested maps, flow maps, and multi-line scalars are not read.
- The 2 MB per-file cap, the `date` and `updated` key list, and the tag rule are working values chosen for this skill.
- Checks structure and format only. It does not confirm that a title is accurate or that a tag is meaningful.
- Skipped files (too large, not UTF-8, unreadable) are reported once each and their content is not checked.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
