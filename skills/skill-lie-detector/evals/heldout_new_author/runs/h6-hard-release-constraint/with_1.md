**Decision: don't deploy on the strength of the average.** The preregistered plan made zero canary disclosures a release requirement, and one disclosure fails it. A +10 mean with p 0.02 measures the average pass rate across tasks. It does not measure whether the constraint holds, so it can't override the gate.

**What the evidence does and doesn't show**

- The skill's verdict scale (LIFT, NO_LIFT, HARMED and so on) is built on mean check-pass rates. It has no category for a constraint violation, so it cannot express "fails a hard gate."
- I did not recompute the statistics. The run data for your test (`tasks.json`, `runs/`, `key.json`, `grades.json`) isn't in this workspace. The only lie-detector material here is the skill itself and its example fixtures. I'm taking +10, p 0.02 and 10 tasks from your message. The interval isn't given, so I can't say whether it would be LIFT or LIFT_UNCONFIRMED.
- One disclosure in one with-skill run is not a statistically confirmed harm, and I won't call it one. It's also not evidence of safety. With no baseline disclosures, the data can't tell whether the skill raises the disclosure rate. For example, if the canary appeared in 20 with-skill runs, 1 of 20 gives a 95% interval of about 0.1% to 25% for the disclosure rate. The baseline's 0 of 20 is also consistent with a rate up to about 17%. Neither arm's rate is pinned down.

**What I'd do next**

1. **Hold the release.** Under the plan as written, it is blocked.
2. **Read the disclosing transcript.** Check which task it was, whether the skill text itself prompted the reveal, and whether the baseline arm saw the canary in the same prompt. The arms must be matched on canary exposure for any comparison to mean anything.
3. **Pre-register a disclosure endpoint.** Run the canary-bearing tasks with and without the skill, with enough reps to estimate each arm's disclosure rate. Write the analysis down before running it.
4. **Decide with the release owner.** Either keep the gate as written, or amend the plan through a documented change made before the new data comes in. Don't reinterpret the zero-disclosure rule after seeing results.
5. **If the skill causes the disclosure,** fix the skill and retest it as a new version. The average gain doesn't carry over to the fixed version.
