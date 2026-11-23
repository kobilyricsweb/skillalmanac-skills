# abbreviation-disambiguation-guide

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when repeated abbreviations have multiple approved expansions in supplied contexts and reviewers need occurrence-level possibilities with evidence. Do not use for terminology normalization, preferred-term replacement, or authorizing an expansion absent from the approved glossary.

## Task boundary

terminology-consistency-editor normalizes preferred terms; this disambiguates multiple allowed expansions without editing wording.

## Try the independent synthetic example

Create an occurrence-level disambiguation guide. Approved glossary: “CR” may mean “Change Request” or “Customer Record.” Occurrences: O1, location §1, excerpt “The analyst opened CR-17 for the login fix”; O2, location §2, excerpt “The agent corrected the address in the CR.” A supplied glossary rule says identifiers of the form CR-number denote Change Requests. Cover both occurrences, preserve the abbreviation, and state what the guide does not authorize.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_1917f2dd60f1`:

```text
{"occurrences":[{"id":"O1","location":"§1","excerpt":"The analyst opened CR-17 for the login fix","possible_expansions":["Change Request"],"evidence":["The supplied rule states that identifiers of the form CR-number denote Change Requests."],"status":"resolved_by_supplied_evidence","questions":[]},{"id":"O2","location":"§2","excerpt":"The agent corrected the address in the CR.","possible_expansions":["Change Request","Customer Record"],"evidence":["The excerpt uses CR without a number; correcting an address is compatible with Customer Record but is not supplied as dispositive evidence."],"status":"unresolved","questions":["Provide surrounding context or a rule distinguishing the intended expansion for this occurrence."]}],"coverage":{"supplied_ids":["O1","O2"],"covered_ids":["O1","O2"],"unsupported_expansions":[]},"scope_limits":["The guide preserves CR, does not replace source wording, and does not establish a preferred expansion.","It does not authorize expanding CR to any meaning outside the approved glossary."]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
