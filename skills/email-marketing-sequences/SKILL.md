---
name: email-marketing-sequences
description: Designs automated email sequences (drip campaign, welcome series, onboarding, nurture, win-back) as a JSON plan with trigger, goal, exit conditions, cadence, one job per email, consent and unsubscribe fields, then checks it with a script. Use when a small business asks for an email automation, lifecycle flow, drip, welcome or re-engagement series, or wants an existing sequence audited for compliance, cadence, spam-trigger subjects or duplicate CTAs. Do not use for one-to-one email replies, HTML template design, one-off newsletters, or sending to purchased or scraped lists.
license: Apache-2.0
compatibility: The checker script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, apply the check table in references/sequence_schema.md by hand.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Email marketing sequences

Turn a business goal into an automated email sequence that is written down as data, checked by a script, and safe to hand to the person who loads it into their sending tool. This skill plans and validates; it does not send anything and it is not legal advice.

## Output contract

Every run produces two things.

1. `sequence.json`, in the shape below (field-by-field rules and every check code are in [references/sequence_schema.md](references/sequence_schema.md)).
2. A plan note in the fixed shape at the end of this file.

```json
{
  "sequence": {
    "name": "", "type": "onboarding|nurture|winback|other",
    "trigger": "", "goal": "",
    "consent_basis": "express_consent|double_opt_in|existing_customer|legitimate_interest|other",
    "consent_evidence": "", "regions": ["US"],
    "sender": {"from_name": "", "from_email": "", "postal_address": ""},
    "exit_conditions": ["goal reached", "unsubscribed", "hard bounce or complaint"],
    "min_gap_days": null
  },
  "emails": [
    {"id": "", "day": 0, "job": "", "subject": "", "preheader": "",
     "cta": {"label": "", "url": ""},
     "unsubscribe": true, "list_unsubscribe_header": true,
     "exit_conditions": [], "sender": null, "transactional": false}
  ]
}
```

`day` is days after the trigger event, not after the previous email. Use only fields the user gave you or that you flag as a placeholder in the plan note; never invent a postal address, a consent record or a URL and present it as real.

## Workflow

```
- [ ] 1 Collect the six inputs (or flag them as open)
- [ ] 2 Pick the sequence type and cadence row
- [ ] 3 Write the sequence contract
- [ ] 4 Write each email contract
- [ ] 5 Run the checker, fix, re-run
- [ ] 6 Add deliverability checklist and measurement plan
- [ ] 7 Report
```

1. **Collect inputs.** Audience and how they got on the list (this decides the consent basis); trigger event; one measurable goal with a time window; sender name, From address and postal address; the sending tool; regions of the recipients. If the how-they-joined answer is "bought", "rented", "scraped" or "from a business card pile", stop and read the compliance rule below before designing anything.
2. **Pick type and cadence.** Use the row in the table. Number of emails is a ceiling, not a target; fewer is fine when the goal can be reached sooner.

   | Type | Typical trigger | Emails | Days after trigger | Min gap the checker enforces |
   |---|---|---|---|---|
   | onboarding | account created, first purchase, trial start | 4 to 6 | 0, 1-2, 4-5, 7-9, 12-14 | 1 day |
   | nurture | lead magnet download, enquiry | 3 to 6 | 0, 3, 7, 14, 21 | 2 days |
   | winback | no purchase or login for a lapse period | 3 | 0, 5, 12 | 3 days |

   Read only the matching section of [references/playbooks.md](references/playbooks.md) for the job of each email in that type, example subjects, and sunset rules.

   Define "lapsed" for a win-back as roughly 1.5 to 2 times the customer's normal repurchase interval (a working rule), not a round 90 days by default. Longer or shorter gaps are allowed; below the minimum the checker fails the email unless `min_gap_days` is set deliberately, which produces a warning.
