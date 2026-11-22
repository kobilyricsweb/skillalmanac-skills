"""Check ad headlines, descriptions and paths against user-supplied limits.

The script reads one JSON file (layout in SKILL.md), never writes files and
makes no network calls. It reports character overruns, duplicate headlines,
all-caps text, trailing punctuation and excess exclamation marks.

Usage:
    python -I scripts/ad_limits.py <input.json>

Exit codes:
    0  no findings
    1  one or more findings reported (JSON on stdout)
    2  usage or input error (one-line JSON error on stderr)
"""

import json
import os
import sys
import unicodedata

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_NESTING = 20
MAX_ADS = 2000
MAX_LIMIT = 10000

TOP_KEYS = ("limits", "rules", "ads")
LIMIT_KEYS = ("headline", "description", "path")
REQUIRED_LIMIT_KEYS = ("headline", "description")
RULE_KEYS = ("forbid_trailing", "max_exclamation", "all_caps_min_letters")
AD_KEYS = ("headline", "description", "path")
REQUIRED_AD_KEYS = ("headline", "description")

DEFAULT_RULES = {
    "forbid_trailing": "",
    "max_exclamation": 1,
    "all_caps_min_letters": 4,
}

NOTE = ("Limits and rules are the values supplied in the input file. They are "
        "working values, not verified against any platform.")


def fail(message):
    sys.stderr.write(json.dumps({"error": message}) + "\n")
    sys.exit(2)


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def max_depth(root):
    deepest = 0
    stack = [(root, 1)]
    while stack:
        node, depth = stack.pop()
        if depth > deepest:
            deepest = depth
        if isinstance(node, dict):
            stack.extend((v, depth + 1) for v in node.values())
        elif isinstance(node, list):
            stack.extend((v, depth + 1) for v in node)
    return deepest


