# Agent session cost review

**One-line summary:** Reads a saved agent session transcript and shows which turns, files and commands used up your tokens, with one fix for each.

## What it does

A Python script (standard library only, no network) parses a session transcript, either JSONL in the common layouts or a plain log with `###` markers. It attributes tokens to every event, groups them by phase (explore, edit, run, reply, prompt) and by tool, lists the 10 costliest turns, and applies seven rules that each name a cause of waste: failing-command loops, repeated commands, repeated reads of an unchanged file, oversized tool output nobody cited, bulky early results carried unused, whole-file reads, and very long replies. Every finding carries a line number, a token estimate, an estimated saving and a remedy. Output is strict JSON; message bodies are cut to 80 characters and key-shaped strings are redacted.

## Capabilities

- Totals per role, phase and tool; top 10 costliest events
- Seven ranked finding kinds with `evidence_line`, `estimated_tokens`, `remedy`
- A savings table that counts each event once
- A data-quality block: unparseable lines (counted, not hidden), mixed sessions, missing timestamps
- Adjustable thresholds by flag; exit code 1 when over 20% of lines could not be parsed

## When to use

- You hit a usage limit and want to know which part of a session caused it
- A session felt slow or expensive and you want the turns named
- You want a short, evidence-backed list of changes to prompts and settings

## When not to use

- To make replies shorter from now on: use a terse-output skill (it changes behaviour; this one measures a finished session and does not change how the agent writes)
- To carry a session over to a new one: use a session-handoff skill (it writes the continuation; this one only tells you whether a fresh start would have paid off)
- To read invoices or billing data: this is an estimate from a transcript, not an account statement

## Requirements

Python 3.9 or newer. No network. Tested only on the fixtures in this package.

## Install

One folder, `agent-session-cost-review/`, placed in the skills directory of the tool you use (`.claude/skills/` or `.agents/skills/` in the project or home folder). Pin to the version in the frontmatter.

## Examples

**Prompt:** "That session hit my limit. Review `claude_style.jsonl` and tell me what to change." (run with the low demo thresholds)

**Actual script output (abridged, from `evals/fixtures/claude_style.jsonl`, 24 events, about 906 estimated tokens, 13 of them from usage counts):**

```
1. repeated_read     lines 6, 10, 14      ~202 tokens  3 identical reads of src/cart.py, 2 with no edit in between
2. oversized_output  line 5               ~140 tokens  558 characters returned, 0 shared identifiers with later turns
3. verbose_reply     line 18              ~119 tokens  one assistant text block
4. failing_loop      lines 8,12,16,20     ~107 tokens  4 identical calls, 3 with failing results
5. whole_file_read   line 7               ~76 tokens
6. unused_context    line 3               ~68 tokens
Possible saving: 586 tokens (64.7% of this session's estimate)
By phase: explore 61.7%, run 16.3%, reply 15.9%, edit 5.1%, prompt 1.0%
```

The agent's fix for the loop is a hypothesis and an edit instead of a fourth `pytest` run; for the reads, restating the three functions in the plan after the first read.

**Second prompt:** "Is anything wasteful in `plain_log.txt`?" Result: one finding, `git status --short` run 3 times (lines 32, 35, 38, about 24 tokens). The three reads of `client.py` are not flagged because each follows an edit to that file.

## Limits

- Estimates, not billing; hidden reasoning, system prompts and cached context that the export leaves out are not counted
- The cost of re-sending a large early result with every later turn is not modelled, so findings are floors
- "Cited later" is an identifier-overlap test and can misjudge results used by eye
- Unknown tool names are classed `other`; shell commands are classed by their first program word
- Thresholds are working values

## Evidence

| Check | Result | Date |
|---|---|---|
| Lint | 0 FAIL, 0 WARN | 2026-11-21 |
| Fixture run (`python evals/run_fixtures.py`) | 12/12 cases | 2026-11-21 |
| Trigger test, task evals with and without the skill, cross-tool, human review | Not run | |

## Demo script (60 to 90 seconds)

1. Prompt: "My agent ate my limit on one bug fix. Review this transcript." Attach `claude_style.jsonl`.
2. The agent runs the script and shows the data-quality block: 22 lines, 0 unparseable, one session.
3. It reads the ranked findings: three identical reads, a failing test run four times, one 558-character grep nobody used.
4. It gives one fix per finding and the possible saving (about 65% of the session).
5. Before and after: an unmeasured "it used a lot" becomes six named lines and a list of changes to paste.

## FAQ seeds

- Does it need network? No; it reads only the file you give it and prints JSON.
- Does it upload my transcript? No. Output previews are cut to 80 characters and key-like strings are redacted.
- Does it work with my tool? It reads common JSONL layouts and a plain marker format; the cross-tool run has not been done.
- Are the token numbers what I was billed? No; they are estimates from characters unless the log holds usage counts, and they exclude re-sent context.
- How is it different from a terse-output skill? That one tells the agent to write less; this one measures where a finished session spent its tokens.
- How is it different from a handoff-notes skill? That one writes the notes for the next session; this one tells you whether and why a fresh start was worth it.
- How do I uninstall? Delete the folder.

## Changelog

- 0.1.0 (2026-11-21): first draft; fixtures only.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No independent human review has taken place yet.
