---
name: json-schema-from-sample
description: Infers a JSON Schema from one or more sample JSON files with a Python standard-library script. It marks a property required only when every sample has it, merges types, infers array item schemas and flags string formats that every sample matches. Use when you have example JSON payloads and need a first draft schema, or when a schema must be re-derived from several samples after the payload changes. Do not use for validating data against an existing schema, for OpenAPI or XML schemas, or for writing a schema from prose requirements.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# JSON Schema from samples

This skill runs `scripts/infer_schema.py` on the sample files you give it and
returns the schema the script prints. The script does the merging. Your job is
to choose the samples, run the command, check the findings, and report.

## Files in this package

- `SKILL.md` (this file): procedure and contracts.
- `scripts/infer_schema.py`: the inference script (stdlib only, read-only on inputs).
- `fixtures/sample_a.json`, `fixtures/sample_b.json`: two objects, one without `nickname`.
- `fixtures/sample_conflict.json`: a deliberately mismatched object for the findings path.
- `LICENSE.txt`: Apache-2.0 license text.

## Workflow

1. **Collect samples.** Gather 1 to 100 JSON files, each holding one JSON value
   (usually an object). Output: a list of absolute file paths.
   Stop if any file is larger than 2 MB (the script refuses it anyway).
2. **Pick the output mode.** Output: one of two choices, recorded in your report.
   - Stdout (default): schema text goes to the console.
   - `-o NEW_FILE`: the path must not exist yet and must not be one of the samples.
3. **Run the script** with the exact command in "Command line" below. Output: the
   exit code and, on success, the schema text.
4. **Branch on the exit code.**
   - 0: go to step 5.
   - 1: the schema was written. Go to step 5 and list every `FINDING` line.
   - 2: no schema was written. Read the one-line JSON error, fix the input or
     the arguments, and rerun once. A second exit 2 ends the task (see "Refuse / stop when").
5. **Check the required list against the samples.** Output: a one-line statement
   per property in `required`, confirming it appears in every sample. Do this for
   at least the first three properties in the `required` array.
6. **Report** in the output contract below.

## Inference rules (fixed, do not change them by hand)

| Situation across samples | Schema result |
|---|---|
| Key present in every object instance at that position | Listed in `required` |
| Key present in some instances only | Listed in `properties`, not in `required` |
| Value `null` in some instances, one other type elsewhere | `"type": ["<type>", "null"]` |
| Only `1` and `2.5` seen for one position | `"type": "number"` (integer is absorbed) |
| Two non-null types seen (for example integer and string) | `"type": [...]` listed, plus a `FINDING` line, exit 1 |
| Every string at a position matches `date-time` | `"format": "date-time"` |
| Every string matches `date` (and not `date-time`) | `"format": "date"` |
| Every string matches `email` | `"format": "email"` |
| Every string matches `uri` | `"format": "uri"` |
| Strings match a format only in part | No `format` key |
| Array with at least one element somewhere | `"items"` built from all elements at that position |
| Array that is always empty | No `items` key |
| Strings longer than 2048 characters | Not checked for formats |

Format regexes are working values, not validators: `date` only checks the shape
`YYYY-MM-DD`, and `email` only checks `x@y.z` shape. The script never emits
`additionalProperties`, `minItems`, `enum`, or numeric bounds.

## Script limits (working values)

| Limit | Value | Behaviour when exceeded |
|---|---|---|
| Input file size | 2 MB (2,097,152 bytes) | Exit 2 |
| Nesting depth | 32 levels | Exit 2 |
| Sample files per run | 100 | Exit 2 |
| Integer literal digits | 40 | Exit 2 (parse error) |
| Float literal characters | 40 | Exit 2 (parse error) |

## Script contract

- Command: `python -I scripts/infer_schema.py [-o NEW_FILE] SAMPLE [SAMPLE ...]`
- Arguments: `-o` or `--output` (optional, new file path); `SAMPLE` one or more paths.
- Stdout (exit 0 or 1): the schema, JSON, 2-space indent, UTF-8, ends with a newline.
  Top-level keys used: `type`, `format`, `properties`, `required`, `items`.
  The script does not emit `$schema`; the schema uses 2020-12 keywords only.
- Stderr, exit 1: one line per finding, `FINDING <json-path>: conflicting types <a>, <b>`.
- Stderr, exit 2: one line of JSON, `{"error": "<message>"}`. Nothing on stdout.
- Exit codes: 0 success with no findings; 1 schema written with findings;
  2 usage or input error (including argparse usage errors).
- The script never opens a network connection, never starts a subprocess, and
  never reads a sample for writing. It refuses an output path that exists or
  that resolves to a sample path.

## Output contract (your report)

Use these headings, in this order:

1. `## Samples`: a bullet per file, as given.
2. `## Exit code`: the number.
3. `## Schema`: the schema JSON in a fenced `json` block, copied from stdout or
   from the `-o` file.
4. `## Findings`: each `FINDING` line verbatim, or the word `none`.
5. `## Required check`: one bullet per checked `required` property, `name: present in all N samples`.

## Refuse / stop when

- Any sample path is outside the samples the user supplied (do not add files you found yourself).
- The user asks for validation of data against a schema. This skill infers only.
- The user asks for an OpenAPI, XML, or prose-derived schema.
- The output path exists or is a sample path. Choose a new path; do not delete the old file.
- The same exit 2 happens twice in a row.
- Any sample holds personal data and the user has not confirmed that a schema derived from it may be shared.

## Command line

```
python -I scripts/infer_schema.py fixtures/sample_a.json fixtures/sample_b.json
```

Expected: exit 0, schema with `nickname` absent from `required`, `created` with
`"format": "date-time"`, and `contact` with `"format": "email"`.
