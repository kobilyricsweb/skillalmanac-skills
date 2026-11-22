---
name: openapi-spec-from-endpoints
description: Drafts an OpenAPI 3.0 YAML spec from route code or sample requests and responses the user supplies, and marks every guessed type or status code in a GUESSED table. Use when an API has endpoints in code or sample traffic but no spec, and a first OpenAPI draft is needed for review. Do not use for designing a new API from requirements, generating server stubs or client SDKs, or documenting endpoints that are absent from the supplied input.
license: Apache-2.0
compatibility: Requires none beyond a text-capable agent (type B); no scripts and no network.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# OpenAPI spec from endpoints

Turn supplied route code and sample traffic into an OpenAPI 3.0.3 draft. Anything not shown in the input is written as a guess and listed in the GUESSED table. Never copy a sample value into the output; only types appear.

## Inputs

- Route code: any file that declares HTTP routes (Express, Flask, FastAPI, Spring, ASP.NET or similar).
- Samples: JSON bodies, each tagged with `method`, `path`, `kind` (`request` or `response`) and, for responses, `status`.
- Optional: an API name and a server base URL. Missing values use the defaults in the decision table.
- Worked input: `fixtures/books_routes.js` (30 lines, 4 routes) and `fixtures/samples.json` (4 samples).

## Workflow

1. Intake check. Confirm at least one route definition, or at least one sample with `method` and `path`. If neither exists, set Status to `stopped` and return the questions in "Refuse / stop when". Output: the Status line.
2. Endpoint inventory. List every route with method, path, source (`file:line` or sample `id`), request body source, and status codes shown. Convert path syntax with the path table. Output: the Endpoint inventory table.
3. Parameters. Path parameters come from the route syntax. Query parameters are documented only when the code reads them (`req.query`, `request.args`, a `Query(...)` declaration). Output: `parameters` in the YAML plus any GUESSED rows.
4. Schemas. Build one component per distinct request or response body shape and apply the decision table to every field. Output: `components.schemas` in the YAML plus any GUESSED rows.
5. Responses. Document only status codes that appear in code or samples. A status with no body sample gets schema `{}` and a NO_SAMPLE row. A 204 or other status that the code sends with no body needs no schema or row. Output: `responses` in the YAML.
6. Assemble. Write the YAML, then the GUESSED table (one row per guessed item), then the counts, then Open questions. Output: the parts listed in "Output contract", in that order.

## Path syntax

| Source syntax | OpenAPI path | Parameter type | GUESSED reason |
| --- | --- | --- | --- |
| `:name` (Express) | `{name}` | string | PATH_TYPE_DEFAULT |
| `<int:name>` (Flask) | `{name}` | integer, from the converter | none |
| `<name>` (Flask) | `{name}` | string | PATH_TYPE_DEFAULT |
| `{name}` (FastAPI, Spring, ASP.NET) | `{name}` | type annotation if present, else string | PATH_TYPE_DEFAULT when no annotation |

## Decision table

Values marked "working value" are not from a published spec.

| Situation | Rule | Value | Reason code |
| --- | --- | --- | --- |
| Samples needed before a field can be required | Field is required only when it appears in every sample of that schema and the schema has at least this many samples | 2 (working value) | none |
| One sample for a schema | No field is required; every field gets a row | 1 sample | ONE_SAMPLE |
| Integer or number | `integer` only when every sample value is a whole number and the code has no decimal literal; otherwise `number` | none | none |
| Type conflict across samples | Schema is `{}` | none | MIXED_TYPE |
| Array with no elements in any sample | `items` is `{}` | none | EMPTY_ARRAY |
| Object nesting | Inline up to this depth; deeper objects become `type: object` with no properties | 3 (working value) | DEPTH_CUTOFF |
| Query parameter with no type cast or annotation | `string` | none | NO_TYPE_HINT |
| Response status with no body sample, where the code sends a body | Schema `{}` | none | NO_SAMPLE |
| Field read in code with no sample (such as a `req.body` destructuring) | Type `string` and list the field | none | CODE_ONLY |
| Date-like string | `format: date-time` only when every sample value is an ISO 8601 date-time with a time zone; otherwise plain string with no row | none | none |
| `info.title` not in input | First path segment that is not a version (such as `v1`), capitalized, plus " API" | 1 title row | INFO_DEFAULT |
| `info.version` not in input | `0.1.0` | 1 version row | INFO_DEFAULT |
| Server URL not in input | `/` | 1 row | SERVER_URL_DEFAULT |

## Reason codes

| Code | Meaning |
| --- | --- |
| ONE_SAMPLE | Field or schema typed from a single sample |
| CODE_ONLY | Field read from code (req.body destructuring) with no sample; typed string and listed |
| NO_SAMPLE | Status shown in code, body schema not shown |
| MIXED_TYPE | Samples disagree on a field type |
| EMPTY_ARRAY | Array with no elements in any sample |
| DEPTH_CUTOFF | Object deeper than the nesting limit |
| NO_TYPE_HINT | Parameter read with no type cast or annotation |
| PATH_TYPE_DEFAULT | Path parameter type not shown, string used |
| INFO_DEFAULT | `info.title` or `info.version` inferred |
| SERVER_URL_DEFAULT | No server URL in input |

## Output contract

The reply has these parts, in this order.

1. `Status: complete`, `Status: partial`, or `Status: stopped`. Complete means every route parsed and no clause refused. Partial means at least one clause was refused or one route line could not be parsed. Stopped means the intake check failed.
2. `## Endpoint inventory`: columns `#`, `Method`, `Path`, `Source`, `Request body`, `Status codes`. One row per operation.
3. `## openapi.yaml`: one fenced YAML block with `openapi: 3.0.3`, `info`, `servers`, `paths`, and `components.schemas`. No `securitySchemes`, no `security` key, no example values.
4. `## GUESSED`: columns `#`, `Location` (method and path, `Schema.field`, or `info`), `Item`, `Guess`, `Reason`. One row per guessed item. Write "None." when there are no rows.
5. `## Counts`: four lines in this order: `Paths: N` (distinct path strings), `Operations: N` (method and path pairs), `Schemas: N` (entries in `components.schemas`), `GUESSED rows: N`.
6. `## Open questions`: numbered list, or "None.".

## Refuse / stop when

- There is no route definition and no sample with method and path. Set Status to `stopped`, and reply with only this numbered list: (1) paste the route file or files that declare the endpoints; (2) or paste at least one request or response sample with its method, path, and status.
- A requested endpoint is not in the input. Refuse that clause only, keep the rest, set Status to `partial`, and list the endpoint under Open questions.
- A requested auth scheme or `security` block is not shown in the input. Refuse that clause only, set Status to `partial`, and list it under Open questions. If the code names an auth middleware, report the name and `file:line` there; do not name a scheme.
- A sample holds a credential-like field (token, key, password, or an Authorization header). Use only its type, never its value, and name the sample `id` under Open questions.
- A route line cannot be parsed. Skip it, set Status to `partial`, and list `file:line` under Open questions.
