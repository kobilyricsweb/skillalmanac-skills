---
name: log-message-contract-review
description: "Use when reviewing proposed log templates against declared event fields, redaction rules, required diagnostic context, and severity guidance. Do not use for runtime verification, configuration-drift explanations, incident diagnosis, or inferring behavior from emitted logs."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

Review only the supplied log templates, event definitions, required-context list, redaction policy, and severity guidance. Treat each template as a static contract; do not request secrets, execute code, inspect runtime output, or infer that a template proves production behavior.

Produce a review table with one row per template. Include the event identifier, declared fields found, required fields missing, prohibited fields present, severity supplied, severity assessment, repair notes, and unresolved questions. Evaluate field names exactly as declared. Mark a field as missing only when the required list names it and the template does not. Mark a field as prohibited only when the policy names it. If severity guidance is absent, conflicting, or inapplicable, report that condition rather than choosing a severity.

Preserve uncertainty when event identity, field meaning, or policy scope is ambiguous. If inputs conflict, show the conflict and avoid silently reconciling it. If templates or definitions are missing, return an incomplete review naming the missing inputs. Verify the report by checking every supplied template against every applicable required and prohibited list, then state that the result assesses declared contracts only and does not establish runtime behavior.

For each repair note, propose the smallest contract-level change supported by the inputs. Do not invent fields, policies, identifiers, or operational remedies. Use [input contract](references/input-contract.md) and [worked example](references/worked-example.md) as supporting references.

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