def read_input(path):
    if not os.path.isfile(path):
        fail("input file not found")
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
    except OSError:
        fail("input file cannot be read")
    if len(raw) > MAX_INPUT_BYTES:
        fail("input file exceeds 2 MB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("input file is not valid UTF-8")
    try:
        doc = json.loads(text)
    except (ValueError, RecursionError, MemoryError):
        fail("input file is not valid JSON")
    if max_depth(doc) > MAX_NESTING:
        fail("input nests deeper than 20 levels")
    return doc


def parse_limits(raw):
    if not isinstance(raw, dict):
        fail("limits must be an object")
    unknown = sorted(set(raw) - set(LIMIT_KEYS))
    if unknown:
        fail("unknown limits key: " + unknown[0])
    for key in REQUIRED_LIMIT_KEYS:
        if key not in raw:
            fail("limits." + key + " is required")
    limits = {}
    for key in LIMIT_KEYS:
        if key in raw:
            value = raw[key]
            if not is_int(value) or not 1 <= value <= MAX_LIMIT:
                fail("limits." + key + " must be an integer from 1 to 10000")
            limits[key] = value
    return limits


def parse_rules(raw):
    rules = dict(DEFAULT_RULES)
    if raw is None:
        return rules
    if not isinstance(raw, dict):
        fail("rules must be an object")
    unknown = sorted(set(raw) - set(RULE_KEYS))
    if unknown:
        fail("unknown rules key: " + unknown[0])
    if "forbid_trailing" in raw:
        value = raw["forbid_trailing"]
        if not isinstance(value, str) or len(value) > 20:
            fail("rules.forbid_trailing must be a string of at most 20 characters")
        rules["forbid_trailing"] = value
    if "max_exclamation" in raw:
        value = raw["max_exclamation"]
        if not is_int(value) or not 0 <= value <= 50:
            fail("rules.max_exclamation must be an integer from 0 to 50")
        rules["max_exclamation"] = value
    if "all_caps_min_letters" in raw:
        value = raw["all_caps_min_letters"]
        if not is_int(value) or not 2 <= value <= 50:
            fail("rules.all_caps_min_letters must be an integer from 2 to 50")
        rules["all_caps_min_letters"] = value
    return rules


def parse_ads(raw, limits):
    if not isinstance(raw, list) or not raw:
        fail("ads must be a non-empty list")
    if len(raw) > MAX_ADS:
        fail("ads may hold at most 2000 entries")
    ads = []
    for number, ad in enumerate(raw, 1):
        if not isinstance(ad, dict):
            fail("ad %d must be an object" % number)
        unknown = sorted(set(ad) - set(AD_KEYS))
        if unknown:
            fail("ad %d has unknown key: %s" % (number, unknown[0]))
        for key in REQUIRED_AD_KEYS:
            if key not in ad:
                fail("ad %d is missing %s" % (number, key))
        clean = {}
        for key in AD_KEYS:
            if key not in ad:
                continue
            value = ad[key]
            if not isinstance(value, list) or not all(isinstance(t, str) for t in value):
                fail("ad %d field %s must be a list of strings" % (number, key))
            if key == "path" and "path" not in limits:
                fail("ad %d has path but limits.path is not set" % number)
            clean[key] = value
        ads.append(clean)
    return ads


def normalized(text):
    return unicodedata.normalize("NFC", text)


def add(findings, ad, field, slot, check, message, **extra):
    item = {"ad": ad, "field": field, "slot": slot, "check": check, "message": message}
    item.update(extra)
    findings.append(item)


def scan(ads, limits, rules):
    findings = []
    text_count = 0
    headline_places = {}
    for ad_no, ad in enumerate(ads, 1):
        for field in AD_KEYS:
            if field not in ad:
                continue
            limit = limits[field]
            for slot, text in enumerate(ad[field], 1):
                text_count += 1
                value = normalized(text)
                length = len(value)
                if length > limit:
                    add(findings, ad_no, field, slot, "length",
                        "%d characters, limit %d" % (length, limit),
                        length=length, limit=limit, excess=length - limit)
                if field == "path":
                    continue
                stripped = value.strip()
                if rules["forbid_trailing"] and stripped and stripped[-1] in rules["forbid_trailing"]:
                    add(findings, ad_no, field, slot, "trailing_punctuation",
                        "ends with a forbidden trailing character")
                marks = value.count("!")
                if marks > rules["max_exclamation"]:
                    add(findings, ad_no, field, slot, "exclamation",
                        "%d exclamation marks, limit %d" % (marks, rules["max_exclamation"]),
                        excess=marks - rules["max_exclamation"])
                cased = [c for c in value if c.islower() or c.isupper()]
                if len(cased) >= rules["all_caps_min_letters"] and not any(c.islower() for c in cased):
                    add(findings, ad_no, field, slot, "all_caps",
                        "all cased letters are uppercase")
                if field == "headline":
                    key = " ".join(value.casefold().split())
                    if key:
                        headline_places.setdefault(key, []).append((ad_no, slot))
    for places in headline_places.values():
        if len(places) > 1:
            first_ad = places[0][0]
            for ad_no, slot in places[1:]:
                add(findings, ad_no, "headline", slot, "duplicate_headline",
                    "same text as the headline in ad %d" % first_ad,
                    duplicate_of_ad=first_ad)
    return findings, text_count


def main(argv):
    if len(argv) != 2:
        fail("usage: python -I scripts/ad_limits.py <input.json>")
    doc = read_input(argv[1])
    if not isinstance(doc, dict):
        fail("top level must be an object")
    unknown = sorted(set(doc) - set(TOP_KEYS))
    if unknown:
        fail("unknown top-level key: " + unknown[0])
    if "limits" not in doc:
        fail("limits is required")
    limits = parse_limits(doc["limits"])
    rules = parse_rules(doc.get("rules"))
    ads = parse_ads(doc.get("ads"), limits)
    findings, text_count = scan(ads, limits, rules)
    counts = {}
    for item in findings:
        counts[item["check"]] = counts.get(item["check"], 0) + 1
    result = {
        "ok": not findings,
        "findings_count": len(findings),
        "counts_by_check": counts,
        "checked": {"ads": len(ads), "texts": text_count},
        "limits": limits,
        "rules": rules,
        "findings": findings,
        "note": NOTE,
    }
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
