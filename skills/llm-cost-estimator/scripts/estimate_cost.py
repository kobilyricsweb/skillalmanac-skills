#!/usr/bin/env python3
"""Estimate the cost of an LLM workload from a user-supplied price table.

    python estimate_cost.py spec.json [--sample prompt.txt] [--today YYYY-MM-DD]

Reads: the JSON spec (price table + usage profile + options + optional
subscription) and, optionally, one plain-text sample of a typical prompt.
Writes: one JSON report on stdout. Nothing is written to disk, no network.
No price is built in: every price comes from the spec. A spec without a
price date, a unit or a currency is refused.

Exit codes: 0 report produced (warnings allowed), 1 spec has errors (the
report lists them and has no scenarios), 2 unreadable file or bad arguments.
"""
import datetime
import json
import os
import sys

STALE_PRICE_DAYS = 60       # vendor prices change often; older than this is only a hint
LOW_VOLUME = 0.7            # default low scenario: 30 percent less traffic, average tokens
HIGH_VOLUME = 1.3           # default high scenario: 30 percent more traffic, p95 tokens
P95_FALLBACK = 2.0          # p95 = 2 x average when the user gave no p95
CHARS_PER_TOKEN_PROSE = 4.0     # common rule of thumb for English prose
CHARS_PER_TOKEN_CODE = 3.0      # code and markup are denser in tokens
CHARS_PER_TOKEN_NONLATIN = 1.5  # CJK, Cyrillic, Arabic, Hebrew etc. cost far more per character
CODE_PUNCT = set("{}[]()<>;=_/\\\"'`:#$|&*")
CODE_PUNCT_SHARE = 0.12         # above this share of punctuation the sample is treated as code
UNITS = {"per_1M": 1.0, "per_1K": 1000.0}  # multiplier that converts a price to per 1M tokens
PRICE_FIELDS = ("input", "output", "cached_input", "cache_write")


def load_json(path):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"error: cannot read JSON file {path}: {exc}", file=sys.stderr)
        raise SystemExit(2)


def estimate_tokens(text):
    """Character heuristic. Returns a dict that is always labelled an estimate."""
    chars = len(text)
    words = len(text.split())
    if chars == 0:
        return {"chars": 0, "words": 0, "estimated_tokens": 0, "kind": "empty", "label": "estimate"}
    nonlatin = sum(1 for c in text if ord(c) >= 0x0370 and not c.isspace())
    ascii_punct = sum(1 for c in text if c in CODE_PUNCT)
    latin = chars - nonlatin
    code_like = ascii_punct / max(latin, 1) > CODE_PUNCT_SHARE
    per_latin = CHARS_PER_TOKEN_CODE if code_like else CHARS_PER_TOKEN_PROSE
    tokens = latin / per_latin + nonlatin / CHARS_PER_TOKEN_NONLATIN
    kind = "code-like" if code_like else "prose"
    if nonlatin / chars > 0.2:
        kind += "+non-latin"
    return {
        "chars": chars, "words": words, "estimated_tokens": int(round(tokens)), "kind": kind,
        "words_cross_check": int(round(words / 0.75)),
        "label": "estimate, expect +/- 25 percent; use the vendor token counter before committing a budget",
    }


def num(value, name, errors, minimum=0.0, required=True, default=None):
    if value is None:
        if required:
            errors.append(f"missing {name}")
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append(f"{name} must be a number")
        return default
    if value < minimum:
        errors.append(f"{name} must be at least {minimum}")
        return default
    return float(value)


