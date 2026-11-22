---
name: api-reference-from-source
description: Writes an API reference page for each endpoint in supplied route handlers or JSON response samples, using only what the code and samples show. Use when clients need endpoint docs, when an API has no reference yet, or when handler files or sample payloads are at hand. Do not use for auth, rate limit, or status code docs the code does not show, for OpenAPI spec generation, or for tutorials.
license: Apache-2.0
compatibility: None beyond a text-capable agent; no scripts and no network access.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# API reference from source

Writes one reference page per endpoint from route handler source or JSON response samples. Every fact on the page comes from the supplied input and carries a file and line citation. Anything the input does not show goes into NOT-DOCUMENTED.

Supported handler languages: Python, Java, JavaScript, TypeScript, Go, and Ruby. Any other language triggers the stop rule.

Shipped files:
- [fixtures/sample_handlers.txt](fixtures/sample_handlers.txt): 35-line Python handler file with three routes. It is the offline smoke input.
- [LICENSE.txt](LICENSE.txt): Apache License 2.0.

## Workflow

1. **Intake.** Output: an intake table with the columns File, Language, Lines, and Role (handler, sample, or other). Required facts: at least one handler file or one JSON sample. If a required fact is missing, apply the stop rule.
2. **Find routes.** Scan for registrations that bind an HTTP method to a path: route or get/post decorators, router calls, and mapping annotations. Output: the endpoint index, numbered R1, R2, and so on in file order. Record the method and path exactly as written, plus the handler name and its first and last line.
3. **Parameters.** For each route, list path parameters (from `<int:name>`, `{name}`, or `:name` placeholders), query parameters (reads of the request query string), and header reads. Output: one row per parameter. Type comes from an annotation, a converter, or an explicit cast; otherwise the cell reads "not stated in code". Required is yes when the code returns or raises on a missing value, no when a default exists, and "not stated in code" otherwise.
4. **Request body.** Output: body rows (name, type, required, source) from body reads or a typed request class. Write "None in code." when the handler reads no body. Record the content type only when the code states it.
5. **Responses.** Output: response rows. A status appears only where the handler writes it: a literal in a return tuple, a status argument, or a response constructor. Body keys come from dict or object literals in return statements. When a JSON sample is supplied, its keys and types fill the cell and the cell reads "from sample". If a sample and the code disagree, use the code and add an open question.
6. **Errors.** Output: error rows from abort, raise, and literal error returns, with the condition in the code's own words. Do not infer a condition the code does not state.
7. **Summary and NOT-DOCUMENTED.** Summary is the first line of a docstring or an adjacent comment, cited by line. If none exists, write "No description in code." Output: the NOT-DOCUMENTED list (see the contract) and any open questions.
8. **Assemble and self-check.** Write the page in the output contract. Before returning, confirm that the endpoint sections match the endpoint index rows one for one, that every table row has a source citation, and that no status code appears without a literal in the code.

## Decision table

| Situation | Action |
|---|---|
| Path built at runtime (concatenation or a variable) | Do not guess. Add "dynamic path at file:line" to NOT-DOCUMENTED. |
| Handler calls another function that does the work | Follow one call level. Deeper calls go to NOT-DOCUMENTED. |
| No type annotation and no cast | Type cell reads "not stated in code". |
| Success status not written in the handler | Record it under the NOT-DOCUMENTED topic "Success status codes". |
| Only one JSON sample supplied | Mark sample-derived cells "from one sample". |
| More than 50 routes in the input | Document the first 50 in file order, set status partial, and list the rest in Open questions. Working value. |
| One file longer than 2,000 lines | Read it in sections and note "read in sections" in the intake table. Working value. |
| Secret literal (key, password, token) in a handler | Write [redacted] in place of the value, add an open question, and set status partial. |
| Code and sample disagree on a field | Use the code. Put the sample value in Open questions. |

Thresholds marked "working value" are not published specs.

## Output contract

The page has this shape, in this order:

- Title line: `# API reference: ` followed by a short service label taken from the file name or a module docstring.
- Status line: `Status: complete`, `Status: partial`, or `Status: stopped`.
- `Inputs:` line with the input file names, comma-separated.
- `## Endpoint index` table with the columns ID, Method, Path, Handler, Source.
- One section per endpoint, headed `## R1 METHOD path`, in index order. Each section holds seven subsections in this fixed order: Summary, Path parameters, Query parameters, Request body, Responses, Errors, Source.
  - Path parameters: Name, Type, Required, Source.
  - Query parameters: Name, Type, Required, Default, Source.
  - Request body: Name, Type, Required, Source.
  - Responses: Status, Body keys, Types, Source.
  - Errors: Status, Condition, Source.
  - Source: file name and line range of the handler.
  An empty subsection reads "None in code."
- `## NOT-DOCUMENTED`: six fixed topics in this order: Authentication, Rate limits, Success status codes, Versioning, Idempotency, Caching. Each topic appears once, even when the input says nothing about it. Topics the handlers raise, such as dynamic paths or result ordering, follow the fixed six.
- `## Open questions`: a numbered list, or "None."

Status values:
- complete: every endpoint documented and no open questions.
- partial: a page exists but has open questions, a refused clause, or an applied cap.
- stopped: no page. Only the status line and the question list are returned.

## Stop rule

Set status stopped and write no endpoint section when:
- No handler file and no JSON sample is supplied.
- No route registration can be found in any supplied file.
- The handler language is outside the supported list.
- The code is minified or obfuscated so that paths cannot be read.

When stopped, return the status line and a numbered question list of at most five questions. Each question asks for one missing fact, for example "Which file holds the route registrations?"

## Refuse / stop when

- The request asks you to state auth, rate limits, or status codes that the input does not show. Refuse that clause only. Keep the rest of the page, set status partial, and list the refused item under Open questions.
- An endpoint's handler is not in the supplied input. Do not document it. Add it to Open questions.
- A secret literal appears in the input. Redact it as the decision table says.
- The request is for OpenAPI output or a tutorial. Those are out of scope. Say so and stop.

## Limits

The page reflects the supplied input only. It does not confirm that the code runs, that the service is deployed, or that a sample matches live traffic. It does not verify security behavior, performance, or error handling beyond the literal branches in the code.
