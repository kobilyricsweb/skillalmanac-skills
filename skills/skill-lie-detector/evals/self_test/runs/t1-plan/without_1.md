I read the skill's SKILL.md, LISTING.md, the script, and the fixture. I ran nothing. Here is the plan.

## What "better" has to mean

The skill has two parts with different value:

- **The script** does the conversion and enforces guards: no overwrite, a 2 MB cap, exit codes, and reporting of skipped items. A competent agent without the skill can write a 30-line Python converter, so the script's real value is probably the guards and consistency.
- **The prose** (decision table, workflow, output contract) mostly restates what a good agent would do anyway, and it costs context on every run.

Hypothesis to test, and try to falsify: **the skill helps with guard and reporting behavior, not with conversion accuracy on ordinary inputs.**

## Arms

- **A, skill:** your agent with json-records-to-csv installed.
- **B, baseline:** same agent, model, and settings, with the skill folder absent from the sandbox. Hiding it from the skill list is not enough, because the agent can find it by searching.
- **C, prose-only (optional):** a copy of SKILL.md with the script and command removed. Run it only if A beats B, to see whether the value comes from the rules or the script.

Prompts are natural user requests and never name the skill. Naming it tests triggering, not value. Give each run a fresh session, a fresh copy of the input in an empty directory, and no leftover output file.

## Stage 0: is the script right? (no LLM, under an hour)

The skill is marked "Provisional. One smoke run." Before crediting the agent, check the script against the spec in SKILL.md. Write a reference converter in the test harness from the spec rules, without importing `json_to_csv.py`, since using the skill's own code as the oracle is circular. Diff the two on the whole corpus. I hand-checked the LISTING example against the fixture (16 missing values, 9 columns), and it matches.

## Corpus (about 43 cases)

1. **Happy path (8):** flat records, the fixture, nesting 1 to 4 levels, unicode, quotes/commas/embedded newlines, UTF-8 BOM and CRLF input, key sets that differ across records.
2. **Arrays (6):** string arrays, number arrays, arrays of objects in join mode and row mode, several unequal arrays in one record (row mode), empty arrays.
3. **Value fidelity (5):** null vs. missing, booleans, `9.50` (the skill writes `9.5`), large integers, `1e21`.
4. **Must refuse (10):** top-level object; scalar; empty array; array of only scalars; invalid JSON; `NaN`; non-UTF-8; a file of 2,097,153 bytes; missing input; output exists; output equals input; URL input; a request for `.xlsx`.
5. **Partial success (3):** some non-object items. Expect exit 1, the CSV delivered, and the skipped indices listed.
6. **Boundaries (3):** exactly 2,097,152 bytes must pass; 1000-level nesting must give a clean exit 2 with no traceback.
7. **Ambiguity (3):** no output name given; JSON pasted inline in chat (the skill never says how to handle this, a real gap); a spreadsheet request with no format named.
8. **Messy real-world (3):** a `{"data": [...]}` wrapper; keys present in only half the records; keys containing dots.
9. **Formula-like values (2):** a cell starting with `=HYPERLINK(...)`. The skill documents this as a limit but does not mitigate it.

For every case, write the expected result (exit code or refusal, output or no output, and the oracle CSV) before any run.

## Running

- **Pilot:** 8 cases × 2 arms × 1 rep = 16 runs. Check that the skill is actually loaded in arm A (a Skill call or a read of SKILL.md in the transcript). If it never loads, the test measures nothing.
- **Core run:** groups 1 to 5 (32 cases) × 2 arms × 3 reps = 192 runs. Full set is about 258 runs.
- Use your runner's headless mode, one prompt per run (if you use Claude Code, `claude -p`; check the flags for your version). Save the transcript, output files, final message, tool calls, tokens, and wall time.
- Hash every input file before and after the run, to detect modification.

## Scoring

**Automated, by a grader that does not know the arm:**
- Correctness: parse the output CSV and compare it with the oracle on row count, column set, and each cell. Compare numbers numerically, and flag the `9.5` case separately as lossy. Score = matching cells; pass = all match.
- Guards: exit or refusal matches expected, output exists or not as expected, input hash unchanged.
- Partial success: the skipped indices in the final message match the real ones.

**Reviewed blind, rubric 0/1/2:**
- Report accuracy: the final message gives the right rows, columns, missing count, and status. No success is claimed when there is none.
- Refusal quality: the refusal names the problem and a fix.

**Recorded, not scored:** tool calls, tokens, time.

**Hard fails** (fail the run regardless of other scores):
- Overwrote an existing output file.
- Wrote output over the input file.
- Dropped skipped items without saying so.
- Claimed success with no file, or with the wrong file.
- Invented values not present in the input.
- Refused a valid input.

## Decision rules (write these down before the core run)

Compare A and B on pass rate and hard-fail count, per case. Three reps is thin, so use Wilson intervals or add reps wherever the result is close.

- **Keep as is:** A beats B by at least 10 points on the core set, or B commits a guard hard fail that A avoids; AND A has no false refusals; AND median tokens are at most 2× B.
- **Dead weight:** correctness within 5 points and no hard fail avoided. Cut it. If A is also cheaper than B, you can keep it as a speed or consistency tool, but say so.
- **Harmful:** A is less correct, has any false refusal, or has a hard fail B does not. Fix or remove.
- **Mixed:** if only the guards help, slim the skill to the guard rules and script. If C (prose-only) matches A, drop the prose.

My prediction, which the test should confirm or refute: B already handles groups 1 to 3 well, so the skill's measurable edge is in the guards (groups 4 and 5) and reporting. If so, the result is "mixed" and most of the prose can go.

## Things in the skill to check or decide on

- `9.50` becomes `9.5`. It is documented, but spreadsheet users may consider that a defect.
- Keys containing dots collide with nested paths. Documented, not handled.
- Formula-like cells pass through unescaped.
- No guidance for pasted inline JSON.
- The 25% blank threshold is a working value, not derived from anything.

## Timeline

- **Day 1:** stage 0 (script vs. oracle), build the corpus and expected results, write the grader.
- **Day 2:** pilot; fix harness problems, including confirming the skill loads in arm A.
- **Day 3:** core run.
- **Day 4:** blind grading, apply the decision rules, write up.

I can write the corpus files, the reference converter, and the grader script now. That is file-writing only, with no agent runs, so you can review them before next week.
