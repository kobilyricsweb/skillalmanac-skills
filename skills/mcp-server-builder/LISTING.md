# Listing page content: mcp-server-builder

**One line:** Helps an agent design a Model Context Protocol server correctly and validates its tool manifest.

## What it does

The skill gives an agent a seven-step procedure for building an MCP server: write a brief, sort every capability into tool, resource or prompt, draft the manifest, validate it, pick transport and auth, test with a client harness, and run a publish checklist. It carries concrete defaults an agent would otherwise improvise: description length, page sizes, output caps, a fixed error contract, a destructive-tool confirm rule and a semantic-versioning table for tool changes. A script checks a tool manifest for 22 named problems and prints strict JSON. Protocol facts the authors could not confirm are marked "verify against modelcontextprotocol.io (unconfirmed)" and listed in one reference file.

## Capabilities

- `scripts/validate_manifest.py`: names, duplicates, "Use when" wording, description size, schema shape, `additionalProperties`, unbounded arrays, destructive verbs without `confirm`; JSON report with exit codes 0, 1 and 2
- Decision tables for tool vs resource vs prompt, stdio vs HTTP, auth by deployment shape, splitting and merging tools
- A seven-class test plan with a client-harness spec and a pass bar
- A publishing checklist and versioning rules
- A fixed report format

## When to use

You are building, extending or reviewing an MCP server, want to expose an API or database to an agent, or the model keeps choosing the wrong tool.

## When not to use

Installing or configuring someone else's MCP server, comparing servers, or building an agent or chatbot that only consumes tools. How it differs from the existing `coding-agent-guardrails` and `workflow-automation-builder` skills: those do not cover server-side tool design or manifest validation.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent applies the rule list by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both come from the saved fixture run (`python evals/run_fixtures.py`, 7 of 7 cases pass).

1. `python scripts/validate_manifest.py evals/fixtures/bad_manifest.json`: 5 tools, 8 errors, 9 warnings, exit 1. Includes `name-not-snake-case` for `SearchTickets`, `destructive-no-confirm` for a `delete_ticket` with no `confirm`, `name-duplicate`, and `schema-type-not-object`.
2. `python scripts/validate_manifest.py evals/fixtures/good_manifest.json`: 3 tools, `"ok": true`, no findings, exit 0.

No with-skill agent run exists yet, so there is no saved design to show.

## Limits

- The validator checks manifest hygiene, not whether descriptions help a model choose.
- "Use when" detection is a phrase match.
- Numeric thresholds are working values, not protocol limits.
- Protocol and SDK details change between revisions; items marked unconfirmed must be checked.
- Auth guidance is not a security audit.

## Evidence

See `VERIFICATION.md`. Static lint and 7 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour, native discovery, cross-tool installs, human review, live protocol accuracy.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a manifest with `SearchTickets`, a `delete_ticket` without `confirm` and a vague description.
2. Run the validator: 8 errors listed by tool and rule.
3. The agent fixes names, adds `confirm`, rewrites descriptions with "Use when", bounds arrays.
4. Re-run: `"ok": true`. Show the report, including the unconfirmed protocol items.

## FAQ seeds

1. Does it need network? No.
2. Does it work with any language or SDK? The rules are language-neutral; the script reads a JSON manifest.
3. Is the manifest check enough to call a server safe? No; it checks hygiene only.
4. Which protocol revision does it target? None is pinned; unconfirmed details point to the live specification.
5. How is it different from reading the specification? It adds defaults, tables, a test plan and a checker the specification does not give.
6. What data leaves my machine? None from the script.
7. How do I uninstall? Delete the folder.

## Changelog

0.1.0, 2026-11-21: first draft; static and fixture checks only.

## License and authorship

Apache-2.0, Copyright 2026 Global Media Holdings. Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
