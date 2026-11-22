#!/usr/bin/env python3
"""scale_recipe.py - scale and convert a plain-text ingredient list. Arithmetic only.

Usage:
    python scale_recipe.py RECIPE.txt MODE [options]

    MODE (exactly one):
      --factor F                         F is 2, 1.5 or 3/2
      --from-servings A --to-servings B  factor = B / A
      --from-pan P --to-pan Q            factor = area(Q) / area(P); P and Q look like
                                         9x13, 22x33cm, round:9, round:23cm, square:8

    Options:
      --units keep|metric|us             target unit system (default keep)
      --basis keep|mass|volume           mass or volume needs a density (default keep)
      --system us|metric                 meaning of tsp, tbsp and cup in the input: us =
                                         4.93 / 14.79 / 236.59 ml, metric = 5 / 15 / 250 ml
      --density FILE.csv                 your own densities, lines "ingredient,g_per_cup"
      --format json|text                 json (default) or the final list as plain text
      --out FILE [--force]               write the result to FILE (never over an input)

Input: one ingredient per line, for example "1 1/2 cups flour", "2-3 tbsp oil",
"200 g sugar", "1 (14 oz) can tomatoes", "1 cup (227 g) butter". Blank lines and lines
starting with # are skipped; a line ending in ":" is kept as a header.

Reads: the recipe file and the optional density file. Writes: only the --out file, and
only when it is not the recipe or density file (checked after resolving links).
Exit codes: 0 ok, 1 some lines could not be parsed (see "unparsed"), 2 usage or
input error. Standard library only; no network.
"""
import argparse
import csv
import json
import math
import os
import re
import sys
from fractions import Fraction as F

VERSION = "0.1.0"

# Warn when a scale factor is outside this range: pan, equipment and time stop being predictable.
FACTOR_HIGH = F(4)
FACTOR_LOW = F(1, 4)
# Non-linear heuristics (leavening, salt, spice, simmering liquid) start at these factors.
NL_HIGH = F(2)
NL_LOW = F(1, 2)
# Prefer a larger unit (for example cup over tbsp) only when rounding to it loses at most 3 percent.
LADDER_TOL = F(3, 100)
# Flag a line when rounding to a practical measure moves the value by more than this percent.
ROUND_WARN_PCT = 10
# A bundled or user density outside this range (g per US cup) is almost certainly a typo.
DENSITY_MIN, DENSITY_MAX = 20, 600

# --- units (exact definitions: 1 US fl oz = 29.5735295625 ml, 1 oz = 28.349523125 g, 1 lb = 453.59237 g)
FLOZ = F("29.5735295625")
OZ_G = F("28.349523125")
LB_G = F("453.59237")
CUP_US = FLOZ * 8
SYSTEMS = {
    "us": {"tsp": FLOZ / 6, "tbsp": FLOZ / 2, "cup": CUP_US},
    "metric": {"tsp": F(5), "tbsp": F(15), "cup": F(250)},
}
FIXED_ML = {"floz": FLOZ, "pint": FLOZ * 16, "quart": FLOZ * 32, "gallon": FLOZ * 128,
            "ml": F(1), "l": F(1000), "stick": FLOZ * 4}
MASS_G = {"g": F(1), "kg": F(1000), "oz": OZ_G, "lb": LB_G}
METRIC_UNITS = {"ml", "l", "g", "kg"}

ALIASES = {}
KIND = {}


def plural(word):
    return word + "es" if word.endswith(("ch", "sh", "s", "x")) else word + "s"


def _reg(canon, kind, *names):
    KIND[canon] = kind
    for name in (canon,) + names:
        ALIASES[name] = canon


_reg("tsp", "vol", "tsps", "teaspoon", "teaspoons")
_reg("tbsp", "vol", "tbsps", "tbs", "tbl", "tablespoon", "tablespoons")
_reg("cup", "vol", "cups")
_reg("floz", "vol")
_reg("pint", "vol", "pints", "pt")
_reg("quart", "vol", "quarts", "qt")
_reg("gallon", "vol", "gallons", "gal")
_reg("ml", "vol", "milliliter", "milliliters", "millilitre", "millilitres")
_reg("l", "vol", "liter", "liters", "litre", "litres")
_reg("g", "mass", "gram", "grams")
_reg("kg", "mass", "kilogram", "kilograms")
_reg("oz", "mass", "ounce", "ounces")
_reg("lb", "mass", "lbs", "pound", "pounds")
_reg("stick", "stick", "sticks")
for _c in ("can", "tin", "package", "packet", "jar", "bottle"):
    _reg(_c, "pack", plural(_c))
