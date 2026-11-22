---
name: "threat-model-stride-worksheet"
description: "Walks a feature through a STRIDE threat-modelling worksheet: takes assets, actors, trust boundaries and data flows from the user, checks each flow against the six STRIDE categories, and records threat, likelihood, impact (1-3), mitigation, owner and residual risk. Use when a team is designing or changing a feature that handles logins, credentials or personal data and needs a threat model before build. Do not use for claiming a system is secure, writing attack steps, or reviewing existing code."
license: Apache-2.0
compatibility: None beyond a text-capable agent, with no scripts and no network access.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# STRIDE threat-model worksheet

Produce one worksheet per feature. The user supplies the system description (step 1). You fill the tables in steps 2 to 5 and emit the output contract in step 6. The worksheet lists threats and mitigations. It never states that the system is secure.

## Step 1: Collect inputs

Check that the user has supplied all five items. If an item is missing, list it under "Missing inputs" in the output and continue only with what is present.

1. Feature name and a one-sentence purpose.
2. Assets: data or capabilities worth protecting (for example credentials, sessions, personal data, payment tokens).
3. Actors: each user type, each operator, and each external system.
4. Trust boundaries: each point where data moves between zones (browser to server, service to database, service to an outside mail provider).
5. Data flows: numbered flows, each with source, destination, data carried, and the boundary it crosses.

Minimum acceptable input: 3 flows, and at least one flow that carries a credential or reset secret. If more than two of the five items are missing, stop (see the refuse list).

## Step 2: Assign IDs

- Assets: A1, A2, and so on. Actors: U1, U2, and so on. Flows: F1, F2, and so on.
- Threat IDs take the form T-Fn-X, where X is the STRIDE letter. Example: T-F2-I.
- If one flow has two threats in one category, add a number: T-F2-I1, T-F2-I2.

## Step 3: Walk each flow through six STRIDE categories

Every flow is checked against all six categories. Each category ends in either one or more threats or a "none" entry with a reason of at least 10 words.

| Letter | Category | Question to ask of the flow |
|---|---|---|
| S | Spoofing | Can an actor pass as another identity on this flow? |
| T | Tampering | Can data on this flow change without detection? |
| R | Repudiation | Can an actor deny an action because no record exists? |
| I | Information disclosure | Can data reach a party that should not see it? |
| D | Denial of service | Can legitimate users be blocked or made to fail? |
| E | Elevation of privilege | Can an actor gain rights they were not granted? |

## Step 4: Score each threat

Likelihood (L):

| Value | Meaning |
|---|---|
| 1 | Needs insider access or unusual conditions |
| 2 | Reachable by an outside actor using known techniques |
| 3 | Reachable by anyone with no special access |

Impact (I):

| Value | Meaning |
|---|---|
| 1 | No personal data and no account control exposed |
| 2 | One account or one user's data exposed |
| 3 | Many accounts, credentials, payment data or admin control exposed |

Score = L x I, a value from 1 to 9.

| Score | Priority | Required before build |
|---|---|---|
| 6 to 9 | High | Concrete mitigation in the design, and a named owner role |
| 3 to 4 | Medium | Mitigation, or an accepted risk with owner sign-off |
| 1 to 2 | Low | Record only; owner sign-off to accept |

These cut-offs (1 to 3 scales, score bands 6 to 9, 3 to 4, 1 to 2) are working values for this worksheet. They are not an industry standard.

## Step 5: Mitigation, owner and residual risk

- Each High threat needs a named control, such as "single-use reset token, 256 random bits, expires after 30 minutes (working value), stored hashed". Mitigations like "be secure" or "add monitoring" are rejected: write "Rejected: vague mitigation" and rewrite before output.
- Owner: a role (for example "Identity team lead"). Never a person's name. If the role is unknown, write "owner to confirm".
- Residual risk: re-score the threat after the mitigation with the same L and I tables. If the residual priority is still High, add the threat to Open items with "escalate to owner".

## Step 6: Output contract

Emit these four sections in this order, with these exact headings. No other top-level headings.

`## Scope`: feature name, purpose, then the asset, actor, boundary and flow lists with their IDs.

`## Threat table`: one row per threat with these columns, in this order:
ID | Flow | STRIDE | Threat | L | I | Score | Priority | Mitigation | Owner role | Residual L | Residual I | Residual priority

`## Coverage check`: one row per flow, columns F | S | T | R | I | D | E. Each cell holds a threat ID or "none: reason". No empty cells.

`## Open items`: bulleted list covering missing inputs, residual High items marked "escalate to owner", and assumptions you made.

End with one line: `Limits: covers only the flows listed in Scope; does not establish that the feature is secure.`

## Refuse / stop when

- The user asks you to confirm that the system is secure, safe or compliant. Reply that the worksheet can list threats and mitigations but cannot certify security.
- The user asks for exploit steps, payloads, commands aimed at a live system, or how to bypass a control. Give a one-sentence threat description only, with no technique detail.
- More than two of the five step 1 inputs are missing. Return the missing-input list and stop.
- The target system belongs to a third party and the user has no stated authority over it.
- The user asks you to name people as owners or to record sign-offs. Use roles and "owner to confirm".
