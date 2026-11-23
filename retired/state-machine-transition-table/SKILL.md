---
name: state-machine-transition-table
description: "Use when plain-text behavior notes define states, events, guards, and effects but leave permitted transitions unclear. Do not use for comparing document assertions, implementing code, or inferring forbidden transitions from silence."
license: Apache-2.0
metadata:
  author: "Skill Almanac Editorial"
  version: "0.1.0"
  network: "none"
  license: "Apache-2.0"
  author_model: "gpt-5.6-luna"
---

Read the supplied state names, event definitions, guard notes, and effects as the complete evidence set. Normalize equivalent labels only when the notes explicitly establish equivalence. For each documented source-state/event combination, record the guard, destination, and effect exactly as supported. Mark a combination as unspecified when the notes do not address it; do not convert absence into prohibition. If notes conflict, preserve each statement, identify the conflicting sources, and mark the transition unresolved rather than choosing a preferred rule.

Produce a transition table with source state, event, guard, destination, effect, evidence reference, and status. Use statuses such as documented, conditional, conflicting, and unspecified. Include a short unresolved-cases section covering missing guards, destinations, effects, and contradictory wording. Do not claim executability, completeness, runtime validity, or authorization to change the system. Report normalization assumptions separately from observed rules.

If required inputs are missing, return a partial table and name the missing elements. If state or event names are ambiguous, retain the original text and ask for clarification in the unresolved section. Keep the result limited to the supplied notes. See the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies the required fields and uncertainty representations; a [synthetic JSON example](references/schema-example.json) shows the shape. Human-readable example tables illustrate equivalent content, not a different contract. Do not treat the example as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
