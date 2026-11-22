---
name: llm-cost-estimator
description: Estimates the monthly cost of an LLM API or agent workload before it is built, from a price table the user supplies, a usage profile and optional cache, batch and subscription terms, with a script that does the arithmetic and returns low, expected and high scenarios, a cache-savings line, a subscription break-even and a sensitivity table. Use when the user asks how much will this cost, API cost per month, token cost, is caching worth it, is batch worth it, subscription or API, or what a token is worth in money. Do not use to look up current prices, count exact tokens, compare model quality, or audit a bill already received.
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# LLM cost estimator

Turn a usage profile into a cost range with arithmetic, not memory. The skill holds no prices. Every price comes from a table the user pastes from the vendor page, stamped with the date it was read. If the user has no table, stop and ask for one; never fill a price from memory, a blog post or an earlier conversation.

## Inputs to collect

| Group | Needed | Notes |
|---|---|---|
| Price table | `as_of` date, `currency`, `unit` (`per_1M` or `per_1K`), `source`, per model `input`, `output`, optional `cached_input`, `cache_write`, `batch_discount` | A missing unit or date is a hard error. `batch_discount` is a fraction (0.5 = half off). |
| Usage | `requests_per_day`, `input_tokens_avg`, `output_tokens_avg`, optional p95 of each, `prefix_share`, `retry_rate`, `tool_calls_per_request`, `days_per_month` | Token counts are per model call. `prefix_share` is the part of the prompt that is byte-identical across calls (system prompt, tool definitions, fixed documents). |
| Options | `use_cache`, `calls_per_prefix`, `batch_share`, `batch_stacks_with_cache` | `calls_per_prefix` = how many calls reuse one cache write before it expires. |
| Optional | `subscription.price_per_month`, a plain-text sample prompt | A sample lets the script estimate input tokens. |

Field-by-field spec and the output schema: [references/spec-and-output.md](references/spec-and-output.md). Read it before writing the spec file.

## Workflow

```
- [ ] 1 Get the price table and its date from the user
- [ ] 2 Get the usage profile; mark every guessed number as a guess
- [ ] 3 Write spec.json
- [ ] 4 Run the script
- [ ] 5 Read errors and warnings first
- [ ] 6 Apply the decision tables
- [ ] 7 Report
```

1. **Price table.** Ask for the vendor's per-token prices, the date read and where. Convert nothing yourself: copy the unit exactly as the page states it.
2. **Usage.** Prefer measured numbers (logs, a vendor usage page, a token counter) over guesses. Without measurements, estimate input tokens from a real sample prompt with the script (step 4) and label the figure an estimate.
3. **Spec.** Write `spec.json` with the Write tool. Keep unknowns out rather than inventing them; the script reports each default it applies under `assumptions[]`.
4. **Run:**

```bash
python scripts/estimate_cost.py spec.json [--sample prompt.txt]
```

   Prints one JSON report. Exit 0 = report produced (warnings allowed), 1 = the spec has errors and no scenarios, 2 = unreadable file. Run it; do not edit it to silence a check.
5. **Read `errors[]`, then `warnings[]`, then `assumptions[]`.** Fix errors with the user. A price older than 60 days, an output price below the input price, `prefix_share` above 1, a missing unit and mixed currencies are all caught. Pass the warnings on to the user in the report.
6. **Decide** with the tables below, using the report's numbers.
7. **Report** in the fixed shape at the end.

## Decision tables

**Caching.** Let `w` = cache_write / input and `r` = cached_input / input. Caching pays only when the calls sharing one write exceed `(w - r) / (1 - r)`; the script prints this as `break_even_cache`. With a typical write premium near 1.25x and a read near 0.1x the threshold is about 1.3, so two calls per write already win; with a write at 2x it is 2.1. Cache nothing that changes per call, and nothing whose reuse is separated by more than the vendor's cache lifetime (ask the user for it). Ceiling on savings: `prefix_share` x (1 - r) of input cost.

**Batch.**

| Situation | Use batch? |
|---|---|
| Result needed within seconds or minutes | No |
| Result can wait for the vendor's stated batch window (often hours) | Yes for that share only |
| Mixed traffic | Set `batch_share` to the fraction that can wait; saving is about `batch_share` x `batch_discount` |
| Vendor does not allow batch plus cache discounts together | Leave `batch_stacks_with_cache` false (the default) |

**Subscription or API.** The script prints `break_even_requests_per_month` = subscription price / expected cost per request. API wins below that volume, subscription above it. Subscriptions usually carry usage caps and may bar automated or commercial use; the numbers alone do not settle it. Say so.

**Token rule of thumb**, always an estimate: English prose about 4 characters or 0.75 words per token; code and markup about 3 characters per token; non-Latin scripts (CJK, Cyrillic, Arabic, Hebrew) about 1.5 characters per token. Error band plus or minus 25 percent. For a budget that will be committed, use the vendor's own token counter on a real sample.

**Agents.** Calls per request = (1 + tool_calls) x (1 + retry_rate). Each tool round trip re-sends the context, so fan-out multiplies input cost far more than output cost; cache the stable prefix first.

## Report format

```
Prices: <currency>, <unit>, read <as_of> from <source>; age <n> days
Expected: <monthly> per month (<per request> per request); range <low> to <high>
Annual (expected): <annual>
Cache: <saves X per month | not worth it | not used>; break-even <n> calls per write
Subscription: <cheaper option> (break-even <n> requests per month) or not asked
Biggest lever: <top row of the sensitivity table, with its ratio>
Warnings: <from the script, verbatim>
Guessed inputs: <assumptions that came from defaults or from the user's guess>
Not checked: tokens counted by heuristic; prices not verified against the vendor page by me
```

## Limits

- The script does arithmetic on the numbers it is given. It does not know whether the table is right.
- Token estimates from a sample are a heuristic and never replace a vendor token counter.
- The model is linear: no tiered pricing by context length, no volume discounts, no minimum commitments, no taxes, no image or audio tokens, no reasoning-token surcharge. If the vendor has any of these, add them to the price as an explicit extra input token count and say so.
- Scenario multipliers (0.7x low volume, 1.3x high volume at p95 tokens) are defaults, adjustable through `options.scenarios`.
- Retries are billed in full; real failures often bill less.
- Without Python: do the same arithmetic by hand with the formulas in the reference file, and label the result unchecked by script.
