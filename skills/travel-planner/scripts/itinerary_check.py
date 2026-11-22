#!/usr/bin/env python3
"""Validate a trip itinerary file (JSON) and print one strict JSON report.

Usage:
    python scripts/itinerary_check.py <itinerary.json>

Reads the one file given; writes nothing; no network. Standard library only.
Output: a single JSON object on stdout (no NaN, ASCII only).
Exit codes: 0 no errors (warnings allowed), 1 at least one error, 2 the file
could not be read or is not a JSON object.

Checks (finding codes in brackets):
  schema            [schema] malformed fields, bad times, bad dates, bad enums
  overlaps          [overlap] two timed blocks on one day share minutes
  pacing            [pacing_limit] more activities than the trip style allows
                    [long_day] scheduled non-meal hours above the style cap
                    [no_meal_block] a day with activities and no meal block
  transit buffers   [missing_transit_buffer] gap between two places is shorter
                    than travel time plus the default buffer
                    [missing_location] an item has no location; it is still
                    buffer-checked (area, else assumed a different place)
  facts             [unverified_fact] a fact is not marked verified
                    [verified_without_source] verified but no source or date
                    [stale_check] verified more than 30 days before the trip
                    [hours_not_listed] a timed activity has no hours fact
                    [price_not_listed] a paid item has no price fact
  budget            [over_budget] [thin_contingency] [missing_cost]
                    [mixed_currency]

The script never decides that a fact is true. It only reports which facts the
itinerary admits are still unchecked, so the agent must send them to the user.
"""
import json
import re
import sys
from datetime import date
from decimal import Decimal, InvalidOperation

TOOL_VERSION = "1.0.0"

# Maximum "activity" blocks per day by trip style. Meals and transit do not
# count. Reason: more than 2 big sights a day is the usual cause of skipped
# plans in a relaxed trip; 4 is the ceiling people sustain for a few days.
PACE_LIMIT = {"relaxed": 2, "balanced": 3, "packed": 4}
# Scheduled non-meal hours per day by style (activities plus transit blocks).
DAY_HOURS_CAP = {"relaxed": 6, "balanced": 8, "packed": 10}
# A day marked travel_day (arrival, departure, long transfer) loses one slot.
TRAVEL_DAY_PENALTY = 1
# Minimum minutes between two places, on top of any declared travel time.
BUFFER_SAME_AREA = 15   # walking, locating the entrance, a queue
BUFFER_OTHER_AREA = 30  # ticket machine, a missed connection, a wrong turn
# A verified fact older than this before the first trip day is flagged.
STALE_DAYS = 30
# Spend above this share of the budget leaves no room for surprises.
CONTINGENCY_FLOOR = Decimal("0.10")

KINDS = ("activity", "meal", "transit", "lodging", "other")
FACT_KINDS = ("hours", "price", "visa", "booking", "transport", "other")
CATEGORIES = ("lodging", "food", "activities", "transport", "other")
DOC_STATUS = ("have", "todo", "unverified")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


class Report:
    def __init__(self):
        self.findings = []
        self.to_verify = []

    def add(self, severity, code, message, day=None, item=None):
        self.findings.append({"severity": severity, "code": code,
                              "day": day, "item": item, "message": message})

    def err(self, code, message, day=None, item=None):
        self.add("error", code, message, day, item)

    def warn(self, code, message, day=None, item=None):
        self.add("warning", code, message, day, item)


def minutes(text):
    m = TIME_RE.match(text) if isinstance(text, str) else None
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def parse_date(text):
    try:
        return date.fromisoformat(text) if isinstance(text, str) and len(text) == 10 else None
    except ValueError:
        return None


