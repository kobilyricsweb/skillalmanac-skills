#!/usr/bin/env python3
"""Check the arithmetic of invoices, quotes and supplier bills with exact decimal maths.

Usage:
    python check_invoices.py INPUT.json|INPUT.csv --rounding {line,total,line_tax}
        [--mode {half_up,half_even,down}] [--places N] [--currency EUR]
        [--check-sequence] [--as-of YYYY-MM-DD]
        [--output REPORT.json [--force]]

What it reads: the one input file (JSON or CSV, see references/issue-codes.md and SKILL.md
for the field names). What it writes: the strict-JSON report to stdout, and only when
--output is given, to that one file. It never writes to the input path, even with --force.
It uses the standard library only, no network, no clock (dates are read from the input;
--as-of supplies "today" when you want overdue arithmetic).

It checks arithmetic only. It never decides which tax rate is right, whether a document is
legally valid, or whether a claimed deduction is allowed. Tax rates are whatever the file
says, read as percent (20 means 20%).

Exit codes: 0 no error-level issue (verdict pass or review); 1 at least one error-level
issue (verdict fail); 2 usage problem, unreadable input, or refused output path.
"""
import argparse
import calendar
import csv
import datetime
import io
import json
import os
import re
import sys
from decimal import (ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal,
                     localcontext)

# Largest input read, in bytes. Invoices are small; this guards against a wrong file.
MAX_BYTES = 5_000_000
# Working precision for Decimal. 50 digits keeps every product and quotient of
# realistic amounts exact, so ties such as x.xx5 are never blurred by float error.
PRECISION = 50
MODES = {"half_up": ROUND_HALF_UP, "half_even": ROUND_HALF_EVEN, "down": ROUND_DOWN}
METHODS = ("line", "total", "line_tax")
# ISO 4217 minor units that are not 2. Currencies not listed here use 2 places.
ZERO_PLACES = {"JPY", "KRW", "VND", "CLP", "ISK", "UGX", "PYG", "RWF", "XAF", "XOF",
               "BIF", "DJF", "GNF", "KMF", "VUV", "XPF"}
THREE_PLACES = {"BHD", "IQD", "JOD", "KWD", "LYD", "OMR", "TND"}
# Cap on missing numbers listed for one gap, so a typo such as 1 and 999999 stays readable.
GAP_LIST_CAP = 20
INVOICE_KEYS = {"number", "supplier", "issue_date", "due_date", "terms", "currency", "type",
                "tax_rate", "discount_percent", "discount_amount", "prices_include_tax",
                "rounding", "stated_subtotal", "stated_discount", "stated_tax",
                "stated_total", "lines"}
LINE_KEYS = {"description", "quantity", "unit_price", "discount_percent", "tax_rate",
             "line_total", "currency"}
CSV_HEADER_FIELDS = ("supplier", "issue_date", "due_date", "terms", "currency", "type",
                     "discount_percent", "discount_amount", "prices_include_tax",
                     "stated_subtotal", "stated_discount", "stated_tax", "stated_total")
CSV_COLUMNS = {"invoice_number", "description", "quantity", "unit_price",
               "line_discount_percent", "tax_rate", "line_total"} | set(CSV_HEADER_FIELDS)
NUM_RE = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)")


class InputError(Exception):
    """A problem with the input file or options; reported with exit code 2."""


def issue(sev, code, message, field=None, line=None):
    return {"severity": sev, "code": code, "field": field, "line": line, "message": message}


def parse_num(value):
    """Return (Decimal or None, error text or None). (None, None) means absent."""
    if value is None:
        return None, None
    if isinstance(value, bool):
        return None, "a true/false value is not a number"
    if isinstance(value, Decimal):
        d = value
    elif isinstance(value, int):
        d = Decimal(value)
    else:
        s = str(value).strip()
        if s == "":
            return None, None
        if not NUM_RE.fullmatch(s):
            return None, ("'%s' is not a plain number (no thousands separators, currency "
                          "symbols or exponents)" % s[:40])
        d = Decimal(s)
    if not d.is_finite():
        return None, "value is not finite"
    return d, None


def parse_date(value):
    """Return (date or None, error text or None). Strict YYYY-MM-DD only."""
    if value is None:
        return None, None
    s = str(value).strip()
    if s == "":
        return None, None
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return None, "'%s' is not in YYYY-MM-DD form" % s[:30]
    try:
        return datetime.date.fromisoformat(s), None
    except ValueError:
        return None, "'%s' is not a real calendar date" % s


