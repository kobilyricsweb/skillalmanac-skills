---
name: plan-stress-test
description: Stress-tests a written plan (project, launch, migration, rollout) before execution. Use when the user says stress test this plan, poke holes, red team my plan, pre-mortem, what could go wrong, or is this plan solid. A script parses the Markdown for steps with no owner, date or done criterion and dependencies never defined; a fixed procedure covers hidden assumptions, single points of failure and missing rollback and ends in a ranked risk register as validated JSON. Do not use for writing a plan from scratch, estimating effort, reviewing code or contracts, or security threat modelling.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, do the manual structural pass in step 2.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
  license: Apache-2.0
  author_model: claude-sonnet-5-5
---

# Plan stress test

Read a plan as an opponent would: find what makes it fail, rank it, and say where in the plan the evidence is. You criticise the plan; you do not rewrite it, and you do not invent facts about the project. Every risk must quote the plan or say precisely what the plan lacks.

## Workflow

Copy this checklist and tick it off:

```
- [ ] 1 Get the plan into one Markdown file
- [ ] 2 Run the structural scan
- [ ] 3 Read the plan in full; write goal, scope, assumptions
- [ ] 4 Run the six attack passes in order
- [ ] 5 Pre-mortem
- [ ] 6 Score and rank
- [ ] 7 Write the register JSON and validate it
- [ ] 8 Report
```

1. **One file.** If the plan lives in chat, a document or a ticket, save it as `plan.md` first (headings, checklist items or numbered steps, a table with Step/Owner/Due columns all parse). Do not tidy or reword it: the scan and the evidence quotes must match the author's text. Prose-only plans are fine; the scan will say `unstructured` and the passes below carry the work.
2. **Scan.** Run `python scripts/plan_scan.py scan plan.md` (add `--today YYYY-MM-DD` to flag open steps whose date has passed). Read [references/scan_output.md](references/scan_output.md) once to learn what each finding kind means and where it misfires; treat every finding as a question to check against the text, not a verdict. Without Python, check each open step by eye for: owner, date, done criterion, named dependencies that no step defines; then look for any rollback wording and any success criteria.
3. **Read, then state.** Write down in three lines: the goal as the plan states it, what is in and out of scope, and the plan's own assumptions. If the goal has no measurable end state, that is already a risk (category `done_criteria`).
4. **Attack passes**, always in this order, one at a time. For each pass, open the matching section of [references/attack_questions.md](references/attack_questions.md) and use only that section:
   1. Goal and done criteria: can anyone tell on the last day whether it worked?
   2. Hidden assumptions: what must be true that the plan never says? For each, ask which steps fail if it is false.
   3. Dependencies and sequence: undefined dependencies, wrong order, circular waits, external parties with no date.
   4. Ownership and single points of failure: people, accounts, vendors, approvals, one-person knowledge.
   5. Schedule realism: parallel work on one person, no slack, handoffs and approvals with no lead time, dates that bunch before a deadline.
   6. Failure and reversal: how it is detected that a step failed, what the point of no return is, and the way back.
5. **Pre-mortem.** Assume it is the day after the deadline and the plan failed. Write the three most likely causes in one line each. Any cause not already in your list from step 4 is added; any cause the plan already handles is dropped.
6. **Score and rank.** Merge findings with the same root cause into one risk. Give each risk likelihood and impact from 1 to 5 using the anchors below, score = likelihood x impact. Sort by score, highest first; break ties by harder to detect early, then by harder to undo. Keep at most 12 risks; fewer is better.
7. **Register.** Write the register as JSON in the contract below, then run `python scripts/plan_scan.py register plan.md register.json`. Fix every error and re-run until `"ok": true`. Read the `warnings`: a high-severity scan finding that no risk cites is either folded into another risk (cite its line there) or a false positive (say so in the report).
8. **Report** in the fixed shape below.

## Scoring anchors

| Score | Likelihood | Impact |
|---|---|---|
| 1 | Needs two unrelated things to go wrong | Absorbed by slack; nobody outside the team notices |
| 2 | Happens to some similar plans | One step slips under a week, or rework |
| 3 | Plausible; the plan does nothing about it | A milestone slips or quality visibly drops |
| 4 | Likely; the plan already shows a sign of it | The goal date or goal metric is missed materially |
| 5 | Will happen unless the plan changes (a contradiction inside the plan) | Goal fails, or loss that cannot be undone, or customer-visible outage |