_reg("package", "pack", "packages", "pkg", "pkgs")
for _c in ("pinch", "dash", "handful", "knob", "bunch", "sprig", "slice", "clove",
           "head", "stalk", "splash", "drop", "scoop", "sheet"):
    _reg(_c, "informal", plural(_c))

DISPLAY = {"floz": "fl oz"}
PLURAL_UNITS = {"cup", "pint", "quart", "gallon", "stick"}
DECIMAL_UNITS = {"ml", "l", "g", "kg"}

# --- text normalisation and parsing
UNI = {"¼": "1/4", "½": "1/2", "¾": "3/4", "⅐": "1/7", "⅑": "1/9",
       "⅒": "1/10", "⅓": "1/3", "⅔": "2/3", "⅕": "1/5", "⅖": "2/5",
       "⅗": "3/5", "⅘": "4/5", "⅙": "1/6", "⅚": "5/6", "⅛": "1/8",
       "⅜": "3/8", "⅝": "5/8", "⅞": "7/8"}
UNI_CLASS = "[" + "".join(UNI) + "]"
DASHES = "‐‑‒–—−"
NUM = r"\d+\s+\d+/\d+|\d+/\d+|\d*\.\d+|\d+"
QTY_RE = re.compile(r"^(?P<lo>" + NUM + r")(?:\s*(?:-|to|or)\s*(?P<hi>" + NUM + r"))?(?![\d/])", re.I)
TERM_RE = re.compile(r"^(?P<plus>\+\s*|and\s+)?(?P<n>" + NUM + r")(?![\d/])\s*", re.I)
FLOZ_RE =re.compile(r"^(fl\.?\s*oz\.?|fluid\s+ounces?)(?![A-Za-z])", re.I)
WORD_RE = re.compile(r"^([A-Za-z]+)\.?")
WORD_NUM_RE = re.compile(r"^(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|half)\b", re.I)
UNKNOWN_UNIT_RE = re.compile(r"^([A-Za-z]+)\s+(of\s+.*)$", re.I)
BUTTER_RE = re.compile(r"\b(butter|margarine)\b", re.I)
EGG_RE = re.compile(r"\beggs?\b", re.I)
LIQUID_RE = re.compile(r"\b(juice|stock|broth|wine|vinegar|syrup|cream|milk|water|oil|honey)\b", re.I)


def normalise(text):
    for ch in DASHES:
        text = text.replace(ch, "-")
    text = re.sub(r"(\d)(" + UNI_CLASS + ")", r"\1 \2", text)
    text = re.sub(UNI_CLASS, lambda m: UNI[m.group(0)], text)
    # "1-1/2 cups" is a mixed number, not a range (a range such as 1/2-3/4 is left alone)
    text = re.sub(r"(?<![\d/])(\d+)-(\d+/\d+)", r"\1 \2", text)
    return re.sub(r"[ \t]+", " ", text)


def to_f(s):
    s = s.strip()
    if " " in s:
        whole, frac = s.split()
        return int(whole) + F(frac)
    return F(s)


def parse_unit(rest):
    """Return (canonical unit, remainder) or None."""
    m = FLOZ_RE.match(rest)
    if m:
        return "floz", rest[m.end():].lstrip()
    m = WORD_RE.match(rest)
    if m and m.group(1).lower() in ALIASES:
        return ALIASES[m.group(1).lower()], rest[m.end():].lstrip()
    return None


# --- rounding to practical measures
CUP_FRACS = sorted({F(0), F(1), F(1, 8), F(1, 4), F(1, 3), F(3, 8), F(1, 2), F(5, 8), F(2, 3), F(3, 4), F(7, 8)})


def nearest(x, step):
    return step * math.floor(x / step + F(1, 2))


def _step(unit, x):
    if unit == "tsp":
        return F(1, 8) if x < 1 else F(1, 4)
    if unit == "tbsp":
        return F(1, 4) if x < 4 else F(1, 2)
    if unit in ("floz",):
        return F(1, 2)
    if unit in ("pint", "quart", "gallon", "lb", "stick"):
        return F(1, 4)
    if unit == "ml":
        return F(1, 2) if x < 10 else (F(5) if x < 100 else F(10))
    if unit in ("l", "kg"):
        return F(1, 20)
    if unit == "g":
        return F(1, 2) if x < 5 else (F(1) if x < 20 else (F(5) if x < 200 else F(10)))
    if unit == "oz":
        return F(1, 4) if x < 4 else F(1, 2)
    return F(1, 2) if x < 10 else F(1)  # counts, packs, informal units


