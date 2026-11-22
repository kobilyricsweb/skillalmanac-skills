---
name: service-request-routing-table
description: "Use when incoming service requests must be assigned deterministically from supplied category, urgency, location, exception, precedence, role-directory, and fallback rules. Do not use for approval-path mapping, staffing allocation, form completeness, or choosing between overlapping rules without documented precedence."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.2"
  network: none
---

Build a deterministic routing table from the supplied categories, routing conditions, precedence clauses, role directory, and approved fallback. Normalize each rule into explicit conditions, destination, precedence, and exceptions. Apply precedence only when documented; otherwise mark overlapping matches ambiguous. Treat urgency overrides as operative only when their trigger and scope are defined.

For each test request, show matched rules, selected destination, applied precedence, fallback use, and any ambiguity or gap. Unknown or unmatched requests may go only to the approved fallback. If none is supplied, leave them unrouted. Select at most one destination unless the policy explicitly permits multiple routing.

Validate every named rule and fallback destination against the supplied directory when directory validation is required. Always report an explicit directory-validation finding: name missing destinations, state that validation cannot be completed when the directory is absent, or state that all named destinations are present. Record this finding in `input_gaps`, even when it is a positive finding, so directory validation is never merely implied by using listed names.

Do not infer routing authority from a role name or invent destinations, thresholds, locations, exceptions, or precedence. Preserve conflicting inputs. Keep approval authority, staffing capacity, and external dispatch outside scope.

Return the routing rules, request results, fallback behavior, input gaps including the directory-validation finding, and scope exclusions as JSON matching the [output schema](references/output-schema.json). Follow the [input contract](references/input-contract.md) and use the [worked example](references/worked-example.md) only as a synthetic illustration.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit 0 means structural validity, 1 contract violations, and 2 invalid input or unsupported contract. The bounded checker reads at most 2 MiB, 50,000 nodes, and depth 100; rejects duplicate keys and nonfinite or oversized numbers; and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
