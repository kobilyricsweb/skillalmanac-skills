## תקציר

- תוכן עמוד ה-skill: כותב מסמך דרישות מוצר (PRD) מהערות מבולגנות.
- מפריד בין עובדה, החלטה, רצון ולא-ידוע; סתירות הופכות לשאלות פתוחות ולא מוכרעות בשקט.
- כל דרישה מקבלת מזהה, עדיפות ובדיקת קבלה. אין מספרים או תאריכים מומצאים.
- כולל script שבודק מבנה ושכל מספר מקורו בהערות. בלי רשת.
- טיוטה: לא לפרסום לפני סקירה אנושית.

---

# Listing page content: prd-writer

**One line:** Turn a pile of chat threads and meeting notes into a requirements document that shows what is decided, what is not, and how each requirement will be tested.

## What it does

You paste the raw material. The skill first sorts every statement into fact, decision, wish or unknown, and marks statements that contradict each other. Contradictions go to the top of the document as decisions someone must make; they are not settled by the writer. Each requirement gets an ID, a priority and a check a tester can run. Targets the notes do not contain are either left as "needs data" or clearly marked as a proposal. A script checks the structure and that every number in the document comes from the notes or is marked.

## Capabilities

- A PRD with fixed sections, starting with "Decisions needed".
- Requirements written as `R1 (Must) ... Accept: ...`.
- Non-goals that record every exclusion the notes state.
- `prd_check.py`: section check, requirement format, untestable words, and number tracing against the notes.
- A review-only mode for an existing PRD (not tested).

## When to use

You have a Slack dump, call notes or a list of customer requests and need a PRD, spec or feature brief; engineering asks "what exactly are we building"; you want a PRD checked for gaps.

## When not to use

Technical design docs, ticket breakdowns, roadmaps, market research, effort estimates.

## Before and after (from saved test runs)

**Without the skill.** From notes on a bulk invoice export, the plain assistant wrote requirements as unnumbered bullets with no acceptance checks and no requirement on who may export.

**With the skill.** With the skill each requirement has an ID, a priority and an acceptance check; link expiry (24 hours or 7 days) and who may export are listed as decisions needed; the sales promise of "Q1" is recorded as an unverified commitment, not a date.

## Requirements

Python 3.9 or newer for the script (standard library only). No network access. English wording is assumed by the script.

## Install

To be generated at publication: one pinned command per tool.

## Examples (from saved test runs)

1. Prompt: "Write a PRD for this. Eng wants it by Thursday." Result: `evals/runs/p2-bulk-export/with_skill/prd.md`. 7 of 7 assertions; blind score 8 against 6.
2. Prompt: "Can you make a product requirements doc from this dump?" Result: `evals/runs/p3-reminders/with_skill/prd.md`. 7 of 7; both versions passed, the with-skill one was judged clearly more usable.

## Limits

- It added one requirement of its own in two of three tests (labelled, but given a real priority).
- It names a decider for open questions even when the notes do not.
- The script checks form and number sources, not whether the scope is right.
- Thin notes produce a document that is mostly open questions; that is intended.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model, Claude Code only, 2026-11-20. Blind grader: with skill preferred in 3 of 3. Static check: 0 fails. Token overhead about +13%. Not tested: other tools, real triggering, repeated runs, human review.

## Demo script (60 to 90 seconds)

1. Show the notes: "keep saved carts for 30 days" and, six lines later, "90 days is what the loyalty team asked for".
2. Plain assistant's PRD: a requirements table with no priorities or tests.
3. With the skill: the "Decisions needed" block, then one requirement with its Accept line, then `prd_check.py --notes`: RESULT PASS.
4. End on the delivery note: decisions needed before build.

## FAQ seeds

- Will it invent success metrics? Targets not in your notes are marked [proposed] or [needs data]. One unmarked target slipped through in testing.
- Does it pick between conflicting opinions in my notes? No. Both positions are listed for a named person to decide.
- Does it estimate effort or dates? No.
- Does it need internet access? No.
- Can it review a PRD I already wrote? Yes, with the script. Not tested in this round.
- Which template does it use? Its own: decisions needed, problem, users, success metrics, non-goals, requirements, risks and assumptions, open questions.

## Changelog

- 0.1.0 (2026-11-20): first version, batch 01.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