def check_prices(table, model, errors, warnings, today):
    """Validate the price table and return (per-1M prices for model, as_of date or None)."""
    if not isinstance(table, dict):
        errors.append("price_table is missing: supply prices from the vendor page, none are built in")
        return None, None
    unit = table.get("unit")
    if unit not in UNITS:
        errors.append("price_table.unit must be 'per_1M' or 'per_1K' (a missing or mixed unit is the commonest 1000x error)")
    if not table.get("currency"):
        errors.append("price_table.currency is missing (e.g. USD)")
    as_of = None
    raw_date = table.get("as_of")
    if not raw_date:
        errors.append("price_table.as_of is missing: write the date you read the prices from the vendor page")
    else:
        try:
            as_of = datetime.date.fromisoformat(str(raw_date))
        except ValueError:
            errors.append("price_table.as_of must be YYYY-MM-DD")
    if as_of is not None:
        age = (today - as_of).days
        if age < 0:
            warnings.append(f"price_table.as_of {as_of} is in the future")
        elif age > STALE_PRICE_DAYS:
            warnings.append(f"prices are {age} days old (limit {STALE_PRICE_DAYS}); re-read the vendor page")
    if not table.get("source"):
        warnings.append("price_table.source is empty; note where the prices were read")
    models = table.get("models")
    if not isinstance(models, dict) or not models:
        errors.append("price_table.models must map a model name to its prices")
        return None, as_of
    if model not in models:
        errors.append(f"model '{model}' is not in price_table.models: {sorted(models)}")
        return None, as_of
    entry = models[model]
    if entry.get("currency") and table.get("currency") and entry["currency"] != table["currency"]:
        errors.append(f"currency mixing: model '{model}' is {entry['currency']}, table is {table['currency']}")
    mult = UNITS.get(unit, 1.0)
    prices = {}
    for field in ("input", "output"):
        prices[field] = num(entry.get(field), f"models.{model}.{field}", errors, required=True)
    for field in ("cached_input", "cache_write"):
        prices[field] = num(entry.get(field), f"models.{model}.{field}", errors, required=False)
    prices["batch_discount"] = num(entry.get("batch_discount"), f"models.{model}.batch_discount", errors, required=False)
    if prices["batch_discount"] is not None and prices["batch_discount"] > 1:
        errors.append("batch_discount is a fraction between 0 and 1 (0.5 means 50 percent off)")
    if errors:
        return None, as_of
    for field in PRICE_FIELDS:
        if prices[field] is not None:
            prices[field] *= mult
    if prices["output"] < prices["input"]:
        warnings.append("output price is below input price; most vendors charge more for output, check the unit and the column")
    if prices["cached_input"] is not None and prices["cached_input"] >= prices["input"]:
        warnings.append("cached_input is not cheaper than input; caching cannot pay")
    if prices["cache_write"] is not None and prices["cache_write"] < prices["input"]:
        warnings.append("cache_write is below the plain input price; usually a write costs a premium, check the table")
    return prices, as_of


def break_even_reads(p):
    """Calls that must share one cache write before caching beats plain input.

    Per cached token over n calls: write + (n-1) reads against n plain inputs.
    Pays when n > (write - read) / (input - read).
    """
    if p["cached_input"] is None or p["cached_input"] >= p["input"]:
        return None
    write = p["cache_write"] if p["cache_write"] is not None else p["input"]
    n = (write - p["cached_input"]) / (p["input"] - p["cached_input"])
    if n < 1.0:
        return {"calls_per_prefix_must_exceed": round(n, 4), "min_whole_calls": 1}
    return {"calls_per_prefix_must_exceed": round(n, 4), "min_whole_calls": int(n) + 1}


def call_cost(p, tokens_in, tokens_out, prefix_share, cache_on, n_per_prefix, batch_share, batch_stacks):
    """Cost in currency of one model call (prices are per 1M tokens)."""
    def standard():
        if cache_on and p["cached_input"] is not None:
            write = p["cache_write"] if p["cache_write"] is not None else p["input"]
            prefix = tokens_in * prefix_share
            per_tok = (write + (n_per_prefix - 1) * p["cached_input"]) / n_per_prefix
            cin = (tokens_in - prefix) * p["input"] + prefix * per_tok
        else:
            cin = tokens_in * p["input"]
        return (cin + tokens_out * p["output"]) / 1e6

    std = standard()
    if batch_share <= 0 or p["batch_discount"] is None:
        return std
    keep = 1.0 - p["batch_discount"]
    batch = std * keep if batch_stacks else (tokens_in * p["input"] + tokens_out * p["output"]) / 1e6 * keep
    return (1.0 - batch_share) * std + batch_share * batch


