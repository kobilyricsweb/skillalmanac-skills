---
name: idempotency-key-behavior-spec
description: "Use when converting supplied idempotency-key scope, retention, replay, payload comparison, and error rules into a bounded behavior matrix. Do not use for retry-budget audits, live payment diagnosis, proving retry safety, or filling undocumented duplicate-request behavior by assumption."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

Construct a behavior matrix from supplied idempotency-key scope, retention, replay, payload comparison, and documented error rules. Cover first request, exact replay within retention, changed-payload replay, concurrent duplicate, and request after expiry. For every cell record the supplied outcome, cell-specific comparison basis, response behavior, timing condition, evidence, and contract status. Use the cell-specific comparison basis when supplied; otherwise inherit the global basis only when the input clearly applies it to that cell.

Use “specified” only when the input directly states the behavior. Use machine status “unspecified” together with an explicit entry in unspecified_questions for undocumented cases. Do not infer global uniqueness, retry safety, durable responses, or duplicate rejection. Keep scope explicit. If inputs conflict, preserve both rules and mark affected cells “conflicting.” If retention or comparison is missing, identify affected cells and missing decisions.

Do not execute requests, inspect stores, calculate retry budgets, or prescribe production actions. Verify every required scenario against every supplied rule and confirm that no undocumented cell was silently completed. State that the matrix is a proposed contract representation, not evidence of implementation. Include [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return JSON matching [references/output-schema.json](references/output-schema.json). Each scenario item includes its own nullable comparison_basis; the global value is only a default where applicable. [references/schema-example.json](references/schema-example.json) shows the shape. Do not treat examples as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
