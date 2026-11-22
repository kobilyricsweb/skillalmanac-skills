# brand-tone-constraint-card

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when approved brand samples, explicit voice preferences, and prohibited tone patterns must become a concise tone constraint card for new copy. Do not use for glossary normalization, factual claim validation, performance promises, or inferred brand positioning.

## Task boundary

brand-guidelines-kit develops broader brand guidance and copywriting-landing-pages writes copy; this extracts a bounded tone-constraint card from supplied approved samples, distinct from terminology-consistency-editor.

## Try the independent synthetic example

Build a tone constraint card from these inputs. Approved sample for onboarding email: “You can finish setup in three short steps.” Explicit preference: use direct second-person language and calm, practical wording in onboarding emails. Prohibited pattern: do not use urgency claims such as “Act now” in onboarding emails. Context limit: these rules apply only to onboarding email copy. Separate observed wording from approved rules and give writer tests, supported counterexamples, and open questions.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_830edb813b91`:

```text
{"entries":[{"constraint":"Use direct second-person language and calm, practical wording.","type":"positive_anchor","source":"explicit_preference","scope":"onboarding emails only","writer_test":"Does the copy address the reader directly in calm, practical terms?","counterexample":"","status":"approved_constraint"},{"constraint":"The approved sample uses concise, practical setup language: \"You can finish setup in three short steps.\"","type":"observation","source":"approved_sample","scope":"approved onboarding email sample only","writer_test":null,"counterexample":null,"status":"observed_only"},{"constraint":"Do not use urgency claims such as \"Act now\".","type":"prohibition","source":"prohibited_pattern","scope":"onboarding emails only","writer_test":"Does the copy pressure the reader with an urgency claim?","counterexample":"Act now to finish setup.","status":"approved_constraint"}],"conflicts":[],"open_questions":["Does the preference apply to all onboarding email formats or only this sample's setup message?"],"verification":{"all_constraints_sourced":true,"tests_wording_only":true,"factual_claims_approved":false}}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
