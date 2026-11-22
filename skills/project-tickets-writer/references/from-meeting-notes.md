# Turning meeting notes into tickets

Read this only when the source is notes, a chat log or a transcript.

1. Tag every line with one of: `DECISION` (something chosen), `ACTION` (a named person must do something), `WISH` (someone would like), `QUESTION` (unresolved), `CONTEXT` (background).
2. Only `DECISION` and `WISH` lines produce tickets or criteria. A `WISH` becomes a ticket only after the user confirms it is in scope; otherwise list it under open items.
3. An `ACTION` owned by an engineer becomes a ticket if it changes the product. An `ACTION` to "talk to X" or "send the deck" is not a ticket; leave it out and mention the count in the report.
4. A `QUESTION` blocks the tickets that depend on its answer. Either ask it (one of your three questions) or write the assumption and mark `ASSUMED:`.
5. Quantities in notes are often rough ("about a minute"). Keep the number in the criterion and mark it `ASSUMED:` if no one confirmed it.
6. Two speakers disagreeing without a decision is a `QUESTION`, never a criterion.
7. Keep a trace: put the note line number or speaker in the report, so a stakeholder can check a ticket against what was said.
