# service-request-routing-table

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when incoming service requests must be assigned deterministically from supplied category, urgency, location, exception, precedence, role-directory, and fallback rules. Do not use for approval-path mapping, staffing allocation, form completeness, or choosing between overlapping rules without documented precedence.

## Task boundary

Nearest is approval-path-mapper; this routes incoming work rather than mapping authorization decisions.

## Try the independent synthetic example

Build a routing table and apply it to the test requests. Categories: plumbing and electrical. Urgent means active water flow or exposed live wire. Locations: North and South. Directory: North Facilities, South Facilities, Emergency Desk, General Intake. Rules: R1 plumbing in North routes to North Facilities. R2 plumbing in South routes to South Facilities. R3 electrical routes to General Intake. R4 has higher precedence than R1-R3 and routes any urgent request to Emergency Desk. Unknown or unmatched categories route to General Intake. One destination per request. Tests: T1 plumbing, North, active water flow; T2 plumbing, South, no active water flow; T3 painting, North, not urgent. Show matches, precedence, fallback use, and gaps. Do not assess staffing, approval authority, or dispatch work.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_e7fab106acae`:

```text
{"routing_rules":[{"rule_id":"R1","conditions":["category is plumbing","location is North","not urgent"],"destination_role":"North Facilities","precedence":null,"exception":"R4 urgent override"},{"rule_id":"R2","conditions":["category is plumbing","location is South","not urgent"],"destination_role":"South Facilities","precedence":null,"exception":"R4 urgent override"},{"rule_id":"R3","conditions":["category is electrical","any location","not urgent"],"destination_role":"General Intake","precedence":null,"exception":"R4 urgent override"},{"rule_id":"R4","conditions":["request is urgent: active water flow or exposed live wire"],"destination_role":"Emergency Desk","precedence":"higher than R1-R3","exception":null},{"rule_id":"Fallback","conditions":["unknown or unmatched category"],"destination_role":"General Intake","precedence":null,"exception":null}],"request_results":[{"request_id":"T1","matched_rules":["R1","R4"],"selected_destination":"Emergency Desk","status":"routed","ambiguity_or_gap":"R4 takes precedence because active water flow is urgent."},{"request_id":"T2","matched_rules":["R2"],"selected_destination":"South Facilities","status":"routed","ambiguity_or_gap":null},{"request_id":"T3","matched_rules":["Fallback"],"selected_destination":"General Intake","status":"routed","ambiguity_or_gap":"Unknown category uses the approved fallback."}],"fallback_behavior":"Unknown or unmatched categories route to General Intake.","input_gaps":["Directory validation: all named destinations are present in the supplied directory."],"scope_exclusions":["Staffing","Approval authority","Dispatch work"]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
