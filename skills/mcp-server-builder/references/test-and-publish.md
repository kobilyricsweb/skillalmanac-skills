# Test plan and publishing checklist

## Contents

1. Client harness
2. Seven test classes
3. Pass bar
4. Publishing checklist
5. Versioning rules

## 1. Client harness

Write a small script that acts as a client, using the official SDK client for your language (verify the current client API at modelcontextprotocol.io (unconfirmed)). It must be able to:

1. Start the server the way a user would (stdio: spawn the command from the README; HTTP: connect to a locally started instance).
2. Run the initialize handshake and record the server's declared name, version and capabilities.
3. List tools, resources and prompts and save the raw result as `manifest.json`, the input for `scripts/validate_manifest.py`.
4. Call a tool with given arguments and return the raw result, the error flag and the elapsed time.
5. Fail the test run when anything unexpected appears on stdout (stdio) or when the process exits early.

Keep the harness in the repository under `tests/` so a stranger can run it with one command.

## 2. Seven test classes

| # | Class | What to do | Example assertion |
|---|---|---|---|
| 1 | Handshake | Initialize, list everything | Name, version and capability list match the README |
| 2 | Manifest | Run the validator on the saved list | `ok` is true, zero errors |
| 3 | Happy path | One call per tool with typical arguments | Result parses, keys are stable, size under the cap |
| 4 | Bad input | Missing required argument, wrong type, extra argument, 10 MB string | Error result with code `invalid_argument`; process stays alive; no stack trace in the text |
| 5 | Side effects | Call each writer twice with the same arguments; call each destructive tool without and with `confirm` | Documented idempotency holds; no confirm means nothing changed |
| 6 | Bounds | Ask for a list with no limit, limit 1000, a cursor loop to the end | Default 20, capped at 100, cursor ends with null; output under 25,000 chars |
| 7 | Secrets and logs | Start with a canary secret in the environment; run classes 3 to 6; search every output, error and log for the canary | Zero hits |

Add, for HTTP: missing or wrong credential returns an auth failure; a request with a foreign `Origin` is refused; two clients at once do not see each other's data.

Add a model-in-the-loop check when a real client is available: give a model 10 realistic requests and the tool list; record which tool it picked. Target 9 of 10 correct first picks (working value). Every wrong pick is a description to rewrite, not a prompt to tune.

## 3. Pass bar

- Classes 1 to 7 all pass; any failure in 5 or 7 blocks publication.
- Validator reports zero errors; each remaining warning is listed with a reason.
- Cold start to first response under 5 s for stdio (working value); a typical tool call under 2 s, none over 30 s.
- The run is repeatable: two consecutive runs give the same results apart from timings and generated ids.

## 4. Publishing checklist

Copy and tick:

```
- [ ] README states: what it does, who it is for, tools in a table (name, one-line purpose, read-only or writer), transport, auth, required environment variables
- [ ] README has a copy-paste client configuration for each supported transport, with placeholders (never real secrets)
- [ ] README has 3 example conversations with real outputs from the harness
- [ ] README lists limits: page sizes, output cap, timeout, rate limit
- [ ] Safety section: which tools write, which are destructive, what confirm does, what the server never touches
- [ ] Manifest validator: zero errors; manifest.json saved in the repository
- [ ] Content scan for secrets across the whole repository, including history and examples
- [ ] LICENSE file; dependencies pinned and licence-checked
- [ ] Version number in one place, read by the server at start-up and reported in the handshake
- [ ] CHANGELOG with the tool changes of each release
- [ ] Install tested from a clean machine or container using only the README
- [ ] Issue contact or tracker link, and a note on supported protocol revisions
- [ ] Registry or directory listing prepared only if the owner decided to publish there (verify submission rules at modelcontextprotocol.io (unconfirmed))
```

## 5. Versioning rules

Use semantic versioning, treating the tool list as the public API.

| Change | Bump |
|---|---|
| New tool, new optional argument, new output key | minor |
| Description rewrite with no behaviour change | patch |
| Tool renamed or removed, argument removed or made required, output key removed or retyped, a read tool becoming a writer | major |
| New destructive tool | minor, and call it out in the CHANGELOG under "Safety" |

Rename by adding the new tool and keeping the old name as a deprecated alias for at least one minor release; say "Deprecated: use new_name" in the old description. Never reuse a removed name for a different job.
