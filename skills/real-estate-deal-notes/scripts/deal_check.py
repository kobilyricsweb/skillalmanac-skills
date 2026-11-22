#!/usr/bin/env python3
"""Compute stated formulas from a property deal JSON and flag input problems.

Usage:
    python deal_check.py check <deal.json> [--today YYYY-MM-DD]
    python deal_check.py compare <deal1.json> <deal2.json> ... [--today YYYY-MM-DD]

Reads only the files named on the command line. Writes nothing. Uses no
network. Prints one strict JSON document to stdout (no NaN, no Infinity).

It is arithmetic on the supplied inputs. It never ranks, scores, rates or
recommends, and it never fills in a missing input with a guess.

Exit codes:
    0  ran; no flag of severity "error"
    1  ran; at least one flag of severity "error" (input problem)
    2  usage problem, unreadable file, or invalid JSON (error is printed as JSON)
"""
import json
import math
import os
import sys
from datetime import date

DISCLAIMER = ("Arithmetic on the supplied inputs only, not advice. "
              "Verify every figure and decision with a licensed professional.")

# Facts the file is stale after this many days (market figures move; 90 days is a
# working value, not a measured optimum).
STALE_AS_OF_DAYS = 90
# Individual source documents (rent roll, quote, listing) are allowed to be older.
STALE_SOURCE_DAYS = 180
# down_payment + loan_amount may differ from price by this share before flagging
# (rounding, seller credits). Beyond it the financing story needs a note.
FINANCING_TOLERANCE = 0.01
# An operating-expense ratio below this share of income usually means an omitted
# cost category; it is a prompt to look, not a finding.
LOW_OPEX_RATIO = 0.10
# Override debt service may differ from the computed amortisation by this share.
DEBT_SERVICE_TOLERANCE = 0.05
# Result ranges outside which the input is more likely a unit slip (monthly vs
# annual, percent vs fraction) than a real property. Input-error detection only.
YIELD_RANGE = (0.01, 0.30)
CAP_RANGE = (0.0, 0.25)
# compare: as_of dates further apart than this make the columns not like-for-like.
COMPARE_SPREAD_DAYS = 30

AREA_UNITS = ("sqft", "sqm")
DD_STATUS = ("open", "done", "blocked", "na")
KEY_SOURCED_FIELDS = ("purchase_price", "income.gross_scheduled_rent_annual",
                      "expenses.operating_expenses_annual")


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def get(d, path):
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def parse_date(v):
    if not isinstance(v, str):
        return None
    try:
        return date.fromisoformat(v)
    except ValueError:
        return None


def has_note(v):
    return isinstance(v, str) and v.strip() != ""


class Flags:
    def __init__(self):
        self.items = []

    def add(self, severity, code, field, message):
        self.items.append({"severity": severity, "code": code, "field": field, "message": message})

    def count(self, severity):
        return sum(1 for f in self.items if f["severity"] == severity)


def amortised_annual_payment(loan, rate, years):
    """Level monthly payment on a fully amortising loan, times 12."""
    n = int(round(years * 12))
    r = rate / 12.0
    if r == 0:
        return loan / n * 12.0
    pmt = loan * r / (1.0 - (1.0 + r) ** (-n))
    return pmt * 12.0


def r4(x):
    return None if x is None else round(x, 4)


def r2(x):
    return None if x is None else round(x, 2)


