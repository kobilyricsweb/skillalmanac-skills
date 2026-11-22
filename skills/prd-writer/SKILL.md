---
name: prd-writer
description: Writes a product requirements document (PRD) from messy inputs (chat threads, meeting notes, tickets), keeping facts, decisions, wishes and unknowns apart. Conflicts become open questions, every requirement gets an ID, priority and acceptance check, and no metric or date is invented; a bundled script checks structure and number sources. Use when the user asks for a PRD, product spec, requirements doc, feature brief or one-pager from their notes, or wants a PRD reviewed for gaps. Do not use for technical design docs, sprint tickets, roadmaps or market research.
license: Apache-2.0
compatibility: The check script needs Python 3.9 or newer (standard library only). No network access is used. Without Python, walk the checklist in the Verify step by hand.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# PRD writer

Write the document that lets engineering, design and the business agree on what is being built and how they will know it worked. A PRD fails in two ways: it sounds complete while hiding the decisions nobody has made, or it states targets and dates that came from the writer instead of the team.

## Ground rules

1. **Four kinds of statement, never mixed.** Fact (measured, with where it came from), decision (made, by whom), wish (someone wants it), unknown. A wish from a senior person is still a wish until it is written as a decision.
2. **No invented numbers.** Every figure, date and target comes from the notes. A target the notes do not contain may be suggested on a line marked `[proposed]`. An assumed figure is marked `[assumption]`. A missing baseline is written `[needs data]`.
3. **Conflicts are surfaced, not settled.** When the notes disagree (two retention periods, two dates, two channels), write both positions under Open questions with who should decide. Do not pick one in the requirements.
4. **Every requirement is testable.** A tester can read the acceptance check and say pass or fail. Words like "fast" or "easy" are replaced by a number from the notes or by a named behaviour, or the requirement goes to Open questions.
5. **Say what is out.** Non-goals name the things a reader would assume are included.
6. **What, not how.** Requirements describe behaviour the user or the business can observe. Leave architecture, schemas and library choices to the design doc, except constraints the notes state.

## Workflow

### 1. Collect and sort

Put all source material into `notes.md` unchanged. Build a sorting table before drafting:

```
statement | kind: fact / decision / wish / constraint / unknown | who said it | conflicts with
```

Mark every pair of statements that cannot both be true.

### 2. Ask, if someone can answer

If the user is available, ask at most five questions, most blocking first: the problem's evidence, who the user is, the success measure, the conflicts found, the hard constraints. If not, proceed and carry each unanswered item into Open questions.

### 3. Draft

Follow [references/prd-template.md](references/prd-template.md); read it before the first PRD in a session. Required sections: Decisions needed, Problem, Users, Success metrics, Non-goals, Requirements, Risks and assumptions, Open questions.

Requirement format, one per line:

```
- **R1 (Must)** <observable behaviour> (Source: <person or team in the notes>; <legal / contractual / mandatory, if stated>). Accept: <what a tester does and what they see>.
```

Every requirement names who in the notes asked for it. When the notes say something is required by law, contract or policy, or "not optional", say so in the Source and make it Must; it is a constraint, not a preference. Write no requirement that has no source line in the notes; put such ideas under Open questions.

Priorities are Must, Should, Could. A release that ships every Must and nothing else has to solve the stated problem; if it would not, the priorities are wrong.

Save as `prd.md`.

### 4. Verify

```bash
python scripts/prd_check.py prd.md --notes notes.md
```

- `FAIL section missing`: add it; write "None known" with a reason if it is truly empty.
- `FAIL ... no priority` / `no acceptance check`: complete the requirement line.
- `FAIL ... number(s) not in the notes`: take the figure from the notes, or mark the line `[proposed]` or `[assumption]`, or remove it.
- `FAIL success metric without a number`: give the baseline from the notes and a marked target, or `[needs data]`.
- `WARN untestable word`: rewrite, or move the item to Open questions.
- Re-run until PASS. Do not edit the script or the notes to make the check pass.

Then check by reading: every requirement has a Source and every legal or mandatory item from the notes is attributed to its owner; every conflict from step 1 appears under Open questions and is not decided elsewhere in the document; every person, team and date named in the PRD is in the notes; the Must requirements alone solve the problem.

If the script cannot run, do the same checks by hand and list every number in the PRD beside its line in the notes.

### 5. Deliver

Give the PRD, then:

```
Decisions needed before build: <the blocking open questions, with who should decide>
Marked as proposed or assumed: <count, and the lines>
Left out on purpose: <non-goals a stakeholder may push back on>
Check: <PASS, or "manual">
```

For a review-only request, run the script on the existing PRD and report findings with line references; do not rewrite unless asked.

## Limits

- The script checks form and whether numbers trace to the notes. It cannot judge whether the problem is real or the scope is right.
- A PRD written from thin notes will be mostly open questions. That is the correct output; do not pad it.
- Estimates of effort, cost or delivery date are not produced. Dates appear only when the notes give them.
- English section names are expected by the script.
