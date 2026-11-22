---
name: escalation-trigger-catalog
description: "Use when an operational policy must be converted into observable escalation triggers with thresholds, evidence, destinations, timing, and explicit non-triggers. Do not use for approval-path mapping, inventing severity levels, diagnosing incidents, or filling policy gaps with industry norms or personal judgment."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.4"
  network: none
---

Convert the supplied escalation policy into a trigger catalog. For each documented trigger, record the observable condition, exact threshold or count, evidence, destination, timing, supplied boundary or non-trigger, source trace, and policy gap.

Preserve measurement windows, repetition requirements, comparison operators, units, exceptions, and overrides exactly. “Exceeds 25 for two consecutive checks” is not “reaches 25 once.” Distinguish trigger conditions from evidence requirements: repeated observations do not establish an evidence source unless the policy says they do. Distinguish triggers from warnings, recommendations, examples, and quoted data. A non-trigger example does not establish the full converse of a rule.

For every missing severity, threshold, evidence source, destination, or timing definition, use the contract’s missing representation and identify the exact information needed. If policy statements conflict or remain ambiguous, report the conflict and do not choose a value. Do not infer a threshold or evidence source from an example or supply an industry default.

Evaluate each supplied example as `triggers`, `does_not_trigger`, or `cannot_determine`, citing the controlling condition and exception. In `verification_report`, record a check for every catalog field and controlling operator, window, repetition count, and boundary; mark each `preserved`, `unresolved`, or `conflicting` and identify its source and any issue.

Always list alert design or implementation, sending notifications, incident diagnosis, and performing or authorizing an escalation in `outside_scope`; the catalog is analysis, not execution. Use the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return JSON matching the [domain output schema](references/output-schema.json). The [synthetic JSON example](references/schema-example.json) illustrates shape only and is not executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema. The checker validates structure, not facts or judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
