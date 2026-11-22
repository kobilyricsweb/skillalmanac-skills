## תקציר

- זהו תוכן עמוד ה-skill באתר: מה הוא עושה, מתי להשתמש, דוגמאות, מגבלות, תסריט הדגמה ושאלות נפוצות.
- ה-skill מבצע code review על diff או PR ומחזיר פסק דין קצר ומדורג שבו לכל ממצא יש מיקום, תרחיש כשל מוחשי ואימות.
- העיקרון: רוב הפגמים החמורים נמצאים מחוץ ל-diff (קוראים שלא עודכנו, בדיקות שהוחלשו, טבלה שכבר מכילה שורות), ולכן חובה לצאת מה-diff ולהריץ.
- חשוב: גם בלי ה-skill המודל מצא את כל הפגמים השתולים בשלוש המשימות. היתרון שנמדד הוא בצורה: שורות מדויקות, תרחיש כשל לכל ממצא, פחות הערות שוליות (9 מול 8 בכל משימה).
- הדוגמאות והמספרים לקוחים מריצות שמורות; טיוטה, לא לפרסום לפני סקירה אנושית והשלמת הבדיקות.

---

# Listing page content: reviewing-code-changes

**One line:** Code review that leaves the diff, proves its findings, and fits in two minutes of reading.

## What it does

The skill has the agent write down the claims in the change description, map the diff by risk with a script, search the whole repo for every use of each changed definition, compare new code paths with their siblings, treat tests as evidence (weakened assertions, deleted tests, tests that cannot fail), and make each blocking finding concrete with a failing input, running it where possible. The review has a fixed shape: verdict first, then Blocking, Should fix, at most three Notes, Questions, and what was and was not checked.

## Capabilities

- `scripts/diff_risk_map.py`: reading order by risk, changed and removed definitions to search for, numeric constants whose old value disappeared, and signal lines (removed or weakened tests, swallowed errors, broad catches, string-built SQL, risky schema statements, skipped tests, debug leftovers)
- A defect-pattern reference by change type: interfaces, handlers, queries, migrations, refactors, retries, concurrency, money and time, config, tests
- A fixed review format with a 'Fails when' line and a verification note per finding

## When to use

You ask for a code review, a PR review, a second pair of eyes, whether a change is safe to merge, or a check of what an agent just wrote.

## When not to use

Writing the change or its tests, explaining code, reviewing prose, contracts or designs with no diff.

## Requirements

Python 3.9+ for the script. No network. Best with the repo checked out.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples (from saved runs)

1. Prompt: "Review the change in pricing-svc/ before I merge it." Result: `evals/runs/r1-changed-contract/with_skill/reply.md`: 'Do not merge'; `billing/invoice.py:6-7` (not in the diff) still treats the result as a percentage, verified by running `invoice_total(20000, "gold")` which returns `19970.0` instead of `17000`; the weakened and the deleted test; and a cart rounding change that was not one of the planted defects. The run without the skill found the planted defects too, in a longer review.
2. Prompt: "Review the change in notifier/ before I merge it." Result: `evals/runs/r3-quiet-refactor/with_skill/reply.md`: three blocking findings (timeout cut from 30 to 3 seconds against a stated 8 second p99, retry widened to every exception, NOT NULL column without default on a 40 million row table) and three should-fix items, six in total.

## Limits

- Without the repo, callers and tests cannot be checked.
- The script reads diff text, not parsed code; it does not find callers.
- On the three test changes the same model without the skill found every planted defect; the measured benefit is a tighter, better-evidenced review, not more defects found.
- Not tested on large diffs, where leaving the diff matters most.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model, Claude Code only, 2026-11-20. Assertions passed: 21/21 with the skill against 18/21 without. A blind grader preferred the with-skill result in 3 of 3 tasks. Average token overhead 7,842 per run (+10%). Blinding was imperfect and each cell ran once. Not tested: other tools, real triggering, human review.

## Demo script (60 to 90 seconds)

1. A PR titled 'pure refactor, no behaviour change'. Run the diff map: a constant whose old value 30 disappeared, a NOT NULL column, a broad except.
2. The agent searches for callers and runs a one-liner: the wrong invoice total appears.
3. The review scrolls: verdict, three blocking items each with 'Fails when', a 'Checked / Not checked' footer.
4. Side by side with the review from the same model without the skill: same defects, twice the length.

## FAQ seeds

- Does it find more bugs than the model alone? Not in our tests: both found every planted defect in three small changes. The skill's reviews were shorter, cited lines and showed failing inputs.
- Does it post to my pull request? No. It writes the review; posting is up to you.
- Does it run my tests? It tells the agent to, where the repo allows, and to say what ran.
- Will it nitpick style? Notes are capped at three and style a linter enforces is excluded.
- Does it need network? No.
- Languages? The method is general. The script's signal patterns cover common Python, JavaScript/TypeScript, Go, Java and SQL forms.

## Changelog

- 0.1.0 (2026-11-20): first version; all evals ran on this version.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
