---
name: user-story-splitter
description: Splits one large user story into three to six thin, testable slices, each with Given/When/Then acceptance criteria, an S or M size label, and a first slice that delivers one complete outcome. Use when a product manager or team has a story too big to finish in one cycle, asks how to break a feature into deliverable pieces, or needs acceptance criteria for each piece. Do not use for writing new requirements, adding features the story does not mention, estimating hours, assigning owners or dates, or ranking a backlog across stories.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# User story splitter

Use this procedure to turn one user story into slices. Every slice must come from items already named in the story. Thresholds in this file are working values, not a published standard.

## Workflow

1. **Intake check.** Confirm the text names a who (an actor) and a what (an action or outcome). A bare umbrella verb (manage, handle, support) with no named actions fails this check. Output: pass, or status `needs-input` (see the stop rules).
2. **Restate.** Write Who, What and Why. If the story gives no reason, write `not stated`. Do not invent a Why. Output: three labeled lines.
3. **Inventory the scope.** List every workflow step, business rule, data variation, interface (screen, channel), path (happy or edge) and action that the story names, in the story's own words; an item is implied only if the story states a rule or step that cannot work without it. This list is the only allowed source for slices. Output: a bullet list with a count `N`.
4. **Run the splitting table** (below). Mark each axis Used or Not used. Output: the six-row table.
5. **Form slices.** Group the Used splits into three to six slices. Each slice delivers one outcome. Output: slice name, one-sentence Delivers line, and Depends on (`none` or a slice number).
6. **Write acceptance criteria.** Give each slice two to four Given/When/Then criteria. Each criterion checks one observable result. Output: numbered criteria.
7. **Size each slice** with the table below. A slice that is L must be split again at step 5. Output: `Size: S` or `Size: M`.
8. **Pick the first slice.** It is the smallest slice that lets one user finish one happy-path outcome start to finish. Output: one line naming the slice and a reason of one sentence.
9. **Scope check.** Compare each slice with the step 3 list. Remove anything not on that list and record it under Not added. Output: the Not added list, or `none`.

## Splitting table (step 4)

| Axis | Ask | Used when |
|---|---|---|
| Workflow steps | Can the steps run one at a time? | The story names two or more ordered steps |
| Business rules | Does each rule change the result? | The story states two or more rules |
| Data variations | Do different data types need different handling? | The story names two or more kinds of data or account state |
| Interface | Is the outcome reached through more than one screen or channel? | The story names two or more screens or channels |
| Happy vs edge path | Is there a failure or exception the story mentions? | The story describes a failure, cancel or reversal |
| Operations | Does the story name view, create, change or end actions? | The story names two or more of these actions |

An axis is Used only if it creates a slice boundary. Mark the rest Not used.

## Decision and threshold table

| Check | Working value | Action when outside the value |
|---|---|---|
| Slice count | 3 to 6 | Under 3: status `partial`, explain why. Over 6: merge the two smallest adjacent slices until 6 remain. |
| Criteria per slice | 2 to 4 | 1 or 5 or more: rewrite or split the slice |
| Size S | 2 criteria, 1 workflow step, no new data field | Label S |
| Size M | 3 or 4 criteria, or 2 workflow steps, or 1 new data field | Label M |
| Size L | Anything beyond size M | Not allowed in output. Split again at step 5. |
| First slice | Smallest slice that completes one happy path for one user | Mark as the first slice |

## Output contract

Return Markdown with these headings, in this order:

```
# Story split: <short title>
Status: complete | partial | needs-input | refused
Who: <actor>
What: <action or outcome>
Why: <reason, or "not stated">

## Scope items
- <item> (N items total)

## Splitting table
| Axis | Candidate split | Used |
|---|---|---|

## Slices
### Slice 1: <name>
Size: S | M
Depends on: none | Slice <n>
Delivers: <one sentence>
Acceptance criteria:
1. Given <context>, when <action>, then <result>.
2. Given ...

## First slice
Slice <n>: <reason in one sentence>

## Not added
- <item the story does not contain>, or `none`
```

Status values:
- `complete`: three to six slices, every slice has two to four criteria and a size label.
- `partial`: the restatement and table are done, but a slice lacks valid criteria or fewer than three slices are possible. Give the parts that exist and a numbered list of the gaps.
- `needs-input`: intake failed. Output only the status and the Who, What and Why lines that are known, then a numbered list of up to five questions. Produce no slices.
- `refused`: the whole request is outside this skill. Output the status and one line naming the request.

## Refuse / stop when

- The text has no identifiable actor or no action or outcome (status `needs-input`).
- The text has fewer than four words (status `needs-input`).
- The main verb is a bare umbrella (manage, handle, support) and the story names no actions. Return status `needs-input` with one numbered question per missing action, up to five, and produce no slices.
- The request asks to estimate hours or story points, assign an owner, set a date, or rank several stories (status `refused`).
- The request asks you to add a feature, role, channel, rule or data field that the story does not contain. Do not add it. List it under Not added and split only the original story.
- A slice would need an invented edge path. Use an edge path as a slice only when the story names it or states a rule that implies it.

The license text for this skill ships as LICENSE.txt beside this file.
