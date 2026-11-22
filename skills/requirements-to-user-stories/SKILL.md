---
name: requirements-to-user-stories
description: Turns a requirements document into user stories with Given/When/Then acceptance criteria, a traceability table, and an uncovered list for vague requirements. Use when a product owner or analyst asks for user stories, backlog items, or acceptance criteria written from a requirements list, or needs every requirement traced to a story. Do not use for writing the requirements themselves, for adding features or user roles the document does not state, for story point estimates, or for full test plans.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B); no scripts, no network.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Requirements to user stories

Run this procedure on one requirements document at a time. Every story traces back to one numbered requirement, and every requirement ends in exactly one result: COVERED or UNCOVERED. Do not add features, roles, benefits, or numbers that the document does not state.

## Intake

Required: the requirements text pasted by the user.

A requirement is a line that states something a person or the system must be able to do or must have. Titles, role lists, scope notes, dates, and owners are context, not requirements. The roles you may use are only the roles the document names.

## Workflow

1. Number the requirements. Read the document from top to bottom and assign IDs R-01, R-02, and so on in document order. Copy each requirement text unchanged. Output: the Requirements rows.
2. Test each requirement in this order and stop at the first failure. Record its code.
   - VAGUE_OUTCOME: no measurable or observable result. Words such as fast, easy, good, robust, appropriate, or user-friendly, with no number or checkable state, fail this test.
   - UNRESOLVED_REFERENCE: uses it, this, that, or they with no clear antecedent in the same line or the line above.
   - NO_ROLE: names no role from the document as actor or recipient. When the actor is the system and a role is the recipient (for example, "emails the employee"), that recipient counts as the role.
   Output: the Result and Code columns for each requirement.
3. Write stories for COVERED requirements only, in this exact form: "As a <role>, I want <capability>, so that <result>." Rules:
   - The role is the role found in step 2.
   - The capability repeats the requirement verb and object.
   - The so-that clause restates the requirement result in the role's terms. It never adds a benefit the document does not state. If the requirement states no result, the so-that clause repeats the requirement outcome and an Open question asks the owner for the real benefit.
   - One story per requirement by default. Use two stories only when the requirement names two roles with different needs (working value: maximum two per requirement).
   Output: the story blocks with IDs S-01, S-02, and the covering requirement ID.
4. Write acceptance criteria for each story as Given/When/Then, using AC1, AC2, and so on. Each criterion may use only the actors, objects, and values that appear in its source requirement. Output: the AC lines under each story.
5. Build the traceability table with one row per requirement in ID order. For UNCOVERED rows, write none in Story IDs and 0 in Criteria.
6. Build the uncovered table. For each UNCOVERED requirement, give its code and the one missing fact that would make it testable, phrased as a question for the owner.
7. Self-check before replying. Confirm that: requirements equal covered plus uncovered; every story ID appears in the traceability table; every role used appears in the document; every story has 2 to 4 criteria; no number in any criterion is absent from the document.

## Decision table: requirement result

| Condition (checked in this order) | Result | Code |
|---|---|---|
| Fails the outcome test | UNCOVERED | VAGUE_OUTCOME |
| Fails the reference test | UNCOVERED | UNRESOLVED_REFERENCE |
| No role found | UNCOVERED | NO_ROLE |
| Passes all three tests | COVERED | none |

## Thresholds

| Item | Value | Basis |
|---|---|---|
| Acceptance criteria per story | 2 to 4 | working value |
| Stories per requirement | 1, or 2 when two roles have different needs | working value, maximum 2 |
| Requirement IDs | R-01 to R-99 | working value |
| Story IDs | S-01 upward, two digits | working value |
| Requirements read from one input | up to 99 | working value |

## Status values

| Status | When to use it |
|---|---|
| complete | Every requirement is COVERED and no clause was refused. |
| partial | At least one requirement is UNCOVERED, or a requested clause was refused. |
| stopped | No requirement line is found in the input. |

## Output contract

Reply with these sections, in this order, using these exact headings:

1. "## Status": line one is the status value. Line two is "Totals: requirements N, covered C, uncovered U, stories S, criteria K."
2. "## Requirements": table with columns ID | Text | Result | Code. Code is none for COVERED rows.
3. "## User stories": one block per story. Heading "### S-01 (covers R-01)", then the story sentence, then the criteria as "- AC1: Given ..., When ..., Then ..." lines.
4. "## Traceability": table with columns Requirement | Story IDs | Criteria | Result.
5. "## Uncovered": table with columns Requirement | Code | Missing fact. Write one row with none in each column when nothing is uncovered.
6. "## Open questions": numbered list, at most five items. Use it for refused clauses and for the missing facts from step 6.

## Refuse or stop when

- No requirement line is found: set status stopped, and reply only with a numbered list of up to three questions asking the user to paste the requirements as numbered lines that state what the product must do.
- The user asks for a feature, role, metric, or time limit the document does not state: refuse only that clause. Keep the rest of the deliverable, set status partial, and list the refused item under Open questions.
- A criterion or so-that clause would need an invented fact: leave the fact out and mark the requirement UNCOVERED with the missing fact named.
- The user asks for story points, priority, or test steps: out of scope for this skill. Say so in one line under Open questions and continue with the stories.
- Context lines (roles, dates, scope notes, owners) are not requirements. Do not give them story IDs.

## Shipped files

- SKILL.md: this procedure.
- LICENSE.txt: the Apache License 2.0 text that covers this skill.
