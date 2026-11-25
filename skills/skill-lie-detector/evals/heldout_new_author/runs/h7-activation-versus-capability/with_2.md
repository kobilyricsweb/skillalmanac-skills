**No, you can't say installing it improves the ordinary user experience.** The 25-point result and the 40-request result answer different questions, and only the first one was measured with the skill loaded.

The report should separate:

1. **Conditional effect: does the skill improve output once it is read?** The paired test answers this: same model, same tasks, with and without the skill, blind grading. The 25-point result on eight matched tasks is evidence here. Check its interval and sign-flip p (verdict.py's output) before calling it a LIFT, since eight tasks with two runs each is the stated minimum, not a strong result.

2. **Activation: how often does the skill load on requests nobody asked it to read?** This is a trigger question, and the lie-detector does not test it. The skill says so directly: use the trigger tests in skill-authoring-and-evals for that. The 40 production requests answer this one, and the answer was zero loads. Those requests were not a paired comparison, so they say nothing about output quality either way. They do show that on those requests, installation changed nothing the user would see.

The user-experience claim needs both. Roughly, the expected gain on ordinary requests is the activation rate times the conditional lift, and that assumes the eight matched tasks represent production work, which is a third assumption to state. The explicit "read this skill" instruction forces the condition that never happened in production, so the 25-point figure describes what the skill does when it is used, not what users get by installing it.

The report should therefore say: a measured conditional lift on eight tasks; zero activation in 40 ordinary requests; no evidence that installation improves ordinary requests; and a next step of measuring activation with trigger tests, or improving the description if the lift is real and the user wants it to fire.

I read `SKILL.md` but did not run the workflow, since no new calls were authorized. I also did not open the files it references (`references/formats.md`, the grader prompt, the scripts), so I have not checked the stored eight-task results against verdict.py's output.
