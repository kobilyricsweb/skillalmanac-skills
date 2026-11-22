# Mermaid pitfalls and checker codes

Read this when a finding code is unclear, or when a diagram that the checker accepts does not render for the user. Syntax is described from the official Mermaid pages for flowcharts (mermaid.js.org/syntax/flowchart.html) and sequence diagrams (mermaid.js.org/syntax/sequenceDiagram.html); behaviour differs between Mermaid versions, so test in the user's renderer.

## Contents

- Finding codes
- Flowchart pitfalls
- Sequence pitfalls
- Thresholds

## Finding codes

| Code | Level | Meaning and fix |
|---|---|---|
| `syntax` | error | A line the parser cannot read. Check brackets, arrow spelling and stray characters. |
| `unsupported_type` | warn | Not a flowchart, graph or sequenceDiagram. Not checked here. |
| `empty_diagram` | error | No text, or a sequence diagram with no messages. |
| `bad_direction` | error | Direction after `flowchart` is not TB, TD, BT, LR or RL. |
| `unclosed_shape`, `unclosed_quote` | error | A shape bracket or a quoted label is never closed. |
| `unbalanced_subgraph`, `unbalanced_block`, `unbalanced_end`, `stray_branch` | error | A `subgraph` or block lacks `end`, an `end` has nothing to close, or `else`/`and` sits outside a block. |
| `duplicate_id` | error | The same id is defined with two different labels, a subgraph id repeats, a subgraph shares an id with a node, or a participant is declared twice. Mermaid keeps one definition and the diagram silently shows the wrong thing. |
| `reserved_id` | error | The id `end` in lowercase breaks the flowchart parser. |
| `too_dense` | error | More than 25 nodes or 40 edges (sequence: 10 participants or 30 messages). Split. |
| `dense` | warn | More than 15 nodes or 25 edges (sequence: 7 participants or 20 messages). |
| `orphan_node` | warn | A node or participant with no edges or messages. Connect it or remove it. |
| `duplicate_label` | warn | Two ids carry the same label: one thing drawn twice. Merge them. |
| `case_variant_ids` | warn | Ids that differ only by case, such as `DB` and `db`. They are separate nodes. |
| `hyphen_id` | warn | A hyphen inside an id. Some versions and tools split it; use underscores. |
| `ox_edge_pitfall` | warn | `---` followed directly by an id starting with o or x is read as a circle or cross edge. Add a space. |
| `risky_unquoted_label` | warn | Brackets or parentheses inside an unquoted label. Wrap the label in double quotes. |
| `no_direction` | warn | No direction after `flowchart`. State it. |
| `long_label` | warn | Over 40 characters. Shorten or move detail to a second line. |
| `deep_nesting` | warn | Subgraphs or blocks nested more than 2 deep. |
| `hub_node` | warn | One node touches 8 or more edges. |
| `unlabeled_edges` | warn | From 4 edges up, more than half have no label. |
| `sequence_in_flowchart` | warn | 3 or more edge labels start with a step number. Use a sequenceDiagram. |
| `opaque_ids` | warn | From 4 nodes up, more than half of the ids are one letter. |
| `mixed_levels` | warn | Code symbols and infrastructure words in one diagram. |
| `singleton_subgraph`, `empty_subgraph` | warn | A boundary around one node or none. |
| `undeclared_participant`, `late_declaration` | warn | Some participants declared, others only implied; or declared after first use. The lane order then follows first use. |
| `unbalanced_activation` | warn | More `+` activations than `-` deactivations for a participant, or the reverse. |
| `empty_message` | warn | A sequence message with no text. |

## Flowchart pitfalls

- A node defined once with a label can be referenced later by id alone. Redefining the id with a new label is the usual cause of "the wrong box appears".
- Special characters in an unquoted label (parentheses, braces, quotes, a semicolon) are a common cause of parse errors. Double quotes around the label avoid it.
- An edge to a subgraph id is allowed and draws to the boundary; the checker does not count the subgraph as a node.
- Edge text can be written `A -->|text| B` or `A -- text --> B`. The first is easier to read in source.
- Lines starting with `style`, `classDef`, `class`, `linkStyle` and `click` are skipped by the checker; they do not affect counts.
- Text after `%%` on its own line is a comment. Inline trailing comments are not reliable across versions; keep comments on their own lines.

## Sequence pitfalls

- A message needs a colon and text: `A->>B: text`. The arrow set the checker reads is `->`, `-->`, `->>`, `-->>`, `-x`, `--x`, `-)`, `--)`.
- `+` after an arrow activates the receiver, `-` deactivates the sender. They must balance.
- Participants used without a declaration appear in the order of first use; declare them all to control the layout.
- Block keywords supported: `loop alt opt par critical break rect box`, with `else`, `and`, `option` as branches and `end` to close.

## Thresholds

Warn and fail limits are in the `thresholds` field of the script output. They are working values chosen for one-screen readability. A deliberately large specialist diagram may exceed them; say so in the report instead of editing the script.