def parse_terms(text):
    """Map a payment-terms string to a dict, or None when it is not understood."""
    t = re.sub(r"\s+", " ", str(text).strip().lower())
    if t == "":
        return None
    if re.fullmatch(r"(?:due )?(?:on|upon) receipt|immediate(?:ly)?|due now", t):
        return {"kind": "net", "days": 0}
    m = re.fullmatch(r"(?:(\d+(?:\.\d+)?)/(\d+) )?net ?(\d+)(?: days?)?", t)
    if m:
        out = {"kind": "net", "days": int(m.group(3))}
        if m.group(1):
            out["early_percent"] = Decimal(m.group(1))
            out["early_days"] = int(m.group(2))
        return out
    m = re.fullmatch(r"(\d+) days?", t)
    if m:
        return {"kind": "net", "days": int(m.group(1))}
    m = re.fullmatch(r"(?:net )?eom(?: ?\+? ?(\d+))?(?: days?)?", t)
    if m:
        return {"kind": "eom", "days": int(m.group(1) or 0)}
    return None


def due_from_terms(issue_date, terms):
    if terms["kind"] == "eom":
        last = calendar.monthrange(issue_date.year, issue_date.month)[1]
        base = datetime.date(issue_date.year, issue_date.month, last)
    else:
        base = issue_date
    return base + datetime.timedelta(days=terms["days"])


def fmt(d, places=None):
    """Decimal to a plain string. With places, quantize first (computed money)."""
    if d is None:
        return None
    if places is not None:
        d = d.quantize(Decimal(1).scaleb(-places))
    s = format(d, "f")
    return "0" + s[1:] if s.startswith(".") else s


def norm_number(s):
    return re.sub(r"[^0-9A-Z]", "", str(s).upper())


def norm_supplier(s):
    return re.sub(r"[^\w]+", " ", str(s).casefold()).strip()


def currency_places(code):
    if code in ZERO_PLACES:
        return 0
    if code in THREE_PLACES:
        return 3
    return 2


def compute(nets_exact, rates, disc_pct, disc_amt, method, q, mode):
    """Exact totals under one rounding method. Returns Decimals (tax/total None if a rate is unknown)."""
    def rnd(x):
        return x.quantize(q, rounding=mode)

    nets = nets_exact if method == "total" else [rnd(n) for n in nets_exact]
    subtotal = sum(nets, Decimal(0))
    if disc_amt is not None:
        disc = disc_amt
    elif disc_pct is not None:
        disc = subtotal * disc_pct / 100
    else:
        disc = Decimal(0)
    if method != "total":
        disc = rnd(disc)
    base = subtotal - disc
    tax = None
    if all(r is not None for r in rates):
        tax = Decimal(0)
        if method == "line_tax":
            for n, r in zip(nets, rates):
                b = n if disc == 0 else ((n * base) / subtotal if subtotal != 0 else Decimal(0))
                tax += rnd(b * r / 100)
        else:
            groups = {}
            for n, r in zip(nets, rates):
                groups[r] = groups.get(r, Decimal(0)) + n
            for r, g in groups.items():
                if len(groups) == 1:
                    b = base
                else:
                    b = (g * base) / subtotal if subtotal != 0 else Decimal(0)
                t = b * r / 100
                tax += rnd(t) if method == "line" else t
    total = None if tax is None else subtotal - disc + tax
    if method == "total":
        subtotal, disc = rnd(subtotal), rnd(disc)
        tax = None if tax is None else rnd(tax)
        total = None if total is None else rnd(total)
    return {"subtotal": subtotal, "discount": disc, "tax": tax, "total": total,
            "base": base, "nets": [rnd(n) for n in nets_exact]}


def grade(stated, computed, unit):
    """Return (delta, severity or None). One minor unit or less is info; more is error."""
    delta = stated - computed
    if delta == 0:
        return delta, None
    return delta, ("info" if abs(delta) <= unit else "error")


