**No, the task-general claim is not established.** The p-value comes from treating 1,000 answers per condition as 1,000 independent task examples. There are only two tasks, so the sample size for generalizing to new invoices is 2, not 1,000.

**What the repetitions can tell you**

- How consistently the model behaves on invoice A and invoice B under each condition. Each task's pass rate can be estimated tightly, and the standard error for those two items is small.
- Whether the condition difference shows up on those two specific invoices, and how big it is there.
- How much run-to-run noise there is, so you can see whether a single run is representative.

**What they cannot tell you**

- Anything about other invoices. Generalizing requires variation between tasks, and with two tasks you cannot estimate that variation at all. Any invoice-level effect, such as one invoice being unusually easy, a format quirk, or a field that happens to be present in one task only, is invisible.
- Whether the difference is driven by the condition or by which invoice each condition saw. This depends on the design. If each condition ran on both invoices, the comparison is at least balanced. If not, task and condition are confounded.
- The 500 repetitions of one task are not independent of each other with respect to the task. They share the same invoice, prompt and content, so they behave like one observation repeated, not 500 separate ones.

**The p-value is an artifact of the unit of analysis**

The skill's method treats the task as the unit, with runs as repeated measures within each task. Its rules point the same way:

- Its sign-flip test is computed over tasks. With two tasks, the smallest two-sided p-value possible is 0.5 (2 of the 4 sign patterns give a mean at least as extreme as observed). No amount of repetition can get below that.
- Its rules require at least 6 tasks before a LIFT or HARMED verdict, and it notes that even 5 unanimous tasks give only p = 0.0625. Its own minimum of 4 tasks is for any verdict at all.

So a p below 0.000001 from two tasks is what pseudoreplication looks like. The 1,000 runs inflate the apparent sample size by roughly 500× per task.

**What would support a task-general claim**

- Many distinct invoices, sampled from a defined population or chosen to span the variation you care about. The skill's minimum is 6 tasks for a verdict, but for a claim about new invoices you would want considerably more.
- Several runs per invoice, to estimate each invoice's rate.
- A mixed model with a random intercept (and ideally a random slope for condition) for invoice, or a paired analysis at the invoice level, with the between-invoice variance reported. Report the interval, not just the p-value.
- A held-out set of invoices chosen before the comparison, so the claim is tested rather than fitted.

**What you can honestly say now:** the condition difference was X on invoice A and Y on invoice B, with narrow intervals for those two items, and the data say nothing about other invoices.

I didn't run the skill's pipeline here. Nothing in this working directory contains the experiment's data, and the skill tests whether a skill helps, not whether a statistic is valid. I applied its unit-of-analysis and sample-size rules instead. If you share the per-run outputs or grades, I can compute the per-invoice rates and intervals.
