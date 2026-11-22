# Protocol notes and unconfirmed items

Written from the authors' knowledge of the protocol; no live specification was fetched while writing this skill. Everything below is in the authors' own words.

## Contents

1. Sources to check
2. Statements the skill relies on, with confidence
3. Items marked "verify against modelcontextprotocol.io (unconfirmed)"

## 1. Sources to check

- https://modelcontextprotocol.io/specification : the versioned specification; open the revision the target clients support.
- https://modelcontextprotocol.io/docs : introductory and how-to material, including server quick starts.
- https://github.com/modelcontextprotocol : the official SDKs and the reference servers, useful for current client and server APIs.
- https://json-schema.org/ : the schema vocabulary used for tool inputs.

## 2. Statements the skill relies on

| Statement | Confidence |
|---|---|
| Messages are JSON-RPC 2.0; a session starts with an initialize exchange where both sides declare capabilities and a protocol version | High |
| Servers can offer three primitives: tools (model-controlled), resources (application-controlled) and prompts (user-controlled) | High |
| With stdio the client launches the server and messages travel over stdin and stdout, so stdout must carry only protocol messages and logs go to stderr | High |
| Tool inputs are described by a JSON Schema object | High |
| Tool execution failures are reportable inside a normal tool result with an error flag, separately from protocol errors | Medium: confirm the flag name and when each kind applies |
| Tools can carry advisory annotations (read-only, destructive, idempotent, open-world hints) that clients must not trust blindly | Medium: confirm names and status |
| HTTP servers should validate the Origin header and bind to localhost when run locally | Medium: confirm current wording |
| HTTP authorization follows OAuth-style flows with the server acting as a protected resource | Medium: confirm the revision and required metadata |

## 3. Items marked "verify against modelcontextprotocol.io (unconfirmed)"

| Item | Question to ask the current spec |
|---|---|
| Client support for resources and prompts | Which major clients surface them; is a tool fallback still needed |
| Tool annotation field names | Exact keys and defaults |
| Error flag on tool results | Exact key; interaction with structured output |
| Standard HTTP transport name and session behaviour | Which transport is standard; how sessions and resumption work |
| Authorization section | Token audience rules, discovery documents, dynamic client registration |
| Official client API for the harness | Class and method names in the SDK for the chosen language |
| Registry or directory submission | Whether one exists, its format and review process |
| Allowed characters and length for tool names | Whether the spec states limits beyond this skill's snake_case rule |
| Structured output and output schemas | Whether tools can declare output schemas and how clients validate them |
