---
name: case-study-interview-kit
description: "Use when preparing neutral customer-interview questions, fact-confirmation requests, evidence requests, quotation-permission prompts, and optionally a timed agenda from supplied case-study material. Do not use to invent statements, grant publication rights, conduct market research, or make legal or causal conclusions."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

# Case Study Interview Kit

Create a tailored interview guide for gathering case-study material while separating customer statements, company assumptions, supplied records, and unknowns.

Parse the supplied outcome summary into baseline, change, timeframe, method, measure, source, and ownership. Label each item and do not upgrade an assumption into a result. Draft neutral questions about what happened, when, for whom, how it was measured, alternatives, conditions, limitations, and counterexamples. Add targeted follow-ups for missing baselines, denominators, dates, scope, causality, implementation effort, and evidence.

Add fact-confirmation prompts and quotation-permission prompts covering wording, attribution, role, organization, editing boundaries, channels, and approval status as questions only. Respect approved topics and restrictions; an unsupported claim outside the approved topics is an internal clarification item, not permission to expand the interview.

If a time cap is supplied, include a proposed timed core agenda whose estimated allocations total no more than that cap, with opening, questions, evidence, and permission follow-ups. Mark allocations as planning estimates and label extra questions optional/outside the core time box.

Return JSON matching the output schema: context, source items, core questions, fact confirmations, permission prompts, evidence requests, unresolved items, and timed agenda when applicable. Do not invent quotes, outcomes, permissions, legal compliance, customer results, or causal conclusions.

Return JSON matching the [domain output contract](references/output-schema.json); the [synthetic shape example](references/schema-example.json) is an illustration, not executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.

Resources: [input contract](references/input-contract.md), [worked example](references/worked-example.md).
