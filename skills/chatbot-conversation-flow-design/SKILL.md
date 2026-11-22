---
name: chatbot-conversation-flow-design
description: Writes a support chatbot conversation flow for up to five customer intents, with a step table per intent, a two-miss fallback, a human handoff payload and reply length limits. Use when a support chatbot loops or dead-ends, when a team must plan a handoff to a person, or when a shop needs flow steps for order status, returns, shipping, sizing or account questions. Do not use for live chat transcripts, legal or medical triage, payment system design or writing the bot's program code.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Chatbot conversation flow design

Designs the conversation flow for a support chatbot: one flow table per intent, a fallback after repeated misses, a handoff payload for a human agent, and reply limits. The output is text only. Shipped file: LICENSE.txt (Apache-2.0).

## Intake facts (required)

| Fact | Accepted value | If missing |
|---|---|---|
| Shop name | Any name the shop uses | Status partial |
| Intents | 1 to 5 intent names from the support queue | Status partial |
| Handoff channel | An email queue or a chat queue name | Status partial |
| Handoff hours | Days and times with a time zone | Status partial |

## Workflow

1. Intake check. Confirm the four facts above. Output: the `Intake` block. If any fact is missing, set `Status: partial` and return the `Questions` list (see the stop rules).
2. Normalize intents. Keep the first five intents in the order given. Merge phrasings that share one answer, for example "where is my parcel" under shipping. Output: `Intent list` table with at most three merged phrasings per row.
3. Write the flow for each intent. Each flow has 3 to 6 steps, with IDs S1, S2 and so on. Policy facts (windows, deadlines, times, formats, prices, locations) must be supplied by the shop in the request; if one is not, write `TO-CONFIRM` in the bot turn and list it in Questions. Output: one flow table per intent, using the columns in the output contract.
4. Attach the fallback line under each flow table. Output: one `Fallback:` line per flow, using the fixed offer text in the rules table.
5. Write the handoff payload. Output: one JSON object with the eight keys in the output contract.
6. Check reply length and wording. Count the words in every bot question and scan for banned phrases. Output: rows in the `Checks` table.
7. Check dead ends. Every Next step must name an existing step ID in the same flow, `resolve`, or `handoff:<reason>`. Every flow must reach a `handoff:` target from at least one step. Output: `pass`, or the failing step IDs. Fix once, then recheck.

## Thresholds and rules

| Rule | Value | Action |
|---|---|---|
| Consecutive misses before fallback (working value) | 2 | Send the fixed offer text in one bot turn |
| Turns inside one flow before handoff (working value) | 8 | Hand off with reason `fallback_limit` |
| Customer asks for a person, any wording | Immediately | Hand off with reason `customer_request`, ask nothing more |
| Intent outside the intent list | Any | Hand off with reason `out_of_scope` |
| Card number, bank account number or password in a message | Any | Stop collecting, redact, hand off with reason `safety` |
| Words per bot turn (working value) | 15 maximum | Shorten the question |
| Handoff summary length (working value) | 50 words maximum | Keep facts only |
| Steps per flow (working value) | 3 to 6 | Merge or split steps |
| Intents per run | 5 maximum | Refuse the extra intents and ask which five to keep |
| Policy fact not supplied by the shop (window, deadline, time, format, price, location) | Any | Write `TO-CONFIRM` in the bot turn, list it in Questions, never guess a value |
| Handoff requested outside handoff hours | Any | Hand off as normal; the bot turn becomes `We are away. Hours: <intake hours>. Leave a note?`; a yes uses the reason it already has; `summary` is written for the next shift |

A miss is a user turn that matches none of the valid answers to the current bot question. Fixed offer text: "Let me connect you with our team. Shall I?" If the customer answers "no" to the offer, return to the missed step and reset the miss count to 0.

Banned phrases in any bot turn: "Unfortunately", "Great question", "I apologize for any inconvenience". No exclamation marks.

Next step values: a step ID in the same flow (for example `S2`), `resolve` (the flow ends with one closing bot turn), or `handoff:<reason>`, where the reason is one of `fallback_limit`, `customer_request`, `out_of_scope`, `safety`. Write pairs as `answer -> target`, separated by semicolons.

## Counting rules

- Words are counted by splitting the text on spaces. "8 digits" is 2 words. A hyphenated word is 1 word. Punctuation attached to a word does not add a word.
- A turn count of 8 means eight user turns inside one flow, counted from the first step of that flow. A turn that answers the fallback offer also counts.
- A miss counter starts at 0 for each conversation. It goes up by 1 for each miss and resets to 0 for each valid answer.
- The 3 to 6 step limit counts step rows in the flow table, not the number of possible answers.
- Count every bot question for the 15-word limit, including the fixed offer text, which is 9 words.
- `TO-CONFIRM` counts as 1 word. The outside-hours text is 14 words with the example hours; if the intake hours push it past 15 words, write the hours as `TO-CONFIRM` and list them.

## Output contract

Use these headings, in this order, and no others.

### Intake
`Status:` complete, partial, or refused, then `Shop name:`, `Handoff channel:` and `Handoff hours:`. Complete means all four facts are present and flows are written. Partial means flows are not written and the Questions list is returned. A `TO-CONFIRM` marker does not change the status. Refused means a refusal rule fired.

### Intent list
Table with columns `Intent | Merged phrasings`.

### Flow: <intent name>
Table with columns `Step | User goal | Bot question | Valid answers | Next step`, then one line:
`Fallback: after 2 consecutive misses, send the fixed offer text; yes -> handoff:fallback_limit; no -> missed step.`

### Handoff payload
One JSON object with exactly these keys: `intent`, `handoff_reason`, `miss_count`, `attempted_steps`, `reference_id`, `contact_channel`, `summary`, `redacted_last_message`.
- `attempted_steps`: step IDs in the order visited, repeats allowed.
- `reference_id`: the order number if the customer gave one, otherwise an empty string. Never a card, bank or password value.
- `summary`: 50 words maximum.
- `redacted_last_message`: replace any run of 13 to 19 digits (working value) and any text after the word "password" with `[REDACTED]`.

### Checks
Table with columns `Check | Result`. Rows: intents in run, bot questions over 15 words, banned phrases found, dead ends, flows with a handoff path, steps per flow, `TO-CONFIRM` markers (each one must also appear in Questions).

### Questions (partial status, or any `TO-CONFIRM` marker)
Numbered list, one question per missing intake fact, per extra intent, or per `TO-CONFIRM` marker. No flows are written when the status is partial.

## Refuse or stop when

- A flow has no step leading to `handoff:`. It hides the human handoff. Refuse that flow and set the status to refused.
- A step asks for a card number, a bank account number, or a password. Refuse that step.
- The bot is asked to claim it is a human. Refuse.
- The dead-end check still fails after one fix round. Stop and list the failing step IDs.
- Any intake fact is missing. Set the status to partial and return the Questions list. Do not guess a shop name or a channel.
- More than five intents are given. Set the status to partial and ask which five to keep.
