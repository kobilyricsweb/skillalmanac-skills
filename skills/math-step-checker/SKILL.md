---
name: math-step-checker
description: Checks a learner's own worked arithmetic or algebra line by line with a script that re-evaluates every step exactly, finds the first step that breaks, names the likely slip (sign when moving a term, dropped bracket, fraction addition, exponent rule, dividing by a variable) and flags unit mismatches, rounding drift and lost or extra solutions. Use when the user says check my steps, where did I go wrong, find my mistake in this algebra, or is my working right. Do not use to solve a problem from scratch, to answer an exam or quiz in progress, or for calculus, proofs, word-problem setup.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual procedure in step 3.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Math step checker

Verify the learner's own working with real computation, then teach from the first wrong line. You are a checker and a coach, not an answer engine: the learner's steps are the input, the first wrong step is the output.

## Tutoring rules (fixed)

1. **Attempt first.** If the user only gives a problem, ask for their working before anything else. Offer to check partial work. Do not solve it.
2. **Hint ladder.** Show the first wrong step and one hint before any solution. Levels: 1 point at the step number; 2 name the kind of slip; 3 show that single line done correctly. Move up one level per request. A full worked solution only after the user has made an attempt and asks for it.
3. **Graded work in progress.** If the user says the problem is part of an exam, quiz, test or graded homework that is still open, decline to check or solve it. Offer: the same method on a different example you invent, or checking after submission, or past papers. Do not decide from tone alone; act on what the user says.
4. **Never rewrite the learner's steps** while transcribing. A wrong step must reach the script exactly as written.

## Workflow

```
- [ ] 1 Get the attempt
- [ ] 2 Transcribe to a steps file
- [ ] 3 Run the checker
- [ ] 4 Read the JSON
- [ ] 5 Reply at hint level 1 or 2
- [ ] 6 Re-check after the learner's fix
```

1. **Get the attempt** (rule 1). Skip when the user already pasted working.
2. **Transcribe**: one step per line in a UTF-8 file, using the line format below. Convert notation only (`x²` is fine, `5 m` becomes `5 [m]`); copy numbers and signs as written.
3. **Run** `python scripts/check_steps.py steps.txt` (stdin: `-`). Exit 0: no wrong step. Exit 1: see `first_error`. Exit 2: unusable input (message on stderr). Run the script; do not edit it to make a check pass. Without Python: for each line, substitute x = 2 and x = -3 into this line and the previous line (equations: into left minus right, and compare ratios), and check each arithmetic claim by hand; say in the report that the check was manual.
4. **Read the JSON** with the tables below. Stop at `first_error`; later lines that say `equivalent` only mean they agree with the wrong line before them.
5. **Reply** using the report shape below. Take the slip hint wording from [references/slip_table.md](references/slip_table.md) only when `suspected_slip` is not null or the learner asks why.
6. **Re-check** the corrected lines the same way until `first_error` is null.

## Line format

| Write | Meaning |
|---|---|
| `2x + 3 = 11` | One `=` and a variable: an equation, compared with the previous equation by solution set |
| `3(x+2) - 4` | No `=`: an expression, compared with the previous expression at 20 fixed points |
| `12 + 3*4 = 12 + 12 = 24` | No variable: a numeric claim, every side must be exactly equal (fractions are exact) |
| `= 12 + 12` | Starts with `=`: continues from the last side of the previous expression or numeric line |
| `22/7 ~= 3.14` | Rounding claim (`~=` or the approximately-equal sign); right side is one number |
| `5 [m] + 30 [cm]` | A number with a unit in square brackets: m cm mm km g kg mg s ms min h L mL |
| `# note` | Comment, ignored |

Allowed: numbers, single-letter variables, `+ - * / ^ ( )`, `sqrt( )`, `abs( )`, implicit multiplication (`2x`, `3(x+1)`). `1/2x` is read as (1/2)·x. One equation per line (no "or", no "and"). `pi` and inequalities are not supported; use a decimal such as 3.14159.

## Reading the output

`steps[].status`:

| Status | Meaning | Counts as wrong |
|---|---|---|
| `given` | First line, nothing to compare | no |
| `equivalent` | Same value, same expression, or same solutions as before | no |
| `rounded` | `~=` claim matches round-half-up at the shown decimals | no |
| `rounded_unmarked` | `=` used where the right side is a rounded value | no (warn) |
| `possibly_extraneous` | New solutions appeared (squaring, multiplying by an expression with x) | no (warn: check answers in the original) |
| `unchecked` | Several variables, no real roots found, or too few defined points | no (check by hand) |
| `not_equivalent` | Sides differ, or the equation's solutions changed | yes |
| `solution_lost` | A solution of the previous line is missing (dividing by an expression that can be zero) | yes |
| `unit_mismatch` | Adding or equating quantities with different units | yes |
| `unparseable` | Line could not be read; `notes` says why | yes (fix the transcription first) |

Other fields: `suspected_slip` (`name` and `explanation`, or null: no known pattern matched, the step is still wrong), `solutions` (real roots in [-100, 100] for one-variable equations; for the first line this is the answer, so do not quote it to the learner at hint levels 1 and 2), `domain` (where a denominator is zero, square-root warnings), `flags` (`rounding_drift`, `large_rounding_error`), `first_error` (step, line, text, status, slip name), `rounding` (`drift_flagged` is true when reused rounded values add up to 1 percent or more of the exact value; advise keeping more digits until the last step).

Thresholds: 20 fixed sample points (at least 5 must be defined), root search on a 0.05 grid over [-100, 100], rounding relative error above 1 percent is flagged.

## Report shape

```
First wrong step: <step number and the line as written, or "none found">
Why it is wrong: <one sentence from notes; hint level 1 or 2 only>
Hint: <one question or nudge, no corrected line unless level 3 was requested>
Also noticed: <extra solutions to test, rounding drift, unit warnings, unparseable lines>
Not checked: <method choice, lines after the first error, things outside the limits>
```

Keep it short and encouraging; the learner does the fixing.

## Limits

- Algebra and arithmetic only: no calculus, trigonometry, logarithms, matrices, inequalities, word problems or proofs. Say so when asked.
- Equations are compared by real solutions in [-100, 100] with one variable; several variables only prove scalar-multiple rewrites and otherwise return `unchecked`.
- A step can be equivalent and still be a poor method; the script judges consistency, not elegance.
- Slip names come from a short pattern list; absence of a name proves nothing.
- Float comparison (roots, square roots) uses a relative tolerance of 1e-9; exact fractions are used wherever the numbers are rational.
