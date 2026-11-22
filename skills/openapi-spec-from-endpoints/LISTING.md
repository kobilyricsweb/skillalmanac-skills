# openapi-spec-from-endpoints

## One line

Drafts an OpenAPI 3.0.3 YAML file from pasted route code or sample JSON, and lists every type it had to guess.

## What it does

Reads route declarations and sample JSON bodies you supply, then writes one path per route, one operation per HTTP method, and one component schema per distinct body shape. Path syntax from Express, Flask, FastAPI, Spring and ASP.NET is converted to braces. Field types come from sample values. A field is marked required only when it appears in every sample for its schema, and the skill needs at least two samples before it marks any field required. Anything the input does not show, such as an info title, a server URL, a query parameter type with no cast, or a response body with no sample, is written as a guess and listed in a GUESSED table with a reason code. The reply ends with counts of paths, operations, schemas and guessed rows, so a reviewer can compare the draft with the route file quickly. Sample values are never copied into the YAML, and the skill refuses to document endpoints absent from the input or to invent an authentication scheme.

## When to use

Use it when a service declares its routes in code, possibly with a few captured request or response bodies, and nobody has written a spec. It fits small to medium services whose routes sit in one or two files. The reviewer then corrects the GUESSED rows instead of writing the whole document from scratch.

## When not to use

Do not use it to design an API from a requirements list, to generate server stubs or client code, or to document endpoints that were not pasted. It does not read a live server or fetch a URL, and it does not decide security schemes.

## Requirements

A text-capable agent. No scripts and no network access. The input is pasted text: route source code and JSON samples tagged with method, path, and for responses a status code.

## Example

Input: `fixtures/books_routes.js` (30 lines, 4 routes) and `fixtures/samples.json` (4 samples). The output below is the complete reply.

Status: complete

### Endpoint inventory

| # | Method | Path | Source | Request body | Status codes |
| --- | --- | --- | --- | --- | --- |
| 1 | GET | /books | fixtures/books_routes.js:6 | none | 200 |
| 2 | GET | /books/{id} | fixtures/books_routes.js:11 | none | 200, 404 |
| 3 | POST | /books | fixtures/books_routes.js:17 | NewBook (sample s1) | 201 |
| 4 | DELETE | /books/{id} | fixtures/books_routes.js:25 | none | 204 |

### openapi.yaml

```yaml
openapi: 3.0.3
info:
  title: Books API
  version: 0.1.0
servers:
  - url: /
paths:
  /books:
    get:
      parameters:
        - name: limit
          in: query
          required: false
          schema:
            type: string
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema: {}
    post:
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NewBook'
      responses:
        '201':
          description: Created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Book'
  /books/{id}:
    get:
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Book'
        '404':
          description: Not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
    delete:
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '204':
          description: No content
components:
  schemas:
    Book:
      type: object
      required: [id, title, pages, price]
      properties:
        id: {type: string}
        title: {type: string}
        pages: {type: integer}
        price: {type: number}
    NewBook:
      type: object
      properties:
        title: {type: string}
        pages: {type: integer}
        price: {type: number}
    ErrorResponse:
      type: object
      properties:
        error: {type: string}
```

### GUESSED

| # | Location | Item | Guess | Reason |
| --- | --- | --- | --- | --- |
| 1 | info | title | Books API | INFO_DEFAULT |
| 2 | info | version | 0.1.0 | INFO_DEFAULT |
| 3 | servers[0] | url | / | SERVER_URL_DEFAULT |
| 4 | GET /books | limit (query) | string | NO_TYPE_HINT |
| 5 | GET /books | 200 body | {} | NO_SAMPLE |
| 6 | GET /books/{id} | id (path) | string | PATH_TYPE_DEFAULT |
| 7 | DELETE /books/{id} | id (path) | string | PATH_TYPE_DEFAULT |
| 8 | NewBook | title | string | ONE_SAMPLE |
| 9 | NewBook | pages | integer | ONE_SAMPLE |
| 10 | NewBook | price | number | ONE_SAMPLE |
| 11 | ErrorResponse | error | string | ONE_SAMPLE |

### Counts

Paths: 2
Operations: 4
Schemas: 3
GUESSED rows: 11

### Open questions

None.

## Limits

- It does not run the code. Routes generated at runtime or by a framework plugin are missed unless their source is in the pasted text.
- It cannot judge whether samples are representative. Two samples can agree by accident, and the required list follows them.
- The thresholds (2 samples before a field is required, nesting depth 3) are working values, not a published rule.
- It does not check that the YAML validates against the OpenAPI schema, and it does not confirm that the spec matches live behavior.
- It does not judge meaning. A field named `status` is typed only from its sample value.
- It does not document error responses the code does not show. Those appear, if at all, under Open questions.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
