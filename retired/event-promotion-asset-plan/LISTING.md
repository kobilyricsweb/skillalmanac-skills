# event-promotion-asset-plan

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when turning confirmed event facts, channels, permissions, and milestones into a bounded promotional asset plan. Do not use for overall campaign strategy, invented event details, publishing assets, or registration assumptions unsupported by the supplied event process.

## Task boundary

Nearest is marketing-campaign-brief; this specifies a bounded event asset set rather than overall campaign strategy.

## Try the independent synthetic example

Create a promotional asset plan, not finished assets. Confirmed event: Data Basics Webinar; online via supplied webinar link; 2026-12-10 at 14:00 UTC; confirmed benefit: live demonstration of two spreadsheet-cleaning techniques. Approved audience: registered library staff. Registration closes 2026-12-08. Allowed channels: email and intranet. Speaker permissions: Ana Ruiz—name allowed in email and intranet; likeness and quotes not allowed. Milestones: event page details finalized before email drafting; email review must occur before registration closes. Plan suitable artifacts, dependencies, deadline relations, and boundaries.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_841e1c0a25f5`:

```text
{"assets":[{"artifact_name":"Event details page","channel":"intranet","purpose":"Present confirmed webinar information to eligible staff.","audience":"Registered library staff","required_facts":["Data Basics Webinar","Online via supplied webinar link","2026-12-10 at 14:00 UTC","Live demonstration of two spreadsheet-cleaning techniques","Registration closes 2026-12-08"],"dependencies":["Event page details must be finalized before email drafting."],"deadline_relation":"Finalize event page details before drafting the email; complete email review before 2026-12-08.","permitted_references":["Ana Ruiz's name"],"content_boundary":"Do not use Ana Ruiz's likeness or quotes; no additional benefits, claims, or registration terms.","status":"planned"},{"artifact_name":"Email invitation","channel":"email","purpose":"Invite the approved audience to register or review the confirmed webinar details.","audience":"Registered library staff","required_facts":["Data Basics Webinar","Online via supplied webinar link","2026-12-10 at 14:00 UTC","Live demonstration of two spreadsheet-cleaning techniques","Registration closes 2026-12-08"],"dependencies":["Finalized event page details"],"deadline_relation":"Email review must occur before registration closes on 2026-12-08.","permitted_references":["Ana Ruiz's name"],"content_boundary":"Do not use Ana Ruiz's likeness or quotes; production and sending are not authorized by this plan.","status":"planned"}],"dependency_summary":["Event page details precede email drafting.","Email review precedes 2026-12-08 registration close."],"blocked_items":[],"open_questions":[],"outside_scope":["Producing, approving, distributing, or publishing assets"]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
