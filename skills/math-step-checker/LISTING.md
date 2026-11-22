# Math step checker (listing)

## One-line summary

Re-computes each line of a learner's own algebra or arithmetic, finds the first wrong step and coaches from it without giving the answer away.

## What it does

The learner (or a tutor) supplies their working, one step per line. A standard-library Python script parses every line with `ast` and a whitelist evaluator (no `eval`), compares each line with the one before it, and prints strict JSON. Equations are compared by solution set, expressions at 20 fixed sample points, and numeric claims with exact fractions. The agent then follows a fixed tutoring procedure: show the first wrong step and a hint, never the full solution first, and decline to help with graded work the user says is in progress.

## Capabilities

- Finds the first step that does not follow from the previous one.
- Names the likely slip from a pattern list: sign when moving a term, distributing a negative, dropped bracket, fraction addition without a common denominator, exponent-rule misuse, operation on one side only, dividing by an expression that can be zero, decimal-place and unit-conversion slips.
- Flags steps that add solutions (squaring, multiplying by an expression with x) or lose them (dividing by x), and reports where denominators are zero.
- Checks units written as `5 [m]` (dimension mismatch, unit-conversion factors) and rounding (half-up check, unmarked rounding, drift when rounded values are reused).
- Strict JSON output with `first_error`, per-step `status` and `suspected_slip`.

## When to use / when not to

Use for: "check my steps", "where did I go wrong", a tutor verifying a student's lines, a parent checking homework working after the child has tried.

Do not use for: solving a problem from scratch, answering an exam or quiz that is in progress, calculus, trigonometry, proofs, word-problem setup, spreadsheet formulas.

Differs from neighbouring skills: study-and-teaching-kit and classroom-quiz-builder design learning material and quizzes; the misconception-diagnostic-set designs tests. This skill verifies one learner's own lines with real computation and teaches from the first error.

## Requirements

Python 3.9 or newer, standard library only. No network. No packages to install.

## Install

Copy the `math-step-checker` folder to `.claude/skills/` or `.agents/skills/` (project or home directory). Not yet verified in any tool; see Evidence.

## Examples

Prompt: "I'm practising for next week. This is my working for 4(x - 3) = 2x + 6 and I got x = 4.5 but the textbook says something else. Where did I go wrong?" (file `evals/files/t1-distribute-slip/steps.txt`).

Real script output (shortened; run on 2026-11-21):

```json
{
  "step_count": 4,
  "steps": [
    {"step": 1, "text": "4(x - 3) = 2x + 6", "status": "given", "suspected_slip": null},
    {"step": 2, "text": "4x - 3 = 2x + 6", "status": "not_equivalent",
     "suspected_slip": {"name": "dropped_parenthesis",
       "explanation": "A factor was applied to the first term of a bracket only, as if the bracket were dropped."}}
  ],
  "first_error": {"step": 2, "line": 2, "text": "4x - 3 = 2x + 6", "status": "not_equivalent", "suspected_slip": "dropped_parenthesis"}
}
```

Reply shape at hint level 1: "First wrong step: step 2, `4x - 3 = 2x + 6`. Hint: count how many terms inside the bracket the 4 was applied to. Steps 3 and 4 agree with step 2, so they carry the same error. Try step 2 again and I will re-check it."

Second example, from fixture `extraneous.txt`: lines for `sqrt(x + 6) = x` that square both sides get status `possibly_extraneous` with the note that x = -2 is a new solution to test in the original equation; dropping it in the last line is accepted with a reminder that the check must have been done.

## Limits

Algebra and arithmetic only. Equations are compared by real solutions in [-100, 100] with one variable; several variables only prove scalar-multiple rewrites. Slip names come from a short pattern list. The script judges consistency, not the quality of the method.

## Evidence

Script fixtures: 16/16 cases pass (`python evals/run_fixtures.py`, Python 3.11, Windows, 2026-11-21). Static lint: 0 FAIL, 0 WARN. Not run: trigger tests, with/without-skill efficacy evals, native discovery, cross-tool runs, human review. See VERIFICATION.md.

## Demo script (60 to 90 seconds)

1. Prompt: the learner pastes the four lines and asks where they went wrong.
2. The agent saves them to `steps.txt` unchanged and runs `python scripts/check_steps.py steps.txt`.
3. The JSON shows step 2 as `not_equivalent` with `dropped_parenthesis`; the agent states step 2 as the first wrong line and gives hint level 1.
4. The learner replies with `4x - 12 = 2x + 6`; the agent re-checks, all lines `equivalent`, `first_error` null.

## FAQ seeds

- Does it need network access? No.
- Will it just give me the answer? No: it shows the first wrong step and a hint first; the solution only after you try.
- Can it help during an exam? No; it declines in-progress graded work.
- What notation does it read? One step per line, `^` for powers, units like `5 [m]`; see the line format in SKILL.md.
- Does it handle calculus or word problems? No.
- What if it says "unchecked"? The step could not be proven either way (several variables or no defined points); check it by hand.
- How do I uninstall? Delete the folder.

## Changelog

0.1.0, 2026-11-21: first draft; script fixtures and lint only.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
