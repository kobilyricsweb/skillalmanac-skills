**Short answer: the evidence doesn't show that the skill helps, beyond one task.** The overall gap is real but comes almost entirely from t1.

**Overall (4 checks × 6 tasks × 2 reps per arm, 24 runs):**

| Arm | Checks passed | Rate |
|---|---|---|
| With skill | 30 / 48 | 62.5% |
| Without skill | 22 / 48 | 45.8% |

**Per task (checks passed, both reps summed, out of 8):**

| Task | With | Without | Diff |
|---|---|---|---|
| t1 | 8 | 0 | +8 |
| t2 | 2 | 4 | −2 |
| t3 | 4 | 6 | −2 |
| t4 | 6 | 4 | +2 |
| t5 | 6 | 4 | +2 |
| t6 | 4 | 4 | 0 |

Excluding t1, both arms score 22 / 40 (55%). The whole gap is t1, where the without arm got 0/8 and said "1,174.00 USD", "8% sales tax", "amounts in euros". Both without runs repeated that same wrong answer.

**Per check (out of 12 runs per arm):**

| Check | With | Without |
|---|---|---|
| Total correct | 12 | 10 |
| Duplicate line named | 10 | 10 |
| No invented tax rate | 6 | 2 |
| Currency is USD | 2 | 0 |

The skill's clearest effect is on the no-invented-tax check. The currency check fails in almost every run for both arms. Several with-skill runs (for example t2 `6jsw28`, which I read) still say "8% sales tax" and "euros", the same error as the without arm. So the skill is not reliably fixing the currency and tax errors on t2–t6.

**How much to trust this:**
- I spot-checked 8 of the 48 graded outputs against the checks, including the t1 without runs, and the grades matched.
- The invoice CSVs and the skill's SKILL.md are not in `results/`. I could not verify the expected totals against the source files, and I could not check what the skill tells the model about currency and tax, which is probably why it doesn't stick.
- Two reps per task across six near-identical invoices is a small sample. One task is carrying the result.

**Verdict:** the skill improves results on t1 and makes the model less likely to invent a tax rate, but it does not show a reliable overall benefit. It also doesn't fix the currency error. Before relying on it, I'd rerun with more reps (around 10 per task), include invoices with a different currency or an explicit tax line, and look at the skill's currency and tax wording. If you can point me to the skill file, I can check that wording against the failing runs.
