# source-note-to-outline

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when turning labeled source notes into a traceable content outline with unsupported sections left as research gaps. Do not use for external research, factual certification or an unrestricted article rewrite.

## Task boundary

abstract-structure-builder writes bounded abstracts, faithful-summary-writer summarizes and research-synthesis combines research; this builds a source-traced outline with explicit research gaps from labeled notes.

## Try the independent synthetic example

Create a traceable outline from these notes. Notes: N1: "Aster exports reports as CSV." N2: "Aster keeps exported files for one day." Purpose: brief new support agents. Requested sections in order: Export format; Retention; Pricing. Use only the notes and return a basis summary, outline, gaps, conflicts, and verification.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_c864bb4806b3`:

```text
{"basis_summary":{"note_ids":["N1","N2"],"purpose":"Brief new support agents","purpose_status":"supplied"},"outline":[{"heading":"Export format","purpose":"State the supplied export format.","support_status":"supported","supporting_note_ids":["N1"],"subpoints":[{"text":"Aster exports reports as CSV.","evidence_kind":"direct","note_ids":["N1"]}]},{"heading":"Retention","purpose":"State the supplied retention period.","support_status":"supported","supporting_note_ids":["N2"],"subpoints":[{"text":"Aster keeps exported files for one day.","evidence_kind":"direct","note_ids":["N2"]}]},{"heading":"Pricing","purpose":"Identify pricing information needed for support agents.","support_status":"gap","supporting_note_ids":[],"subpoints":[]}],"gap_register":[{"section":"Pricing","reason":"No note supplies pricing information.","research_question":"What pricing information should support agents have, and what source supports it?"}],"conflict_register":[],"verification_report":{"substantive_points_traced":true,"unsupported_requested_sections_isolated":true,"note_instructions_executed":false,"omissions":[]}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
