---
name: mcp-server-builder
description: "Designs and reviews a Model Context Protocol (MCP) server: tool design rules, JSON Schema inputs, bounded outputs, error contract, tool vs resource vs prompt choice, stdio vs HTTP transport, auth and secrets, a client-harness test plan and a publish checklist, plus a script that validates a tool manifest. Use when the user is building, extending or reviewing an MCP server, asks how to expose an API or database to an agent as tools, or says the model picks the wrong tool. Do not use for installing or configuring someone else's MCP server, or for building an agent or chatbot that only consumes tools."
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, apply the checklist in step 4 by hand.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# MCP server builder

Design the server on paper first, check the tool manifest with the script, then write code. Most bad servers fail at the manifest: too many overlapping tools, vague descriptions, unbounded outputs, side effects nobody labelled.

Protocol details that move between spec revisions are marked "verify against modelcontextprotocol.io (unconfirmed)". Check those before relying on them; [references/protocol-notes.md](references/protocol-notes.md) lists every one with the question to ask.

## Workflow

```
- [ ] 1 Write the server brief
- [ ] 2 Sort every capability into tool, resource or prompt
- [ ] 3 Draft the manifest (names, descriptions, schemas, error contract)
- [ ] 4 Validate the manifest with the script and fix
- [ ] 5 Choose transport and auth
- [ ] 6 Write code; run the test plan
- [ ] 7 Publish checklist and report
```

1. **Brief.** Four lines: who calls it (which agent or client), what system it wraps, the three most common user requests it must serve, and what it must never do. If the third line needs more than 8 tools, split it into two servers.
2. **Sort capabilities.** Use the table below; the longer version with edge cases is in [references/decision-tables.md](references/decision-tables.md) (read the transport and auth tables when you reach step 5).

   | Capability | Use | Because |
   |---|---|---|
   | Model decides to do or fetch something, args vary | Tool | Model-controlled, takes arguments |
   | Read-only data addressed by a stable URI the app can attach | Resource | Application-controlled, no model decision needed |
   | Parameterised URI family (one per record) | Resource template | Avoids one tool per record type |
   | Canned workflow the user starts by choice | Prompt | User-controlled, appears as a command |
   | Anything with a side effect | Tool, never resource | Reads must stay safe to repeat |

   Many clients only surface tools, so a resource-only server can look empty. Offer a read tool beside important resources (client support varies; verify against modelcontextprotocol.io (unconfirmed)).
3. **Manifest.** Apply the rules below to every tool.
4. **Validate.** Save the `tools/list` result or your tool array as JSON and run `python scripts/validate_manifest.py manifest.json`. Fix every error; fix warnings or justify each in the report. Re-run until `"ok": true`. Do not edit the script to make a check pass.
5. **Transport and auth** per the tables in the decision reference. Default: stdio for a local single-user tool, HTTP for anything shared, remote or multi-user.
6. **Test** with the plan in [references/test-and-publish.md](references/test-and-publish.md) (harness, 7 test classes, pass bar).
7. **Publish** with the checklist in the same file, then give the report (format at the end).

## Tool design rules

Working values below are this skill's defaults, not protocol limits.

| Rule | Default |
|---|---|
| One job per tool; no `mode` argument that switches behaviour | split when a tool has 2 verbs |
| Name | lowercase snake_case, verb first (`search_tickets`), at most 64 chars; no duplicates |
| Description | 40 to 600 chars; first sentence says what, then a sentence starting "Use when ..."; say what it does NOT do if a neighbour tool exists |
| Server size | 8 to 15 tools is comfortable; above 30 expect wrong-tool picks (working value) |
| Input schema | `type: object`, every argument in `properties` with a description, `required` listed, `additionalProperties: false`, enums for closed sets, `maxLength` on free text, `maxItems` on arrays |
| Ids | accept the id the previous tool returned, unchanged; never ask the model to build ids |
| List tools | `limit` default 20, hard max 100, opaque `cursor`; return `next_cursor` or null |
| Output size | cap text at about 25,000 chars (roughly 6,000 tokens); when cut, say so and say how to narrow |
| Output shape | one object with stable keys; names and ids together; no HTML, no raw logs |
| Idempotency | state it in the description for every writer: "Safe to retry" or "Not idempotent: a retry creates a second record"; accept an optional `idempotency_key` on non-idempotent creators |
| Side-effect label | in the description and in annotations: read-only, writes, destructive, touches the outside world; annotations are hints and must never be the only guard (verify field names against modelcontextprotocol.io (unconfirmed)) |
| Destructive tools | name contains delete, remove, drop, purge, wipe, reset and the like; schema has required boolean `confirm`; the tool refuses when it is not true and returns what would be affected |
| Timeouts | answer within 30 s; for longer work return a job id plus a status tool |