class Plan:
    """The validated usage profile and options for one model."""

    def __init__(self, prices, usage, options, calls_mult):
        self.p, self.u, self.o, self.calls_mult = prices, usage, options, calls_mult

    def per_request(self, tin, tout, cache_on=None, calls_mult=None):
        cache = self.o["use_cache"] if cache_on is None else cache_on
        mult = self.calls_mult if calls_mult is None else calls_mult
        return mult * call_cost(self.p, tin, tout, self.u["prefix_share"], cache, self.o["calls_per_prefix"],
                                self.o["batch_share"], self.o["batch_stacks_with_cache"])


def money(x, places=2):
    return round(x, places) + 0.0  # + 0.0 turns -0.0 into 0.0


def build_report(spec, sample_text, today, spec_dir):
    errors, warnings, assumptions = [], [], []
    report = {"tool": "estimate_cost.py", "ok": False, "assumptions": assumptions, "warnings": warnings,
              "errors": errors, "scenarios": []}
    usage = spec.get("usage") or {}
    options = spec.get("options") or {}
    table = spec.get("price_table")
    model = spec.get("model")
    if not model and isinstance(table, dict) and isinstance(table.get("models"), dict) and len(table["models"]) == 1:
        model = next(iter(table["models"]))
        assumptions.append(f"model not named; using the only model in the table: {model}")
    prices, as_of = check_prices(table, model, errors, warnings, today)
    report["model"] = model
    report["currency"] = (table or {}).get("currency") if isinstance(table, dict) else None
    report["price_as_of"] = str(as_of) if as_of else None
    report["price_age_days"] = (today - as_of).days if as_of else None

    rpd = num(usage.get("requests_per_day"), "usage.requests_per_day", errors, minimum=0.0)
    days = num(usage.get("days_per_month"), "usage.days_per_month", errors, required=False, default=30.0, minimum=1.0)
    if "days_per_month" not in usage:
        assumptions.append("days_per_month not given; 30 used")
    token_est = None
    in_avg = num(usage.get("input_tokens_avg"), "usage.input_tokens_avg", errors, required=False)
    if sample_text is not None:
        token_est = estimate_tokens(sample_text)
        if in_avg is None:
            in_avg = float(token_est["estimated_tokens"])
            assumptions.append(f"input_tokens_avg taken from the sample file: {in_avg:.0f} tokens (estimate)")
    if in_avg is None:
        errors.append("give usage.input_tokens_avg or a sample file")
    out_avg = num(usage.get("output_tokens_avg"), "usage.output_tokens_avg", errors)
    in_p95 = num(usage.get("input_tokens_p95"), "usage.input_tokens_p95", errors, required=False)
    out_p95 = num(usage.get("output_tokens_p95"), "usage.output_tokens_p95", errors, required=False)
    if in_avg is not None and in_p95 is None:
        in_p95 = in_avg * P95_FALLBACK
        assumptions.append(f"input_tokens_p95 not given; {P95_FALLBACK} x average used")
    if out_avg is not None and out_p95 is None:
        out_p95 = out_avg * P95_FALLBACK
        assumptions.append(f"output_tokens_p95 not given; {P95_FALLBACK} x average used")
    if in_avg is not None and in_p95 is not None and in_p95 < in_avg:
        warnings.append("input_tokens_p95 is below the average; check the numbers")
    if out_avg is not None and out_p95 is not None and out_p95 < out_avg:
        warnings.append("output_tokens_p95 is below the average; check the numbers")
    share = usage.get("prefix_share", 0.0)
    if isinstance(share, bool) or not isinstance(share, (int, float)) or share < 0 or share > 1:
        errors.append("usage.prefix_share must be a fraction from 0 to 1; above 1 means more than 100 percent of the prompt is reusable")
        share = 0.0
    retry = num(usage.get("retry_rate"), "usage.retry_rate", errors, required=False, default=0.0)
    fan = num(usage.get("tool_calls_per_request"), "usage.tool_calls_per_request", errors, required=False, default=0.0)
    if "retry_rate" not in usage:
        assumptions.append("retry_rate not given; 0 used")
    if "tool_calls_per_request" not in usage:
        assumptions.append("tool_calls_per_request not given; 0 used (one model call per request)")
    use_cache = bool(options.get("use_cache", False))
    n_prefix = num(options.get("calls_per_prefix"), "options.calls_per_prefix", errors, required=False, default=1.0, minimum=1.0)
    if use_cache and "calls_per_prefix" not in options:
        warnings.append("use_cache is on but options.calls_per_prefix is missing; 1 used, so caching is priced as all writes")
    batch_share = num(options.get("batch_share"), "options.batch_share", errors, required=False, default=0.0)
    if batch_share is not None and batch_share > 1:
        errors.append("options.batch_share is a fraction from 0 to 1")
    if use_cache and prices is not None and prices["cached_input"] is None:
        warnings.append("use_cache is on but the price table has no cached_input price; caching ignored")
    if use_cache and prices is not None and prices["cache_write"] is None and prices["cached_input"] is not None:
        assumptions.append("cache_write price not given; plain input price used for the write")
    if batch_share and prices is not None and prices["batch_discount"] is None:
        warnings.append("batch_share is above 0 but the price table has no batch_discount; batching ignored")
    sub = spec.get("subscription")
    if isinstance(sub, dict):
        sub_cur = sub.get("currency")
        if sub_cur and report["currency"] and sub_cur != report["currency"]:
            errors.append(f"currency mixing: subscription is {sub_cur}, prices are {report['currency']}")
        if not sub_cur:
            warnings.append("subscription.currency missing; assumed to match the price table")
        num(sub.get("price_per_month"), "subscription.price_per_month", errors, minimum=0.0)
    elif sub is not None:
        errors.append("subscription must be an object with price_per_month")
    if errors:
        return report, token_est
    plan = Plan(prices, {"prefix_share": share},
                {"use_cache": use_cache, "calls_per_prefix": n_prefix, "batch_share": batch_share,
                 "batch_stacks_with_cache": bool(options.get("batch_stacks_with_cache", False))},
                (1.0 + fan) * (1.0 + retry))
    report["calls_per_request"] = round(plan.calls_mult, 4)
    assumptions.append("token counts are per model call; calls per request = (1 + tool_calls) x (1 + retry_rate)")
    assumptions.append("a retried call is billed in full (input and output)")
    if batch_share:
        assumptions.append("batch-priced calls " + ("stack the discount on cache pricing" if plan.o["batch_stacks_with_cache"]
                           else "use plain uncached prices minus the batch discount (set batch_stacks_with_cache to change)"))
    report["break_even_cache"] = break_even_reads(prices) if use_cache or prices["cached_input"] is not None else None
    if use_cache and report["break_even_cache"] and n_prefix <= report["break_even_cache"]["calls_per_prefix_must_exceed"]:
        warnings.append("calls_per_prefix is at or below the cache break-even; caching costs more than it saves")
    scen = options.get("scenarios") or {}
    low_v = float(scen.get("low_volume", LOW_VOLUME))
    high_v = float(scen.get("high_volume", HIGH_VOLUME))
    defs = [("low", low_v, in_avg, out_avg), ("expected", 1.0, in_avg, out_avg), ("high", high_v, in_p95, out_p95)]
    assumptions.append(f"scenarios: low = {low_v} x volume at average tokens; expected = stated volume at average tokens; "
                       f"high = {high_v} x volume at p95 tokens")
    for name, vol, tin, tout in defs:
        per_req = plan.per_request(tin, tout)
        daily = per_req * rpd * vol
        monthly = daily * days
        no_cache = plan.per_request(tin, tout, cache_on=False) * rpd * vol * days
        report["scenarios"].append({
            "name": name, "requests_per_day": round(rpd * vol, 4), "input_tokens": round(tin, 2),
            "output_tokens": round(tout, 2), "cost_per_request": money(per_req, 6), "daily": money(daily),
            "monthly": money(monthly), "annual": money(monthly * 12),
            "cache_savings_monthly": money(no_cache - monthly) if use_cache else 0.0,
        })
    exp = report["scenarios"][1]
    exp_monthly = exp["monthly"]
    report["subscription"] = None
    if isinstance(sub, dict):
        price = float(sub["price_per_month"])
        per_req = exp["cost_per_request"]
        be = price / per_req if per_req > 0 else None
        monthly_requests = rpd * days
        report["subscription"] = {
            "price_per_month": price,
            "break_even_requests_per_month": round(be, 1) if be is not None else None,
            "expected_requests_per_month": round(monthly_requests, 1),
            "api_expected_monthly": exp_monthly,
            "cheaper": "subscription" if exp_monthly > price else "api",
            "note": "a subscription usually has usage caps; check that the plan covers the volume before relying on this line",
        }
    sens = []
    base = exp_monthly
    cases = [("input_tokens_2x", dict(tin=in_avg * 2, tout=out_avg), 1.0, None),
             ("output_tokens_2x", dict(tin=in_avg, tout=out_avg * 2), 1.0, None),
             ("volume_2x", dict(tin=in_avg, tout=out_avg), 2.0, None),
             ("retry_rate_plus_10_points", dict(tin=in_avg, tout=out_avg), 1.0, (1.0 + fan) * (1.0 + retry + 0.10)),
             ("cache_off", dict(tin=in_avg, tout=out_avg), 1.0, "nocache")]
    for name, tk, vol, special in cases:
        if special == "nocache":
            per_req = plan.per_request(tk["tin"], tk["tout"], cache_on=False)
        elif special is not None:
            per_req = plan.per_request(tk["tin"], tk["tout"], calls_mult=special)
        else:
            per_req = plan.per_request(tk["tin"], tk["tout"])
        monthly = per_req * rpd * vol * days
        sens.append({"case": name, "monthly": money(monthly), "delta_vs_expected": money(monthly - base),
                     "ratio_vs_expected": round(monthly / base, 3) if base else None})
    report["sensitivity"] = sens
    comparison = []
    for other, entry in table["models"].items():
        scratch_errors, scratch_warnings = [], []
        pr, _ = check_prices(table, other, scratch_errors, scratch_warnings, today)
        if pr is None:
            continue
        other_plan = Plan(pr, {"prefix_share": share}, plan.o, plan.calls_mult)
        comparison.append({"model": other, "expected_monthly": money(other_plan.per_request(in_avg, out_avg) * rpd * days)})
    report["comparison"] = sorted(comparison, key=lambda r: r["expected_monthly"])
    report["ok"] = True
    return report, token_est


