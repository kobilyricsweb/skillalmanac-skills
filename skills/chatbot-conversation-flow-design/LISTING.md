# chatbot-conversation-flow-design

## One line

Writes a support chatbot flow for up to five intents: a step table per intent, a two-miss fallback, a handoff payload and reply length limits.

## What it does

The skill turns a short list of support intents into flow tables. Each intent gets three to six numbered steps. Every step lists the user goal, the bot question, the valid answers and the next step, which is either another step, a closing `resolve`, or a `handoff:` target with a reason. The skill checks that every target exists and that each flow can reach a human. It counts the words in each bot question so that no single turn runs past 15 words, and it rejects a small set of stock phrases that make bots sound scripted.

The handoff section fixes the payload a human agent receives. It has eight keys, a 50-word summary limit, and a redaction rule for long digit runs and for anything typed after the word "password". The fallback is a single fixed offer after two consecutive misses. A "no" returns the customer to the step they were on, so a customer who declines a handoff is not dropped out of the flow.

Policy facts the shop has not supplied, such as delivery times, return windows or size ranges, are written as `TO-CONFIRM` and listed for the shop to answer, never guessed. Outside handoff hours, the offer states the hours and the summary is kept for the next shift.

## When to use

Use it when a support chatbot repeats the same question, or when a team has a short intent list and needs the flow written down before any bot code is built. It suits a shop with order, returns, shipping, sizing and account questions, because those intents resolve in three or four turns each.

## When not to use

Do not use it to review a live chat transcript, to design payment handling, or to decide legal, medical or safety triage. It writes text flows only and does not write program code for a bot platform.

## Requirements

Any text-capable agent. No tools, no network access, no packages. The intake needs a shop name, the intents, a handoff channel and handoff hours.

## Example

The example is a complete run for a five-intent smoke shop. The intake was complete, so flows were written. Six policy facts were not supplied, so they appear as `TO-CONFIRM` and are listed under Questions. The first flow shows the fallback path: a customer typed "tomorrow" twice when asked for an order number, accepted the offer, and was handed off.

### Intake
Status: complete
Shop name: Example Shop
Handoff channel: support email queue
Handoff hours: Monday to Friday, 9:00 to 17:00 Eastern

### Intent list
| Intent | Merged phrasings |
|---|---|
| Order status | where is my order; track my order; order not arrived |
| Returns | return an item; refund question; exchange an item |
| Shipping | delivery time; shipping cost; international delivery |
| Sizing | which size; size chart; fit question |
| Account | reset password; change email; login problem |

### Flow: Order status
| Step | User goal | Bot question | Valid answers | Next step |
|---|---|---|---|---|
| S1 | Give order number | What is your order number? | an order number; "no number" | an order number -> S2; "no number" -> S3 |
| S2 | Pass the number on | I can pass this order number to the team. Shall I connect you? | "yes"; "no" | "yes" -> handoff:customer_request; "no" -> resolve |
| S3 | Find the number | Want a person to check your order number? | "yes"; "no" | "yes" -> handoff:customer_request; "no" -> S1 |

Fallback: after 2 consecutive misses, send the fixed offer text; yes -> handoff:fallback_limit; no -> missed step.

### Flow: Returns
| Step | User goal | Bot question | Valid answers | Next step |
|---|---|---|---|---|
| S1 | Start a return | Which item do you want to return? Give the order number. | an order number; "not sure" | an order number -> S2; "not sure" -> S3 |
| S2 | Check the return window | Was it delivered within TO-CONFIRM days? | "yes"; "no" | "yes" -> S4; "no" -> handoff:out_of_scope |
| S3 | Find the order number | Want a person to check your order number? | "yes"; "no" | "yes" -> handoff:customer_request; "no" -> S1 |
| S4 | Send the label | Return label: TO-CONFIRM. Anything else? | "yes"; "no" | "yes" -> S1; "no" -> resolve |

Fallback: after 2 consecutive misses, send the fixed offer text; yes -> handoff:fallback_limit; no -> missed step.

