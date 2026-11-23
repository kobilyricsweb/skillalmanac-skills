# message-asset-reuse-map

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when mapping approved messages to exact locations in supplied assets with audience and reuse restrictions. Do not use for general factual verification, campaign plans or promotional-variant validation.

## Task boundary

promotion-variant-check checks that exactly one declared field changed from a baseline; this maps which supplied message assets can be reused for stated channels and what remains to adapt. landing-page-message-sequencer orders approved messages; offer-comparison-matrix aligns supplied offer attributes.

## Try the independent synthetic example

Create a reuse map from this synthetic record. Messages: M1, exact wording “Setup takes ten minutes.” Audience: existing administrators; context: onboarding; authorized use: help-center onboarding pages only; restriction: do not use in sales material. Assets: A1 summarizes the administrator setup sequence, location /help/setup#start, audience existing administrators, context onboarding, permission allows help-center reuse. A2 is a sales deck at /sales/deck#4 for prospects. Requested placements: A1 and A2. Rule: audience, context, permission, and restriction must all agree. Known gaps: none. Do not assess whether the message is true or draft variants.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_1aee4012a0c1`:

```text
{"placements":[{"message_id":"M1","exact_message":"Setup takes ten minutes.","audience":"existing administrators","context":"onboarding","asset_id":"A1","location":"/help/setup#start","status":"direct reuse","allowed_placement":"help-center onboarding pages only","restriction":"Do not use in sales material.","adaptation_request":null},{"message_id":"M1","exact_message":"Setup takes ten minutes.","audience":"existing administrators","context":"onboarding","asset_id":"A2","location":"/sales/deck#4","status":"unsupported placement","allowed_placement":null,"restriction":"Help-center onboarding pages only; do not use in sales material.","adaptation_request":null}],"unpaired_messages":[],"unused_assets":["A2 for permitted reuse"],"blocked_placements":["M1 in A2: sales material is explicitly prohibited."],"unresolved_authority":[],"scope_limits":["No claim-truth assessment, sales use, or message variant drafting."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
