# API reference from source

## One line

Writes an endpoint-by-endpoint API reference from route handler source or JSON response samples, and records every gap as NOT-DOCUMENTED instead of guessing.

## What it does

Given handler files in a supported language, or JSON response samples, the skill finds each route registration and fills one fixed page per endpoint: path parameters, query parameters, request body, responses, errors, and a source citation on every row. Types come only from annotations, converters, or explicit casts; otherwise the cell reads "not stated in code". A success status code appears only where a handler writes it. A fixed six-topic NOT-DOCUMENTED list records what the input cannot show, including authentication and rate limits, which the skill never invents. The result is a status of complete, partial, or stopped, so a reviewer can see at once whether the page is ready to publish or still has questions for the code owner.

## When to use

Use it when a client team needs endpoint documentation for a service whose route handlers sit in the repository, or when a service has sample payloads but no reference at all. It suits a first draft that the service owner checks line by line against the code. Each row cites its file and line, so the check takes minutes rather than a full reread.

## When not to use

Do not use it to generate OpenAPI files, write tutorials, design authentication, set rate-limit policy, or document a service whose handlers were not supplied. It does not replace a runtime test against a deployed service.

## Requirements

A text-capable agent and the handler files or JSON samples pasted or attached as text. The skill needs no scripts, no packages, and no network access. The shipped sample handler file is the offline smoke input.

## Example

```markdown
# API reference: sample_handlers

Status: complete
Inputs: sample_handlers.txt

## Endpoint index
| ID | Method | Path | Handler | Source |
|---|---|---|---|---|
| R1 | GET | /orders/<int:order_id> | get_order | sample_handlers.txt:9-15 |
| R2 | POST | /orders | create_order | sample_handlers.txt:18-27 |
| R3 | GET | /orders/search | search_orders | sample_handlers.txt:30-35 |

## R1 GET /orders/<int:order_id>
### Summary
Return one order by id. (line 11)
### Path parameters
| Name | Type | Required | Source |
|---|---|---|---|
| order_id | integer | yes | lines 9-10 |
### Query parameters
None in code.
### Request body
None in code.
### Responses
| Status | Body keys | Types | Source |
|---|---|---|---|
| not written in handler | id, item, qty | id: integer (path parameter, line 15); item, qty: not stated in code | line 15 |
### Errors
| Status | Condition | Source |
|---|---|---|
| 404 | order is None | lines 13-14 |
### Source
sample_handlers.txt lines 9-15

## R2 POST /orders
### Summary
No description in code.
### Path parameters
None in code.
### Query parameters
None in code.
### Request body
| Name | Type | Required | Source |
|---|---|---|---|
| item | not stated in code | yes (line 23 returns 400 when missing) | lines 21, 23 |
| qty | integer | no (default 1) | line 22 |
### Responses
| Status | Body keys | Types | Source |
|---|---|---|---|
| 201 | id | integer (len(ORDERS) + 1, line 25) | line 27 |
### Errors
| Status | Condition | Source |
|---|---|---|
| 400 | not item; body {"error": "item is required"} | lines 23-24 |
### Source
sample_handlers.txt lines 18-27

## R3 GET /orders/search
### Summary
No description in code.
### Path parameters
None in code.
### Query parameters
| Name | Type | Required | Default | Source |
|---|---|---|---|---|
| q | not stated in code | no | "" | line 32 |
| limit | integer | no | 10 | line 33 |
### Request body
None in code.
### Responses
| Status | Body keys | Types | Source |
|---|---|---|---|
| not written in handler | array of objects: id, item | not stated in code | lines 34-35 |
### Errors
None in code.
### Source
sample_handlers.txt lines 30-35

## NOT-DOCUMENTED
- Authentication: not in input. No authentication check appears in the handlers.
- Rate limits: not in input.
- Success status codes: not written in R1 or R3. R2 writes 201 (line 27).
- Versioning: no version in the paths or the input.
- Idempotency: not stated in code. R2 assigns the new id as the entry count plus one (line 25), so each POST creates a new order.
- Caching: not in input.
- Result ordering: not stated in code. R3 returns hits in ORDERS iteration order (line 34).

## Open questions
None.
```

## Limits

The page reflects the supplied input only. It does not confirm that the code runs, that the service is deployed, or that a sample matches live traffic. It does not resolve dynamic paths or follow calls deeper than one level. The thresholds of 50 routes and 2,000 lines are working values, not published specs. The skill does not verify security behavior, performance, or error handling beyond the literal branches in the code.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