## Register contract

One JSON object, nothing else in the file:

```json
{
  "plan": "short name of the plan",
  "risks": [
    {
      "rank": 1,
      "id": "R1",
      "title": "five to ten words",
      "category": "assumption | dependency | single_point_of_failure | ownership | done_criteria | schedule | scope | external | rollback | resource",
      "evidence": {"quote": "verbatim text from the plan", "line": 13},
      "scenario": "one or two sentences: how it fails and what that costs",
      "likelihood": 4,
      "impact": 5,
      "score": 20,
      "detection": "the earliest observable sign that it is happening",
      "mitigation": "the smallest change to the plan that removes or contains it",
      "source": "script | judgement"
    }
  ],
  "not_checked": ["what you could not verify from the plan text"]
}
```

- `evidence` has exactly one of `quote` (verbatim; whitespace and Markdown emphasis are ignored when matched) or `absent` (one sentence naming what the plan lacks, for example a rollback). `line` is optional and 1-based.
- `rank` runs 1..n in order, `score` equals likelihood x impact and never rises down the list, ids are unique, 3 to 12 risks, `not_checked` is never empty.
- `source` is `script` when a scan finding led to it, `judgement` otherwise. A copyable skeleton is in [assets/risk_register_template.json](assets/risk_register_template.json); replace every placeholder before validating.

## Report

Give this, in this order, after the register validates:

```
Verdict: <ready | ready after fixes | not ready>: one sentence why
Top risks: up to 5 lines: rank. title (L x I = score), evidence line N, smallest fix
Hidden assumptions: up to 6 lines: "must be true: ...; if false: ..."
Questions for the plan author: up to 5, each one answerable in a sentence
Register: <path>, validator ok
Not checked: <what you did not or could not verify>
```

Verdict rule: any risk scoring 20 or more is `not ready`; otherwise any risk scoring 12 or more is `ready after fixes`; otherwise `ready`. State the rule's outcome even if you disagree, and add your reason on a separate line.

## Scripts

- `scripts/plan_scan.py scan <plan.md> [--today YYYY-MM-DD]`: run it. Prints one JSON object: summary counts, `verdict` (sound, gaps, weak or unstructured), plan-level checks, owner load, every step with its owner, date, verification and dependencies, and findings sorted by severity. Exit 1 when any finding is high severity, 0 otherwise.
- `scripts/plan_scan.py register <plan.md> <register.json>`: run it. Validates the register against the contract and checks that every quote occurs in the plan. Exit 1 on any error.

Both print `{"error": ...}` and exit 2 for a missing, empty or unreadable file. Do not edit the script to make a check pass.

The ideas behind the passes (pre-mortem, planning fallacy, critical path) are cited in [references/sources.md](references/sources.md); read it only when the user asks where a method comes from.

## Boundaries

- This is a review of a plan's text. It does not know the people, the budget or the market; say so in `not_checked` rather than guessing.
- Do not invent owners, dates or numbers when suggesting fixes; propose that the author supply them.
- Do not use the register to blame a named person. Risks are about the plan's structure.
- Medical, legal, financial or safety-critical plans get the same review, and the report states that it is not professional sign-off.

## Limits

- The scan is lexical. It finds owners written as `@name` or `owner: name`, dates in ISO, month-name, quarter and weekday forms, and done criteria introduced by words such as verify, done when, accept, pass, confirm or a number with a threshold. A person named in other words reads as unowned; a test named in a step title is not credited as a done criterion.
- Dependency matching compares words, not meaning: a named dependency is "defined" when a step, heading or dependency-list item shares most of its words. It can resolve a dependency to the wrong step or miss a rephrased one.
- Dates are compared only when the year is written. Time zones, holidays and working days are not modelled.
- Thresholds (40% of open steps for owner concentration, 20% and 50% gap rates for the verdict) are working values, not measured optima.
- Plans in languages other than English are only partly parsed.
- The ranking rests on your likelihood and impact estimates, which no script checks.