def round_unit(unit, x):
    if unit == "cup":
        whole = math.floor(x)
        best = min(CUP_FRACS, key=lambda c: (abs(c - (x - whole)), c))
        res, smallest = whole + best, F(1, 8)
    else:
        step = _step(unit, x)
        res, smallest = nearest(x, step), step
    return smallest if res == 0 and x > 0 else res


US_VOL = [("cup", F(1, 4)), ("tbsp", F(1)), ("tsp", F(0))]
ML_L = [("l", F(1)), ("ml", F(0))]
G_KG = [("kg", F(1)), ("g", F(0))]
OZ_LB = [("lb", F(1)), ("oz", F(0))]


def keep_ladder(unit):
    for lad in (US_VOL, ML_L, G_KG, OZ_LB):
        if unit in [u for u, _ in lad]:
            return lad
    return [(unit, F(0))]


def unit_size(unit, system):
    if unit in SYSTEMS[system]:
        return SYSTEMS[system][unit]
    return FIXED_ML[unit] if unit in FIXED_ML else MASS_G[unit]


def express(lo, hi, ladder, system):
    """Pick the largest unit in the ladder whose rounding error is within LADDER_TOL."""
    top = hi if hi is not None else lo
    for i, (unit, minimum) in enumerate(ladder):
        size = unit_size(unit, system)
        last = i == len(ladder) - 1
        if top / size >= minimum or last:
            rlo = round_unit(unit, lo / size)
            rhi = round_unit(unit, hi / size) if hi is not None else None
            err = abs((rhi if rhi is not None else rlo) * size - top) / top
            if err <= LADDER_TOL or last:
                return unit, rlo, rhi, err
    raise AssertionError("unreachable")


def fmt_mixed(r):
    whole = math.floor(r)
    frac = r - whole
    if frac == 0:
        return str(whole)
    if whole == 0:
        return "%d/%d" % (frac.numerator, frac.denominator)
    return "%d %d/%d" % (whole, frac.numerator, frac.denominator)


def fmt_dec(r):
    return ("%.2f" % float(r)).rstrip("0").rstrip(".")


def fmt_range(unit, rlo, rhi):
    f = fmt_dec if unit in DECIMAL_UNITS else fmt_mixed
    if rhi is None or rhi == rlo:
        return f(rlo)
    return f(rlo) + "-" + f(rhi)


def unit_text(unit, top, raw=None):
    if raw is not None:
        return raw
    name = DISPLAY.get(unit, unit)
    if (unit in PLURAL_UNITS or KIND.get(unit) in ("pack", "informal")) and top > 1:
        name = plural(name)
    return name


def join(*parts):
    return " ".join(p for p in parts if p)


