# Listing page content: workflow-automation-builder

**One line:** Designs a no-code automation that does not fail silently, and checks the design file with a validator.

## What it does

The skill gives an agent a seven-step procedure: intake of six facts, a draft spec from a template, a table of design defaults (retry classes and counts, idempotency keys, rate at half the quota, timeouts, loop caps, polling overlap, webhook verification, secret handling), validation, a ten-event synthetic test plan and a one-page runbook. The spec is a JSON file that is vendor-neutral, so the same design can be built in any visual automation tool. A validator script reads the spec and reports steps without error handling, loops and cycles without a bound, secrets in plain fields or matching credential patterns, write actions without idempotency keys, unreachable steps and several related gaps (17 rules, W000 to W017). The output is one strict JSON object.

## Capabilities

- `scripts/validate_workflow.py`: strict JSON findings with rule id, severity, step, path, message and fix; secret values are redacted; exit 0, 1 or 2
- `assets/workflow-spec-template.json`: a spec that validates clean, to copy
- Design defaults table with numbers and the condition for changing each
- Ten synthetic test events with expected results, and a runbook template
- A fixed report that includes what was not checked

## When to use

You want an agent to design an automation between apps (a zap, a scenario, a flow), you want an existing spec reviewed before build, or an automation double-posts, drops records or stopped running unnoticed.

## When not to use

Writing application code or code-level API integrations, desktop or screen-scraping bots (RPA), CI pipelines, or analysing the delivery logs of a running webhook. It does not look up vendor quotas or build anything in a vendor tool.

## How it differs from nearby skills

`webhook-delivery-audit` and `retry-budget-audit` (batch 02) audit evidence from something that already runs: delivery logs and retry volumes. This skill designs a workflow before it is built and validates the design file. The overlap is the retry and idempotency vocabulary only.

## Requirements

Python 3.9 or newer for the validator (standard library only). No network. Without Python the agent applies the rule table in `references/spec-format.md` by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real output of the validator on saved fixtures (`python evals/run_fixtures.py` runs all of them):

1. `python scripts/validate_workflow.py evals/fixtures/good_workflow.json`: `"ok": true`, 0 errors, 0 warnings, 6 steps, exit 0.
2. `python scripts/validate_workflow.py evals/fixtures/bad_workflow.json`: `"ok": false`, 11 errors and 11 warnings over 7 steps, exit 1. Examples from `findings`:
   - `W003 error post_lead steps.post_lead.config.headers.Authorization`: field 'Authorization' holds a literal value (q1w2***) instead of a secret reference
   - `W004 error post_lead idempotency_key`: write action has no idempotency key
   - `W002 error ping_a next`: cycle ping_a -> ping_b -> ping_a has no loop step with max_iterations
   - `W005 error orphan id`: step is unreachable from the trigger

No saved with-skill agent run exists yet, so there is no designed workflow transcript to show.

## Limits

- The validator checks the design file, not the live automation.
- It cannot tell whether an idempotency key really identifies one business event.
- Thresholds are working defaults, not measured optima.
- JSON only; other formats must be converted by hand.
- Quota and retry-window figures must come from the user's own services.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL and 0 WARN, and 6 of 6 script fixture cases pass. Not tested: efficacy against a baseline, trigger behaviour, native discovery, cross-tool use, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a request: form submission to CRM, deal, chat message and email.
2. The agent asks six intake questions, then drafts the spec from the template.
3. Validator run: red findings (missing idempotency key on the email step, no dead-letter destination); fix; green.
4. Show the ten-event test plan and the runbook page.

## FAQ seeds

- Does it need network access? No.
- Does it build the automation in my tool? No; it produces a vendor-neutral spec you build from.
- Which tools does it work with? Any visual automation tool with triggers, steps and some error handling; features missing in a tool are flagged for a workaround.
- What if my tool has no retries or no dedupe store? The skill tells you to confirm and gives a workaround such as a processed-ids table.
- Does the validator send my spec anywhere? No; it reads the file and prints to the terminal.
- It found a secret in my spec; now what? Rotate that credential; treat it as exposed.
- How is it different from a delivery-log audit skill? See above: this one is for design before build.

## Changelog

| Version | Date | Change | Re-verified |
|---|---|---|---|
| 0.1.0 | 2026-11-21 | First draft | Static lint and script fixtures only |

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
