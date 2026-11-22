# question-to-source-routing-guide

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when routing recurring questions to a supplied source inventory under explicit authority, precedence, evidence, freshness, and fallback rules. Do not use for answering the questions, inferring authority from titles or recency, converting source notes into prose, or changing sources, policies, or operational settings.

## Task boundary

Nearest is source-note-to-outline; this routes future questions to sources rather than organizing notes into prose.

## Try the independent synthetic example

Build a routing guide for the question "How do staff reset a VPN password?" Source inventory: KB1 is the IT procedure for VPN password resets; NOTE1 is a team tips note. Authority rule R1 says KB1 is primary for VPN reset procedures and NOTE1 may be used only when KB1 is unavailable. Update dates: KB1 2026-11-10; NOTE1 2026-11-15. The supplied fallback is NOTE1. Acceptable evidence is the reset procedure recorded in the authorized source. Include the route, freshness cue, fallback, basis, exceptions, and verification report.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_43ab592dfb69`:

```text
{"routes":[{"question_pattern":"Questions about resetting a VPN password","requested_information":"The authorized VPN password-reset procedure","route_status":"resolved","selected_source":"KB1","acceptable_evidence":["The reset procedure recorded in KB1"],"freshness_cue":{"status":"known","update_date":"2026-11-10","note":"KB1 has a supplied update date; no age threshold was provided."},"fallback":"NOTE1","basis":["R1 makes KB1 primary for VPN password-reset procedures.","NOTE1 may be used only if KB1 is unavailable."]}],"exceptions":[],"verification_report":{"coverage":"full","uncovered_questions":[],"unsupported_inferences_avoided":["NOTE1 was not preferred because it is newer.","The question was routed without answering it."],"unresolved_items":[]}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
