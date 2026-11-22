---
name: project-decision-log
description: Keeps a durable DECISIONS.md log of project decisions with stable ids, context, options, reasons, consequences, revisit conditions and status, and supersedes old entries instead of rewriting them. Use when a decision is hard to undo, costly or contested and future sessions or teammates must know what was decided and why, or when a new session must read prior decisions before acting on a topic. Do not use for meeting notes, task tracking, bug reports or personal journaling.
license: Apache-2.0
compatibility: none beyond a text-capable agent (type B)
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Project Decision Log

Keep one file, DECISIONS.md, at the project root as the record of decisions that later sessions and teammates must not re-argue by accident. Each entry is written once. A later change is made by adding a new entry that supersedes the old one, never by rewriting the old one.

## Files in this package

- `SKILL.md`: this procedure. This is the only file the agent needs at run time.
- `LICENSE.txt`: Apache-2.0 license text.

There are no scripts. Every step uses the agent's file read and file write tools.

## Step 1: Read before acting

1. Open `DECISIONS.md` at the project root.
2. If the file does not exist, create it with the single line `# Decisions` and set the next id to `D-001`.
3. Note every entry id and its status. Find the highest id.
4. If the task touches a topic an active entry already covers, read that entry in full before acting. Follow it, or log a supersession in Step 5. Never silently contradict it.

Required output: `Read: <N> entries, highest id D-<NNN>, active: <comma list of active ids or none>`

## Step 2: Decide whether to log

Log when at least one row of this table says Yes. Otherwise skip and say so.

| Signal | Log? | Working value (not an industry standard) |
|---|---|---|
| Hard to undo: changes a data format, public interface, contract or license | Yes | undoing it would take more than 1 working day |
| Costly: commits money or more than 1 working day of effort | Yes | any stated amount, or more than 1 working day |
| Contested: two or more people or sources took different positions | Yes | at least 2 positions named |
| Reversible within 1 hour with no outside effect | No | none |
| Naming, formatting or layout inside one file | No | none |
| Restates an active entry without change | No | none |

Required output: `Log: yes (row: <signal>)` or `Log: no (reason: <row or rule>)`. If no, stop here.

## Step 3: Assign the id

The new id is the highest existing id plus 1, written with three digits (`D-004`). Ids are never reused and never renumbered, even after an entry is superseded.

Required output: `Id: D-<NNN>`

## Step 4: Fill the template

Write the entry with exactly this shape. All ten lines must be present.

```
## D-<NNN> <short title, 60 characters or fewer>
- Date: <YYYY-MM-DD, the session date>
- Status: active
- Supersedes: none
- Decision: <one sentence, active voice>
- Context: <what forced the decision, 1 to 3 sentences>
- Options considered: <A) ...; B) ...; at least 2 options, or "only one option: <reason>">
- Reason: <why this option, 1 to 3 sentences>
- Consequences: <what this now requires or rules out>
- Revisit by: <YYYY-MM-DD, or an observable condition>
```

Filling rules:

- Use only facts from the user or the session. Never invent options, reasons or dates.
- If a value is missing, write `unknown` and list the field in the reply under Open questions.
- Revisit by defaults to the session date plus 90 days unless the user gives a condition. A condition must be checkable, for example "when the vendor ships version 3", not "when things change".

## Step 5: Supersede, do not edit

Use this step only when the new decision replaces an active entry.

1. In the new entry, set `Supersedes:` to the old id, for example `- Supersedes: D-001`.
2. In the old entry, change exactly one line: `- Status: active` becomes `- Status: superseded by D-<NNN>`.
3. Change nothing else in the old entry.

If the target entry is already superseded, or does not exist, stop (see the refusal list).

## Step 6: Append

Add the new entry at the end of the file, with one blank line before it. Never insert in the middle of the file and never reorder entries.

## Step 7: Verify

Re-read the whole file and check each item:

- ids are unique and increase from top to bottom;
- each new entry has all ten lines;
- each supersession pair is consistent: the old entry names the new id, and the new entry names the old id;
- the old entry differs from its previous text only on its Status line.

Required output: `Check: pass`, or the name of the first failed item. On a failure, stop and report. Do not repair the file silently.

## Output contract

Reply with these headings, in this order, and nothing else:

- `## Read`: the Step 1 line.
- `## Logged`: one line per new entry, `D-<NNN> | <title> | status active | supersedes <old id or none>`. If nothing was logged, write `none` and the Step 2 reason.
- `## Changed`: the old id and its Status line before and after, for example `D-001: active -> superseded by D-004`. Write `none` if no supersession happened.
- `## Open questions`: a bullet per field written as `unknown`, or `none`.
- `## Check`: `pass` or the failed item.

## Refuse / stop when

- The request is to edit, delete, reorder or renumber an entry, apart from the Status line in Step 5.
- The request is to reuse an id, to write an entry with a status other than `active` or `superseded by`, or to change an old entry's body.
- The decision or its reason cannot be stated from user words or session facts, and the user does not supply them after one question. Write `unknown` and stop before inventing content.
- DECISIONS.md has duplicate ids, a missing field in any existing entry, or cannot be read. Stop and report the line numbers.
- The supersession target is already superseded or does not exist.
- The entry would contain a password, token, key, personal identifier or customer record. Refuse, and name the part to remove.
