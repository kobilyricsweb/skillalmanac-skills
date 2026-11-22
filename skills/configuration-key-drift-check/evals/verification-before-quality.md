# Verification — configuration-key-drift-check

Status: unpublished free candidate; no Platform Score or native verification.

The bundled offline Python script passed **15/15** retained fixtures.
These totals are generated from actual checker records; expected nonzero finding/error exits
are successful fixture results. Python 3.11.9; platform Windows-10-10.0.26300-SP0.
Script SHA-256: `4afc72c156f0f04a7a38f21a8de130b35e0544bd00458d22b499c8e3e350c71f`.
Raw results: `evals/script_results.json`; input/expectations: `evals/fixtures.json` and `evals/fixtures/`.

| Fixture | Exit | Result |
|---|---:|---|
| good | 0 | PASS |
| domain-defect | 1 | PASS |
| malformed | 2 | PASS |
| boundary | 0 | PASS |
| extra-not-used | 1 | PASS |
| numeric_token_bound | 2 | PASS |
| nonstring_config_key | 2 | PASS |
| unhashable_declared_key | 2 | PASS |
| unhashable_config_name | 2 | PASS |
| overlapping_declarations | 2 | PASS |
| case_sensitive_keys | 1 | PASS |
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

`python content/review/tools/replay_package.py content/review/batch_04_free_utilities/configuration-key-drift-check --mode fixtures`

Replays retained script outputs/exits; it is a regression comparison, not independent truth.