def analyse(deal, today):
    flags = Flags()
    not_computed = []
    if not isinstance(deal, dict):
        flags.add("error", "NOT_AN_OBJECT", "", "Top level of the deal file must be a JSON object.")
        return {"flags": flags, "results": {}, "not_computed": [], "deal": {}}

    # ---- required fields and units ------------------------------------
    def need_text(path):
        v = get(deal, path)
        if not has_note(v):
            flags.add("error", "MISSING_FIELD", path, "Required text field is missing or empty.")
        return v

    def need_num(path, lo=None, hi=None, required=True):
        v = get(deal, path)
        if v is None:
            if required:
                flags.add("error", "MISSING_FIELD", path, "Required number is missing.")
            return None
        if not is_num(v):
            flags.add("error", "NOT_A_NUMBER", path, "Must be a plain JSON number, not text or null.")
            return None
        if lo is not None and v < lo:
            flags.add("error", "OUT_OF_RANGE", path, "Value %s is below the minimum %s." % (v, lo))
            return None
        if hi is not None and v > hi:
            code = "RATE_NOT_FRACTION" if hi == 1 else "OUT_OF_RANGE"
            msg = ("Value %s is above %s. Rates are fractions (0.065 for 6.5 percent)." % (v, hi)
                   if hi == 1 else "Value %s is above the maximum %s." % (v, hi))
            flags.add("error", code, path, msg)
            return None
        return v

    need_text("property.address")
    need_text("property.type")
    cur = get(deal, "currency")
    if not (isinstance(cur, str) and len(cur) == 3 and cur.isalpha() and cur.isupper()):
        flags.add("error", "BAD_CURRENCY", "currency", "Use a 3-letter uppercase code such as USD.")
    as_of_raw = get(deal, "as_of")
    as_of = parse_date(as_of_raw)
    if as_of is None:
        flags.add("error", "BAD_DATE", "as_of", "Required date in YYYY-MM-DD form is missing or malformed.")

    price = need_num("purchase_price", lo=0.000001)
    gsr = need_num("income.gross_scheduled_rent_annual", lo=0)
    vac = need_num("income.vacancy_rate", lo=0, hi=1)
    other = need_num("income.other_income_annual", lo=0, required=False)
    opex = need_num("expenses.operating_expenses_annual", lo=0)
    closing = need_num("closing_costs", lo=0, required=False)
    reno = need_num("renovation_cost", lo=0, required=False)
    down = need_num("financing.down_payment", lo=0, required=False)
    loan = need_num("financing.loan_amount", lo=0, required=False)
    rate = need_num("financing.interest_rate", lo=0, hi=1, required=False)
    term = need_num("financing.term_years", lo=0.000001, required=False)
    ads_override = need_num("financing.annual_debt_service", lo=0, required=False)

    if get(deal, "property.area_value") is not None or get(deal, "property.area_unit") is not None:
        av = need_num("property.area_value", lo=0.000001, required=False)
        au = get(deal, "property.area_unit")
        if au not in AREA_UNITS:
            flags.add("error", "BAD_AREA_UNIT", "property.area_unit",
                      "Area unit must be one of %s." % ", ".join(AREA_UNITS))
        if av is None:
            flags.add("error", "MISSING_FIELD", "property.area_value", "Area unit given without a numeric area.")

    # ---- defaults that must be visible ---------------------------------
    if other is None and get(deal, "income.other_income_annual") is None:
        flags.add("info", "DEFAULTED_TO_ZERO", "income.other_income_annual", "Not supplied; treated as 0 in the arithmetic.")
        other = 0.0
    if closing is None and get(deal, "closing_costs") is None:
        flags.add("warn", "DEFAULTED_TO_ZERO", "closing_costs", "Not supplied; treated as 0, which lowers cash invested and raises cash-on-cash.")
        closing = 0.0
    if reno is None and get(deal, "renovation_cost") is None:
        flags.add("warn", "DEFAULTED_TO_ZERO", "renovation_cost", "Not supplied; treated as 0, which lowers cash invested and raises cash-on-cash.")
        reno = 0.0

    # ---- dates, sources, staleness -------------------------------------
    if as_of is not None:
        age = (today - as_of).days
        if age < 0:
            flags.add("warn", "FUTURE_DATE", "as_of", "as_of is %d days after the reference date." % (-age))
        elif age > STALE_AS_OF_DAYS:
            flags.add("warn", "STALE_AS_OF", "as_of", "Figures are %d days old (limit %d)." % (age, STALE_AS_OF_DAYS))

    sources = get(deal, "sources")
    sourced = set()
    if sources is None:
        sources = []
    if not isinstance(sources, list):
        flags.add("error", "BAD_SOURCES", "sources", "sources must be a list of {field, source, date}.")
        sources = []
    for i, s in enumerate(sources):
        where = "sources[%d]" % i
        if not isinstance(s, dict) or not has_note(s.get("field")) or not has_note(s.get("source")):
            flags.add("error", "BAD_SOURCE_ENTRY", where, "Each source needs text fields field and source.")
            continue
        sourced.add(s["field"])
        d = parse_date(s.get("date"))
        if d is None:
            flags.add("warn", "SOURCE_NO_DATE", where, "Source for %s has no valid YYYY-MM-DD date." % s["field"])
        else:
            sage = (today - d).days
            if sage < 0:
                flags.add("warn", "FUTURE_DATE", where, "Source date is %d days after the reference date." % (-sage))
            elif sage > STALE_SOURCE_DAYS:
                flags.add("warn", "STALE_SOURCE", where, "Source for %s is %d days old (limit %d)." % (s["field"], sage, STALE_SOURCE_DAYS))
    for f in KEY_SOURCED_FIELDS:
        if f not in sourced:
            flags.add("warn", "NO_SOURCE", f, "No entry in sources for this key input.")

    dd = get(deal, "due_diligence")
    dd_summary = {"total": 0, "open": 0, "done": 0, "blocked": 0, "na": 0, "overdue": 0}
    if dd is not None and not isinstance(dd, list):
        flags.add("error", "BAD_DUE_DILIGENCE", "due_diligence", "due_diligence must be a list of {item, owner, due, status}.")
        dd = None
    for i, it in enumerate(dd or []):
        where = "due_diligence[%d]" % i
        if not isinstance(it, dict) or not has_note(it.get("item")):
            flags.add("error", "BAD_DD_ENTRY", where, "Each entry needs a text field item.")
            continue
        dd_summary["total"] += 1
        status = it.get("status")
        if status not in DD_STATUS:
            flags.add("warn", "DD_BAD_STATUS", where, "status must be one of %s." % ", ".join(DD_STATUS))
            status = "open"
        dd_summary[status] += 1
        if status in ("open", "blocked"):
            if not has_note(it.get("owner")):
                flags.add("warn", "DD_NO_OWNER", where, "Open item '%s' has no owner." % it["item"])
            due = parse_date(it.get("due"))
            if due is None:
                flags.add("warn", "DD_NO_DATE", where, "Open item '%s' has no valid due date." % it["item"])
            elif due < today:
                dd_summary["overdue"] += 1
                flags.add("warn", "DD_OVERDUE", where, "Open item '%s' was due %s." % (it["item"], it["due"]))

    # ---- arithmetic ----------------------------------------------------
    res = {k: None for k in ("gross_yield", "effective_gross_income", "net_operating_income", "cap_rate",
                             "total_cash_invested", "annual_debt_service", "cash_flow_before_tax",
                             "cash_on_cash", "dscr")}
    core_ok = None not in (price, gsr, vac, opex) and other is not None
    if price is not None and gsr is not None:
        res["gross_yield"] = gsr / price
    else:
        not_computed.append({"metric": "gross_yield", "missing": [p for p, v in (("purchase_price", price), ("income.gross_scheduled_rent_annual", gsr)) if v is None]})
    egi = noi = None
    if core_ok:
        egi = gsr * (1.0 - vac) + other
        noi = egi - opex
        res["effective_gross_income"] = egi
        res["net_operating_income"] = noi
        res["cap_rate"] = noi / price
    else:
        miss = [p for p, v in (("purchase_price", price), ("income.gross_scheduled_rent_annual", gsr),
                               ("income.vacancy_rate", vac), ("expenses.operating_expenses_annual", opex)) if v is None]
        not_computed.append({"metric": "net_operating_income", "missing": miss})
        not_computed.append({"metric": "cap_rate", "missing": miss})

    ads = None
    if ads_override is not None:
        ads = ads_override
    elif None not in (loan, rate, term):
        ads = amortised_annual_payment(loan, rate, term)
    if ads_override is not None and None not in (loan, rate, term):
        calc = amortised_annual_payment(loan, rate, term)
        if calc > 0 and abs(ads_override - calc) / calc > DEBT_SERVICE_TOLERANCE:
            flags.add("warn", "DEBT_SERVICE_MISMATCH", "financing.annual_debt_service",
                      "Override %.2f differs from the amortised %.2f by more than %d percent." % (ads_override, calc, int(DEBT_SERVICE_TOLERANCE * 100)))
    res["annual_debt_service"] = ads
    if ads is None:
        not_computed.append({"metric": "annual_debt_service", "missing": [p for p, v in (("financing.loan_amount", loan), ("financing.interest_rate", rate), ("financing.term_years", term)) if v is None] or []})
        not_computed.append({"metric": "dscr", "missing": ["financing.annual_debt_service or loan_amount+interest_rate+term_years"]})
        not_computed.append({"metric": "cash_flow_before_tax", "missing": ["financing.annual_debt_service or loan_amount+interest_rate+term_years"]})
    elif noi is not None:
        res["cash_flow_before_tax"] = noi - ads
        res["dscr"] = (noi / ads) if ads > 0 else None
        if ads == 0:
            not_computed.append({"metric": "dscr", "missing": ["annual_debt_service is 0, ratio undefined"]})
    if down is not None and closing is not None and reno is not None:
        res["total_cash_invested"] = down + closing + reno
        if res["cash_flow_before_tax"] is not None:
            if res["total_cash_invested"] > 0:
                res["cash_on_cash"] = res["cash_flow_before_tax"] / res["total_cash_invested"]
            else:
                not_computed.append({"metric": "cash_on_cash", "missing": ["total_cash_invested is 0, ratio undefined"]})
    else:
        not_computed.append({"metric": "cash_on_cash", "missing": ["financing.down_payment"]})
        not_computed.append({"metric": "total_cash_invested", "missing": ["financing.down_payment"]})

    # ---- consistency checks --------------------------------------------
    if egi is not None and opex is not None:
        if opex > egi and not has_note(get(deal, "expenses.note")):
            flags.add("warn", "EXPENSES_EXCEED_INCOME", "expenses.operating_expenses_annual",
                      "Operating expenses %.2f exceed effective gross income %.2f and expenses.note is empty." % (opex, egi))
        if egi > 0 and opex / egi < LOW_OPEX_RATIO and not has_note(get(deal, "expenses.note")):
            flags.add("warn", "OPEX_RATIO_LOW", "expenses.operating_expenses_annual",
                      "Expenses are %.1f percent of income (below %d percent) and expenses.note is empty; check for omitted categories." % (100.0 * opex / egi, int(LOW_OPEX_RATIO * 100)))
    if vac == 0 and not has_note(get(deal, "income.note")):
        flags.add("warn", "VACANCY_ZERO", "income.vacancy_rate", "Vacancy is 0 and income.note is empty; state the basis (for example a signed lease on every unit).")
    if loan is not None and price is not None and loan > price:
        flags.add("error", "LOAN_EXCEEDS_PRICE", "financing.loan_amount", "Loan amount is larger than the purchase price.")
    if None not in (down, loan, price) and abs(down + loan - price) / price > FINANCING_TOLERANCE and not has_note(get(deal, "financing.note")):
        flags.add("warn", "FINANCING_MISMATCH", "financing",
                  "down_payment + loan_amount = %.2f differs from purchase_price %.2f by more than %d percent and financing.note is empty." % (down + loan, price, int(FINANCING_TOLERANCE * 100)))
    anyfin = [v for v in (loan, rate, term) if v is not None]
    if anyfin and len(anyfin) < 3 and ads_override is None:
        flags.add("warn", "FINANCING_INCOMPLETE", "financing", "loan_amount, interest_rate and term_years must all be given to amortise a payment.")
    if rate == 0 and loan:
        flags.add("info", "ZERO_RATE", "financing.interest_rate", "Rate is 0; payment is loan divided by months.")
    if res["gross_yield"] is not None and not (YIELD_RANGE[0] <= res["gross_yield"] <= YIELD_RANGE[1]):
        flags.add("warn", "RESULT_OUTSIDE_USUAL_RANGE", "gross_yield",
                  "gross_yield %.4f is outside %.2f to %.2f; check for monthly rent entered as annual or a price in the wrong unit." % (res["gross_yield"], YIELD_RANGE[0], YIELD_RANGE[1]))
    if res["cap_rate"] is not None and not (CAP_RANGE[0] <= res["cap_rate"] <= CAP_RANGE[1]):
        flags.add("warn", "RESULT_OUTSIDE_USUAL_RANGE", "cap_rate",
                  "cap_rate %.4f is outside %.2f to %.2f; check units and omitted or duplicated expenses." % (res["cap_rate"], CAP_RANGE[0], CAP_RANGE[1]))

    rounded = {k: (r4(v) if k in ("gross_yield", "cap_rate", "cash_on_cash", "dscr") else r2(v)) for k, v in res.items()}
    return {"flags": flags, "results": rounded, "not_computed": not_computed, "due_diligence": dd_summary, "deal": deal, "as_of": as_of_raw}


