# OpenAPI JSON to Markdown reference

## One line

Turns one local OpenAPI 3 JSON file into a Markdown API reference with a coverage table, a table of contents, per-operation parameter, request body and response tables, and a Gaps section for every field the spec leaves out.

## What it does

The script reads one OpenAPI 3 JSON file, checks that the root is an object with a string `openapi` field starting with `3.` and an object `paths` field, and then walks each path in document order. For each HTTP method present, it writes a heading, the summary and description, a parameters table, a request body section, and a responses table. The parameters table merges path-level parameters with operation-level ones; an operation-level parameter with the same name and location replaces the path-level one. The request body table lists the top-level properties of the first media type when the body is an object. The responses table gives the first media type of each response, its schema type, and the description.

Local `$ref` pointers resolve one hop, so a reference to a component schema shows the schema type, and a reference that cannot be followed is counted as a gap rather than hidden. Every missing or unresolvable field is written as `not documented` and listed in a Gaps section by operation, so a reader can see exactly which parts of the spec need owner input. The top of the file carries a coverage table with operation, parameter, request field and response counts, plus the total of not documented markers.

The script never writes over an existing file, never writes to the input path, and never reads more than 2 MB. It exits 0 when the file is written with no gaps, 1 when it is written with gaps, and 2 when it stops on bad input or an unusable output path, printing a one-line JSON error on stderr.

## When to use

- A spec is available as one local OpenAPI 3.0 or 3.1 JSON file and a readable Markdown reference is needed for review.
- The reviewer wants to know which operations lack a summary, a description, parameter types, request field descriptions, or response descriptions before the spec goes out.
- A new reference file is wanted next to other documents, and an existing reference must not be replaced.

## When not to use

- The spec is YAML, Swagger 2.0, or a JSON file that is not an OpenAPI 3 document.
- The task is to validate the spec against the OpenAPI schema, lint it with a style guide, or test the live API.
- The task is to generate client code, server stubs, or mock responses.
- The spec is larger than 2 MB or lives behind a URL; the script does not download anything.

## Requirements

- Python 3.9 or newer, standard library only. The script runs with `python -I`.
- One local JSON file, UTF-8 encoded, at most 2,097,152 bytes.
- An output folder that already exists and a file name that does not exist yet.
- No network access and no extra packages.

## Example

Smoke run on the shipped fixture `fixtures/sample_openapi.json`, with the output path `<workspace>/sample-reference.md`. Stdout, one line:

```
{"status": "findings", "operations": 3, "parameters": 2, "request_body_fields": 3, "responses": 5, "not_documented": 5}
```

File written (exit code 1):

```markdown
# Pet Store Sample

Spec version: 3.0.3. API version: 1.0.0.

## Coverage

| Measure | Count |
|---|---|
| operations | 3 |
| parameters | 2 |
| request_body_fields | 3 |
| responses | 5 |
| not_documented | 5 |

## Table of contents

- [GET /pets](#get-pets)
- [POST /pets](#post-pets)
- [GET /pets/{petId}](#get-petspetid)

## Gaps

- `POST /pets`: summary; description; request field `id` description; response 201 description
- `GET /pets/{petId}`: description

## Operations

### GET /pets

**Summary:** List pets

**Description:** Returns pets, optionally limited in number.

#### Parameters

| Name | In | Required | Type | Description |
|---|---|---|---|---|
| limit | query | no | integer | Maximum number of pets to return |

#### Request body

None defined.

#### Responses

| Code | Description | Content type | Schema type |
|---|---|---|---|
| 200 | A list of pets | application/json | array of object |

### POST /pets

**Summary:** not documented

**Description:** not documented

#### Parameters

None defined.

#### Request body

Body schema type: object.

| Field | Type | Required | Description |
|---|---|---|---|
| id | integer | no | not documented |
| name | string | yes | Pet name |
| tag | string | no | Optional tag |

#### Responses

| Code | Description | Content type | Schema type |
|---|---|---|---|
| 201 | not documented | application/json | object |
| 400 | Invalid input | none | none |

### GET /pets/{petId}

**Summary:** Get a pet

**Description:** not documented

#### Parameters

| Name | In | Required | Type | Description |
|---|---|---|---|---|
| petId | path | yes | string | Pet identifier |

#### Request body

None defined.

#### Responses

| Code | Description | Content type | Schema type |
|---|---|---|---|
| 200 | The pet | application/json | object |
| 404 | Pet not found | none | none |
```

## Limits

- Structure only. The script does not validate the spec against the OpenAPI schema and does not check that a description is accurate, current, or consistent with the code behind the API.
- Only local `#/` references resolve, one hop deep. Sibling keys next to a `$ref` are ignored.
- The first media type of each request body and response is shown. Other media types are not listed.
- Request bodies list top-level properties only. Nested objects show as `object` and are not expanded.
- Schemas built with `oneOf`, `anyOf` or `allOf` and no `type` show as `composed`.
- Anchors in the table of contents use a simplified GitHub-style slug; headings with non-ASCII text may not link.
- A write failure can leave a partial file at the output path; the script does not clean it up.
- It does not check how the Markdown renders in a particular viewer, does not check deliverability, and does not assess the security of the described API.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
