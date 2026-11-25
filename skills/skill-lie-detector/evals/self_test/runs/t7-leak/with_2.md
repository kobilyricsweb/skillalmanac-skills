**Don't delete it yet.** The 80% vs 78% result doesn't show the skill is useless. Your test breaks the method in SKILL.md in ways that make the numbers unreliable.

1. **The baseline wasn't clean.** The skill was already in the session context from the first 5 runs. Telling the agent to "ignore" it doesn't remove it from context. The method says every run needs a fresh context, and the skill must be out of the skills folder for the baseline.
2. **The baseline prompt named the skill.** SKILL.md says not to mention skills in the baseline prompt, because that reveals which arm the output came from.
3. **Five tasks is too few.** The method needs at least 4 graded tasks for any verdict and at least 6 for LIFT or HARMED. Its recommended minimum before acting on a NO_LIFT is 8 tasks with 2 runs per arm.
4. **Two points on five tasks is noise.** One task changing its pass rate moves the mean by about 20 points. Even a valid test would not separate 80% from 78%.
5. **Unknowns:** I don't know whether the checks were written before the runs, whether the grading was blind, or how many runs each arm had.

Your numbers also don't say "useless" by the method's own rules. A mean difference of +2 points would be LIFT_UNCONFIRMED ("maybe helps"), not NO_LIFT. But because the test is contaminated, neither verdict means anything yet.

Even with a clean result, NO_LIFT doesn't automatically mean delete. The method's own wording is "no measurable gain here; it still costs context each time it loads." Deleting is your call based on the cost and on whether the tasks you chose represent your real work.

**To run a proper test,** I need:
- The path to the installed skill folder. I didn't check `~/.claude/skills` because the Bash call was blocked for approval.
- Your 5 original tasks, plus 3–5 more from your real work that the skill claims to cover. Include a couple where you expect the plain model to slip.
- Permission to move the skill folder out of the skills directory while the baseline runs. I'd put it back afterward.

Then I'd write the checks before any run, run each task twice per arm in fresh subagents, blind the outputs, grade them in a separate grader, and compute the verdict with `verdict.py`. Do you want me to set that up?
