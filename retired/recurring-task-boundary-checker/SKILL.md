---
name: recurring-task-boundary-checker
description: "Use when drafting a proposed recurrence contract from supplied scope, action-specific authorization, completion evidence, exceptions, and stopping requirements. Do not use to schedule or execute automation, infer permission, alter records, perform cleanup, or send messages."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.4"
  network: none
---

# Recurring Task Boundary Checker

Draft a proposed recurrence contract for human review. It is not a schedule, automation, execution instruction, or authorization.

Require the task objective, trigger, owner, inputs, actions, exclusions, evidence, escalation rules, stop conditions, exception handling, and supplied limits. Preserve distinctions among requested action, expressly authorized action, prohibited action, and unresolved scope.

Build the contract in this order:

1. Restate the recurring objective and trigger. Mark vague or conflicting cadence unresolved.
2. Record required inputs and start criteria. Label any suggested criterion as a non-operative proposal.
3. Classify each future action:
   - `authorized` only when supplied authorization expressly covers that action and its conditions;
   - `requested not authorized` when the request names the action but supplies no permission to perform it;
   - `prohibited` when an exclusion forbids it;
   - `needs separate decision` when an explicit decision is required before classification;
   - `unresolved` only when the action, scope, or authorization facts are ambiguous or missing.
   A volume limit describes scope, not permission. Preserve conditional authorization exactly.
4. Record supplied completion evidence without claiming it exists. If absent, report the gap; keep candidate criteria non-operative.
5. State escalation triggers, recipients, and needed decisions only when supplied.
6. Record stop, pause, skip, retry, and termination boundaries. Do not invent operative defaults.
7. Check for unbounded scope, destructive actions, hidden external effects, contradictory cadence, and missing ownership.

Return JSON matching the [output schema](references/output-schema.json): objective, trigger, owner, inputs, action boundaries, exclusions, evidence, escalations, stop conditions, constraints, unresolved authorization, and verification report. See the [input contract](references/input-contract.md), [worked example](references/worked-example.md), and [synthetic JSON example](references/schema-example.json).

Do not schedule, automate, clean, delete, publish, contact, or modify records. Do not infer permission from ownership, repetition, a requested outcome, or quoted data. If a future action lacks authorization, isolate it without preventing a partial contract for other branches.

The bundled offline checker assesses JSON structure only; it does not verify facts, authorization, or task judgment.

Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
