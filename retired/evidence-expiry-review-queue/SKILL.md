---
name: evidence-expiry-review-queue
description: "Use when supplied evidence records have review periods or supersession rules and a collection needs an orderly attention queue. Do not use to declare evidence false, refresh one page’s content, or invent review dates, priority rules, labels, or supersession conclusions."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

Read evidence records, record dates, review or supersession rules, dependent-item links, and the supplied priority policy. For each record, calculate a trigger date only when the rule and date support a calculation; show the arithmetic or cite the explicit trigger. Identify dependent claims or artifacts from supplied links and state why an item’s queue priority follows the supplied policy. Mark records with no review rule as unscheduled, and distinguish “review due” from “false,” “superseded,” or “safe.” Where a supersession note is explicit, record it; where it is absent or ambiguous, ask for resolution. Assign an interim label only from labels provided by the input; otherwise use a neutral provisional phrase such as “review status unresolved.” Verify date calculations, dependency counts or ordering, rule application, and complete record coverage. If dates, rules, links, or priority policy are missing, report the limitation and avoid fabricated scheduling. Produce a queue with item, rule, trigger date, dependent claims, priority basis, interim label, and open questions, followed by a verification report. Do not edit dependent content or treat elapsed time as proof of falsity. See [input contract](references/input-contract.md) and [worked example](references/worked-example.md).\n\n## Machine-checkable artifact contract\n\nReturn the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.\n

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
