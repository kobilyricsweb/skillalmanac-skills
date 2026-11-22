---
name: architecture-diagrams
description: Use when the user asks for an architecture diagram, system diagram, C4-style view, sequence diagram, data-flow or deployment sketch in Mermaid, or says the diagram is a mess or too big. Produces readable Mermaid text from a codebase or a description under fixed rules for abstraction level, naming, direction, grouping and what never shares a diagram, then validates it with a script that counts nodes and edges, flags orphans, duplicate ids and over-dense diagrams, and prints JSON. Do not use for rendering to images, ER or class diagrams, UML tooling, or drawing tools.
license: Apache-2.0
compatibility: The checker needs Python 3.9 or newer, standard library only. No network access is used. Without Python, apply the checklist in step 5 by hand.
metadata:
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
  license: Apache-2.0
---

# Architecture diagrams

Write Mermaid text that a new team member can read in under a minute and that matches the code. One diagram answers one question at one level of detail. When a second question appears, draw a second diagram.

## Workflow

Copy this checklist:

```
- [ ] 1 Fix the question, the audience and the level
- [ ] 2 Collect the facts, each with a source
- [ ] 3 Draft within the size budget
- [ ] 4 Apply the naming, direction and grouping rules
- [ ] 5 Validate, fix, validate again
- [ ] 6 Report
```

1. **Question, audience, level.** Write one sentence: "This diagram shows <what> for <who>." Pick the level from the table. Read [references/abstraction-levels.md](references/abstraction-levels.md) for the contents of each level and a starter template; read only the level you chose.

| Level | Shows | Mermaid form | Typical size |
|---|---|---|---|
| Context | the system as one box, people, external systems | `flowchart LR` | 4 to 9 nodes |
| Container | deployable or runnable parts and data stores inside the system | `flowchart LR` with one `subgraph` for the system boundary | 6 to 15 nodes |
| Component | parts inside one container | `flowchart TB`, one subgraph per layer or module group | 6 to 15 nodes |
| Interaction | one scenario over time | `sequenceDiagram` | 3 to 7 participants, up to 20 messages |
| Deployment | where containers run (regions, clusters, networks) | `flowchart TB` with nested subgraphs, depth 2 at most | 6 to 15 nodes |

2. **Facts with sources.** From a codebase, read the files that declare structure: compose or orchestration files, service entry points, route tables, queue and topic names, connection settings in config (names only, never secrets). Keep a private list `node or edge -> file:line`. Anything you cannot source is drawn dashed (`-.->`) with a label ending in `?`, and goes into the report as unverified. From a description alone, say so in the report and mark nothing as confirmed.
3. **Draft within budget.** Aim for 15 nodes or fewer and 25 edges or fewer. The checker warns above that and fails above 25 nodes or 40 edges (sequence: warns above 7 participants or 20 messages, fails above 10 or 30). Over budget means split by level or by scenario, never shrink the font. Fold anything that does not serve the question (logging, metrics, CI, utility libraries) into the diagram that is about it.
4. **Rules.**
   - Names. Ids are short ASCII words in `lower_snake` that name the thing (`orders_api`, not `A` or `svc-1`). Labels use the team's own noun, one line, under 40 characters; put the technology on a second line with `<br/>` when it matters. The same thing has the same label in every diagram of a set. Never use `end` as an id.
   - Direction. Put `LR` or `TB` on the first line, never leave it implicit. `LR` for request paths from user to data; `TB` for layers and ownership. Arrows point from the caller to the callee, not the way data moves; when they differ, say the data direction in the label (for example "reads orders").
   - Edges. Every edge in a system diagram has a label: the protocol or the verb. Use `-.->` for asynchronous or optional links and say so in the label; `==>` only for the one path the diagram is about.
   - Grouping. A `subgraph` is a real boundary (the system, a trust zone, a network, a team-owned service) and holds at least two nodes. Nest at most 2 deep. External systems and people sit outside the system boundary.
   - Style. No colour-only meaning. If you use `classDef`, name the class by what it means (`external`, `datastore`) and add a comment line saying so, since not every viewer applies the colours.
   - Quote any label that contains brackets, parentheses or colons: `db[("Orders DB")]`, `api["Orders API (v2)"]`.
   - Recommended, not checked by the script: put a comment on line 1 or 2: `%% level: container; scope: web shop; source: docker-compose.yml`.
5. **Validate.** Run:

```bash
python scripts/mermaid_check.py diagram.mmd
```

   A Markdown file with mermaid fences also works; each block is checked. Fix every `error`; fix every `warn` or state in the report why it stays. Re-run until the verdict is `pass`, or `warn` with each warning justified. Do not edit the script to change a verdict. If Python is not available, count nodes and edges by hand against the budget, check that every id appears in an edge, every `subgraph` has an `end`, and no two ids carry the same label.
6. **Report** in this shape, after the diagram:

```
Question: <the one-sentence purpose>
Level: <context|container|component|interaction|deployment>
Size: <nodes> nodes, <edges> edges (checker verdict: <pass|warn|fail>)
Sources: <files read>
Unverified: <dashed or ? items, or none>
Left out on purpose: <what was folded away and where it would go>
Not checked: <rendering, correctness against runtime behaviour>
```

## Never in one diagram

- Two levels: code symbols (functions, classes, file names) next to servers, queues or databases. The checker warns on `mixed_levels`.
- Runtime flow and deployment topology. "Who calls whom" and "where it runs" are different questions.
- A time-ordered scenario in a flowchart. Step numbers on edges mean it should be a `sequenceDiagram`.
- Two scenarios in one sequence diagram, or the happy path plus every error path. Draw the main path, then one separate diagram for a failure that matters.
- Current and planned architecture without a visible mark. Keep them in separate files.
- A hub that touches everything (an "Event Bus" or "Database" with 8 or more edges). Group its clients instead, or state the pattern in a sentence.
- Secrets, hostnames, IP addresses or account ids taken from config. Use the role name.

## Script

`scripts/mermaid_check.py <file> [--strict]`: run it, do not edit it. It prints JSON with `schema_version`, `verdict`, and per diagram `type`, `direction`, `metrics` (nodes, edges, subgraphs, max_nesting, max_degree, unlabeled_edge_ratio, max_label_chars), `orphans`, `duplicate_ids` and `findings` (level, code, line, message), plus the `thresholds` used. Exit 0 for pass or warn, 1 for fail (or warn with `--strict`), 2 for a missing, empty or unreadable file. Finding codes and the syntax pitfalls behind them are in [references/mermaid-pitfalls.md](references/mermaid-pitfalls.md); read it when a code is unclear or the user's Mermaid does not render.

## Limits

- The checker validates a subset: `flowchart`/`graph` and `sequenceDiagram`. Other types are reported as unsupported, not checked. Native Mermaid C4 blocks are not parsed; use flowchart subgraphs for C4-style views.
- It does not render, so it cannot prove the diagram renders in a given Mermaid version. A pass means no problem it knows about was found.
- It checks structure, not truth: a clean diagram can still show a wrong architecture. Correctness comes from step 2.
- Size thresholds are working values for readability, not measured optima. A dense diagram can be right for a specialist audience; say so in the report.
- Node shapes written with the newer `id@{ shape: ... }` syntax are accepted but their labels are not read.
- The infrastructure-word and step-number heuristics are English; labels in other languages still get the structural checks.