FORMULAS = {
    "gross_yield": "gross_scheduled_rent_annual / purchase_price",
    "effective_gross_income": "gross_scheduled_rent_annual * (1 - vacancy_rate) + other_income_annual",
    "net_operating_income": "effective_gross_income - operating_expenses_annual (debt service excluded)",
    "cap_rate": "net_operating_income / purchase_price",
    "annual_debt_service": "12 * level monthly payment on loan_amount at interest_rate/12 over term_years*12 months, or financing.annual_debt_service if given",
    "cash_flow_before_tax": "net_operating_income - annual_debt_service",
    "total_cash_invested": "down_payment + closing_costs + renovation_cost",
    "cash_on_cash": "cash_flow_before_tax / total_cash_invested",
    "dscr": "net_operating_income / annual_debt_service",
}


def load(path):
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def emit(obj):
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def fail(message):
    emit({"tool": "deal_check", "status": "usage_error", "error": message, "disclaimer": DISCLAIMER})
    return 2


def parse_args(argv):
    today = date.today()
    files = []
    i = 0
    while i < len(argv):
        if argv[i] == "--today":
            if i + 1 >= len(argv):
                return None, None, "--today needs a YYYY-MM-DD value."
            today = parse_date(argv[i + 1])
            if today is None:
                return None, None, "--today must be YYYY-MM-DD."
            i += 2
        else:
            files.append(argv[i])
            i += 1
    return today, files, None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not argv or argv[0] not in ("check", "compare"):
        return fail("Usage: deal_check.py check <deal.json> | compare <deal.json> <deal.json> ... [--today YYYY-MM-DD]")
    cmd = argv[0]
    today, files, err = parse_args(argv[1:])
    if err:
        return fail(err)
    if cmd == "check" and len(files) != 1:
        return fail("check takes exactly one deal file.")
    if cmd == "compare" and len(files) < 2:
        return fail("compare takes two or more deal files.")
    analyses = []
    for path in files:
        if not os.path.isfile(path):
            return fail("File not found: %s" % path)
        try:
            deal = load(path)
        except (OSError, ValueError) as exc:
            return fail("Cannot read %s as JSON: %s" % (path, exc))
        analyses.append((path, analyse(deal, today)))

    if cmd == "check":
        path, a = analyses[0]
        fl = a["flags"]
        out = {
            "tool": "deal_check", "command": "check", "file": os.path.basename(path),
            "reference_date": today.isoformat(), "as_of": a.get("as_of"),
            "status": "input_errors" if fl.count("error") else ("flags" if fl.count("warn") else "ok"),
            "formulas": FORMULAS, "results": a["results"], "not_computed": a["not_computed"],
            "due_diligence": a.get("due_diligence"),
            "flags": fl.items,
            "counts": {"error": fl.count("error"), "warn": fl.count("warn"), "info": fl.count("info")},
            "disclaimer": DISCLAIMER,
        }
        emit(out)
        return 1 if fl.count("error") else 0

    rows = []
    table_flags = Flags()
    errors = 0
    for path, a in analyses:
        deal = a["deal"] if isinstance(a["deal"], dict) else {}
        r = a["results"]
        errors += a["flags"].count("error")
        rows.append({
            "file": os.path.basename(path), "address": get(deal, "property.address"),
            "currency": get(deal, "currency"), "as_of": a.get("as_of"),
            "area_unit": get(deal, "property.area_unit"),
            "purchase_price": get(deal, "purchase_price") if is_num(get(deal, "purchase_price")) else None,
            "gross_yield": r.get("gross_yield"), "cap_rate": r.get("cap_rate"),
            "cash_on_cash": r.get("cash_on_cash"), "dscr": r.get("dscr"),
            "errors": a["flags"].count("error"), "warnings": a["flags"].count("warn"),
            "open_due_diligence": (a.get("due_diligence") or {}).get("open", 0) + (a.get("due_diligence") or {}).get("blocked", 0),
        })
    currencies = {r["currency"] for r in rows}
    if len(currencies) > 1:
        table_flags.add("error", "CURRENCY_MIXED", "currency", "Rows use different currencies (%s); amounts are not comparable." % ", ".join(sorted(str(c) for c in currencies)))
    units = {r["area_unit"] for r in rows if r["area_unit"]}
    if len(units) > 1:
        table_flags.add("warn", "AREA_UNIT_MIXED", "property.area_unit", "Rows use different area units (%s)." % ", ".join(sorted(units)))
    dates = [parse_date(r["as_of"]) for r in rows]
    dates = [d for d in dates if d]
    if len(dates) >= 2 and (max(dates) - min(dates)).days > COMPARE_SPREAD_DAYS:
        table_flags.add("warn", "AS_OF_SPREAD", "as_of", "as_of dates span %d days (limit %d); rows are not like-for-like in time." % ((max(dates) - min(dates)).days, COMPARE_SPREAD_DAYS))
    for r in rows:
        for k in ("gross_yield", "cap_rate", "cash_on_cash", "dscr"):
            if r[k] is None:
                table_flags.add("warn", "CELL_NOT_COMPUTED", r["file"] + ":" + k, "Not computed for this row; see check output for the missing inputs.")
    out = {
        "tool": "deal_check", "command": "compare", "reference_date": today.isoformat(),
        "order": "as given on the command line; not ranked, not scored",
        "formulas": FORMULAS, "rows": rows, "table_flags": table_flags.items,
        "status": "input_errors" if (errors or table_flags.count("error")) else ("flags" if table_flags.count("warn") or any(r["warnings"] for r in rows) else "ok"),
        "disclaimer": DISCLAIMER,
    }
    emit(out)
    return 1 if (errors or table_flags.count("error")) else 0


if __name__ == "__main__":
    sys.exit(main())
