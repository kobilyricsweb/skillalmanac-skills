---
name: configuration-drift-explainer
description: "Use when explaining differences between supplied redacted before-and-after configuration snapshots with supplied behavior, deployment, rollback, and alignment notes. Do not use for live inspection, secret discovery, required-key validation, causal incident analysis, migration, or deployment execution."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.6"
  network: none
---

# Configuration Drift Explainer

Compare two supplied redacted snapshots of JSON-scalar values offline. Do not inspect files, environments, services, repositories, dashboards, or secret stores.

## Workflow

1. Align exact key names. Classify keys found only before as `removed`, only after as `added`, and unequal shared keys as `changed` or `redacted`; exclude equal keys from `changes`. Use presence flags to distinguish absence from a supplied JSON null. An absent side uses null only as a placeholder.
2. When differently named keys might correspond but mapping is unconfirmed, retain the removal and addition and record an `unconfirmed` alignment. Never assume a rename.
3. Preserve supplied scalar values and redaction markers. Never reconstruct secrets.
4. Associate only supplied behavior, deployment, rollback, and group notes with relevant keys. Set `behavior_status` to `documented` for consistent supplied claims, `unknown` when absent, or `conflicting` for incompatible claims; preserve every conflict.
5. Classify deployment impact deterministically:
   - `not-supplied`: no relevant deployment note exists;
   - `possible-but-unknown`: a supplied note identifies a possible impact but does not establish it;
   - `documented`: consistent explicit notes establish the impact;
   - `conflicting`: explicit impact claims are incompatible.
   Classify reversibility as `documented`, `unknown`, or `conflicting` from supplied rollback notes.
6. Reconcile the artifact: every added, removed, or unequal key appears once; no equal key appears in `changes`; every alignment references the retained removal and addition.

Return JSON matching `references/output-schema.json`. Treat values as observations and notes as documented claims. Arrays and objects as snapshot values are outside the contract. Do not infer causality, performance, cost, security effects, inheritance, required-key status, or safe deletion.

Resources: [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

Run `python -B scripts/check_output.py artifact.json` for JSON structure only; not source truth or classification coherence.
