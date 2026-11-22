# Verification — taxonomy-structure-check

Status: unpublished free candidate; no Platform Score or native verification.

The bundled offline Python script passed **12/12** retained fixtures.
These totals are generated from actual checker records; expected nonzero finding/error exits
are successful fixture results. Python 3.11.9; platform Windows-10-10.0.26300-SP0.
Script SHA-256: `78fa6d0e27c7fc50e2f98b612b9591c74c8f0e856d96e913af61b13d2cb5722b`.
Raw results: `evals/script_results.json`; input/expectations: `evals/fixtures.json` and `evals/fixtures/`.

| Fixture | Exit | Result |
|---|---:|---|
| good_forest | 0 | PASS |
| orphan_reference | 1 | PASS |
| malformed_duplicate_ids | 2 | PASS |
| empty_forest_boundary | 0 | PASS |
| numeric_token_bound | 2 | PASS |
| self_parent | 1 | PASS |
| multi_node_cycle | 1 | PASS |
| long_chain_iterative | 0 | PASS |
| duplicate_json_key | 2 | PASS |
| nonfinite | 2 | PASS |
| truncated | 2 | PASS |
| missing_file | 2 | PASS |

Local fixtures cover the bounded supplied extract, parser failures and review-driven regressions.
They do not prove native skill loading/routing, agent efficacy, cross-tool use, deployment state,
security of a live system, dataset completeness, taxonomy meaning or promotional performance.
One independent model-assisted source review found concrete defects; the parent repaired them
and added deterministic regressions. After explicit owner transfer authorization, a fresh gpt-5.6-sol static source review completed.
It found undocumented failure schemas and two broad trigger examples. Version0.1.4 documents
the actual failure variants and narrows those examples; source scripts are unchanged. No fresh
reviewer acceptance or native efficacy is inferred from completion of the review. Apache-2.0/rightsholder approval is recorded; human review and house release gates remain open.

## Reproduce

From the shared sprint evidence directory, use Python 3.9+:

`python "reproduction_tools/replay_package.py" "<absolute-skill-folder>" --mode fixtures`

For instruction-only skills, agent-cases prints the exact prompts/assertions and executes no model.
For scripted skills, fixtures replays all retained script cases and compares exit/JSON against the
saved observed results; it is a regression replay, not independent truth. Original expected checks
remain in the evaluation specifications. Native discovery must be tested separately.

## Authorized review closure, v0.1.4

All six reported contract/trigger findings were assessed as resolved by a fresh bounded static follow-up (utility_review_resolution_v014). No native or release approval inferred. Source scripts unchanged;52/52 explicit utility fixtures re-ran across this batch. See shared review_round_02/authorized_review/REPORT.md and raw jobs.

## Owner licence and commercial decision,2026-11-21

Apache-2.0 is approved for this package. The unmodified standard text is included at the batch root in LICENSE and per package in LICENSE.txt; NOTICE.txt carries Copyright 2026 Global Media Holdings (skillalmanac.com). Historical raw evidence is retained unchanged and does not define current terms.

Editorial metadata tier: `free`. Tier is not computed from Platform Score or User Score. Licence approval does not close native, cross-tool or human review gates. No public launch or score is inferred.

## Portable review command

From the skillalmanac repository root:

`python content/review/tools/replay_package.py content/review/batch_04_free_utilities/taxonomy-structure-check --mode fixtures`

Replays retained script outputs/exits; it is a regression comparison, not independent truth.