def main(argv):
    args = list(argv)
    sample_path = None
    today = datetime.date.today()
    for flag in ("--sample", "--today"):
        if flag in args:
            i = args.index(flag)
            if i + 1 >= len(args):
                print(f"error: {flag} needs a value", file=sys.stderr)
                return 2
            value = args[i + 1]
            del args[i:i + 2]
            if flag == "--sample":
                sample_path = value
            else:
                try:
                    today = datetime.date.fromisoformat(value)
                except ValueError:
                    print("error: --today must be YYYY-MM-DD", file=sys.stderr)
                    return 2
    if len(args) != 1:
        print("usage: estimate_cost.py spec.json [--sample prompt.txt] [--today YYYY-MM-DD]", file=sys.stderr)
        return 2
    spec_path = args[0]
    spec = load_json(spec_path)
    if not isinstance(spec, dict):
        print("error: the spec must be a JSON object", file=sys.stderr)
        return 2
    spec_dir = os.path.dirname(os.path.abspath(spec_path))
    sample_path = sample_path or spec.get("sample_file")
    sample_text = None
    if sample_path:
        full = sample_path if os.path.isabs(sample_path) else os.path.join(spec_dir, sample_path)
        if not os.path.exists(full) and os.path.exists(sample_path):
            full = sample_path
        try:
            with open(full, encoding="utf-8", errors="replace") as fh:
                sample_text = fh.read()
        except OSError as exc:
            print(f"error: cannot read sample file {sample_path}: {exc}", file=sys.stderr)
            return 2
    report, token_est = build_report(spec, sample_text, today, spec_dir)
    report["token_estimate"] = token_est
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
