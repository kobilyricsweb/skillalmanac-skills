# cache-invalidation-scenario-designer

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when turning supplied cache keys, read paths, mutations, invalidation rules, and staleness allowances into explicit offline cache scenarios. Do not use for incident runbooks, hidden dependency discovery, runtime cache testing, or assuming relationships not stated in the specification.

## Task boundary

Nearest is runbook-scenario-table; this designs cache-behavior cases rather than matching incidents to procedures.

## Try the independent synthetic example

Design an offline cache scenario from this specification. K1: item:{id} represents one item. R1: the item page reads K1. M1: rename-item changes that item. I1: M1 invalidates the matching K1 before the mutation response is returned. A1: R1 permits no stale item name after that response. Use only these declared relationships and distinguish specified behavior from runtime proof.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_0a09fdfb2847`:

```text
{"scenario_table":[{"mutation":"M1 rename-item","affected_key":"item:{id}","reader":"R1","relationship_status":"specified","invalidation_timing":"before the mutation response is returned","allowed_staleness":"none after that response","evidence":["K1","R1","M1","I1","A1"]}],"affected_keys":["item:{id}"],"readers":["R1"],"invalidation_timing":"fully_specified","allowed_staleness":"fully_specified","evidence":["K1 represents one item.","R1 reads K1.","M1 changes that item.","I1 explicitly requires matching K1 invalidation before the response.","A1 permits no stale item name after the response."],"unresolved_relationships":[],"conflicts":[],"verification_statement":"This describes specified behavior only; it does not prove runtime cache behavior."}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
