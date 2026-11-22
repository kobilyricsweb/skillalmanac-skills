## Contents

- Onboarding
- Nurture
- Win-back
- Subject and preheader rules with examples
- Exit and sunset rules

Read only the section for the sequence type in hand. Days are days after the trigger.

## Onboarding

Goal: the person reaches the product's first real result.

| Day | Job | Typical CTA |
|---|---|---|
| 0 | Confirm what they signed up for and name the single first step | the first-step page |
| 2 | Get the first result done (a template, an import, a sample) | open the feature with the template loaded |
| 5 | Show one customer outcome that is specific (numbers, time, a name with permission) | read the story |
| 9 | Remove the most common objection, with the offer if there is one | the offer or pricing page |
| 14 | Ask what is stopping them and close the sequence | reply or a two-question form |

Exit early when the first-result event fires; move them to a different "next step" flow rather than continuing this one. Send the day-0 email within minutes of the trigger; later delay misses the moment of highest attention.

## Nurture

Goal: a lead decides to talk, buy or book.

| Day | Job |
|---|---|
| 0 | Deliver what they asked for (the checklist, the guide) and say what comes next and how often |
| 3 | One worked example of the thing they downloaded |
| 7 | One mistake people make, with the fix |
| 14 | A case or comparison that helps them decide |
| 21 | A direct invitation: call, trial or quote |

Every email must be useful if the reader never clicks. Only the last asks for a sale; earlier CTAs lead to content or a small step. Three to six emails, then move the lead to the regular newsletter only if they consented to it separately.

## Win-back

Goal: a lapsed customer buys or logs in again; otherwise stop cleanly.

| Day | Job |
|---|---|
| 0 | Say what is new since they left, or what they had set up; no guilt, no fake urgency |
| 5 | Incentive or help: a real offer, or an offer to fix whatever went wrong, with a reply route |
| 12 | Tell them this is the last one and ask whether to keep sending; the CTA is "keep me subscribed" or a preference page |

Anyone who does not open or click anything in the sequence is suppressed from further marketing after day 12 plus a short grace window (a working rule: 30 days). Sending to unengaged addresses harms inbox placement for everyone else.

## Subject and preheader rules with examples

| Weak | Better | Why |
|---|---|---|
| Re: your order | Your first gear list is ready to build | Fake reply is deceptive and fails the checker |
| LAST CHANCE!!! 50% OFF | Free delivery on your first order, through Friday | No capitals, one claim, a real end date |
| Newsletter #14 | A bookkeeper's checklist, filled in | Names the content |
| (preheader) Free delivery on your first order, through Friday | (preheader) Applies automatically at checkout | The preheader adds, not repeats |

A real deadline may be stated; an invented one may not. A deadline in a subject must match the date in the body and in the offer's own terms.

## Exit and sunset rules

- Goal event reached: exit and tag so other flows can start.
- State changes that make the next email wrong: open support ticket, refund, address change, plan downgrade; list each one in `exit_conditions`.
- Unsubscribe, hard bounce, spam complaint: always exit, and suppress across all marketing flows, not just this one.
- Sunset: a recipient who has ignored a defined number of consecutive marketing emails (a working value: 6 to 10 across flows, or 90 to 180 days) is suppressed or sent one re-permission email.
