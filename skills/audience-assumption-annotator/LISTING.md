# audience-assumption-annotator

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when reviewing a complete draft against a declared audience profile to identify evidenced assumptions about knowledge, access, motivation, or context and propose bounded clarifications. Do not use for procedural prerequisite mapping, speculative interface concerns, audience stereotyping, wholesale rewriting, or claims unsupported by the supplied draft and profile.

## Task boundary

technical-docs-writer audits documentation structure and examples, while plain-language-readability rewrites text for a stated reading level. audience-assumption-annotator does not broadly rewrite or score readability; it locates draft passages that presume knowledge, access, motivation, or context unsupported or contradicted by the supplied audience profile.

## Try the independent synthetic example

Annotate assumptions in this complete draft against the declared profile. Draft P1: “Open the dashboard and export the report as CSV.” P2: “Use the downloaded file for the meeting.” Audience: new contractors who understand reports but have view-only accounts. Known prerequisites: web browsing only. Available resources: dashboard access with viewing permission; no export permission. Excluded inference: do not infer motivation or technical ability from contractor status. Return passage-linked findings, evidence, likely consequence, bounded clarification, unresolved items, and coverage.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `aggregate_isolated_06239c7a7e681a84`:

```text
{"annotations":[{"passage":"Open the dashboard and export the report as CSV.","location":"P1","assumption_type":"access","evidence":"The audience has view-only dashboard accounts, and the available resources explicitly state that no export permission is provided.","status":"mismatch","consequence":"Readers can open and view the dashboard but cannot complete the CSV export.","bounded_clarification":"State who will export and provide the CSV, or replace the export instruction with a view-only action available to these accounts."},{"passage":"Use the downloaded file for the meeting.","location":"P2","assumption_type":"context","evidence":"P2 presumes a downloaded file exists, but the stated lack of export permission prevents the preceding download workflow from producing it.","status":"mismatch","consequence":"Readers will not have the referenced file for the meeting.","bounded_clarification":"Identify the accessible meeting resource, or state that an authorized person will provide the CSV before the meeting."}],"unresolved":[],"coverage":{"reviewed_locations":["P1 reviewed: opening and viewing the dashboard require no annotation because dashboard access with viewing permission is supplied; exporting as CSV is annotated because export permission is explicitly unavailable.","P2 reviewed: reliance on the downloaded file is annotated because the supplied access cannot produce it.","No motivation or general technical-ability assumptions were inferred from contractor status. The statement that readers understand reports supports ordinary report use, while web browsing is the only stated technical prerequisite."],"unavailable_inputs":[]}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
