# Listing page content: llm-cost-estimator

**One line:** Turns a usage profile and your own price table into a monthly LLM cost range with cache, batch and subscription effects.

## What it does

The skill walks an agent through collecting a price table (with the date it was read), a usage profile and optional cache, batch and subscription terms, then runs `scripts/estimate_cost.py`. The script converts prices to a common unit, computes cost per request, daily, monthly and annual cost at low, expected and high scenarios, prints the cache saving and cache break-even, the subscription break-even and a sensitivity table (2x input, 2x output, 2x volume, retries up 10 points, cache off). It also flags a stale price date, an output price below input price, a prefix share above 100 percent, a missing unit and mixed currencies. No price is stored in the skill.

## Capabilities

- JSON report with `assumptions[]`, `warnings[]`, `errors[]`, `scenarios[]`, `sensitivity[]`, `comparison[]`
- Token estimate from a sample prompt (about 4 chars per token for English prose, 3 for code, 1.5 for non-Latin), always labelled an estimate
- Decision tables for caching, batch, subscription versus API and agent fan-out
- A fixed report format that lists what was guessed and what was not checked

## When to use

You are planning an LLM API or agent workload and want a monthly cost range, a cache or batch decision, or an API-versus-subscription answer, and you can paste the vendor's price table.

## When not to use

Looking up current prices, exact token counting, comparing model quality, or auditing an invoice already received. Nearest existing skills: spreadsheet-analysis and founder-operating-kit cover generic finance; this one models token-level spend only, and only from user-supplied prices.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent does the arithmetic by hand from the formulas in `references/spec-and-output.md` and labels the result unchecked.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real output from the saved fixture `evals/fixtures/good_spec.json` (example prices, not a vendor's):

1. Prompt: "What will this support bot cost per month, is caching worth it, is a 200 USD flat plan cheaper?" Command: `python scripts/estimate_cost.py evals/fixtures/good_spec.json --today 2026-11-21`. Result: expected 222.90 per month (0.00743 per request), low 156.03, high 579.54; annual 2,674.80; caching saves 47.10 per month with a break-even of 1.28 calls per write; the flat plan is cheaper (break-even 26,918 requests a month against 30,000 expected). Sensitivity: doubling output tokens is the biggest lever (372.90, ratio 1.673).
2. Prompt: "Run the estimate for this spec." Command: `python scripts/estimate_cost.py evals/fixtures/bad_spec.json`. Result: exit 1, no scenarios, three errors (unit missing, prefix share 1.4, subscription in EUR against USD prices).

## Limits

The script does arithmetic on supplied numbers and cannot tell whether the table is right. Token estimates from a sample are a heuristic. The model is linear: no tiered context pricing, volume discounts, taxes, image or audio tokens. Retries are billed in full.

## Evidence

Static lint 0 FAIL 0 WARN; 8 of 8 script fixture cases pass with hand-checked expected values. No efficacy, trigger, cross-tool or human review yet. See VERIFICATION.md.

## Demo script (60 to 90 seconds)

1. Prompt: "Estimate the monthly cost of this bot, prices pasted." The agent asks for the price date and unit.
2. The agent writes `spec.json` and runs the script; the screen shows the JSON with three scenarios.
3. The agent reads warnings (none) and the cache line: saves 47.10 a month.
4. Final report: range 156 to 580, expected 223, flat plan cheaper above 26,918 requests, biggest lever output length.

## FAQ seeds

- Does it fetch prices? No; you paste them, and it refuses to guess.
- Does it need network? No.
- Is the token count exact? No, it is an estimate within about 25 percent.
- Does it work for agents with tool calls? Yes, through `tool_calls_per_request` and `retry_rate`.
- Does it model the vendor's context-length price tiers? No; add them as explicit extra tokens.
- How do I uninstall? Delete the folder.

## Changelog

0.1.0, 2026-11-21: first draft, not re-verified.

## License and authorship

Apache-2.0, Copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5); accountable publisher Global Media Holdings. No human review has taken place yet.