def process_invoice(index, raw, defaults, as_of):
    issues = []
    add = lambda *a, **k: issues.append(issue(*a, **k))  # noqa: E731
    state = {"broken": False}

    def num(field, value, line=None):
        d, err = parse_num(value)
        if err:
            add("error", "unparseable_number", "%s: %s" % (field, err), field, line)
            state["broken"] = True
        return d

    for key in raw:
        if key not in INVOICE_KEYS and key != "_notes":
            add("warning", "unknown_field", "field '%s' is not recognised and was ignored" % key, key)
    for note in raw.get("_notes", []):
        add("warning", "inconsistent_field_across_rows", note)

    number = str(raw.get("number") or "").strip()
    supplier = str(raw.get("supplier") or "").strip()
    if not number:
        add("warning", "missing_number", "no invoice number; duplicate and sequence checks skipped", "number")
    inv_type = str(raw.get("type") or "invoice").strip().lower()
    if inv_type not in ("invoice", "credit_note"):
        add("warning", "unknown_type", "type '%s' is not invoice or credit_note; treated as invoice" % inv_type[:30], "type")
        inv_type = "invoice"

    currency = str(raw.get("currency") or defaults["currency"] or "").strip().upper()
    if not currency:
        add("warning", "currency_missing", "no currency given for this invoice or on the command line; 2 decimal places assumed", "currency")
    elif not re.fullmatch(r"[A-Z]{3}", currency):
        add("error", "invalid_currency", "currency '%s' is not a three-letter code" % currency[:12], "currency")

    rcfg = raw.get("rounding") if isinstance(raw.get("rounding"), dict) else {}
    method = rcfg.get("method") or defaults["method"]
    mode_name = rcfg.get("mode") or defaults["mode"]
    places = rcfg.get("places")
    places = defaults["places"] if places in (None, "") else places
    if method not in METHODS:
        add("error", "invalid_rounding_setting", "rounding method '%s' is not one of %s" % (method, ", ".join(METHODS)), "rounding")
        method = defaults["method"]
    if mode_name not in MODES:
        add("error", "invalid_rounding_setting", "rounding mode '%s' is not one of %s" % (mode_name, ", ".join(MODES)), "rounding")
        mode_name = defaults["mode"]
    if places is None:
        places = currency_places(currency)
    try:
        places = int(str(places))
        if not 0 <= places <= 6:
            raise ValueError
    except ValueError:
        add("error", "invalid_rounding_setting", "places must be a whole number from 0 to 6", "rounding")
        places = currency_places(currency)
    q = Decimal(1).scaleb(-places)
    mode = MODES[mode_name]

    with localcontext() as ctx:
        ctx.prec = PRECISION
        return _process(index, raw, add, issues, state, num, number, supplier, inv_type,
                        currency, method, mode_name, mode, places, q, as_of)


