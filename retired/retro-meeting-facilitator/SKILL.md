---
name: retro-meeting-facilitator
description: Builds a timed team retrospective agenda, picks a format (start-stop-continue, 4Ls or timeline) from a fixed table, groups pasted sticky notes, runs dot-voting, and turns the top three themes into owned actions with due and check dates. Use when a team has just finished a sprint, release or missed deadline and needs a retro agenda, a capture sheet or an action list from raw notes, or when last retro's actions were never reviewed. Do not use for individual performance reviews, blame assignment for a named person, root-cause analysis of an outage (use a postmortem), or one-to-one feedback.
license: Apache-2.0
compatibility: none beyond a text-capable agent (type B)
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Retro Meeting Facilitator

Use this procedure to run one retrospective of 60 minutes, or the same steps in 45 minutes when the team has 3 or 4 people. Every output is a table so the team can copy it into a tracker. All numbers below are working values chosen for this procedure, not published standards.

## Inputs to collect first

- Team size (3 to 12 people; see Refuse / stop when).
- Retro period (for example "release 4.2, last 3 weeks").
- Situation tag: `routine`, `missed-deadline`, `release-problem`, or `mixed-mood`.
- Pasted notes, one note per line. Keep the author if it is given, but do not repeat it in outputs.
- Actions from the previous retro, with their status if known.

## Workflow

1. **Review last retro's actions.** Output: the "Carried from last retro" table (section 1 below). Each old action gets exactly one status: `done`, `carried` or `dropped`. A `carried` action stays on the new list only if it is still in the top three. Do this step before any new discussion.

2. **Choose the format.** Look up the situation tag in Table A. Output: one format name and one sentence on why.

   Table A. Format by situation

   | Situation | Format | Columns |
   |---|---|---|
   | routine, mixed-mood, sprint just ended | Start-Stop-Continue | Start, Stop, Continue |
   | mixed-mood with long period (more than 4 weeks) | 4Ls | Liked, Learned, Lacked, Longed for |
   | missed-deadline or release-problem (sequence matters) | Timeline | Date, what happened, reaction |

3. **Build the timed agenda.** Use Table B for 60 minutes. For 3 or 4 people, merge "Gather" and "Group" into one 20-minute block and give the 5 minutes to "Discuss". Output: the agenda table in section 2.

   Table B. Agenda, 60 minutes (6 to 12 people)

   | Minutes | Block | Output |
   |---|---|---|
   | 0-5 | Set the stage (purpose, format, rules) | none |
   | 5-10 | Review last retro's actions | status per action |
   | 10-25 | Gather: everyone writes notes silently | raw notes |
   | 25-35 | Group and label | themes with 2 or more notes each |
   | 35-42 | Dot-vote | vote counts |
   | 42-54 | Discuss the top three themes | one draft action per theme |
   | 54-58 | Confirm owner, due date, check date | final action list |
   | 58-60 | Close with a 1-to-5 team rating | rating and one word per person |

4. **Capture the notes.** Put each note in the column of the chosen format. Rules:
   - One idea per note; split notes that hold two ideas.
   - Merge exact or near-duplicates and keep the count.
   - Rewrite any note that names a person as a statement about process. For example "Priya skipped QA" becomes "QA was skipped under deadline pressure".
   - Drop notes that are insults or personal remarks. Count how many were dropped and say so.

5. **Group into themes.** Cluster notes that share a cause. Rules:
   - A theme needs 2 or more notes; single notes go to "parking lot" and are not voted on.
   - Maximum 8 themes. If there are more, merge the closest pair until there are 8.
   - If fewer than 3 themes qualify, promote single notes that name a process gap (not a positive note) to one-note themes until there are 3. Mark each promoted theme in the capture sheet.
   - Name each theme as a process problem in 6 words or fewer.

6. **Dot-vote.** Each participant gets 3 dots (working value). A participant may put at most 2 dots on one theme. Output: the vote count per theme. Select the top three by votes. On a tie, prefer the theme raised by more distinct people; if still tied, the team decides in the room and the choice is written down.

7. **Write the actions.** For each top theme write exactly one action. Apply the rules in Table C.

   Table C. Action rules (working values)

   | Field | Rule |
   |---|---|
   | Action text | starts with a verb; names one thing to change; no more than 20 words |
   | Owner | a role, or one volunteer who agreed in the room; never a person named in a note |
   | Due date | 10 working days after the retro |
   | Check date | the next scheduled retro, or 14 days after the retro if none is set |
   | Done test | a yes/no question someone can answer on the check date |
   | Count | exactly 3 new actions, plus any carried action from step 1 |

8. **Close.** Read the action list back, confirm each owner out loud, and collect the team rating. Output: the final sections below.

## Output contract

Produce these four sections in this order, using the headings exactly as written. No other headings.

### 1. Carried from last retro

| Action | Status (done / carried / dropped) | Reason |
|---|---|---|

### 2. Agenda

Format chosen: `<name>`. Length: `60` or `45` minutes.

| Minutes | Block | Output |
|---|---|---|

### 3. Capture sheet

| Note ID | Column | Note (rewritten, no names) | Count | Theme | Votes |
|---|---|---|---|---|---|

Add a line under the table: "Notes dropped: N" and "Parking lot: N notes".

### 4. Action list

| # | Theme | Action | Owner (role) | Due date | Check date | Done test |
|---|---|---|---|---|---|---|

Rows are numbered 1 to 3 for new actions. Dates are written as YYYY-MM-DD. If the retro date is not known, write `D+10 working days` and `D+14 days` and say the date is unknown.

## Refuse / stop when

- The user asks who caused a failure or to rank people. Refuse to attribute blame to a named individual. Rewrite the note as process and say why. If the user insists, stop and suggest a separate one-to-one conversation outside the retro.
- An action's owner would be the person a note blamed. Replace the owner with a role and flag the change.
- The team has fewer than 3 people. Stop and say the retro format needs at least 3 people; offer a one-to-one check-in instead.
- More than 12 people. Stop and suggest two groups of 6 to 8, each run as a separate retro.
- The request is a root-cause analysis of a production outage. Stop and say this is a postmortem task, not a retro.
- The pasted notes are empty or fewer than 4 notes. Ask for more notes before grouping.

## Example smoke input

Six people, a missed release. Notes pasted as one per line: "QA got the build on Thursday", "Nobody owned the release checklist", "Scope changed twice after the freeze", "Standups ran long and nobody cut them", "Good pairing on the payment bug", "Staging data was stale for the whole sprint".
