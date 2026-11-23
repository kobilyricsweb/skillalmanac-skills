# testimonial-use-readiness

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when reviewing supplied testimonial material for attribution, permission, excerpt scope, edits, duration, and placement readiness. Do not use for conducting interviews, eliciting new testimonials, designing a case-study interview, authenticating claims, assessing legal validity, or predicting campaign performance.

## Task boundary

copywriting-landing-pages audits proof and claims as part of landing-page copy. testimonial-use-readiness does not write the page or authenticate testimonial claims; it checks exact excerpt continuity and whether supplied permission covers attribution, edits, placement, audience, duration, and usage limits.

## Try the independent synthetic example

Review this supplied testimonial use. testimonial_text: Ana Ruiz: "Setup took one day, and support answered twice." permission_terms: Ana permits exact excerpts on the public homepage from November 1, 2026 through January 31, 2027, attributed as "Ana Ruiz, Pico Labs"; no wording edits. attribution_preference: Ana Ruiz, Pico Labs. proposed_placement: public homepage testimonial block for prospective customers on November 21, 2026. intended_excerpt: "support answered twice." Produce the readiness record, blockers, decision summary, and fact trace. Keep source words distinct from the proposed excerpt, note whether its capitalization is an edit covered by permission, and identify anything outside this readiness review. Do not assess whether the claim is true or effective.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `aggregate_isolated_fc876c76d1fdc789`:

```text
{"readiness_records":[{"exact_words":"Setup took one day, and support answered twice.","proposed_excerpt":"support answered twice.","attribution_terms":"Ana Ruiz, Pico Labs","claim_scope":"A statement that support answered twice in Ana Ruiz’s described experience.","edit_disclosure":"The proposed excerpt is an exact contiguous substring of the testimonial. Its lowercase initial matches the source position after ‘and ’, so capitalization has not been edited. No wording edit is proposed.","placement":"Public homepage testimonial block for prospective customers on November 21, 2026","status":"ready","blocker":null}],"blockers":[],"decision_summary":"The proposed exact excerpt, attribution, public-homepage placement, audience, and November 21, 2026 use date are covered by the supplied permission. The use is ready within the stated permission period.","fact_trace":[{"conclusion":"The proposed excerpt is exact and contains no capitalization edit.","supplied_evidence":"The testimonial contains the contiguous text ‘support answered twice.’ with a lowercase ‘s’ at that source position."},{"conclusion":"The excerpt form and attribution are covered.","supplied_evidence":"Ana permits exact excerpts attributed as ‘Ana Ruiz, Pico Labs,’ which matches the proposed excerpt and attribution preference."},{"conclusion":"The placement, audience, and date are covered.","supplied_evidence":"Permission covers the public homepage from November 1, 2026 through January 31, 2027; the proposal is a public homepage testimonial block for prospective customers on November 21, 2026."},{"conclusion":"No wording-edit permission is needed for this proposal.","supplied_evidence":"Although permission prohibits wording edits, the excerpt reproduces an exact contiguous portion of the source."}],"limits":["This review does not assess legal validity, consent authenticity, claim truth, typicality, effectiveness, or campaign performance.","Readiness applies only to the supplied excerpt, attribution, placement, audience, and proposed use date; broader or later uses were not reviewed."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