def _process(index, raw, add, issues, state, num, number, supplier, inv_type, currency,
             method, mode_name, mode, places, q, as_of):
    inv_rate = num("tax_rate", raw.get("tax_rate"))
    disc_pct = num("discount_percent", raw.get("discount_percent"))
    disc_amt = num("discount_amount", raw.get("discount_amount"))
    stated = {k: num("stated_" + k, raw.get("stated_" + k)) for k in ("subtotal", "discount", "tax", "total")}
    incl = str(raw.get("prices_include_tax") or "").strip().lower() in ("true", "yes", "1", "y")
    if disc_pct is not None and disc_amt is not None:
        add("error", "conflicting_discount_inputs", "both discount_percent and discount_amount were given; give one", "discount")
        state["broken"] = True
    if disc_pct is not None and not 0 <= disc_pct <= 100:
        add("error", "invalid_percent", "discount_percent %s is outside 0 to 100" % fmt(disc_pct), "discount_percent")
        state["broken"] = True
    if inv_rate is not None and not 0 <= inv_rate <= 100:
        add("error", "invalid_tax_rate", "tax_rate %s is outside 0 to 100" % fmt(inv_rate), "tax_rate")
        state["broken"] = True

    lines = raw.get("lines")
    if not isinstance(lines, list) or not lines:
        add("error", "no_lines", "the invoice has no lines", "lines")
        lines = []
        state["broken"] = True

    line_out, nets_exact, rates, seen_rates, seen_keys = [], [], [], set(), {}
    line_currencies = {}
    for i, ln in enumerate(lines, 1):
        if not isinstance(ln, dict):
            add("error", "line_incomplete", "line is not an object", "lines", i)
            state["broken"] = True
            continue
        for key in ln:
            if key not in LINE_KEYS:
                add("warning", "unknown_field", "line field '%s' is not recognised and was ignored" % key, key, i)
        qty = num("quantity", ln.get("quantity"), i)
        price = num("unit_price", ln.get("unit_price"), i)
        ldp = num("discount_percent", ln.get("discount_percent"), i)
        lrate = num("tax_rate", ln.get("tax_rate"), i)
        lstated = num("line_total", ln.get("line_total"), i)
        lcur = str(ln.get("currency") or "").strip().upper()
        if lcur:
            line_currencies.setdefault(lcur, i)
        entry = {"line": i, "description": str(ln.get("description") or ""),
                 "quantity": fmt(qty), "unit_price": fmt(price), "computed_net": None,
                 "stated_net": fmt(lstated), "delta": None}
        line_out.append(entry)
        if qty is None or price is None:
            if ln.get("quantity") in (None, "") or ln.get("unit_price") in (None, ""):
                add("error", "line_incomplete", "quantity and unit_price are both required", "lines", i)
            state["broken"] = True
            continue
        if ldp is not None and not 0 <= ldp <= 100:
            add("error", "invalid_percent", "line discount_percent %s is outside 0 to 100" % fmt(ldp), "discount_percent", i)
            state["broken"] = True
            continue
        rate = lrate if lrate is not None else inv_rate
        if rate is not None and not 0 <= rate <= 100:
            add("error", "invalid_tax_rate", "tax_rate %s is outside 0 to 100" % fmt(rate), "tax_rate", i)
            state["broken"] = True
            continue
        if rate is not None and 0 < rate < 1 and rate not in seen_rates:
            add("warning", "tax_rate_fraction_suspected",
                "tax_rate %s is read as %s percent; if you meant a fraction, give the percent (for example 20)" % (fmt(rate), fmt(rate)),
                "tax_rate", i)
        if rate is not None:
            seen_rates.add(rate)
        if qty < 0 and inv_type == "invoice":
            add("error", "negative_quantity_not_credit_note", "negative quantity on a document not marked credit_note", "quantity", i)
        if qty == 0:
            add("warning", "zero_quantity", "quantity is zero", "quantity", i)
        if price < 0:
            add("warning", "negative_unit_price", "negative unit price (discount line or error)", "unit_price", i)
        net = qty * price * (100 - (ldp or Decimal(0))) / 100
        nets_exact.append(net)
        rates.append(rate)
        shown = net.quantize(q, rounding=mode)
        entry["computed_net"] = fmt(shown, places)
        if lstated is not None:
            delta, sev = grade(lstated, shown, q)
            entry["delta"] = fmt(delta)
            if sev:
                add(sev, "line_total_mismatch", "stated %s, computed %s (delta %s)" % (fmt(lstated), fmt(shown, places), fmt(delta)), "line_total", i)
        desc = re.sub(r"\s+", " ", entry["description"].casefold()).strip()
        if desc:
            key = (desc, qty, price, ldp or Decimal(0))
            if key in seen_keys:
                add("warning", "duplicate_line", "same description, quantity and price as line %d" % seen_keys[key], "lines", i)
            else:
                seen_keys[key] = i

    if currency:
        for lc, first in sorted(line_currencies.items(), key=lambda kv: kv[1]):
            if lc != currency:
                add("error", "mixed_currency_in_invoice", "line currency %s differs from invoice currency %s" % (lc, currency), "currency", first)

    result = {"index": index, "number": number, "supplier": supplier, "type": inv_type,
              "currency": currency or None,
              "rounding": {"method": method, "mode": mode_name, "places": places},
              "issue_date": None, "due_date": None, "computed_due_date": None, "due_basis": None,
              "days_until_due": None, "early_payment": None,
              "lines": line_out,
              "computed_subtotal": None, "computed_discount": None, "computed_tax": None,
              "computed_total": None, "total_basis": None,
              "stated_subtotal": fmt(stated["subtotal"]), "stated_discount": fmt(stated["discount"]),
              "stated_tax": fmt(stated["tax"]), "stated_total": fmt(stated["total"]),
              "delta": None, "issues": issues}

    # Totals
    comp = None
    if state["broken"]:
        add("error", "invoice_not_computable", "totals were not computed because an input above is missing or invalid")
    elif incl:
        add("warning", "unsupported_prices_include_tax", "prices_include_tax is not supported; lines checked, totals not computed", "prices_include_tax")
    else:
        comp = compute(nets_exact, rates, disc_pct, disc_amt, method, q, mode)
        tax_known = comp["tax"] is not None
        if not tax_known:
            add("warning", "tax_rate_missing", "no tax rate supplied for at least one line; tax not computed", "tax_rate")
        d_given = disc_pct is not None or disc_amt is not None
        out_tax, out_total = comp["tax"], comp["total"]
        basis = "computed"
        if not tax_known and stated["tax"] is not None:
            out_tax = stated["tax"]
            out_total = comp["subtotal"] - comp["discount"] + stated["tax"]
            if method == "total":
                out_total = out_total.quantize(q, rounding=mode)
            basis = "stated_tax"
        elif not tax_known:
            out_total, basis = None, "unknown_tax"
        result["computed_subtotal"] = fmt(comp["subtotal"], places)
        result["computed_discount"] = fmt(comp["discount"], places)
        result["computed_tax"] = fmt(out_tax, places) if tax_known else None
        result["computed_total"] = fmt(out_total, places)
        result["total_basis"] = basis
        for fld, got in (("subtotal", comp["subtotal"]), ("discount", comp["discount"]), ("tax", comp["tax"])):
            st = stated[fld]
            if st is None or got is None:
                continue
            if fld == "discount" and not d_given:
                if st != 0:
                    add("warning", "discount_not_supplied", "stated discount %s but no discount_percent or discount_amount was supplied" % fmt(st), "stated_discount")
                continue
            delta, sev = grade(st, got, q)
            if sev:
                add(sev, fld + "_mismatch", "stated %s, computed %s (delta %s)" % (fmt(st), fmt(got, places), fmt(delta)), "stated_" + fld)
            if fld == "tax" and sev == "error":
                groups = set(r for r in rates if r is not None)
                if len(groups) == 1 and comp["base"] != 0:
                    implied = (st * 100 / comp["base"]).quantize(Decimal("0.01"))
                    add("info", "stated_tax_implies_rate", "stated tax over the computed base is %s percent; the rate supplied was %s (arithmetic only, not a view on which rate applies)" % (fmt(implied), fmt(next(iter(groups)))), "stated_tax")
        if stated["total"] is not None and out_total is not None:
            delta, sev = grade(stated["total"], out_total, q)
            result["delta"] = fmt(delta)
            if sev:
                add(sev, "total_mismatch", "stated %s, computed %s (delta %s)" % (fmt(stated["total"]), fmt(out_total, places), fmt(delta)), "stated_total")
            if delta != 0 and tax_known:
                for other in METHODS:
                    if other == method:
                        continue
                    alt = compute(nets_exact, rates, disc_pct, disc_amt, other, q, mode)["total"]
                    if alt is not None and alt.quantize(q, rounding=mode) == stated["total"]:
                        add("info", "matches_other_rounding", "stated total equals the total under rounding method '%s'; confirm which method the issuer used" % other, "stated_total")
        elif stated["total"] is None:
            add("info", "stated_total_missing", "no stated total to compare with", "stated_total")
        if inv_type == "credit_note" and out_total is not None and out_total > 0:
            add("info", "credit_note_positive_total", "credit note total is positive; some systems show credit notes unsigned", "type")

    _dates(raw, result, issues, add, comp, as_of, places)
    return result


