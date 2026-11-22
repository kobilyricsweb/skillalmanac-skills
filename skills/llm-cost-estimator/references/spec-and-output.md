## Contents

1. Spec file
2. Formulas
3. Output file
4. Checks the script makes

# Spec file and output contract

## 1. Spec file

JSON object. All prices are numbers in the unit stated by `price_table.unit`. The numbers below are shapes, not prices.

```json
{
  "model": "name-in-table",
  "sample_file": "prompt.txt",
  "price_table": {
    "as_of": "YYYY-MM-DD",
    "currency": "USD",
    "unit": "per_1M",
    "source": "where the prices were read",
    "models": {
      "name-in-table": {"input": 0, "output": 0, "cached_input": 0, "cache_write": 0, "batch_discount": 0.5}
    }
  },
  "usage": {
    "requests_per_day": 0, "days_per_month": 30,
    "input_tokens_avg": 0, "input_tokens_p95": 0,
    "output_tokens_avg": 0, "output_tokens_p95": 0,
    "prefix_share": 0.0, "retry_rate": 0.0, "tool_calls_per_request": 0
  },
  "options": {
    "use_cache": false, "calls_per_prefix": 1,
    "batch_share": 0.0, "batch_stacks_with_cache": false,
    "scenarios": {"low_volume": 0.7, "high_volume": 1.3}
  },
  "subscription": {"price_per_month": 0, "currency": "USD"}
}
```

Required: `price_table.as_of`, `currency`, `unit`, `models`; the chosen model's `input` and `output`; `usage.requests_per_day`, `usage.output_tokens_avg`, and `input_tokens_avg` (or a sample file). Everything else has a stated default that appears under `assumptions[]`. `model` may be omitted when the table has one model. `sample_file` is resolved next to the spec; `--sample` overrides it.

## 2. Formulas

All prices are converted to per 1M tokens first (`per_1K` x 1000). For one model call, with `n` = `calls_per_prefix`, `P` = prefix tokens = input x `prefix_share`:

- Plain input: `input_tokens x input`.
- Cached input: `(input_tokens - P) x input + P x (cache_write + (n - 1) x cached_input) / n`. A missing `cache_write` price is replaced by `input` and noted.
- Output: `output_tokens x output`. All divided by 1,000,000.
- Batch blend: `(1 - batch_share) x standard + batch_share x batch`, where batch = (plain input + output) x (1 - batch_discount), or, when `batch_stacks_with_cache` is true, standard x (1 - batch_discount).
- Per request: call cost x (1 + tool_calls) x (1 + retry_rate).
- Daily = per request x requests per day x scenario volume; monthly = daily x `days_per_month`; annual = monthly x 12.
- Scenarios: low = low_volume at average tokens; expected = stated volume at average tokens; high = high_volume at p95 tokens (p95 defaults to 2 x average when absent).
- Cache break-even: caching pays when `n > (cache_write - cached_input) / (input - cached_input)`.
- Subscription break-even requests per month = subscription price / expected cost per request.

## 3. Output file

One JSON object on stdout:

| Field | Meaning |
|---|---|
| `ok` | true when a report was produced; false when `errors[]` is non-empty |
| `model`, `currency`, `price_as_of`, `price_age_days` | echo of the inputs used |
| `calls_per_request` | (1 + tool_calls) x (1 + retry_rate) |
| `assumptions[]` | every default or derived input and every modelling rule applied |
| `warnings[]` | suspicious but usable inputs |
| `errors[]` | inputs that block a report |
| `scenarios[]` | three objects: `name`, `requests_per_day`, `input_tokens`, `output_tokens`, `cost_per_request`, `daily`, `monthly`, `annual`, `cache_savings_monthly` |
| `break_even_cache` | `calls_per_prefix_must_exceed`, `min_whole_calls`; null when no cached price |
| `subscription` | null or `price_per_month`, `break_even_requests_per_month`, `expected_requests_per_month`, `api_expected_monthly`, `cheaper` (`api` or `subscription`), `note` |
| `sensitivity[]` | `case` (input_tokens_2x, output_tokens_2x, volume_2x, retry_rate_plus_10_points, cache_off), `monthly`, `delta_vs_expected`, `ratio_vs_expected` |
| `comparison[]` | expected monthly cost for every model in the table under the same profile, cheapest first; cost only, not quality |
| `token_estimate` | null or `chars`, `words`, `estimated_tokens`, `kind`, `words_cross_check`, `label` |

Money is rounded to 2 places (6 for per-request cost).

## 4. Checks the script makes

| Condition | Result |
|---|---|
| no `unit`, or a unit other than `per_1M` / `per_1K` | error |
| no `as_of` date, no currency, no price table | error |
| price older than 60 days | warning |
| output price below input price | warning |
| `cached_input` not below `input`; `cache_write` below `input` | warning |
| `prefix_share` outside 0 to 1 | error |
| subscription or model currency differs from the table | error |
| `use_cache` without a cached price, or without `calls_per_prefix` | warning |
| `calls_per_prefix` at or below the cache break-even | warning |
| p95 below the average | warning |
