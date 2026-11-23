---
name: sop-decision-point-extractor
description: "Use when a complete standard operating procedure must be converted into documented decision branches with observable conditions and rejoin points. Do not use for routing incoming requests, inventing policy defaults, diagnosing operations, or mapping approval authority across separate procedures."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.2"
  network: none
---

Extract decision logic only from the supplied SOP. Identify each documented trigger, the question or decision it creates, the observable condition used to answer it, the branch action, the role explicitly assigned to that action, and where the branch rejoins or terminates. Preserve defined terms, role boundaries, exceptions, and defaults; quote or closely paraphrase only the relevant operational meaning.

Represent uncovered conditions as explicit missing branches rather than assigning an action. Separate sequential steps from genuine decisions. If conditions conflict, preserve both and mark precedence unresolved unless the SOP states it. If a condition is vague, report it as non-observable and request a measurable definition. If an action lacks an explicit owner, leave the role unresolved and request the assignment; naming a role elsewhere does not establish ownership. Do not infer converse conditions, implied permissions, or unmentioned exceptions.

Every branch must include the passage reference supporting its condition and action. Decision-level references may additionally support a shared trigger. Verify that branch conditions, actions, roles, and rejoin points are traceable to documented text. If the SOP is incomplete, produce a partial table and input-gap list. Follow the [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

## Machine-checkable artifact contract

Return the artifact as JSON matching the [domain output schema](references/output-schema.json). It specifies required fields and uncertainty representations; the synthetic example shows the shape. Human-readable examples illustrate equivalent content, not a different contract. Do not treat examples as executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory for offline structural checking. Structural validity does not establish behavioral quality.
