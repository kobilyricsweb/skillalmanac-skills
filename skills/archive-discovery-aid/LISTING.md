# archive-discovery-aid

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when a fixed offline archive inventory must become a human-readable finding aid without changing the archive or inventing contents. Do not use for validating taxonomy graphs, reorganizing folders, or inferring item meaning beyond supplied descriptions and hierarchy rules.

## Task boundary

Nearest is taxonomy-structure-check; this describes an archive for discovery rather than validating parent-child graph structure.

## Try the independent synthetic example

Build a finding aid for this fixed inventory. Hierarchy rule: folders define parents; items belong to their stated folder. Folder F1: “Projects,” description “Project administration,” access “Open.” Folder F2: “Orchard,” parent F1, description “Orchard project records,” access “Open.” Item I1, parent F2, date 2024-03-01, description “Approved meeting agenda,” access “Open.” Item I2, parent F2, date 2024-03-05, description “Draft budget,” access “Restricted to finance team.” Preserve identifiers, derive only supported date spans, verify coverage, and state scope.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_af9793f4e8aa`:

```text
{"entries":[{"identifier":"F1","kind":"folder","label":"Projects","parent_identifier":null,"scope_description":"Project administration","date_span":"2024-03-01 to 2024-03-05","access_notes":"Open","certainty":"supported"},{"identifier":"F2","kind":"folder","label":"Orchard","parent_identifier":"F1","scope_description":"Orchard project records","date_span":"2024-03-01 to 2024-03-05","access_notes":"Open","certainty":"supported"},{"identifier":"I1","kind":"item","label":"I1","parent_identifier":"F2","scope_description":"Approved meeting agenda","date_span":"2024-03-01","access_notes":"Open","certainty":"supported"},{"identifier":"I2","kind":"item","label":"I2","parent_identifier":"F2","scope_description":"Draft budget","date_span":"2024-03-05","access_notes":"Restricted to finance team.","certainty":"supported"}],"unclassified":[],"coverage":{"supplied_identifiers":["F1","F2","I1","I2"],"represented_identifiers":["F1","F2","I1","I2"],"duplicates":[]},"unresolved_questions":[],"scope_limits":["Fixed inventory only; no renaming, moving, merging, deletion, or enrichment."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