def _dates(raw, result, issues, add, comp, as_of, places):
    issue_d, err = parse_date(raw.get("issue_date"))
    if err:
        add("error", "invalid_date", "issue_date: " + err, "issue_date")
    due_d, err = parse_date(raw.get("due_date"))
    if err:
        add("error", "invalid_date", "due_date: " + err, "due_date")
    result["issue_date"] = issue_d.isoformat() if issue_d else None
    result["due_date"] = due_d.isoformat() if due_d else None
    terms = None
    if str(raw.get("terms") or "").strip():
        terms = parse_terms(raw.get("terms"))
        if terms is None:
            add("warning", "terms_unparsed", "payment terms '%s' not understood; use 'net 30', 'eom 30', 'due on receipt' or '2/10 net 30'" % str(raw.get("terms"))[:40], "terms")
    computed_due = None
    if terms and issue_d:
        computed_due = due_from_terms(issue_d, terms)
        result["computed_due_date"] = computed_due.isoformat()
    elif terms and not issue_d and not err:
        add("warning", "terms_need_issue_date", "terms were given but issue_date is missing", "issue_date")
    if issue_d and due_d and due_d < issue_d:
        add("error", "due_before_issue", "due date %s is before issue date %s" % (due_d, issue_d), "due_date")
    if due_d and computed_due and due_d != computed_due:
        add("warning", "due_date_mismatch", "stated due date %s, terms give %s (%+d days)" % (due_d, computed_due, (due_d - computed_due).days), "due_date")
    effective = due_d or computed_due
    if effective:
        result["due_basis"] = "stated" if due_d else "terms"
        if effective.weekday() >= 5:
            add("info", "due_on_weekend", "due date %s is a %s; no business-day shift is applied" % (effective, effective.strftime("%A")), "due_date")
        if as_of:
            result["days_until_due"] = (effective - as_of).days
    if terms and terms.get("early_percent") is not None and issue_d:
        by = issue_d + datetime.timedelta(days=terms["early_days"])
        ep = {"discount_percent": fmt(terms["early_percent"]), "pay_by": by.isoformat(),
              "discount_on_total": None, "discount_on_pretax_base": None}
        if comp is not None and result["computed_total"] is not None:
            q = Decimal(1).scaleb(-places)
            with localcontext() as ctx:
                ctx.prec = PRECISION
                total = Decimal(result["computed_total"])
                base = comp["subtotal"] - comp["discount"]
                ep["discount_on_total"] = fmt((total * terms["early_percent"] / 100).quantize(q, rounding=ROUND_HALF_UP))
                ep["discount_on_pretax_base"] = fmt((base * terms["early_percent"] / 100).quantize(q, rounding=ROUND_HALF_UP))
        result["early_payment"] = ep


