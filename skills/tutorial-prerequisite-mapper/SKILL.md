---
name: tutorial-prerequisite-mapper
description: "Use when mapping supplied tutorial steps to prior knowledge, state, inputs and verification cues. Do not use to execute setup, obtain credentials or replace a general handover audit."
license: Apache-2.0
metadata:
  author: "Skill Almanac Editorial"
  version: "0.1.0"
  network: "none"
  license: "Apache-2.0"
  author_model: "gpt-5.6-luna"
---

# Tutorial Prerequisite Mapper

Use this skill when the user supplies tutorial steps and wants hidden dependencies made explicit. Treat the supplied environment description and steps as the full boundary. Do not install packages, fetch credentials, inspect external systems, or execute commands described in the tutorial.

Required inputs are: ordered tutorial steps; stated environment, starting state, or platform; supplied inputs and artifacts; learner assumptions, if any; and verification cues or constraints. First extract each step’s action and its visible output. Then identify dependencies that must exist before the step: knowledge, access or credential state, tool or environment state, prior artifact, input data, or prior step. Distinguish “required and supplied,” “required but omitted,” “stated as unknown,” and “not applicable.” Place each dependency at the earliest step where it is needed, even if the tutorial mentions it later.

Build a prerequisite map with step ID, action, required knowledge, required state, required inputs, produced artifact, verification cue, and dependency status. Add dependency edges when one step consumes a prior artifact or state. Flag late introductions, circular dependencies, ambiguous setup, missing credentials, and verification cues that do not test the stated output. When a prerequisite is not supplied, preserve it as unknown and state the question needed to resolve it. Do not assume operating system, package version, account ownership, permissions, data availability, or successful execution.

Return: scope assumptions; the step-by-step map; dependency edges; gap and late-introduction register; and a verification report. Verify that every step has an explicit status, every consumed artifact has an origin or unknown marker, and no action was executed. Report whether the map is planning-complete or blocked by missing context. Do not turn it into a handover checklist, installation guide, or runnable procedure.

See [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
