# referral-message-kit

Unpublished original; editorial tier: paid-candidate. No public score or release approval.

## What and when

Use when converting supplied referral rules into accurate inviter, recipient, disclosure, and ineligible-case copy with claim-level traceability. Do not use for inventing program terms, deciding individual eligibility, comparing finished promotions, enrolling participants, sending invitations, processing payments, or delivering rewards.

## Task boundary

copywriting-landing-pages writes broader page copy; this drafts supplied-rule-bound referral messages and a standalone disclosure with a fact trace, inventing no reward, deadline or eligibility. promotion-variant-check checks one-field variation rather than drafting messages.

## Try the independent synthetic example

Create a referral message kit from these supplied rules.
Program rules: A current North Gym member may invite one first-time member. Coaches are excluded.
Eligibility: The inviter must be a current member and not a coach; the recipient must be a first-time member.
Reward conditions: The recipient must register and pay a $4 trial fee by 8 May. After payment clears, the inviter receives one guest pass at the front desk within three days. The recipient receives no reward.
Expiration: 8 May.
Prohibited wording: “instant,” “guaranteed,” and “everyone qualifies.”
Approved CTA: Register by 8 May.
Return inviter text, recipient text, short disclosure, ineligible-case response, fact trace, assumptions or conflicts, and the operational scope boundary.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_2421b1f7d582`:

```text
{"inviter_text":"If you are a current North Gym member and not a coach, invite one first-time member. If they register and pay the $4 trial fee by 8 May and payment clears, you receive one guest pass at the front desk within three days. Register by 8 May.","recipient_text":"A North Gym member may invite you if you are a first-time member. Register and pay the $4 trial fee by 8 May. No recipient reward is offered. Register by 8 May.","short_disclosure":"For a current, non-coach member inviting one first-time member: the recipient must register and pay the $4 trial fee by 8 May; after payment clears, the inviter receives one guest pass at the front desk within three days. The recipient receives no reward.","ineligible_case_response":"A person who is not a current North Gym member or is a coach cannot be the inviter. A recipient who is not a first-time member does not meet the supplied eligibility condition.","fact_trace":[{"draft_claim":"Inviter must be current and not a coach.","source_rule":"Eligibility","support_status":"supported"},{"draft_claim":"Recipient must be first-time.","source_rule":"Eligibility","support_status":"supported"},{"draft_claim":"One invitation is allowed.","source_rule":"Program rules","support_status":"supported"},{"draft_claim":"$4 payment by 8 May must clear.","source_rule":"Reward conditions","support_status":"supported"},{"draft_claim":"Inviter receives one guest pass at the front desk within three days.","source_rule":"Reward conditions","support_status":"supported"},{"draft_claim":"Recipient receives no reward.","source_rule":"Reward conditions","support_status":"supported"}],"assumptions_or_conflicts":[{"issue":"No supplied conflict or missing material term identified.","status":"none","effect_on_draft":"No omission required."}],"scope_boundary":"Draft copy guidance only; it does not authorize the program, decide eligibility, register anyone, send invitations, process payments, or issue or deliver rewards."}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