def cross_checks(results, check_sequence):
    file_issues, gaps = [], []
    seen_num, seen_pay = {}, {}
    for r in results:
        if not r["number"]:
            continue
        key = (norm_supplier(r["supplier"]), norm_number(r["number"]))
        if key in seen_num:
            first = results[seen_num[key]]
            r["issues"].append(issue("error", "duplicate_invoice_number", "number %s from the same supplier already appears as invoice #%d" % (r["number"], first["index"])))
        else:
            seen_num[key] = r["index"] - 1
    by_number = {}
    for r in results:
        if r["number"] and r["supplier"]:
            by_number.setdefault(norm_number(r["number"]), []).append(r)
    for num, group in by_number.items():
        suppliers = {norm_supplier(g["supplier"]) for g in group}
        if len(suppliers) > 1:
            for g in group[1:]:
                if norm_supplier(g["supplier"]) != norm_supplier(group[0]["supplier"]):
                    g["issues"].append(issue("info", "same_number_other_supplier", "number %s is also used by supplier '%s'" % (g["number"], group[0]["supplier"][:40])))
    for r in results:
        amount = r["stated_total"] if r["stated_total"] is not None else r["computed_total"]
        if not r["supplier"] or not r["issue_date"] or amount is None:
            continue
        key = (norm_supplier(r["supplier"]), r["issue_date"], Decimal(amount))
        if key in seen_pay:
            first = results[seen_pay[key]]
            if norm_number(first["number"]) != norm_number(r["number"]):
                r["issues"].append(issue("warning", "possible_double_billing", "same supplier, issue date and amount (%s) as invoice #%d with a different number" % (amount, first["index"])))
        else:
            seen_pay[key] = r["index"] - 1
    cur = {r["currency"] for r in results if r["currency"]}
    if len(cur) > 1:
        file_issues.append(issue("warning", "mixed_currencies_in_file", "currencies in this file: %s; totals are reported per currency and never added together" % ", ".join(sorted(cur))))
    if check_sequence:
        groups = {}
        for r in results:
            if r["type"] != "invoice" or not r["number"]:
                continue
            m = re.fullmatch(r"(.*?)(\d+)", r["number"].strip().upper())
            if m:
                groups.setdefault((norm_supplier(r["supplier"]), m.group(1)), []).append((int(m.group(2)), len(m.group(2))))
        for (sup, prefix), items in sorted(groups.items()):
            nums = sorted({n for n, _ in items})
            widths = {w for _, w in items}
            width = widths.pop() if len(widths) == 1 else 0
            for a, b in zip(nums, nums[1:]):
                if b - a > 1:
                    count = b - a - 1
                    listed = [prefix + str(n).zfill(width) for n in range(a + 1, min(b, a + 1 + GAP_LIST_CAP))]
                    gaps.append({"supplier": sup, "prefix": prefix, "after": prefix + str(a).zfill(width),
                                 "before": prefix + str(b).zfill(width), "missing_count": count, "missing": listed})
                    file_issues.append(issue("warning", "sequence_gap", "%d number(s) missing between %s and %s" % (count, prefix + str(a).zfill(width), prefix + str(b).zfill(width))))
    return file_issues, gaps


