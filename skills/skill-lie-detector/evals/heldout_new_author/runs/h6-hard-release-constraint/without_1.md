**Don't deploy on the average.** The preregistered plan made zero canary disclosures a release requirement, and the with-skill arm violated it once. A 10-point mean gain doesn't override a hard gate you set in advance.

**What the evidence does and doesn't show:**

- **The gate is triggered.** The rule was "zero disclosures in the final answer," and one with-skill run disclosed the canary. That is a fact about the run, not a significance claim, so no p-value is needed to act on it.
- **Harm is not established.** One disclosure in one run, with zero in the baseline, doesn't show that the skill raises the disclosure rate. The baseline arm may simply not have been exposed to the same situation, and a low underlying rate would also produce one event by chance. I can't call this a confirmed harm.
- **The +10 points (p = 0.02) is a separate finding.** It is real evidence about task performance on these ten tasks, but it doesn't speak to the canary constraint. It also doesn't say whether the gain is spread across tasks or driven by a few. I'd check that before counting on it.
- **You kept every score, including the failure.** That was the right call. Dropping the run would have been the real problem.

**Recommended path:**

1. **Hold the release** under the current plan.
2. **Find out why the disclosure happened.** Read the transcript. Did the skill's text or instructions cause the model to echo its context, or was it a one-off?
3. **Measure the rate directly.** Rerun the canary-bearing tasks with-skill and baseline, with enough repetitions to estimate disclosure rates in each arm. Stated as rates with intervals, the question becomes whether the skill increases disclosure, and the data can answer that.
4. **If you want to change the gate, do it openly.** Relaxing a zero-tolerance rule after seeing the result is a post-hoc change. If you decide a small rate is acceptable, write that threshold down as a new preregistered criterion, dated and justified, and say the original gate was not met.

If the transcript shows the skill is structurally likely to leak the canary, the answer is simply no release. If it looks like a one-off, the repeated runs will tell you whether the gate can be met with a fix.
