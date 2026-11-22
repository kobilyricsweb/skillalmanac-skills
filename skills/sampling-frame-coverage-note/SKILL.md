---
name: sampling-frame-coverage-note
description: "Use when a supplied sampling frame needs a bounded description of included and excluded populations, duplicate risks, time limits, and unknown coverage. Do not use for taxonomy assignment coverage, representativeness claims, bias estimation, or statistical sampling design beyond the supplied rules."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

Write a bounded coverage note from the supplied target population definition, frame-construction rules, dated frame summary, and known exclusion or duplication notes. State the target population exactly as provided, then describe which units the frame includes and excludes by rule. Record time bounds and distinguish a dated snapshot from a claim about the full target population. Identify duplicate risks only when the input names a possible duplicate mechanism, and describe its consequence without estimating frequency. Mark coverage as unknown where the input does not establish whether a subgroup or period is represented. Keep observable frame rules separate from conclusions about representativeness, bias, response, or quality. If the target definition, frame date, or exclusion note conflicts, report the conflict and avoid synthesis. Produce a concise coverage table, a narrative note, an unknowns section, and a verification report. Verify that every inclusion and exclusion statement is supported by supplied rules, that duplicate risk is not converted into a count, and that no representativeness or bias magnitude is asserted. Do not design a sample, calculate weights, infer missing populations, or contact external systems. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
