# Listing page content: architecture-diagrams

**One line:** Writes Mermaid system and sequence diagrams that stay readable, and checks them for size and structure.

## What it does

The skill gives an agent a six-step procedure: fix the question and the level (context, container, component, interaction, deployment), collect sourced facts from the code, draft inside a size budget, apply naming, direction and grouping rules, validate, and report. A checker script parses a Mermaid file (flowcharts with subgraphs, and sequence diagrams), counts nodes and edges, and prints strict JSON with orphans, duplicate ids and findings such as over-density, hub nodes, unlabeled edges, mixed abstraction levels and unbalanced `subgraph`/`end`. Nothing is rendered and nothing is sent anywhere.

## Capabilities

- `scripts/mermaid_check.py`: JSON report per diagram (type, direction, node, edge and subgraph counts, nesting, orphans, duplicate ids, findings with line numbers, the thresholds used); works on `.mmd` files and on Markdown files with several mermaid fences
- Size budgets: warn above 15 nodes or 25 edges, fail above 25 nodes or 40 edges; sequence warn above 7 participants or 20 messages, fail above 10 or 30
- A "never in one diagram" list (code symbols with infrastructure, runtime with deployment, two scenarios in one sequence, secrets from config)
- Starter templates per level and a table of every finding code with its fix
- A fixed report: question, level, size, sources, unverified items, what was left out, what was not checked

## When to use

You ask for an architecture or system diagram, a C4-style view, a sequence diagram, a data-flow or deployment sketch in Mermaid, from a repo or from a description, or you say the diagram is a mess or too big.

## When not to use

Rendering to PNG or SVG, ER or class diagrams, UML tools, slide-deck graphics, or choosing between architectures. The checker reports other Mermaid types as unsupported, not as valid.

How it differs from neighbours in the catalogue: no other skill here draws or validates diagrams; this one is not a general design-review or documentation skill.

## Requirements

Python 3.9 or newer for the checker (standard library only). No network. Without Python the agent applies the manual checklist in the skill.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved agent-written diagram to show. What exists is the checker on the saved fixtures (`python evals/run_fixtures.py`, 8 of 8 cases pass):

1. `python scripts/mermaid_check.py evals/fixtures/good_flow.mmd`: verdict `pass`, flowchart, direction `LR`, 7 nodes, 6 edges, 1 subgraph, no orphans, no findings, exit 0.
2. `python scripts/mermaid_check.py evals/fixtures/bad_flow.mmd`: verdict `fail`, exit 1. Findings: `unbalanced_subgraph` (error, line 2), `duplicate_id` (error, line 11, `api` redefined as "Billing API"), `no_direction`, `duplicate_label` twice, `orphan_node` for `api2` and `lonely`, `risky_unquoted_label` for `Cache (Redis)`.
3. `python scripts/mermaid_check.py evals/fixtures/dense_flow.mmd`: verdict `fail`, one `too_dense` error: 26 nodes against a hard limit of 25.

## Limits

- Checks a subset: flowchart/graph and sequenceDiagram; native Mermaid C4 blocks and other types are not parsed.
- Does not render, so a pass does not prove the diagram renders in a given Mermaid version.
- Checks structure, not truth: a clean diagram can show a wrong architecture.
- Thresholds are working values for readability, not measured optima.
- Heuristics for infrastructure words and step numbers are English.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and the 8 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, rendering in a real Mermaid version, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Give the agent a compose file; it states the question and level (container) and lists the files read.
2. It drafts the diagram, then runs the checker: a `dense` or `unlabeled_edges` warning appears.
3. It fixes the warning (labels the edges, folds the metrics stack) and re-runs: verdict `pass`.
4. It prints the report, including the unverified items and what was left out.

## FAQ seeds

- Does it render the diagram? No. It produces Mermaid text and validates it; render it in your editor or the Mermaid live editor.
- Does it need network access? No.
- Will a pass guarantee my renderer accepts it? No; the checker knows a subset of the syntax and does not run Mermaid.
- Can it read my codebase and draw it? The agent reads the structural files and cites them in the report; anything it cannot source is marked unverified.
- Why does it limit me to 15 nodes? Larger diagrams stop being read; the numbers are adjustable only by splitting the diagram, and a deliberate exception is stated in the report.
- Does it support native Mermaid C4 syntax? Not in the checker; it draws C4-style views with flowchart subgraphs.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.

## Behaviour notes (fix round 2026-11-21)

- A Mermaid type the script does not parse (for example erDiagram or classDiagram) is reported as `unsupported_type` at warn level, so a file whose only fault is an unsupported block no longer fails.
- `mixed_levels` fires when even one code symbol (function, class or file name) shares a diagram with one infrastructure label.
- The `%% level:` comment is a recommendation; the script does not check it. Colour-only meaning in `classDef` is not detected either.