3. **Sequence contract.** Fill `trigger` (one event the sending tool can detect), `goal` (one event, with a window: "first order within 14 days"), `exit_conditions` and the sender block. Exit conditions must include the goal event (so people who converted stop getting persuasion) plus any state that makes the email wrong (open support ticket, refund requested). Unsubscribe, hard bounce and spam complaint always exit; list them anyway so the loader sets them up.
4. **Email contract**, one per email, all four parts required:
   - **One job**: a single sentence naming what the reader should understand or do. If it needs "and" twice, split it.
   - **Subject**: plain, specific, under 60 characters, no fake `Re:`/`Fwd:`, no more than one `!`, no all-caps words, none of the pressure/prize/free-claim phrases the checker lists. It must be true to what is inside.
   - **Preheader**: complements the subject (never repeats it), under 130 characters.
   - **CTA**: one primary action with a label that names the action ("Open the list builder"), one HTTPS destination, different from every other email's destination in the sequence.
5. **Check.** Run, read the findings, fix, re-run until `ok` is true. Do not edit the script to pass.

```bash
python scripts/sequence_check.py validate sequence.json
python scripts/sequence_check.py validate sequence.json --strict   # warnings also fail
```

6. **Deliverability and measurement.** Add the checklist from [references/measurement_and_deliverability.md](references/measurement_and_deliverability.md) to the plan note, with the user's real answers (authentication status, list age, volume). Read that file for the metrics, guardrail numbers and holdout design; do not report open rate as the success metric.
7. **Report** in the fixed shape below.

## Compliance rule (state it, do not decide it)

Read [references/compliance.md](references/compliance.md) before step 3 when the audience is outside one known country, when the list came from anywhere but the sender's own signup or customers, or when the user asks "is this legal". The skill states basics and always says "verify with counsel"; it does not give a legal opinion for any jurisdiction.

Hard stops, no exceptions:
- Purchased, rented or scraped lists are not a consent basis. Do not draft a sequence to send to one. Offer instead: a consented signup route, a confirmation (re-permission) email sent only where the user has a lawful basis, or paid/organic acquisition that leads to a signup form.
- A marketing email with no working unsubscribe, no sender identity or no postal address is not finished.
- A subject that misstates the content (fake reply, fake order, fake urgency) is deceptive; rewrite it.
- Do not build a sequence whose exit is "never"; every sequence needs an end and a sunset rule for people who never engage.

## Script

`scripts/sequence_check.py validate <file> [--strict] [--min-gap DAYS]`: run it, do not read it for rules. Prints one strict JSON document: `ok`, `summary` (emails, fail, warn), `findings` (level, code, message, email id), `timeline` (day, gap_days, id, subject, cta, job, which exit list applies) and `not_checked`. Exit 0 pass, 1 on any FAIL (or WARN with `--strict`), 2 on a missing, empty or non-object file. It checks structure and surface patterns only. If Python is not available, walk the check table in `references/sequence_schema.md` by hand and say so in the report.

## Plan note (fixed shape)

```
Sequence: <name>, <type>, trigger <event>, goal <event within window>
Timeline: <day: id: subject: cta, one line per email, copied from the checker's timeline>
Consent basis: <basis and where the record lives, or OPEN>
Checker: <ok true/false, N fail, N warn; warnings kept on purpose and why>
Deliverability: <checklist answers, unknowns marked OPEN>
Measurement: <primary metric, guardrails with numbers, holdout, review dates>
Placeholders to replace: <every invented or missing address, URL, evidence>
Not checked: consent actually obtained, legality in any jurisdiction, copy quality, inbox rendering
```

## Limits

- The checker reads a JSON description, not the real emails, so it cannot see body copy, links inside bodies, images or the actual footer.
- Spam-trigger matching is a short English phrase list; modern filters weigh sender reputation and engagement far more than wording. A clean subject is not a deliverability result.
- Cadence minimums (1, 2 and 3 days) and the 60/78-character subject limits are working values, not measured optima.
- Compliance statements are summaries of common rules in the US, EU/UK and Canada for orientation; rules change and differ by case. Always verify with counsel.
- It does not choose a sending platform, build templates, write full email bodies on its own authority, or run any send.