# --- density table (grams per US customary cup, approximate)
# (name, g per cup, [(phrase, confidence)], exclude regex, note)
DENSITY = [
    ("all-purpose flour", 120, [("all-purpose flour", "high"), ("plain flour", "high"), ("ap flour", "high"), ("flour", "medium")], None, "flour varies by scoop method; a spooned and levelled cup is the assumption"),
    ("bread flour", 127, [("bread flour", "high")], None, ""),
    ("whole wheat flour", 120, [("whole wheat flour", "high"), ("wholemeal flour", "high")], None, ""),
    ("granulated sugar", 200, [("granulated sugar", "high"), ("white sugar", "high"), ("sugar", "medium")], None, ""),
    ("brown sugar", 213, [("brown sugar", "high")], None, "assumes a firmly packed cup"),
    ("powdered sugar", 120, [("powdered sugar", "high"), ("confectioners sugar", "high"), ("confectioners' sugar", "high"), ("icing sugar", "high")], None, ""),
    ("butter", 227, [("butter", "high"), ("margarine", "medium")], None, ""),
    ("milk", 245, [("milk", "high")], None, ""),
    ("water", 237, [("water", "high")], None, ""),
    ("honey", 340, [("honey", "high")], None, ""),
    ("vegetable oil", 218, [("vegetable oil", "high"), ("canola oil", "high"), ("sunflower oil", "high"), ("oil", "medium")], None, ""),
    ("olive oil", 216, [("olive oil", "high")], None, ""),
    ("rolled oats", 90, [("rolled oats", "high"), ("old-fashioned oats", "high"), ("oats", "high")], None, ""),
    ("cocoa powder", 85, [("cocoa powder", "high"), ("cocoa", "high")], None, ""),
    ("cornstarch", 128, [("cornstarch", "high"), ("corn starch", "high"), ("cornflour", "medium")], None, ""),
    ("table salt", 288, [("table salt", "high"), ("salt", "medium")], r"kosher|flaky|sea|himalayan|pink|coarse", "table salt only; crystal size changes the density a lot"),
    ("white rice (uncooked)", 185, [("white rice", "high"), ("rice", "medium")], None, ""),
    ("heavy cream", 238, [("heavy cream", "high"), ("whipping cream", "high"), ("double cream", "high"), ("cream", "medium")], r"cream\s+(cheese|of tartar)", ""),
    ("yogurt", 245, [("yogurt", "high"), ("yoghurt", "high")], None, ""),
    ("maple syrup", 315, [("maple syrup", "high")], None, ""),
    ("peanut butter", 258, [("peanut butter", "high")], None, ""),
]
LIQUID_ENTRIES = {"milk", "water", "honey", "vegetable oil", "olive oil", "heavy cream", "maple syrup"}
DESCRIPTORS = set("""sifted fresh plain unsalted salted softened melted cold warm whole skim low-fat lowfat
nonfat reduced-fat full-fat full fat large small medium packed lightly firmly ground fine finely extra
virgin extra-virgin light pure raw organic unbleached bleached the of a""".split())


def clean_name(text):
    t = re.sub(r"\([^)]*\)", " ", text.lower())
    t = t.split(",")[0]
    return re.sub(r"\s+", " ", t.replace("’", "'")).strip()


