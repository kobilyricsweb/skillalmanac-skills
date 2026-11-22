---
name: archive-discovery-aid
description: "Use when a fixed offline archive inventory must become a human-readable finding aid without changing the archive or inventing contents. Do not use for validating taxonomy graphs, reorganizing folders, or inferring item meaning beyond supplied descriptions and hierarchy rules."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.2"
  network: none
---

Read the supplied inventory, descriptions, dates, identifiers, hierarchy rules, and access annotations. Build a finding aid that mirrors only supported archive relationships. Preserve every source identifier and distinguish archive facts from editorial navigation labels.

For each folder or item, record its supported parent, label, scope, date information, and access note. Describe contents only at the level established by the supplied description; do not infer meaning from names, dates, or neighboring entries. Apply explicit hierarchy rules exactly. Put an entry with no supported parent in the uncertain or unclassified section and explain the missing basis.

Derive a folder date span only from dates supplied for that folder and descendants whose placement beneath it is supported. Do not let an unclassified, uncertain-placement, or merely neighboring item expand a folder or series span. If a descendant’s placement is disputed, keep the competing statements visible and leave the aggregate span unresolved when the dispute affects it.

Retain conflicting descriptions together and flag them for review. Keep access annotations attached to their own entries; missing access remains a gap and is not inherited from a parent or neighbor unless an explicit rule says it is.

Verify that every supplied identifier appears exactly once, no supported date range is broadened, and no material is renamed, moved, deleted, merged, or enriched. Return entries, unclassified identifiers, coverage, unresolved questions, and scope limits according to the [input contract](references/input-contract.md) and [output schema](references/output-schema.json). Use the [worked example](references/worked-example.md) and [synthetic schema example](references/schema-example.json) only as illustrations, not evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
