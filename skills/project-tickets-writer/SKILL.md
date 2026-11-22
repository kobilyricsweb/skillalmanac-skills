---
name: project-tickets-writer
description: Writes engineer-ready tickets from a feature description or meeting notes. Use when asked to write tickets, break down a feature, make user stories or a backlog from a spec, split a ticket that is too big, or check tickets before engineers see them. Gives one outcome per ticket, Given/When/Then criteria, size limit, dependencies, non-goals, definition of done, a splitting decision table and a script that validates JSON or Markdown tickets for missing criteria, vague verbs, dependency cycles and duplicate titles. Do not use for roadmaps, sprint planning, estimation poker, or filing tickets in a tracker.
license: Apache-2.0
compatibility: The validation script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, apply the checks in step 6 by hand.
metadata:
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  license: Apache-2.0
  version: "0.1.0"
  network: none
---

# Project tickets writer

Produce tickets an engineer can accept or reject without a meeting. A ticket is accepted when its outcome is one thing, every criterion can be checked by someone who did not write it, and nothing it leaves out is a surprise.

## Ticket contract

Each ticket has exactly these fields (details and both file formats in [references/ticket-format.md](references/ticket-format.md)):

| Field | Rule |
|---|---|
| `id`, `title` | Unique id (`T1`, `PAY-12`). Title is a concrete verb plus object: "Send a reset link by email". Never "handle", "improve", "support", "fix stuff". Two actions joined by "and" means two tickets. |
| `outcome` | One sentence: who can do or see what after this ships. |
| `size` | `XS`=0.5, `S`=1, `M`=3 engineer-days, or a number of days. Over 3 days (`L`, `XL`) is not allowed: split. |
| `depends_on` | Ids that must ship first. Only hard dependencies: the ticket cannot be tested without them. Otherwise `none`. |
| `non_goals` | At least one. Name what a reader would reasonably assume is included, and the ticket that owns it if there is one. |
| `acceptance_criteria` | 1 to 6 items, each `Given <state>, when <one trigger>, then <observable result>`. The result carries a value: a status code, exact text, a count, a time limit. At least one happy path, and one failure or boundary case wherever input is accepted. |
| `definition_of_done` | What must be true to close it beyond the criteria (tests, review, flag, docs). One line is enough; reuse the team's standard if the user gave one. |

## Workflow

```
- [ ] 1 Extract outcomes from the source
- [ ] 2 Mark unknowns and decide: ask or assume
- [ ] 3 Split with the decision table
- [ ] 4 Write each ticket to the contract
- [ ] 5 Set dependencies and order
- [ ] 6 Validate with the script, fix, re-run
- [ ] 7 Report
```

1. **Extract outcomes.** For meeting notes, sort each line first: decision (becomes a criterion or non-goal), action item for a person (not a ticket unless engineers do it), wish or opinion (ask), open question (step 2). Rules for notes are in [references/from-meeting-notes.md](references/from-meeting-notes.md); read it only when the source is notes or a chat log. For a feature description, list every sentence that begins "users can", "the system should" or names a behaviour change. Each distinct change someone could observe is a candidate outcome.
2. **Unknowns.** If you cannot write the `then` of a criterion (no number, no wording, no owner), that is an unknown. Ask at most 3 questions, only for unknowns that change scope. For everything else write the assumption into the ticket as a criterion or non-goal and list it in the report. Never invent a number silently: label invented values `ASSUMED:` in the criterion.
3. **Split** every candidate with this table. Apply rows top to bottom; stop when no row fires.

| If the candidate... | Then |
|---|---|
| is estimated over 3 days | split into vertical slices, each user-visible; never split by layer (all backend, then all UI) unless two teams own the layers |
| needs more than 6 criteria | split along the groups the criteria fall into; each group gets its own outcome |
| has a title that needs "and" between two actions | one ticket per action |
| serves two different actors (admin and member) | one ticket per actor |
| has a part that is a data migration, flag rollout or irreversible change | that part is its own ticket, shipped separately |
| has a `then` you cannot write yet | add a spike: outcome is a written decision, size at most 2 days, no code criteria; the dependants depend on it |
| is a refactor needed by a feature | fold into the feature unless it ships alone with no behaviour change |
| has 3 or more error-handling criteria beside the happy path | keep the happy path ticket, move errors to a follow-up that depends on it |
| is under 0.5 day with fewer than 2 criteria and shares an outcome area with a neighbour | merge into the neighbour |

4. **Write** each ticket from [assets/tickets-template.md](assets/tickets-template.md) (Markdown by default; JSON only if the user's tool needs it). Weak and strong criterion pairs and non-goal patterns are in [references/splitting-and-criteria.md](references/splitting-and-criteria.md); read it when a criterion keeps failing step 6 or the user asks why a ticket was split.
5. **Dependencies and order.** A dependency is justified only by "cannot be tested without". Shared files, same area or "makes sense first" are not dependencies. If a ticket depends on more than 3 others it is probably too large. The script prints a build order when there is no cycle.
6. **Validate.** Save the tickets to a file and run:

```bash
python scripts/tickets_lint.py tickets.md --max-criteria 6 --max-size-days 3
```

   Stdout is one JSON object: `ok`, `errors`, `warnings`, `findings` (`severity`, `rule`, `ticket`, `message`), `build_order` (null if a cycle exists). Exit 0 means no errors, 1 means errors (or any warning with `--strict`), 2 means the file could not be read. Fix every error. Fix each warning or keep it on purpose and say so in the report. Re-run until `ok` is true. Error rules: `missing-acceptance-criteria`, `criterion-not-gwt`, `too-many-criteria`, `vague-title`, `too-large`, `bad-size`, `missing-size`, `missing-outcome`, `missing-id`, `duplicate-title`, `duplicate-id`, `unknown-dependency`, `self-dependency`, `dependency-cycle`. Warning rules: `vague-criterion`, `vague-outcome`, `multiple-outcomes`, `missing-non-goals`, `missing-definition-of-done`, `near-duplicate-title`, `criterion-multiple-when`, `duplicate-criterion`, `outcome-not-one-sentence`. Do not edit the script to make a check pass. The script cannot judge whether a criterion is true to the source; step 7 covers that. Without Python, check by hand: every ticket has all seven fields, every criterion has Given, when and then, none exceeds the limits, and follow each `depends_on` chain looking for a loop.
7. **Report** in this shape, after the tickets:

```
Tickets: <n>, build order <ids>
Splits: <which source items became several tickets and which table row fired>
Assumed: <every ASSUMED value and every question left open>
Warnings kept: <rule, ticket, reason>
Not checked: <that criteria match what the stakeholders meant; estimates are the team's to confirm>
```

## Limits

- The script checks form, not truth: a well-formed criterion can still describe the wrong behaviour.
- Vague-word lists are English only and are heuristics; two-word titles that begin with fix, update, support or make are flagged even when meant well.
- Sizes are the writer's estimate until the team confirms them.
- The script does not read or write any tracker; filing tickets is the user's step.