def _find(phrase, name):
    return re.search(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", name)


def _generic_ok(phrase, name, m):
    if " " in phrase or "-" in phrase:
        return True
    return all(w in DESCRIPTORS for w in name[:m.start()].split())


def lookup_density(name, user):
    n = clean_name(name)
    best = None
    for phrase, gpc in user:
        if _find(phrase, n) and (best is None or len(phrase) > len(best[0])):
            best = (phrase, gpc)
    if best:
        return {"ingredient": best[0], "g_per_cup": best[1], "source": "user", "confidence": "high", "note": ""}
    best = None
    for canon, gpc, phrases, exclude, note in DENSITY:
        if exclude and re.search(exclude, n):
            continue
        for phrase, conf in phrases:
            m = _find(phrase, n)
            if m and _generic_ok(phrase, n, m) and (best is None or len(phrase) > best[0]):
                best = (len(phrase), canon, gpc, conf, note)
    if best:
        return {"ingredient": best[1], "g_per_cup": best[2], "source": "bundled-approximate",
                "confidence": best[3], "note": best[4]}
    return None


def load_density(path):
    rows = []
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as fh:
            for i, row in enumerate(csv.reader(fh), 1):
                if not row or not row[0].strip() or row[0].lstrip().startswith("#"):
                    continue
                if len(row) < 2:
                    raise ValueError("density file line %d needs 'ingredient,g_per_cup'" % i)
                try:
                    gpc = F(row[1].strip())
                except (ValueError, ZeroDivisionError):
                    if i == 1:
                        continue  # header row
                    raise ValueError("density file line %d: '%s' is not a number" % (i, row[1].strip()))
                if not DENSITY_MIN <= gpc <= DENSITY_MAX:
                    raise ValueError("density file line %d: %s g per cup is outside %d-%d; use grams per US cup"
                                     % (i, row[1].strip(), DENSITY_MIN, DENSITY_MAX))
                rows.append((clean_name(row[0]), gpc))
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError("cannot read density file %s: %s" % (path, exc))
    return rows


# --- non-linear heuristics (documented working rules, not measured laws)
NL_RULES = [
    ("leavening", r"baking (powder|soda)|bicarbonate|yeast|cream of tartar|leavening",
     "leavening: linear amount shown; outside about 0.5x to 2x test a small batch or use the source recipe's own scaled version"),
    ("salt", r"\bsalt\b",
     "salt: linear amount shown; add in steps and taste, treating the number as an upper bound"),
    ("spice", r"\b(black pepper|white pepper|pepper flakes|cayenne|chil(i|li|e)|paprika|cinnamon|cumin|nutmeg|cloves?|ginger|curry|oregano|thyme|rosemary|garlic|extract|turmeric|spice)\b",
     "strong flavour: linear amount shown; add in steps and taste"),
    ("simmer", r"\b(stock|broth|wine)\b",
     "simmering liquid: evaporation does not scale with volume; the linear amount is a starting point"),
]
RATIO_CRITICAL_RE = re.compile(r"curing salt|prague powder|pink salt|pickling lime|pectin|nitrite", re.I)

CONF = {3: "high", 2: "medium", 1: "low"}


def process_line(no, raw, factor, opts, user):
    text = normalise(raw.strip())
    if not text or text.startswith("#"):
        return None, None
    base = {"line_no": no, "original": raw.strip(), "scaled": raw.strip(), "converted": None, "note": "",
            "confidence": "n/a", "flags": [], "rounding_error_pct": None, "density": None}

    def bad(reason):
        return None, {"line_no": no, "original": raw.strip(), "reason": reason}

    m = QTY_RE.match(text)
    if not m:
        if text.endswith(":"):
            base["flags"] = ["header"]
            return (base, None), None
        if WORD_NUM_RE.match(text):
            return bad("number written as a word; rewrite it with digits")
        if text[0].isdigit() or text[0] == ".":
            return bad("could not read the quantity")
        base["flags"], base["note"] = ["no_quantity"], "no quantity; left as written"
        return (base, None), None
    try:
        lo = to_f(m.group("lo"))
        hi = to_f(m.group("hi")) if m.group("hi") else None
    except ZeroDivisionError:
        return bad("zero denominator in the quantity")
    if lo <= 0 or (hi is not None and hi <= 0):
        return bad("quantity is zero or negative")
    if hi is not None and hi < lo:
        return bad("range runs backwards")
    if hi == lo:
        hi = None

    rest = text[m.end():].lstrip()
    pack = None
    if rest.startswith("("):
        close = rest.find(")")
        if close != -1:
            after = rest[close + 1:].lstrip()
            u2 = parse_unit(after)
            if u2 and KIND[u2[0]] in ("pack", "informal"):
                pack, rest = rest[:close + 1], after

    unit, raw_unit, kind, remainder = None, None, "count", rest
    parsed = parse_unit(rest)
    notes, flags, level = [], [], 3
    if parsed:
        unit, remainder = parsed
        kind = KIND[unit]
        remainder = re.sub(r"^of\s+", "", remainder, flags=re.I)
        if unit == "stick" and not BUTTER_RE.search(remainder):
            kind = "informal"
            flags.append("ambiguous_unit")
            notes.append("'stick' is read as a butter stick only for butter or margarine; here it is an informal unit")
            level = min(level, 1)
    else:
        mu = UNKNOWN_UNIT_RE.match(rest)
        if mu:
            raw_unit, remainder, kind = mu.group(1), mu.group(2), "unknown"
            flags.append("unknown_unit")
            notes.append("unknown unit '%s'; scaled linearly, not converted" % raw_unit)
            level = min(level, 1)

    # Compound quantity: "1 cup + 2 tbsp", "1 lb 4 oz". Same-family terms are summed into the
    # first unit before scaling; anything else that looks like a second quantity is left unscaled.
    if kind in ("vol", "mass"):
        terms = []
        compound_bad = None
        while True:
            mt = TERM_RE.match(remainder)
            if not mt:
                break
            tail = remainder[mt.end():]
            tu = parse_unit(tail)
            try:
                tval = to_f(mt.group("n"))
            except ZeroDivisionError:
                tval = None
            if tu is None or tval is None or tval <= 0:
                if mt.group("plus"):
                    compound_bad = "'+' not followed by a number and a known unit"
                    break
                if tu is None:
                    break  # a number that belongs to the ingredient name, e.g. "2% milk"
                compound_bad = "unreadable second quantity"
                break
            if KIND[tu[0]] != kind:
                compound_bad = "second quantity is in a different kind of unit (%s)" % tu[0]
                break
            terms.append((tval, tu[0]))
            remainder = tu[1]
        if terms and compound_bad is None and hi is not None:
            compound_bad = "a range combined with a second quantity"
        if compound_bad:
            base["flags"] = ["unparsed_compound"]
            base["confidence"] = "low"
            base["note"] = "compound quantity not scaled (%s); left as written, rewrite as one quantity (for example 1 1/8 cups) and run again" % compound_bad
            return (base, None), None
        if terms:
            size = unit_size(unit, opts.system)
            lo = lo + sum(t * unit_size(u, opts.system) for t, u in terms) / size
            notes.append("compound quantity summed to %s %s before scaling" % (fmt_mixed(lo), unit))

    alt = None
    if kind in ("vol", "mass") and remainder.startswith("("):
        close = remainder.find(")")
        inner = normalise(remainder[1:close]) if close != -1 else ""
        mm = QTY_RE.match(inner)
        if mm:
            try:
                alo = to_f(mm.group("lo"))
                ahi = to_f(mm.group("hi")) if mm.group("hi") else None
                au = parse_unit(inner[mm.end():].lstrip())
            except ZeroDivisionError:
                au = None
            if au and KIND[au[0]] in ("vol", "mass") and not au[1] and alo > 0:
                alt = (alo, ahi, au[0])
                remainder = remainder[close + 1:].lstrip()

    name = clean_name(remainder)
    slo = lo * factor
    shi = hi * factor if hi is not None else None
    conv_text = None
    err = None
    dens_info = None

    if kind in ("vol", "mass", "stick"):
        mult = lambda u: unit_size(u, opts.system)
        blo, bhi = slo * mult(unit), (shi * mult(unit) if shi is not None else None)
        su, rlo, rhi, err = express(blo, bhi, keep_ladder(unit), opts.system)
        top = rhi if rhi is not None else rlo
        alt_text = ""
        if alt:
            a_lo, a_hi, a_u = alt[0] * factor, (alt[1] * factor if alt[1] else None), alt[2]
            asz = unit_size(a_u, opts.system)
            au2, alo2, ahi2, _ = express(a_lo * asz, a_hi * asz if a_hi is not None else None, keep_ladder(a_u), opts.system)
            alt_text = "(" + join(fmt_range(au2, alo2, ahi2), unit_text(au2, ahi2 if ahi2 is not None else alo2)) + ")"
        scaled = join(fmt_range(su, rlo, rhi), unit_text(su, top), alt_text, remainder)

        src_family = "mass" if kind == "mass" else "vol"
        src_sys = "metric" if unit in METRIC_UNITS else "us"
        dst_family = {"keep": src_family, "mass": "mass", "volume": "vol"}[opts.basis]
        dst_sys = src_sys if opts.units == "keep" else opts.units
        if dst_family != src_family or dst_sys != src_sys:
            ok = True
            clo, chi = blo, bhi
            if dst_family != src_family:
                dens = lookup_density(name, user)
                if dens is None:
                    ok = False
                    flags.append("no_density")
                    notes.append("no density for '%s'; add it with --density to convert between volume and weight" % name)
                    level = min(level, 1)
                else:
                    dens_info = {"ingredient": dens["ingredient"], "g_per_cup": float(dens["g_per_cup"]),
                                 "source": dens["source"]}
                    gpc = F(dens["g_per_cup"])
                    if src_family == "vol":
                        clo, chi = clo * gpc / CUP_US, (chi * gpc / CUP_US if chi is not None else None)
                    else:
                        clo, chi = clo * CUP_US / gpc, (chi * CUP_US / gpc if chi is not None else None)
                    if dens["confidence"] != "high":
                        level = min(level, 2)
                        notes.append("density matched loosely to '%s'" % dens["ingredient"])
                    if dens["source"] != "user":
                        notes.append("density is approximate (%s g per US cup)" % dens["g_per_cup"])
                        if dens["note"]:
                            notes.append(dens["note"])
            if ok:
                if dst_sys == "metric":
                    lad = ML_L if dst_family == "vol" else G_KG
                else:
                    lad = US_VOL if dst_family == "vol" else OZ_LB
                cu, clo2, chi2, err = express(clo, chi, lad, opts.system)
                conv_text = join(fmt_range(cu, clo2, chi2), unit_text(cu, chi2 if chi2 is not None else clo2), remainder)
                if alt:
                    notes.append("parenthetical measure dropped from the converted line")
        if unit == "oz" and (LIQUID_RE.search(name) or (lookup_density(name, user) or {}).get("ingredient") in LIQUID_ENTRIES):
            flags.append("ambiguous_unit")
            notes.append("'oz' is read as weight; if fluid ounces were meant, rewrite as 'fl oz'")
            level = min(level, 1)
    else:
        rlo = round_unit("count", slo)
        rhi = round_unit("count", shi) if shi is not None else None
        top = rhi if rhi is not None else rlo
        err = abs(top - (shi if shi is not None else slo)) / (shi if shi is not None else slo)
        ut = unit_text(unit, top, raw_unit) if (unit or raw_unit) else ""
        scaled = join(fmt_range("count", rlo, rhi), pack, ut, remainder)
        if pack and factor != 1:
            notes.append("pack size %s is not scaled; only the count is" % pack)
        if kind == "pack" and (rlo.denominator != 1 or (rhi is not None and rhi.denominator != 1)):
            flags.append("fractional_pack")
            notes.append("fractional pack; open a whole one and measure, or round")
        if EGG_RE.search(name) and (rlo.denominator != 1 or (rhi is not None and rhi.denominator != 1)):
            flags.append("fractional_egg")
            notes.append("fractional egg; beat one egg and use a share by weight (a large egg is about 50 g without shell, approximate)")
            level = min(level, 2)

    if factor >= NL_HIGH or factor <= NL_LOW:
        for cat, rx, msg in NL_RULES:
            if re.search(rx, name):
                flags.append("nonlinear_" + cat)
                notes.append(msg)
                level = min(level, 2)
    if RATIO_CRITICAL_RE.search(name):
        flags.append("ratio_critical")
        notes.append("ratio-critical ingredient; scale only from a tested source for this type of recipe")
        level = 1
    pct = round(float(err) * 100, 1) if err is not None else None
    if pct is not None and pct > ROUND_WARN_PCT:
        flags.append("rounding_large")
        notes.append("rounding moved the amount by %s%%; consider weighing" % pct)
        level = min(level, 2)

    base.update({"scaled": scaled, "converted": conv_text, "note": "; ".join(notes), "confidence": CONF[level],
                 "flags": flags, "rounding_error_pct": pct, "density": dens_info})
    key = (lookup_density(name, user) or {}).get("ingredient") or name
    return (base, {"key": key, "unit": unit if unit else raw_unit, "kind": kind}), None


# --- scale factor
PAN_RE = re.compile(r"^(?:(round|square|loaf|rect)[:=])?(\d+(?:\.\d+)?)(?:x(\d+(?:\.\d+)?))?(in|cm)?$")


def pan_area(spec):
    m = PAN_RE.match(spec.strip().lower().replace(" ", ""))
    if not m:
        raise ValueError("pan '%s' not understood; use 9x13, 22x33cm, round:9 or square:8" % spec)
    shape, a, b, unit = m.group(1), float(m.group(2)), m.group(3), m.group(4)
    if shape == "round":
        if b:
            raise ValueError("pan '%s': a round pan takes one number (the diameter)" % spec)
        area = math.pi * (a / 2) ** 2
    elif b:
        area = a * float(b)
    elif shape == "square":
        area = a * a
    else:
        raise ValueError("pan '%s': give two sides (9x13) or say round:N or square:N" % spec)
    return area / (2.54 ** 2) if unit == "cm" else area


def parse_factor(args):
    modes = [args.factor is not None, args.from_servings is not None or args.to_servings is not None,
             args.from_pan is not None or args.to_pan is not None]
    if sum(modes) != 1:
        raise ValueError("choose exactly one of --factor, --from-servings with --to-servings, --from-pan with --to-pan")
    try:
        if args.factor is not None:
            f, basis = F(args.factor), "factor %s" % args.factor
        elif modes[1]:
            if args.from_servings is None or args.to_servings is None:
                raise ValueError("--from-servings and --to-servings go together")
            f = F(args.to_servings) / F(args.from_servings)
            basis = "servings %s to %s" % (args.from_servings, args.to_servings)
        else:
            if args.from_pan is None or args.to_pan is None:
                raise ValueError("--from-pan and --to-pan go together")
            ratio = pan_area(args.to_pan) / pan_area(args.from_pan)
            f = F(str(round(ratio, 4)))
            basis = "pan %s to %s (area ratio, same batter depth assumed)" % (args.from_pan, args.to_pan)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(str(exc) if str(exc) else "the scale numbers are not valid")
    if f <= 0:
        raise ValueError("the scale factor must be greater than zero")
    return f, basis


def same_path(a, b):
    try:
        if os.path.exists(a) and os.path.exists(b) and os.path.samefile(a, b):
            return True
    except OSError:
        pass
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def build_parser():
    p = argparse.ArgumentParser(description="Scale and convert a plain-text ingredient list.")
    p.add_argument("recipe")
    p.add_argument("--factor")
    p.add_argument("--from-servings", dest="from_servings")
    p.add_argument("--to-servings", dest="to_servings")
    p.add_argument("--from-pan", dest="from_pan")
    p.add_argument("--to-pan", dest="to_pan")
    p.add_argument("--units", choices=["keep", "metric", "us"], default="keep")
    p.add_argument("--basis", choices=["keep", "mass", "volume"], default="keep")
    p.add_argument("--system", choices=["us", "metric"], default="us")
    p.add_argument("--density")
    p.add_argument("--format", choices=["json", "text"], default="json")
    p.add_argument("--out")
    p.add_argument("--force", action="store_true")
    return p


def fail(msg):
    sys.stderr.write("error: " + msg + "\n")
    return 2


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        factor, basis = parse_factor(args)
    except ValueError as exc:
        return fail(str(exc))
    if args.out:
        for inp in (args.recipe, args.density):
            if inp and same_path(args.out, inp):
                return fail("refusing to write over an input file (%s); choose another --out" % inp)
        if os.path.exists(args.out) and not args.force:
            return fail("%s already exists; use --force to replace it" % args.out)
    try:
        with open(args.recipe, "r", encoding="utf-8-sig") as fh:
            raw_lines = fh.read().splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        return fail("cannot read %s as UTF-8 text: %s" % (args.recipe, exc))
    try:
        user = load_density(args.density) if args.density else []
    except ValueError as exc:
        return fail(str(exc))

    lines, unparsed, groups = [], [], {}
    for no, raw in enumerate(raw_lines, 1):
        got, bad = process_line(no, raw, factor, args, user)
        if bad:
            unparsed.append(bad)
        elif got:
            rec, info = got if isinstance(got, tuple) else (got, None)
            lines.append(rec)
            if info and info["kind"] in ("vol", "mass", "stick"):
                groups.setdefault(info["key"], []).append((rec, info["unit"]))
    if not lines and not unparsed:
        return fail("%s has no ingredient lines" % args.recipe)

    for key, members in groups.items():
        units = sorted({u for _, u in members})
        if len(units) > 1:
            for rec, _ in members:
                rec["flags"].append("unit_mismatch")
                rec["note"] = "; ".join(x for x in (rec["note"], "same ingredient also listed in %s; check for double counting" % ", ".join(units)) if x)
                if rec["confidence"] == "high":
                    rec["confidence"] = "medium"

    warnings = []
    if factor > FACTOR_HIGH:
        warnings.append({"code": "FACTOR_HIGH", "message": "factor above 4: a bigger pan, a second batch or longer mixing may be needed; test before trusting linear amounts"})
    if factor < FACTOR_LOW:
        warnings.append({"code": "FACTOR_LOW", "message": "factor below 0.25: tiny amounts are hard to measure; consider weighing or making a full batch and freezing or sharing"})
    if args.from_pan:
        warnings.append({"code": "PAN_DEPTH", "message": "pan factor is the area ratio and assumes the same batter depth; a deeper or shallower layer changes the cooking time"})
    if factor != 1:
        warnings.append({"code": "COOK_TIME", "message": "cook time and temperature are not computed; they do not scale with the factor, so go by the recipe's own doneness test"})

    flagged = sum(1 for r in lines if r["note"])
    result = {
        "tool": "scale_recipe", "version": VERSION,
        "factor": {"value": round(float(factor), 4), "exact": str(factor), "basis": basis},
        "settings": {"units": args.units, "basis": args.basis, "system": args.system,
                     "density": "user file plus bundled approximate table" if args.density else "bundled approximate table"},
        "summary": {"lines": len(lines), "unparsed": len(unparsed), "converted": sum(1 for r in lines if r["converted"]),
                    "with_notes": flagged},
        "lines": lines, "unparsed": unparsed, "warnings": warnings,
        "scaled_list": [r["converted"] or r["scaled"] for r in lines],
    }
    if args.format == "text":
        out = "\n".join(result["scaled_list"] + ["", "factor: %s (%s)" % (result["factor"]["value"], basis)]
                        + ["warning: " + w["message"] for w in warnings]
                        + ["not parsed: %s (%s)" % (u["original"], u["reason"]) for u in unparsed]) + "\n"
    else:
        out = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(out)
        except OSError as exc:
            return fail("cannot write %s: %s" % (args.out, exc))
        sys.stderr.write("wrote %s\n" % args.out)
    else:
        sys.stdout.write(out)
    return 1 if unparsed else 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