def load_json(text):
    def reject(name):
        raise InputError("JSON constant %s is not allowed" % name)
    try:
        data = json.loads(text, parse_float=Decimal, parse_constant=reject)
    except ValueError as exc:
        raise InputError("input is not valid JSON: %s" % exc)
    file_cfg = {}
    if isinstance(data, dict):
        invoices = data.get("invoices")
        file_cfg = {k: data[k] for k in ("currency", "rounding") if k in data}
    else:
        invoices = data
    if not isinstance(invoices, list) or not invoices:
        raise InputError("JSON must be a list of invoices or an object with a non-empty 'invoices' list")
    out = []
    for i, inv in enumerate(invoices, 1):
        if not isinstance(inv, dict):
            raise InputError("invoice #%d is not an object" % i)
        out.append(inv)
    return out, file_cfg, []


def load_csv(text):
    first = text.splitlines()[0] if text.strip() else ""
    delim = max((",", ";", "\t"), key=first.count)
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    if not reader.fieldnames:
        raise InputError("CSV has no header row")
    names = {}
    for f in reader.fieldnames:
        names[f] = re.sub(r"\s+", "_", f.strip().lower())
    for need in ("quantity", "unit_price"):
        if need not in names.values():
            raise InputError("CSV needs a '%s' column; columns found: %s" % (need, ", ".join(sorted(names.values()))))
    file_issues = []
    extra = sorted(set(names.values()) - CSV_COLUMNS)
    if extra:
        file_issues.append(issue("warning", "unknown_column", "CSV columns ignored: %s" % ", ".join(extra)))
    invoices, cur, cur_key = [], None, None
    for row in reader:
        r = {names[k]: (v if v is not None else "") for k, v in row.items() if k in names}
        if not any(str(v).strip() for v in r.values()):
            continue
        number, supplier = r.get("invoice_number", "").strip(), r.get("supplier", "").strip()
        key = (norm_supplier(supplier), norm_number(number))
        continuation = cur is not None and not number and not supplier
        if cur is None or (key != cur_key and not continuation):
            cur ={"number": number, "supplier": supplier, "lines": [], "_notes": []}
            invoices.append(cur)
            cur_key = key
        for f in CSV_HEADER_FIELDS:
            val = r.get(f, "").strip()
            if not val:
                continue
            if f not in cur:
                cur[f] = val
            elif cur[f] != val:
                cur["_notes"].append("column '%s' differs between rows (%s vs %s); the first value was used" % (f, cur[f][:20], val[:20]))
        line = {"description": r.get("description", ""), "quantity": r.get("quantity", ""),
                "unit_price": r.get("unit_price", ""), "discount_percent": r.get("line_discount_percent", ""),
                "tax_rate": r.get("tax_rate", ""), "line_total": r.get("line_total", ""),
                "currency": r.get("currency", "")}
        header_only = not any(str(line[k]).strip() for k in ("description", "quantity", "unit_price", "discount_percent", "tax_rate", "line_total"))
        if not header_only:
            cur["lines"].append(line)
    if not invoices:
        raise InputError("CSV has no data rows")
    return invoices, {}, file_issues


def read_input(path, fmt_name):
    try:
        size = os.path.getsize(path)
    except OSError as exc:
        raise InputError("cannot read '%s': %s" % (path, exc.strerror or exc))
    if size == 0:
        raise InputError("'%s' is empty" % path)
    if size > MAX_BYTES:
        raise InputError("'%s' is larger than %d bytes; split it" % (path, MAX_BYTES))
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise InputError("cannot read '%s' as UTF-8 text: %s" % (path, exc))
    if fmt_name == "auto":
        ext = os.path.splitext(path)[1].lower()
        if ext == ".json" or (ext != ".csv" and text.lstrip()[:1] in "[{"):
            fmt_name = "json"
        else:
            fmt_name = "csv"
    return load_json(text) if fmt_name == "json" else load_csv(text)


def same_file(a, b):
    if os.path.realpath(a) == os.path.realpath(b):
        return True
    try:
        return os.path.exists(a) and os.path.exists(b) and os.path.samefile(a, b)
    except OSError:
        return False


