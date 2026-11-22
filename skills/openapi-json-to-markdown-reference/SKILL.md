---
name: openapi-json-to-markdown-reference
description: Renders an OpenAPI 3 JSON file as a Markdown API reference. Use when a developer has an OpenAPI 3.x JSON spec and needs a readable Markdown reference, or needs to see which operations lack summaries, descriptions or types. Writes a coverage table, a table of contents, per-operation parameter, request body and response tables, and a Gaps section where missing fields read not documented. Do not use for YAML or Swagger 2.0 files, for generating client code or mock servers, or for checking a spec against the OpenAPI schema.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# OpenAPI JSON to Markdown reference

One local OpenAPI 3 JSON file in, one new Markdown reference out. The script is `scripts/openapi_md.py`. It reads the input once, never modifies it, and makes no network calls. Shipped files: `scripts/openapi_md.py`, `fixtures/sample_openapi.json` (smoke input), `LICENSE.txt`.

## Workflow

1. **Confirm the input.** The file must be UTF-8 JSON, at most 2,097,152 bytes, with a root object whose `openapi` string starts with `3.` and whose `paths` value is an object. Output: the input path and the `openapi` version string, kept for the reply.
2. **Pick a new output path.** Use a file name that does not exist yet in a folder that exists, for example `<workspace>/api-reference.md`. The script does not create folders. Output: the chosen output path.
3. **Run the script** with the command in the Script contract section. Output: one JSON line on stdout (exit 0 or 1), or one JSON error line on stderr (exit 2).
4. **Branch on the exit code** with the decision table. Exit 2 stops the workflow; report the `code` value and the `message`.
5. **Read the coverage.** Copy the five rows of the `## Coverage` table and every line of the `## Gaps` section from the output file into the reply, unchanged.
6. **Report the file.** Output: the output path, the `status` value, and the five coverage counts. Gaps stay `not documented` until the spec owner fills them in; do not write summaries, descriptions or types for them.

## Decision table

Size cap 2,097,152 bytes is set in the script (2 MB), not by the OpenAPI spec. The one-hop `$ref` rule is a working value.

| Condition | Exit | `status` or `code` | Action |
|---|---|---|---|
| File written, zero `not documented` markers | 0 | `ok` | Deliver the file |
| File written, one or more `not documented` markers | 1 | `findings` | Deliver the file and list every Gaps line |
| Not exactly two non-empty arguments | 2 | `usage` | Fix the command |
| Input missing, not a regular file, or unreadable | 2 | `input_missing` | Ask for a local file path |
| Input larger than 2,097,152 bytes | 2 | `input_too_large` | Stop; do not truncate, split or re-encode |
| Input is not valid UTF-8 | 2 | `invalid_utf8` | Stop |
| Input is not parseable JSON (YAML included) | 2 | `invalid_json` | Stop |
| Root is not an object, `openapi` is not a string starting with `3.`, or `paths` is not an object | 2 | `not_openapi3` | Stop |
| A path item or operation is not an object, or a path item uses a non-local `$ref` | 2 | `unsupported_structure` | Stop |
| Output path is the input file | 2 | `output_is_input` | Choose a new output path |
| Output path already exists | 2 | `output_exists` | Choose a new output path; never overwrite |
| Output folder does not exist | 2 | `output_dir_missing` | Choose a path in an existing folder |
| Output could not be written | 2 | `output_write_failed` | Stop; report it; a partial file may remain, so do not delete it |

## Script contract

Command, run from the skill folder:

`python -I scripts/openapi_md.py <input-file> <output-file>`

- Arguments: `<input-file>` is the local OpenAPI 3 JSON file; `<output-file>` is the new Markdown path.
- Success stdout, one line: `{"status": ..., "operations": N, "parameters": N, "request_body_fields": N, "responses": N, "not_documented": N}`. `status` is `ok` (exit 0) or `findings` (exit 1). The count keys match the Coverage table rows.
- Error stderr, one line: `{"status": "error", "code": ..., "message": ...}`. The `code` values are listed in the decision table. Exit 2.
- Exit codes: 0 written with no gaps; 1 written with gaps; 2 usage or input/output error.

## Output contract (the Markdown file)

Sections, in this order:

1. `# <info.title>`. If the title is missing, the heading reads `# Untitled API` and the gap `info title` is listed.
2. `Spec version: <openapi>. API version: <info.version>.` The version reads `not documented` when missing.
3. `## Coverage`: columns `Measure | Count`; rows `operations`, `parameters`, `request_body_fields`, `responses`, `not_documented`.
4. `## Table of contents`: one link per operation, or `None.`
5. `## Gaps`: `- Document: ...` for document-level gaps, then one line per operation with gaps, or `None.`
6. `## Operations`: one `### METHOD /path` block per operation, containing `**Summary:**`, `**Description:**`, `#### Parameters` (columns `Name | In | Required | Type | Description`), `#### Request body` (a `Body schema type:` line, then fields when the body is an object with properties: columns `Field | Type | Required | Description`), and `#### Responses` (columns `Code | Description | Content type | Schema type`).

Gap labels that appear in the Gaps section and in cells rendered as `not documented`:

| Label | Raised when |
|---|---|
| `summary`, `description` | Operation summary or description is missing or blank |
| `parameter <name> type`, `parameter <name> description` | Parameter schema has no resolvable type, or the description is missing |
| `parameter name`, `parameter location`, `parameter entry` | Parameter has no usable name or location, or the entry does not resolve |
| `request field <name> type`, `request field <name> description` | Request body property has no resolvable type, or the description is missing |
| `request body schema type` | Request body schema is missing, does not resolve, or has no type |
| `response <code> description`, `response <code> schema type`, `response <code>` | Response description or schema type is missing, or the response reference does not resolve |
| `responses` | Operation has no responses object |
| `info title`, `info version` | Document title or version is missing |

Content type `none` and parameter section `None defined.` are not gaps.

## Refuse / stop when

- The input is YAML, Swagger 2.0, or any file that is not one OpenAPI 3 JSON object. Stop with `invalid_json` or `not_openapi3`.
- The input is over 2,097,152 bytes. Stop. Do not truncate, split or re-encode it.
- The output path already exists. Stop and ask for a new name. Never overwrite a reference, and never write the output to the input path.
- A path item or operation is not a JSON object, or a path item uses a `$ref` that is not local. Stop with `unsupported_structure`.
- The user asks to fetch the spec from a URL, or to call the API it describes. Refuse that clause only; the script has no network. Keep the rest of the job, set status partial, and list the refused item under Open questions.
- The user asks to fill the gaps with invented summaries, descriptions or types. Decline that clause; leave `not documented` in place; set status partial; list the gaps under Open questions.

## Limits the agent must state

- The script checks structure only. It does not validate the spec against the OpenAPI schema, and it does not check that any description is accurate or current.
- It resolves local `#/` references one hop. Sibling keys beside a `$ref` are ignored. An unresolved reference counts as a gap.
- Only the first media type of a request body or response is shown, and only the top-level properties of a request body are listed.
- A schema with `oneOf`, `anyOf` or `allOf` and no `type` shows as `composed`; it is not expanded.
