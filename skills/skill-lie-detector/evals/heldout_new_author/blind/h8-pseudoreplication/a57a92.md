**No, the task-general claim is not established.** The 1,000 answers per condition are not 1,000 independent task examples, and the 1e-6 p-value is not evidence about new invoice tasks.

**Why the repetitions don't add task-level sample size**

- The unit of generalization is the task. You have 2 tasks, so your sample for a claim about new tasks is n = 2.
- Repeating the same task 500 times adds draws, not tasks. All 500 share the same prompt, the same invoice, and the same difficulty and quirks. Their outcomes are strongly correlated through the task, so the design effect is large. If the intra-task correlation is near 1, the effective sample size is close to the number of tasks, not 1,000.
- The p-value treats the 1,000 answers as independent, so it is far too small. Any test whose standard error is computed from the 1,000 rows will overstate precision for task-level questions.

**What the repetitions can tell you**

- For these two specific prompts, the condition effect estimate is reasonably precise, given the model's sampling noise. A binomial or bootstrap interval per task per condition is valid for that question.
- They show how stable each task's outcome is under the sampling setup (temperature, seeds, and so on).
- They can reveal whether the effect is consistent across the two tasks, though with two tasks you cannot tell whether that consistency is typical.
- They describe behavior on these two items only. A large per-task effect there is a finding about those items.

**What they cannot tell you**

- Whether the condition effect holds for other invoice tasks, or the size of the effect across the task population.
- The between-task variance. With two tasks there is one degree of freedom for it, so it cannot be estimated.
- Whether the two tasks are representative. Their agreement or disagreement says little about the population.

**What would support the claim**

1. Sample many distinct invoice tasks from a defined population, ideally a generator or a held-out split, with enough tasks to estimate task-level variance (dozens at minimum, more for tight intervals).
2. Analyze at the task level, or use a mixed-effects model (for example, a logistic regression with a random intercept for task and a random slope for condition). Report the estimate and its interval with task as the source of uncertainty.
3. Use cluster bootstrap over tasks, not over rows.
4. Pre-register the population of tasks and the test, and keep a held-out set of tasks for confirmation.
5. Report per-task effects as well as the pooled estimate, so heterogeneity is visible.

**Suggested wording for the current result**

"On two invoice tasks, condition A outperformed condition B in 500 repeated samples per task. This describes those two tasks only. With two tasks we cannot estimate task-to-task variability, so we make no claim about performance on new invoice tasks. The p-value from pooling repetitions is invalid for that purpose."