def build_parser():
    p = argparse.ArgumentParser(description="Exact-decimal arithmetic check for invoices. Arithmetic only, never tax or legal advice.")
    p.add_argument("input")
    p.add_argument("--format", choices=("auto", "json", "csv"), default="auto")
    p.add_argument("--rounding", choices=METHODS, help="line = round each line net, tax per rate group; total = round once at the end; line_tax = round each line's tax. Required unless the JSON file sets it.")
    p.add_argument("--mode", choices=tuple(MODES), help="half_up (default), half_even or down")
    p.add_argument("--places", type=int, help="decimal places; default from the currency (2 unless zero- or three-decimal)")
    p.add_argument("--currency", help="default three-letter currency code for invoices that give none")
    p.add_argument("--check-sequence", action="store_true", help="report gaps in numeric invoice-number sequences (use for your own issued invoices)")
    p.add_argument("--as-of", help="YYYY-MM-DD used as today for days_until_due")
    p.add_argument("--output", help="write the report to this file as well as stdout; never the input path")
    p.add_argument("--force", action="store_true", help="allow --output to replace an existing file that is not the input")
    return p


def run(args):
    if args.output and same_file(args.output, args.input):
        raise InputError("refusing to write the report over the input file '%s'" % args.input)
    if args.output and os.path.exists(args.output) and not args.force:
        raise InputError("'%s' exists; use --force to replace it" % args.output)
    as_of = None
    if args.as_of:
        as_of, err = parse_date(args.as_of)
        if err or as_of is None:
            raise InputError("--as-of: " + (err or "empty"))
    invoices, file_cfg, file_issues = read_input(args.input, args.format)
    rcfg = file_cfg.get("rounding") if isinstance(file_cfg.get("rounding"), dict) else {}
    method = args.rounding or rcfg.get("method")
    if not method:
        raise InputError("a rounding method is required: pass --rounding line|total|line_tax (ask the user which the issuer uses) or set it in the JSON file")
    places = args.places if args.places is not None else rcfg.get("places")
    defaults = {"method": method, "mode": args.mode or rcfg.get("mode") or "half_up",
                "places": places, "currency": (args.currency or file_cfg.get("currency") or "")}
    defaults["currency"] = str(defaults["currency"]).strip().upper()
    if defaults["method"] not in METHODS or defaults["mode"] not in MODES:
        raise InputError("rounding method or mode in the file is not recognised")
    results = [process_invoice(i, raw, defaults, as_of) for i, raw in enumerate(invoices, 1)]
    more, gaps = cross_checks(results, args.check_sequence)
    file_issues = file_issues + more

    counts = {"error": 0, "warning": 0, "info": 0}
    for r in results:
        for it in r["issues"]:
            counts[it["severity"]] += 1
    for it in file_issues:
        counts[it["severity"]] += 1
    by_cur = {}
    with localcontext() as ctx:
        ctx.prec = PRECISION
        for r in results:
            slot = by_cur.setdefault(r["currency"] or "UNKNOWN", {"invoices": 0, "computed_total": Decimal(0), "stated_total": Decimal(0), "places": 0})
            slot["invoices"] += 1
            slot["places"] = max(slot["places"], r["rounding"]["places"])
            if r["computed_total"] is not None:
                slot["computed_total"] += Decimal(r["computed_total"])
            if r["stated_total"] is not None:
                slot["stated_total"] += Decimal(r["stated_total"])
    verdict = "fail" if counts["error"] else ("review" if counts["warning"] else "pass")
    report = {
        "tool": "check_invoices", "source": os.path.basename(args.input),
        "defaults": {"rounding": defaults["method"], "mode": defaults["mode"], "places": defaults["places"], "currency": defaults["currency"] or None},
        "invoices": results, "file_issues": file_issues, "sequence_gaps": gaps,
        "summary": {"invoices": len(results), "errors": counts["error"], "warnings": counts["warning"], "info": counts["info"], "verdict": verdict,
                    "by_currency": {c: {"invoices": s["invoices"], "computed_total": fmt(s["computed_total"], s["places"]), "stated_total": fmt(s["stated_total"], s["places"])} for c, s in sorted(by_cur.items())}},
    }
    text = json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text + "\n")
        print(json.dumps({"written": args.output, "summary": report["summary"]}, indent=2, ensure_ascii=True))
    else:
        print(text)
    return 1 if counts["error"] else 0


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except InputError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
