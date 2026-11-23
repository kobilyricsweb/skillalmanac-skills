# channel-format-adaptation-brief

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when one approved source message must be planned for multiple channels with supplied limits, protected phrases, qualifiers, format cues, and CTA rules. Do not use for asset discovery, claim invention, qualifier removal, publication, or full campaign planning.

## Task boundary

message-asset-reuse-map plans reuse, social-content-kit produces social assets and copywriting-landing-pages writes landing copy; this maps permitted adaptations of supplied approved content to channel constraints.

## Try the independent synthetic example

Create an adaptation brief, not final copy. Approved source message: "Workshop registration is open for staff through 30 November 2026, subject to 20 available seats." Channel: intranet card, maximum 40 words, plain text with one short heading. Required qualifier: "subject to 20 available seats." Permitted CTA: "Register." Protected phrase: "through 30 November 2026." Report retained elements, allowable compression, format cues, omissions with reasons, CTA status, feasibility, and unresolved gaps.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_3d2db961425b`:

```text
{"source_scope":"Workshop registration is open for staff through 30 November 2026, subject to 20 available seats.","channels":[{"channel":"intranet card","budget":"Maximum 40 words","retained_elements":["Workshop registration","Staff audience","through 30 November 2026","20-seat availability limit"],"allowable_compression":["Shorten connective wording while preserving audience, date, and seat limit."],"format_cues":["Plain text","One short heading"],"protected_phrases":["through 30 November 2026"],"required_qualifiers":["subject to 20 available seats."],"omissions":[],"cta_status":"authorized","permitted_cta":"Register.","feasibility":"feasible","unresolved_gap":null}],"unresolved_gaps":[],"rejected_instructions":[]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
