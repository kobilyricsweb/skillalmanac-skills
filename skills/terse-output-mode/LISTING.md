## תקציר

- זהו תוכן עמוד ה-skill באתר: מה הוא עושה, מתי להשתמש, דוגמאות, מגבלות, תסריט הדגמה ושאלות נפוצות.
- ה-skill מעביר את התשובות למצב מקוצר ("caveman") בשלוש רמות, בלי לגעת בקוד, בפקודות, במספרים, בטקסט שגיאה ובאזהרות בטיחות.
- כלל הליבה: אזהרה על פעולה בלתי הפיכה נכתבת כמשפט מלא אחד לפני הצעד; תפריטי חלופות נחתכים.
- נמדד: 45, 67 ו-155 מילים מחוץ לקוד עם ה-skill מול 121, 115 ו-236 בלי. מדרג עיוור העדיף את ה-skill בשלוש מתוך שלוש (9/9/8 מול 6/6/6).
- הדוגמאות והמספרים לקוחים מריצות שמורות; טיוטה, לא לפרסום לפני סקירה אנושית והשלמת הבדיקות.

---

# Listing page content: terse-output-mode

**One line:** Short replies that keep every command, number, error message and safety warning intact.

## What it does

The skill defines three compression levels with word budgets per reply type, a list of what is cut (greetings, restating, closing offers, stacked hedges, background, menus of alternatives) and a list of what is never altered (code, commands, numbers, exact error text, step order, negations and conditions). Hazards get one complete sentence placed before the step. It leaves files, code and commit messages at normal standards and steps out of the mode for one reply when the user is confused or must give informed consent.

## Capabilities

- Levels lite, full and ultra with length targets, and commands to switch or stop
- Reply shapes for how-to, diagnosis and procedure
- `scripts/terse_check.py`: words outside code against a budget, filler phrases, clipped warnings, and with `--compare` the code lines, inline code, numbers and URLs that the short version lost
- Worked examples at each level

## When to use

You say caveman mode, be terse, less words, stop the fluff, token saving mode, or complain that replies are too long.

## When not to use

Summarising or shortening a document you supply, minifying code, or a character voice for fun.

## Requirements

None for the mode itself. Python 3.9+ for the optional check script. No network.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples (from saved runs)

1. Prompt: "caveman mode. how do I undo my last commit? already pushed to main, teammates pulled it." Result: `evals/runs/t1-undo-pushed-commit/with_skill/reply.md`: one line, the two commands in a block, and one full warning sentence against reset plus force-push. 45 words outside code; the run without the skill used 121 and added four variants.
2. Prompt: "terse mode. orders-api/ keeps dying under load, the log is in logs/error.log. why, and what's the fix?" Result: `evals/runs/t2-diagnose-log/with_skill/reply.md`: cause with file and line, the exact error text quoted, the fix as code. 67 words; the run without the skill used 115 and did not quote the exact error.

## Limits

- Savings are in the reply text only; reading files and running tools cost the same. In the tests the skill added about 6,000 input tokens per run to load.
- Fragments are harder for non-native readers; lite is the fallback.
- The script counts English words and surface forms; it cannot judge meaning.
- Budgets and percentages are the author's working targets, not measured optima.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model, Claude Code only, 2026-11-20. Assertions passed: 17/18 with the skill against 8/18 without. A blind grader preferred the with-skill result in 3 of 3 tasks. Average token overhead 6,078 per run (+8%). Blinding was imperfect and each cell ran once. Not tested: other tools, real triggering, human review.

## Demo script (60 to 90 seconds)

1. Same question twice: 'how do I undo my last commit, already pushed'. Without the skill: 121 words, five variants.
2. With the skill: six lines, the commands, one warning sentence.
3. Run `terse_check.py --compare`: reduction shown, nothing technical missing.
4. Type 'normal mode': the next reply is full length.

## FAQ seeds

- Does it drop safety warnings to save words? No. A hazard gets one full sentence before the step; that rule was checked in the blind grading.
- How much does it save? In three test replies, 34 to 63 percent fewer words outside code than the same model without the skill. Loading the skill costs input tokens.
- Does it shorten my code or commit messages? No. Only what is said to you.
- How do I turn it off? Say 'normal mode'.
- Is it the same as other caveman skills? Same goal. This one defines what may never be cut and ships a checker. No comparison run against another skill has been done.
- Does it need network or scripts? No network. The script is optional.

## Changelog

- 0.1.0 (2026-11-20): first version; all evals ran on this version.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
