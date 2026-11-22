# Decision tables

## Contents

1. Tool, resource or prompt: edge cases
2. Transport: stdio or HTTP
3. Auth and secrets by deployment shape
4. Splitting and merging tools

## 1. Tool, resource or prompt: edge cases

| Situation | Choose | Reason |
|---|---|---|
| "Get the current config" with no arguments | Resource, plus a thin read tool if clients ignore resources | A fixed address the app can attach; the tool covers clients that only list tools |
| "Search" of any kind | Tool | Arguments vary and the model decides when |
| Result changes on every call (clock, queue depth) | Tool | A resource implies a stable thing to subscribe to or cache |
| Large document the user picks from a list | Resource with a template URI | The user or app picks; the model need not spend a call |
| "Summarise this week's incidents" the user triggers on purpose | Prompt that embeds a resource | Starts from the user, carries fixed instructions |
| Create, update, send, delete | Tool | Side effects belong to tools only |
| Same read exposed as both tool and resource | Allowed, give the tool a different job (search) than the resource (fetch by id) | Identical twins confuse tool choice |
| A prompt that always calls the same tool | Drop the prompt, fix the tool description | The description is doing the prompt's job badly |

Who controls each primitive: tools are picked by the model, resources by the application or user, prompts by the user. Confirm the current wording of these roles and any newer primitives at modelcontextprotocol.io (unconfirmed).

## 2. Transport: stdio or HTTP

| Question | stdio | HTTP (streamable) |
|---|---|---|
| Who runs the process | The client launches it as a child process | You host it; clients connect by URL |
| Users | One user, one machine | Many users, many machines |
| Auth | Inherits the launching user's environment; secrets via environment variables | Needs real auth on every request |
| Setup for the user | Install a runtime or binary and add a config entry | Paste a URL and sign in |
| Updates | Every user must upgrade | You deploy once |
| Network exposure | None | Public or internal endpoint to defend |
| Stdout | Reserved for protocol messages; one stray print breaks the session | Free for logs, but still log to stderr or a file |
| Scaling and state | Process per client; state dies with it | Needs session or stateless design; behind a load balancer prefer stateless |
| Local file or device access | Natural | Only through a local agent you ship |
| Debugging | Easy: run it in a terminal | Needs request logs and a tracing id |

Default rule: stdio for tools that touch the user's own machine (files, git, local databases); HTTP for a shared SaaS or team resource. Shipping both from one codebase is common: keep tool logic transport-free and add two thin entry points.

For HTTP servers, treat these as required until a source says otherwise: bind to 127.0.0.1 when running locally, validate the `Origin` header to defeat DNS rebinding, require auth on every request. Older HTTP-plus-event-stream transports exist in old tutorials; check which transport the current revision names as standard (verify against modelcontextprotocol.io (unconfirmed)).

## 3. Auth and secrets by deployment shape

| Shape | Auth | Secret handling | Never |
|---|---|---|---|
| Local stdio, wraps a service the user already has a key for | None on the protocol; key via environment variable named in the README | Read at start-up; fail fast with a clear message if absent | Accept the key as a tool argument; echo it back |
| Local stdio, wraps files | None; restrict to allow-listed root directories | n/a | Follow symlinks out of the root |
| Remote HTTP, one team, internal | Static bearer token per client, rotated at least every 90 days (working value) | Store hashed server-side; per-client tokens so one can be revoked | One shared token in a public README |
| Remote HTTP, many users, acts on their data in a third-party service | OAuth-style flow per user; the server validates access tokens issued for it (verify the current authorization section at modelcontextprotocol.io (unconfirmed)) | Store the upstream refresh token encrypted; request the narrowest scopes | Pass a client's token straight through to another service |
| Remote HTTP, public read-only data | Optional; apply rate limits per client | n/a | Unlimited anonymous writes |

Checks that apply to every row:

1. The manifest and README contain no secret values; run a content scan for key shapes before publishing (for example `AKIA[0-9A-Z]{16}`, `-----BEGIN .* PRIVATE KEY-----`, `sk-` followed by 20 or more characters).
2. Error text and logs contain no tokens, cookies or connection strings.
3. A tool that can act for the user on a third party is labelled "touches the outside world" and needs its own confirm if it sends, pays, posts or deletes.
4. Rate-limit per caller, not just per server: 60 calls per minute per caller is a reasonable starting value (working value).

## 4. Splitting and merging tools

| Symptom | Action |
|---|---|
| A tool has a `mode` or `action` argument with 3 or more values | Split into one tool per action |
| Two tools differ only by one filter | Merge into one tool with an enum |
| Descriptions of two tools start with the same sentence | Rewrite so each says when NOT to use it, or merge |
| The model calls tool A then always tool B | Return B's data from A, or add the id to A's output |
| The model passes the wrong id type | Return the exact id the next tool needs, with a label |
| More than 30 tools | Group into separate servers by user job; connect only the groups needed |
