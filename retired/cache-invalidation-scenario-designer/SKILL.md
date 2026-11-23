---
name: cache-invalidation-scenario-designer
description: "Use when turning supplied cache keys, read paths, mutations, invalidation rules, and staleness allowances into explicit offline cache scenarios. Do not use for incident runbooks, hidden dependency discovery, runtime cache testing, or assuming relationships not stated in the specification."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

Design a scenario table from the supplied cache key patterns, read paths, mutation events, invalidation rules, and stated staleness allowances. For each mutation, connect only the keys and readers whose relationship is explicitly supplied. Report the mutation, affected key, invalidation timing, reader, allowed staleness, evidence, and unresolved relationship gaps.

Distinguish “specified invalidation” from “not specified.” Do not infer that similarly named keys represent the same entity, that a write updates every related list, or that a reader observes an invalidation. If a key pattern contains an identifier but no declared entity relationship, mark the relationship unresolved. A zero-staleness allowance makes an unspecified invalidation a contract gap; it does not prove an implementation defect.

Handle conflicting rules by showing the conflict and identifying the affected scenario. If key patterns, readers, mutations, or allowances are missing, return a partial casebook and name the missing inputs. Preserve explicit tolerated staleness, including its scope and duration when supplied. Do not execute code, inspect cache state, invent hidden dependencies, or recommend operational changes beyond a specification-level question.

Verify by enumerating supplied mutations and checking each against declared key relationships and invalidation rules. State that the result describes specified behavior and gaps only. Include [input contract](references/input-contract.md) and [worked example](references/worked-example.md).

Return the artifact as JSON matching the supplied domain schema. Do not treat examples as executed evidence.

Return JSON matching the [domain output contract](references/output-schema.json); the [synthetic shape example](references/schema-example.json) is an illustration, not executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
