# Listing page content: prompt-writing

**One line:** Writes and lints LLM prompts with a fixed structure, injection rules and a numeric test plan.

## What it does

The skill gives an agent a seven-step procedure for writing or repairing a prompt: name the job, fill six blocks (role, task, context, constraints, output contract, examples), answer a ten-question ambiguity checklist, apply an examples policy with counts, and lint the file. A script reads the prompt file and returns strict JSON for six checks: missing output contract, contradictory instruction pairs, unbounded length wording, placeholders that are never described, hedged phrasing such as "try to", and no rule for treating outside text as data. A reference sets an exposure tier for injection risk and lists twelve attack tests. A template turns the prompt into an evaluation plan with case mix and pass bars.

## Capabilities

- `scripts/prompt_lint.py lint <file>`: JSON with per-check findings (line, rule, match, detail), a score and a verdict; exit 0, 1 or 2
- A prompt skeleton with the six blocks, to copy
- An examples policy (0, 2 to 3, 3 to 5, or move out) and a ten-question ambiguity checklist
- An injection reference: four-tier exposure table, patterns that help, patterns that only look safe, 12 attack tests
- An evaluation-plan template: 20-case mix, numeric bars, 3 runs per case, a frozen subset
- A fixed report that states what was not checked

## When to use

You say write a system prompt, improve this prompt, my prompt gives inconsistent output, make the model follow the format, or you have a template with `{{placeholders}}` and want it tested and hardened.

## When not to use

Questions you ask an assistant in chat, image or video prompts, fine-tuning data, scoring a model on a public benchmark. How it differs from existing skills in this catalogue: `skill-authoring-and-evals` and `agent-instruction-files` write skills and agent instruction files; this one writes the prompts that applications send to a model.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent follows the manual checklist in step 5.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real output of `python scripts/prompt_lint.py lint` on the saved fixtures (run 2026-11-21, results in `evals/fixtures/RESULTS.txt`):

1. `evals/fixtures/bad_support_prompt.md`: `"score": 0`, `"verdict": "fail"`, exit 1. All six checks fail. Findings include `concise-vs-detailed` (line 5), `always-vs-never` (line 7, "Never cite the policy page" against "Always cite the policy page"), `json-only-vs-explanation` (line 8), `no-questions-vs-ask` (line 9), `min-above-max` (line 10, at least 200 words against at most 100), `as-needed` (line 6), `undefined-placeholder` for `{{customer_name}}` and `{{ticket_body}}` (lines 12 and 13), `try-to` (line 5), `if-possible` (line 6).
2. `evals/fixtures/good_support_prompt.md`: `"score": 100`, `"verdict": "pass"`, exit 0, six of six checks pass.
3. `evals/fixtures/edge_no_placeholders.md`: `"score": 75`; two checks are `na` (no placeholders) and the only finding is `might-want` ("Feel free to", line 3).

No saved with-skill agent run exists yet, so there is no rewritten prompt to show.

## Limits

- The script reads English surface wording; contradictions that need meaning are missed.
- A passing score says no listed defect is visible. It does not say the prompt works.
- A placeholder counts as described if its name appears as plain words anywhere; a lazy mention passes.
- Only `{{name}}` placeholders are recognised.
- Evaluation numbers are working defaults, not measured optima.
- Injection resistance reduces risk; it does not remove it.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL / 0 WARN, 8 of 8 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste the weak summarizer prompt; run the linter: score 0, six failing checks.
2. The agent fills the six blocks, resolves the "ask or do not ask" contradiction, defines both placeholders.
3. Re-run the linter: score 100.
4. Show the evaluation plan: case mix, pass bars, "not run against a model" in the report.

## FAQ seeds

- Does it work with any model or provider? The structure and checks are vendor-neutral; no provider syntax is used.
- Does it need network access? No.
- Does a score of 100 mean my prompt is good? No. It means the six structural defects are not visible. Run the evaluation plan.
- Will it make my app immune to prompt injection? No. It lowers the risk and tells you what must be enforced outside the prompt.
- Does it run my prompt against a model? No. It writes the plan; you or your harness run it.
- Does it handle `{name}` or `<name>` placeholders? Not yet; only `{{name}}`.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