### Flow: Shipping
| Step | User goal | Bot question | Valid answers | Next step |
|---|---|---|---|---|
| S1 | Pick the destination | Is the delivery inside the country or abroad? | "domestic"; "international"; "not sure" | "domestic" -> S2; "international" -> S3; "not sure" -> S4 |
| S2 | Learn the domestic time | Domestic delivery takes TO-CONFIRM business days. Anything else? | "yes"; "no" | "yes" -> S1; "no" -> resolve |
| S3 | Learn the international time | International delivery takes TO-CONFIRM business days. Anything else? | "yes"; "no" | "yes" -> S1; "no" -> resolve |
| S4 | Offer a person | I can connect you with the team for that. Connect me? | "yes"; "no" | "yes" -> handoff:customer_request; "no" -> S1 |

Fallback: after 2 consecutive misses, send the fixed offer text; yes -> handoff:fallback_limit; no -> missed step.

### Flow: Sizing
| Step | User goal | Bot question | Valid answers | Next step |
|---|---|---|---|---|
| S1 | Pick the item type | Which item needs a size? | "shoes"; "clothing"; "other" | "shoes" -> S2; "clothing" -> S3; "other" -> handoff:out_of_scope |
| S2 | Give shoe size | What is your usual shoe size? | a shoe size; "not sure" | a shoe size -> S4; "not sure" -> handoff:customer_request |
| S3 | Give clothing size | What is your usual clothing size? | a clothing size; "not sure" | a clothing size -> S4; "not sure" -> handoff:customer_request |
| S4 | Send the chart | Size chart: TO-CONFIRM. Anything else? | "yes"; "no" | "yes" -> S1; "no" -> resolve |

Fallback: after 2 consecutive misses, send the fixed offer text; yes -> handoff:fallback_limit; no -> missed step.

### Flow: Account
| Step | User goal | Bot question | Valid answers | Next step |
|---|---|---|---|---|
| S1 | Pick the issue | Which account issue is it? | "reset password"; "change email"; "login problem"; "other" | "reset password" -> S2; "change email" -> S3; "login problem" -> S4; "other" -> handoff:out_of_scope |
| S2 | Check the reset | Did your password reset work? Reset route: TO-CONFIRM. | "yes"; "no" | "yes" -> resolve; "no" -> handoff:customer_request |
| S3 | Change the email | Shall I connect you to the team for an email change? | "yes"; "no" | "yes" -> handoff:customer_request; "no" -> resolve |
| S4 | Read the login error | Is the error about the password or a locked account? | "password"; "locked"; "other" | "password" -> S2; "locked" -> handoff:customer_request; "other" -> handoff:out_of_scope |

Fallback: after 2 consecutive misses, send the fixed offer text; yes -> handoff:fallback_limit; no -> missed step.

### Handoff payload
```json
{
  "intent": "order_status",
  "handoff_reason": "fallback_limit",
  "miss_count": 2,
  "attempted_steps": ["S1", "S1"],
  "reference_id": "",
  "contact_channel": "support email queue",
  "summary": "Customer asked about an order. No order number after two tries. Customer accepted the offer to speak with a person.",
  "redacted_last_message": "tomorrow"
}
```

### Checks
| Check | Result |
|---|---|
| Intents in run | 5 of 5 allowed |
| Bot questions over 15 words | 0 (longest is 13 words) |
| Banned phrases found | 0 |
| Dead ends | pass |
| Flows with a handoff path | 5 of 5 |
| Steps per flow (3 to 6) | pass: order status 3; returns 4; shipping 4; sizing 4; account 4 |
| TO-CONFIRM markers | 6, each listed under Questions |

### Questions
1. Returns S2: how many days is the return window?
2. Returns S4: what is the return label text?
3. Shipping S2: how many business days is domestic delivery?
4. Shipping S3: how many business days is international delivery?
5. Sizing S4: where is the size chart?
6. Account S2: what is the password reset route?

## Limits

The thresholds for misses, turns, words and steps are working values chosen for readability. They are not published standards, and a team should adjust them to its own channel. The example shop and its hours are invented for the smoke run, and its policy facts are left as `TO-CONFIRM`. The skill does not know a real shop's policies, so every fact in a flow must come from that shop. Reply length is counted by spaces, so a bot question with a long product name may need manual review.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
