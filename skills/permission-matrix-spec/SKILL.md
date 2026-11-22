---
name: permission-matrix-spec
description: "Use when supplied role, resource, operation, condition, exception, and default-rule notes must be organized into an application permission matrix. Do not use for sequencing organizational approvals, inferring permissions from job titles, or changing access controls."
license: Apache-2.0
metadata:
  author: "Skill Almanac Editorial"
  version: "0.1.0"
  network: "none"
  license: "Apache-2.0"
  author_model: "gpt-5.6-luna"
---

Extract roles, resources, operations, permission statements, conditions, exceptions, default rules, and source labels from the supplied notes. Build one cell for each requested role-resource-operation combination. Classify cells as allow, deny, conditional, unspecified, or conflict. Absence of an allow statement remains unspecified unless a supplied default-deny rule applies. Apply conditions only where the notes attach them to that role, resource, and operation; do not generalize from similar wording.

When statements conflict, preserve both sources and mark the cell conflict unless an explicit precedence or exception resolves it. A conditional cell must state its condition and any evidence for the condition. If a default rule fills unmentioned cells, identify that rule in the evidence column rather than presenting the result as an explicit role statement.

Produce a resource-operation matrix plus a notes section for conflicts, unresolved conditions, and missing dimensions. If roles, resources, operations, or default behavior are missing, ask for them or provide a clearly partial matrix. Do not infer permission from a title, organizational seniority, or unrelated approval authority. Do not edit access settings, call an authorization service, or claim that the matrix reflects runtime behavior. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