def money(value):
    """Decimal from a JSON number; None if not a plain non-negative number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        d = Decimal(str(value))
    except InvalidOperation:
        return None
    return d if d.is_finite() and d >= 0 else None


def gap_neg(a, b):
    """True when two blocks overlap; the overlap finding already covers it."""
    return b[0] < a[1]


def norm(text):
    return " ".join(str(text).lower().split()) if text else ""


def check_facts(facts, rep, day_label, item_label, first_date, owner):
    """Validate one facts list; return the set of fact kinds present."""
    kinds = set()
    if facts is None:
        return kinds
    if not isinstance(facts, list):
        rep.err("schema", "facts must be a list", day_label, item_label)
        return kinds
    for fact in facts:
        if not isinstance(fact, dict) or not isinstance(fact.get("claim"), str) or not fact["claim"].strip():
            rep.err("schema", "each fact needs a non-empty claim", day_label, item_label)
            continue
        kind = fact.get("kind", "other")
        status = fact.get("status", "unverified")
        if kind not in FACT_KINDS:
            rep.err("schema", "fact kind '%s' not in %s" % (kind, "/".join(FACT_KINDS)), day_label, item_label)
            continue
        if status not in ("verified", "unverified"):
            rep.err("schema", "fact status must be verified or unverified", day_label, item_label)
            continue
        kinds.add(kind)
        if status == "unverified":
            rep.warn("unverified_fact", "unverified %s fact: %s" % (kind, fact["claim"]), day_label, item_label)
            rep.to_verify.append({"day": day_label, "item": item_label, "kind": kind,
                                  "claim": fact["claim"], "reason": "not verified"})
            continue
        source = fact.get("source")
        checked = parse_date(fact.get("checked_on"))
        if not isinstance(source, str) or not source.strip() or checked is None:
            rep.err("verified_without_source",
                    "fact marked verified needs a source and checked_on (YYYY-MM-DD): %s" % fact["claim"],
                    day_label, item_label)
            rep.to_verify.append({"day": day_label, "item": item_label, "kind": kind,
                                  "claim": fact["claim"], "reason": "verified without source or date"})
        elif first_date and (first_date - checked).days > STALE_DAYS:
            rep.warn("stale_check",
                     "checked %s, more than %d days before the trip: %s" % (fact["checked_on"], STALE_DAYS, fact["claim"]),
                     day_label, item_label)
            rep.to_verify.append({"day": day_label, "item": item_label, "kind": kind,
                                  "claim": fact["claim"], "reason": "check is stale"})
    return kinds


def analyse(doc):
    rep = Report()
    trip = doc.get("trip")
    days = doc.get("days")
    if not isinstance(trip, dict):
        rep.err("schema", "top-level 'trip' object is required")
        trip = {}
    if not isinstance(days, list) or not days:
        rep.err("schema", "top-level 'days' must be a non-empty list")
        days = []

    style = trip.get("style")
    if style not in PACE_LIMIT:
        rep.err("schema", "trip.style must be one of %s" % "/".join(PACE_LIMIT))
        style = None
    currency = trip.get("currency")
    if not isinstance(currency, str) or not currency.strip():
        rep.err("schema", "trip.currency is required (for example EUR)")
        currency = ""
    travelers = trip.get("travelers", 1)
    if isinstance(travelers, bool) or not isinstance(travelers, int) or travelers < 1:
        rep.err("schema", "trip.travelers must be an integer of at least 1")
        travelers = 1
    budget_total = None
    if "budget_total" in trip:
        budget_total = money(trip["budget_total"])
        if budget_total is None:
            rep.err("schema", "trip.budget_total must be a non-negative number")

    dates = [parse_date(d.get("date")) if isinstance(d, dict) else None for d in days]
    valid_dates = [d for d in dates if d]
    first_date = min(valid_dates) if valid_dates else None

    check_facts(trip.get("facts"), rep, None, "trip", first_date, "trip")
    docs = trip.get("documents")
    if docs is not None:
        if not isinstance(docs, list):
            rep.err("schema", "trip.documents must be a list")
        else:
            for dd in docs:
                if not isinstance(dd, dict) or not isinstance(dd.get("name"), str) or dd.get("status") not in DOC_STATUS:
                    rep.err("schema", "each document needs name and status in %s" % "/".join(DOC_STATUS))
                elif dd["status"] != "have":
                    rep.to_verify.append({"day": None, "item": "document", "kind": "document",
                                          "claim": dd["name"], "reason": "status is %s" % dd["status"]})

    by_cat = {c: Decimal(0) for c in CATEGORIES}
    by_day = {}
    seen_dates = set()
    n_items = n_acts = 0

    for di, day in enumerate(days):
        if not isinstance(day, dict):
            rep.err("schema", "day %d is not an object" % (di + 1))
            continue
        dlabel = day.get("date") if isinstance(day.get("date"), str) else "day#%d" % (di + 1)
        if dates[di] is None:
            rep.err("schema", "day needs date as YYYY-MM-DD", dlabel)
        elif dlabel in seen_dates:
            rep.err("schema", "duplicate date", dlabel)
        seen_dates.add(dlabel)
        items = day.get("items")
        if not isinstance(items, list):
            rep.err("schema", "day.items must be a list", dlabel)
            continue

        timed = []
        acts = 0
        has_meal = False
        busy = 0
        day_cost = Decimal(0)
        for ii, it in enumerate(items):
            n_items += 1
            if not isinstance(it, dict):
                rep.err("schema", "item %d is not an object" % (ii + 1), dlabel)
                continue
            label = str(it.get("id") or it.get("title") or "item#%d" % (ii + 1))
            kind = it.get("kind")
            if kind not in KINDS:
                rep.err("schema", "kind must be one of %s" % "/".join(KINDS), dlabel, label)
                continue
            if not isinstance(it.get("title"), str) or not it["title"].strip():
                rep.err("schema", "title is required", dlabel, label)
            if kind == "activity":
                acts += 1
                n_acts += 1
            if kind == "meal":
                has_meal = True
            s, e = minutes(it.get("start")), minutes(it.get("end"))
            if kind == "lodging" and it.get("start") is None and it.get("end") is None:
                pass
            elif s is None or e is None:
                rep.err("schema", "start and end must be HH:MM (24h)", dlabel, label)
            elif e <= s:
                rep.err("schema", "end must be after start (overnight blocks are not supported; split at midnight)", dlabel, label)
            else:
                timed.append((s, e, it, label))
                if kind in ("activity", "transit", "other"):
                    busy += e - s

            # cost
            c1, c2 = it.get("cost"), it.get("cost_per_person")
            cat = it.get("category")
            cost = None
            if c1 is not None and c2 is not None:
                rep.err("schema", "give cost or cost_per_person, not both", dlabel, label)
            elif c1 is not None:
                cost = money(c1)
            elif c2 is not None:
                v = money(c2)
                cost = v * travelers if v is not None else None
            if (c1 is not None or c2 is not None) and cost is None and not (c1 is not None and c2 is not None):
                rep.err("schema", "cost must be a non-negative number", dlabel, label)
            if cost is not None:
                if cat not in CATEGORIES:
                    rep.err("schema", "paid item needs category in %s" % "/".join(CATEGORIES), dlabel, label)
                else:
                    by_cat[cat] += cost
                day_cost += cost
                if it.get("currency") not in (None, currency):
                    rep.err("mixed_currency", "item currency '%s' differs from trip currency '%s'; convert first" % (it.get("currency"), currency), dlabel, label)
            elif kind in ("activity", "meal", "lodging") and c1 is None and c2 is None:
                rep.warn("missing_cost", "no cost given (use 0 for free)", dlabel, label)

            fkinds = check_facts(it.get("facts"), rep, dlabel, label, first_date, "item")
            if kind == "activity" and s is not None and "hours" not in fkinds:
                rep.warn("hours_not_listed", "timed activity has no hours fact; opening hours are unchecked", dlabel, label)
                rep.to_verify.append({"day": dlabel, "item": label, "kind": "hours",
                                      "claim": "opening hours for this slot", "reason": "no hours fact listed"})
            if cost is not None and cost > 0 and "price" not in fkinds:
                rep.warn("price_not_listed", "paid item has no price fact; the price is unchecked", dlabel, label)
                rep.to_verify.append({"day": dlabel, "item": label, "kind": "price",
                                      "claim": "price of %s %s" % (cost, currency), "reason": "no price fact listed"})
        by_day[dlabel] = day_cost

        # overlaps
        timed.sort(key=lambda t: (t[0], t[1]))
        for a, b in zip(timed, timed[1:]):
            if b[0] < a[1]:
                rep.err("overlap", "'%s' (%s-%s) overlaps '%s' (%s-%s)" % (
                    a[3], a[2]["start"], a[2]["end"], b[3], b[2]["start"], b[2]["end"]), dlabel, b[3])

        # pacing
        if style:
            limit = PACE_LIMIT[style] - (TRAVEL_DAY_PENALTY if day.get("travel_day") is True else 0)
            limit = max(limit, 1)
            if acts > limit:
                rep.err("pacing_limit", "%d activities; '%s' style allows %d%s" % (
                    acts, style, limit, " on a travel day" if day.get("travel_day") is True else ""), dlabel)
            if busy > DAY_HOURS_CAP[style] * 60:
                rep.warn("long_day", "%.1f scheduled non-meal hours; '%s' style cap is %d" % (
                    busy / 60.0, style, DAY_HOURS_CAP[style]), dlabel)
        if acts and not has_meal:
            rep.warn("no_meal_block", "activities scheduled but no meal block", dlabel)

        # transit buffers between consecutive non-transit places
        places = [t for t in timed if t[2].get("kind") != "transit"]
        warned_loc = set()
        for a, b in zip(places, places[1:]):
            la, lb = norm(a[2].get("location")), norm(b[2].get("location"))
            # A missing location is a defect, not a free pass: report it once
            # per item and keep checking, using area as the place identity
            # and, when there is no area either, assuming a different place.
            for t in (a, b):
                if not norm(t[2].get("location")) and t[3] not in warned_loc:
                    warned_loc.add(t[3])
                    rep.warn("missing_location", "no location; transit buffer is checked with area (or as a different place)", dlabel, t[3])
            if gap_neg(a, b):
                continue
            if la and lb and la == lb:
                continue
            if not (la and lb) and norm(a[2].get("area")) and norm(a[2].get("area")) == norm(b[2].get("area")):
                continue
            same_area = bool(norm(a[2].get("area"))) and norm(a[2].get("area")) == norm(b[2].get("area"))
            default = BUFFER_SAME_AREA if same_area else BUFFER_OTHER_AREA
            declared = b[2].get("travel_from_previous_min", 0)
            declared = declared if isinstance(declared, int) and not isinstance(declared, bool) and declared >= 0 else 0
            early = b[2].get("arrive_early_min", 0)
            early = early if isinstance(early, int) and not isinstance(early, bool) and early >= 0 else 0
            needed = declared + default + early
            gap = b[0] - a[1]
            # A planned transit block between the two already covers travel.
            covered = sum(t[1] - t[0] for t in timed if t[2].get("kind") == "transit" and a[1] <= t[0] and t[1] <= b[0])
            short = (gap - covered < default + early) if covered else (gap < needed)
            if short:
                rep.err("missing_transit_buffer",
                        "%d min between '%s' and '%s' (%s to %s); needs %d (travel %d + buffer %d + arrive-early %d)" % (
                            gap, a[3], b[3], a[2].get("location"), b[2].get("location"), needed, declared, default, early),
                        dlabel, b[3])

    # budget
    total = sum(by_cat.values(), Decimal(0))
    remaining = None
    if budget_total is not None:
        remaining = budget_total - total
        if total > budget_total:
            rep.err("over_budget", "planned spend %s exceeds budget %s %s by %s" % (total, budget_total, currency, total - budget_total))
        elif budget_total > 0 and remaining < budget_total * CONTINGENCY_FLOOR:
            rep.warn("thin_contingency", "less than %d%% of the budget is left unplanned" % int(CONTINGENCY_FLOOR * 100))
    elif "budget_total" not in trip:
        rep.warn("thin_contingency", "no trip.budget_total; totals cannot be compared with a limit")

    def num(d):
        return float(d.quantize(Decimal("0.01")))

    return {
        "tool": "itinerary_check",
        "version": TOOL_VERSION,
        "ok": not any(f["severity"] == "error" for f in rep.findings),
        "summary": {
            "days": len(days), "items": n_items, "activities": n_acts,
            "errors": sum(1 for f in rep.findings if f["severity"] == "error"),
            "warnings": sum(1 for f in rep.findings if f["severity"] == "warning"),
            "facts_to_verify": len(rep.to_verify),
        },
        "findings": rep.findings,
        "to_verify": rep.to_verify,
        "budget": {
            "currency": currency,
            "by_category": {c: num(v) for c, v in by_cat.items()},
            "by_day": {k: num(v) for k, v in by_day.items()},
            "total": num(total),
            "budget_total": num(budget_total) if budget_total is not None else None,
            "remaining": num(remaining) if remaining is not None else None,
        },
    }


def main(argv):
    if len(argv) != 1 or argv[0] in ("-h", "--help"):
        sys.stderr.write("usage: itinerary_check.py <itinerary.json>\n")
        return 2
    try:
        with open(argv[0], encoding="utf-8-sig") as fh:
            doc = json.load(fh)
    except (OSError, UnicodeDecodeError) as exc:
        sys.stderr.write("cannot read %s: %s\n" % (argv[0], exc))
        return 2
    except json.JSONDecodeError as exc:
        sys.stderr.write("not valid JSON (line %d, column %d): %s\n" % (exc.lineno, exc.colno, exc.msg))
        return 2
    except RecursionError:
        sys.stderr.write("nesting_too_deep: the JSON is nested too deeply to read\n")
        return 2
    except ValueError as exc:
        sys.stderr.write("invalid_number: %s\n" % str(exc)[:120])
        return 2
    if not isinstance(doc, dict):
        sys.stderr.write("top level must be a JSON object\n")
        return 2
    report = analyse(doc)
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