### Error contract

Return tool failures as a tool result flagged as an error, not as a protocol error, so the model can read and recover (verify the flag name against modelcontextprotocol.io (unconfirmed)). Reserve protocol-level errors for malformed requests and unknown tools. The text of every failure follows one shape:

```json
{"error": {"code": "not_found", "message": "No ticket with id T-91.", "retryable": false, "hint": "Call search_tickets to find a valid id."}}
```

Codes: `invalid_argument`, `not_found`, `permission_denied`, `conflict`, `rate_limited`, `upstream_unavailable`, `internal`. Rules: `message` never contains a stack trace, token, path or SQL; `retryable` is true only for `rate_limited` and `upstream_unavailable`; `hint` names the next tool or argument to try.

## Security rules that apply to every server

- Secrets come from the environment or a secret store at start-up, never from tool arguments and never from the manifest. Never print them to stdout (stdio servers share stdout with the protocol) or into error text.
- Treat every argument as hostile: validate against the schema on the server too, resolve paths against an allow-listed root, use parameterised queries, never build shell strings from arguments.
- Treat fetched content (web pages, tickets, file text) returned to the model as untrusted: wrap or label it and never let it select which tool runs next inside your code.
- Least privilege: a read tool uses a read-only credential. One credential per server, scoped to what the tools need.
- Log to stderr or a file; log tool name, duration, outcome and caller id, never argument values that may hold personal data.

## Script

`scripts/validate_manifest.py MANIFEST.json [--max-desc N] [--min-desc N] [--strict]`: run it, do not edit it. Accepts an array of tools or an object with a `tools` array. Prints one strict JSON object: `ok`, `tools`, `errors`, `warnings`, `findings` (each with `tool`, `index`, `rule`, `severity`, `message`). Exit 0 no errors; 1 errors (or any warning with `--strict`); 2 unreadable or invalid input, printed as `{"ok": false, "error": ...}`.

Rules it applies: `name-not-snake-case`, `name-missing`, `name-too-long`, `name-duplicate`, `description-missing`, `description-too-long`, `description-too-short`, `description-no-when-to-use` (needs a phrase such as "Use when" or "Use this to"), `schema-missing`, `schema-type-not-object`, `schema-no-properties`, `schema-no-required`, `schema-required-invalid`, `schema-required-unknown`, `schema-additional-properties-unset`, `property-invalid`, `property-no-description`, `array-unbounded`, `destructive-no-confirm`, `confirm-not-boolean`, `confirm-not-required`, `tool-not-object`. Destructive verbs are read from the tool name only, after splitting camelCase, snake_case, kebab-case and dotted names into words (`deleteUser`, `purge-cache` and `WipeAllData` are all caught): delete, remove, drop, destroy, purge, wipe, erase, truncate, kill, revoke, terminate, overwrite, reset, format. Whole words only, so `formatter_options` is not flagged. The key read for the schema is `inputSchema` (a snake_case `input_schema` gives `schema-missing`).

Without Python, check the same list by hand against each tool.

## Report format

```
Server: <name>, transport <stdio|http>, auth <none|token|oauth>
Tools: <n> (read-only <n>, writers <n>, destructive <n>); resources <n>; prompts <n>
Manifest check: <ok true/false, errors, warnings, each warning kept and why>
Tests run: <classes from the test plan with result>; not run: <classes and why>
Unconfirmed protocol details used: <list, each marked verify against modelcontextprotocol.io>
Open risks: <secrets, auth gaps, unbounded outputs, anything unchecked>
```

## Limits

- The validator checks manifest hygiene only. It cannot judge whether descriptions are good enough for a model to choose correctly; test that with the harness.
- "Use when" detection is a phrase match; an unusual but good wording is reported as an error and may be accepted by the author with a note.
- Numeric thresholds (600 chars, 25,000 chars, 20/100 page sizes, 30 s, 8 to 15 tools) are working values, not protocol limits.
- Protocol and SDK details change between revisions. Anything marked unconfirmed must be checked against the current specification before it goes into code or documentation.
- Auth guidance covers the common shapes (none, static token, OAuth-style) and is not a security audit.
- The skill does not install, run or configure third-party servers.
