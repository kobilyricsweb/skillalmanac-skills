# metric-definition-card

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when turning supplied product or operational metric notes into a definition card that exposes population, window, denominator, exclusion, freshness, and zero-policy gaps. Do not use for calculating metric results, auditing weighted-rate implementations, forecasting outcomes, or making causal, financial, or operational recommendations.

## Task boundary

weighted-rate-audit checks aggregation arithmetic; this documents the supplied population, numerator, denominator, grain and unresolved business definition without computing or endorsing the metric.

## Try the independent synthetic example

Build a metric definition card. Metric name: Weekly activation rate. Purpose: track onboarding completion. Source note: “Weekly activation rate = accounts with an activation event during the Monday–Sunday UTC window / eligible accounts created during that same UTC window.” Activation event means event_name=activated. Eligible accounts exclude test_account=true. Grain: account. Data freshness: available by 09:00 UTC each Monday. Zero-denominator policy: report undefined. Do not calculate a result.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_e6e095d16910`:

```text
{"metric_name":"Weekly activation rate","purpose":"track onboarding completion","formula":"accounts with an activation event during the Monday–Sunday UTC window / eligible accounts created during that same UTC window","metric_class":"rate","numerator":"Accounts with event_name=activated during the Monday–Sunday UTC window","denominator":"Eligible accounts created during that same Monday–Sunday UTC window","population":"Accounts eligible under the supplied account-creation condition","window":"Monday–Sunday UTC window; exact boundary convention not supplied","timezone":"UTC","exclusions":["test_account=true"],"grain":"account","freshness":"Available by 09:00 UTC each Monday","zero_policy":"undefined","source_notes":["Activation event means event_name=activated.","Eligible accounts exclude test_account=true.","Source formula supplied by user."],"unresolved_choices":["Exact inclusivity of Monday and Sunday boundaries is not supplied."],"implementation_questions":["Are both window endpoints inclusive, and which timestamp defines event occurrence and account creation?"]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
