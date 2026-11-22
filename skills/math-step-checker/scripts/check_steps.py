#!/usr/bin/env python3
"""check_steps.py - re-evaluate the lines of a worked arithmetic or algebra solution.

Usage:
    python check_steps.py STEPS_FILE        # one step per line, UTF-8; "-" reads stdin

Reads the file, writes nothing, uses no network. Prints one JSON document to stdout.
Exit codes: 0 no step is wrong, 1 at least one step is wrong (see "first_error"),
2 unusable input (missing or empty file, bad encoding, too many lines).

Line format (details in SKILL.md):
    a = b = c      numeric claim: every side must have the same value (exact fractions)
    a ~= b         rounding claim; also written with the approximately-equal sign
    2x + 3 = 11    equation: compared with the previous equation by solution set
    3(x+2) - 4     expression: compared with the previous expression at 20 points
    = 12 + 12      continuation: the previous line's last side is the left side
    5 [m]          a number with a unit; units are written in square brackets
Allowed: numbers, single-letter variables, + - * / ^ ( ), sqrt( ), abs( ), implicit
multiplication (2x, 3(x+1)). Expressions are parsed with the ast module and evaluated by a
whitelist walker; nothing is ever passed to eval or exec.
"""
import ast
import json
import math
import re
import sys
from decimal import Decimal, InvalidOperation
from fractions import Fraction

VERSION = "0.1.0"

MAX_LINES = 200            # a worked solution longer than this is almost certainly the wrong input
MAX_LINE_CHARS = 300       # keeps parse time and note size bounded
MAX_TOKENS = 120           # per side; deep nesting is a sign of a pasted formula, not a school step
MAX_NODES = 250            # AST size cap per side
MAX_EXP = 64               # exact integer powers only up to this; beyond it floats are used
GRID_LO, GRID_HI, GRID_N = -100.0, 100.0, 4000   # root search: step 0.05 over [-100, 100]
CLOSE = 1e-5               # two roots closer than this (relative to max(1, |r|)) are the same root
ZERO_TOL = 1e-9            # a float value this small counts as a root during the search
MIN_POINTS = 5             # valid sample points needed before two expressions count as equal
DRIFT = Fraction(1, 100)   # 1 percent: cumulative relative error of reused rounded values
SLIP_CONSTANT_LIMIT = 8    # number of literals tried when looking for a one-sided operation
MAX_REPORTED_ROOTS = 6

# 20 fixed sample points: never 0, 1 or -1, mixed signs, mixed denominators, so that
# accidental equality of two different expressions is very unlikely and runs repeat exactly.
POINTS = [Fraction(n, d) for n, d in (
    (2, 1), (-3, 1), (1, 2), (5, 3), (-7, 4), (7, 1), (3, 5), (-2, 9), (11, 5), (-13, 6),
    (4, 1), (-5, 1), (9, 2), (1, 7), (-8, 3), (13, 4), (6, 1), (-11, 7), (17, 5), (-19, 8))]

ZERO_DIMS = (0, 0, 0)  # exponents of metre, kilogram, second
UNITS = {
    "m": (Fraction(1), (1, 0, 0)), "cm": (Fraction(1, 100), (1, 0, 0)),
    "mm": (Fraction(1, 1000), (1, 0, 0)), "km": (Fraction(1000), (1, 0, 0)),
    "g": (Fraction(1, 1000), (0, 1, 0)), "kg": (Fraction(1), (0, 1, 0)),
    "mg": (Fraction(1, 1000000), (0, 1, 0)),
    "s": (Fraction(1), (0, 0, 1)), "ms": (Fraction(1, 1000), (0, 0, 1)),
    "min": (Fraction(60), (0, 0, 1)), "h": (Fraction(3600), (0, 0, 1)),
    "L": (Fraction(1, 1000), (3, 0, 0)), "mL": (Fraction(1, 1000000), (3, 0, 0)),
}
FUNCS = ("sqrt", "abs")

SLIPS = {
    "sign_when_moving_term": "A term was moved to the other side without changing its sign.",
    "distribute_negative": "A minus sign in front of a bracket was not applied to every term inside it.",
    "dropped_parenthesis": "A factor was applied to the first term of a bracket only, as if the bracket were dropped.",
    "divide_only_one_term": "A sum was divided by a number but only one term was divided.",
    "fraction_no_common_denominator": "Fractions were added by adding numerators and denominators instead of using a common denominator.",
    "exponent_rule": "An exponent or root rule was misapplied (for example (a+b)^2 treated as a^2+b^2).",
    "operation_on_one_side_only": "A number was multiplied or divided on one side of the equation only.",
    "divided_by_expression_that_can_be_zero": "Both sides were divided by an expression that is zero for some x, which loses those solutions.",
    "sign_error": "The result has the right size but the wrong sign.",
    "decimal_place": "The result is off by a power of ten: a decimal point slip.",
    "unit_conversion_factor": "The sides differ by a unit conversion factor.",
    "truncated_not_rounded": "The value was cut off instead of rounded.",
}

# Worst first: a line with several findings reports the first status in this list that occurs.
RANK = ["unparseable", "unit_mismatch", "not_equivalent", "solution_lost", "possibly_extraneous",
        "rounded_unmarked", "unchecked", "rounded", "equivalent", "given"]
ERRORS = {"unparseable", "unit_mismatch", "not_equivalent", "solution_lost"}
LIMITS = [
    "No calculus, no inequalities, no word problems, no matrices, no trigonometry or logarithms.",
    "Equations are compared by real solutions found in [-100, 100] with one variable; with several variables only scalar-multiple rewrites are proven.",
    "Unknown slip patterns are reported as suspected_slip null: a wrong step is still wrong.",
    "A passing check means the line is consistent with the previous line, not that the method is the best one.",
]


class ParseError(Exception):
    pass


class UnitError(Exception):
    pass


class DomainError(Exception):
    pass


NUMS = {}  # placeholder name -> Q for every number literal parsed in this run


class Q:
    """A value (Fraction when exact, float otherwise) with SI dimension exponents."""
    __slots__ = ("v", "d")

    def __init__(self, v, d=ZERO_DIMS):
        self.v = v
        self.d = d


def dims_text(d):
    parts = ["%s^%d" % (sym, e) for sym, e in zip(("m", "kg", "s"), d) if e]
    return " ".join(parts) if parts else "dimensionless"


def fmt_num(v):
    if isinstance(v, Fraction):
        if max(v.numerator.bit_length(), v.denominator.bit_length()) > 100:  # too long to print exactly
            try:
                return "about %.6g" % float(v)
            except OverflowError:
                return "a very large number"
        if v.denominator == 1:
            return str(v.numerator)
        den = v.denominator
        while den % 2 == 0:
            den //= 2
        while den % 5 == 0:
            den //= 5
        if den == 1:  # terminating decimal: show it exactly
            return str(Decimal(v.numerator) / Decimal(v.denominator))
        return "%d/%d (about %.6g)" % (v.numerator, v.denominator, float(v))
    return "%.6g" % v


def same(a, b):
    if isinstance(a, Fraction) and isinstance(b, Fraction):
        return a == b
    try:
        fa, fb = float(a), float(b)
    except OverflowError:
        return a == b
    return abs(fa - fb) <= 1e-9 * max(1.0, abs(fa), abs(fb))


def is_zero(v):
    return v == 0 if isinstance(v, Fraction) else abs(v) < 1e-12


# ---------------------------------------------------------------- tokenising and parsing

TOKEN_RE = re.compile(r"\s*(?:(\d+\.\d+|\d+|\.\d+)|([A-Za-z]+)|\[([A-Za-z]+)\]|(\*\*|[-+*/^()]))")
REPLACEMENTS = (("×", "*"), ("·", "*"), ("⋅", "*"), ("÷", "/"), ("−", "-"),
                ("–", "-"), ("²", "^2"), ("³", "^3"), ("√", "sqrt"))


class Expr:
    def __init__(self, tree, variables, literals, text):
        self.tree = tree
        self.variables = variables
        self.literals = literals  # list of (Fraction, decimals)
        self.text = text


def tokenize(text):
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    toks, pos = [], 0
    while pos < len(text):
        m = TOKEN_RE.match(text, pos)
        if not m:
            if not text[pos:].strip():
                break
            raise ParseError("unexpected character %r" % text[pos:].lstrip()[0])
        pos = m.end()
        num, word, unit, op = m.groups()
        if num is not None:
            try:
                frac = Fraction(Decimal(num))
            except InvalidOperation:
                raise ParseError("bad number %r" % num)
            toks.append(("num", (frac, len(num.split(".")[1]) if "." in num else 0)))
        elif word is not None:
            if word in FUNCS:
                toks.append(("func", word))
            elif word.lower() in ("or", "and"):
                raise ParseError("write one equation per line instead of joining them with %r" % word)
            elif len(word) > 2:
                raise ParseError("unknown word %r: variables are single letters, functions are sqrt and abs" % word)
            else:
                toks.extend(("var", ch) for ch in word)
        elif unit is not None:
            if unit not in UNITS:
                raise ParseError("unknown unit [%s]; known: %s" % (unit, " ".join(sorted(UNITS))))
            toks.append(("unit", unit))
        elif op == "(":
            toks.append(("lp", op))
        elif op == ")":
            toks.append(("rp", op))
        else:
            toks.append(("op", op))
        if len(toks) > MAX_TOKENS:
            raise ParseError("expression too long")
    return toks


def validate(tree):
    call_funcs = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if not (isinstance(node.func, ast.Name) and node.func.id in FUNCS
                    and len(node.args) == 1 and not node.keywords):
                raise ParseError("only sqrt(x) and abs(x) may be called")
            call_funcs.add(id(node.func))
    count = 0
    for node in ast.walk(tree):
        count += 1
        if count > MAX_NODES:
            raise ParseError("expression too long")
        if isinstance(node, (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Load, ast.Add, ast.Sub,
                             ast.Mult, ast.Div, ast.Pow, ast.UAdd, ast.USub, ast.Call)):
            continue
        if isinstance(node, ast.Name):
            if node.id in FUNCS:
                if id(node) not in call_funcs:
                    raise ParseError("%s must be followed by brackets, for example %s(9)" % (node.id, node.id))
            elif not re.fullmatch(r"N\d+|v_[A-Za-z]|U_[A-Za-z]+", node.id):
                raise ParseError("unsupported name")
            continue
        raise ParseError("unsupported syntax")


def parse_expr(text):
    toks = tokenize(text)
    if not toks:
        raise ParseError("empty expression")
    pieces, literals, variables, prev = [], [], set(), None
    for kind, val in toks:
        if prev is not None and prev in ("num", "var", "unit", "rp") and kind in ("num", "var", "func", "unit", "lp"):
            if prev == "num" and kind == "num":
                raise ParseError("two numbers in a row; put an operator between them")
            pieces.append("*")  # implicit multiplication: 2x, 3(x+1), (a)(b)
        if kind == "num":
            name = "N%d" % len(NUMS)
            NUMS[name] = Q(val[0])
            literals.append(val)
            pieces.append(name)
        elif kind == "var":
            variables.add(val)
            pieces.append("v_" + val)
        elif kind == "unit":
            pieces.append("U_" + val)
        elif kind == "op":
            pieces.append("**" if val in ("^", "**") else val)
        else:
            pieces.append(val)
        prev = kind
    try:
        tree = ast.parse(" ".join(pieces), mode="eval")
    except (SyntaxError, RecursionError, ValueError):
        raise ParseError("could not read this as an expression; check brackets and operators")
    validate(tree)
    return Expr(tree, variables, literals, text.strip())


# ---------------------------------------------------------------- evaluation (whitelist walker)

def q_add(a, b, sign):
    if a.d != b.d:
        raise UnitError("cannot %s %s and %s" % ("add" if sign > 0 else "subtract", dims_text(a.d), dims_text(b.d)))
    return Q(a.v + sign * b.v, a.d)


def q_sqrt(a):
    if a.v < 0:
        raise DomainError("square root of a negative number")
    if any(e % 2 for e in a.d):
        raise UnitError("square root of a quantity with odd unit exponents")
    d = tuple(e // 2 for e in a.d)
    if isinstance(a.v, Fraction):
        n, den = a.v.numerator, a.v.denominator
        rn, rd = math.isqrt(n), math.isqrt(den)
        if rn * rn == n and rd * rd == den:
            return Q(Fraction(rn, rd), d)
    return Q(math.sqrt(float(a.v)), d)


def q_pow(a, b):
    if b.d != ZERO_DIMS:
        raise UnitError("an exponent cannot have units")
    e = b.v
    if isinstance(e, Fraction) and e.denominator == 1 and abs(e.numerator) <= MAX_EXP:
        n = e.numerator
        if is_zero(a.v) and n <= 0:
            raise DomainError("zero to a non-positive power")
        return Q(a.v ** n, tuple(x * n for x in a.d))
    if a.d != ZERO_DIMS:
        raise UnitError("a non-integer or very large power of a quantity with units")
    if isinstance(e, Fraction) and e == Fraction(1, 2):
        return q_sqrt(a)
    av, evf = float(a.v), float(e)
    if (av == 0 and evf <= 0) or (av < 0 and evf != math.floor(evf)):
        raise DomainError("power is not a real number")
    return Q(av ** evf, ZERO_DIMS)


def ev(node, vs):
    t = type(node)
    if t is ast.Expression:
        return ev(node.body, vs)
    if t is ast.Constant:  # only built internally, never produced by parse_expr
        return Q(Fraction(node.value))
    if t is ast.Name:
        n = node.id
        if n in vs:
            return vs[n]
        if n in NUMS:
            return NUMS[n]
        if n.startswith("U_"):
            scale, dims = UNITS[n[2:]]
            return Q(scale, dims)
        raise DomainError("variable %s has no value" % n[2:])
    if t is ast.UnaryOp:
        a = ev(node.operand, vs)
        return Q(-a.v if isinstance(node.op, ast.USub) else a.v, a.d)
    if t is ast.BinOp:
        a, b, op = ev(node.left, vs), ev(node.right, vs), node.op
        if isinstance(op, ast.Add):
            return q_add(a, b, 1)
        if isinstance(op, ast.Sub):
            return q_add(a, b, -1)
        if isinstance(op, ast.Mult):
            return Q(a.v * b.v, tuple(x + y for x, y in zip(a.d, b.d)))
        if isinstance(op, ast.Div):
            if is_zero(b.v):
                raise DomainError("division by zero")
            return Q(a.v / b.v, tuple(x - y for x, y in zip(a.d, b.d)))
        if isinstance(op, ast.Pow):
            return q_pow(a, b)
    if t is ast.Call:
        a = ev(node.args[0], vs)
        if node.func.id == "sqrt":
            return q_sqrt(a)
        return Q(abs(a.v), a.d)
    raise ParseError("unsupported syntax")


def safe_ev(tree, vs):
    try:
        return ev(tree, vs)
    except (OverflowError, ZeroDivisionError, ValueError):
        raise DomainError("value too large to evaluate")


def point_vars(variables, i):
    return {"v_" + v: Q(POINTS[(i + 3 * j) % len(POINTS)]) for j, v in enumerate(variables)}


def trees_compare(t1, t2, variables):
    """'equal', 'different', 'insufficient' or ('unit', message) over the fixed sample points."""
    points = len(POINTS) if variables else 1
    valid, domain_diff = 0, False
    for i in range(points):
        vs = point_vars(variables, i)
        a = b = None
        ea = eb = False
        try:
            a = safe_ev(t1, vs)
        except DomainError:
            ea = True
        try:
            b = safe_ev(t2, vs)
        except DomainError:
            eb = True
        if ea and eb:
            continue
        if ea != eb:
            domain_diff = True
            continue
        if a.d != b.d:
            return "unit", "left side is %s but right side is %s" % (dims_text(a.d), dims_text(b.d))
        valid += 1
        if not same(a.v, b.v):
            return "different", domain_diff
    return ("equal" if valid >= (MIN_POINTS if variables else 1) else "insufficient"), domain_diff


def eq_diff(t1, t2, vs):
    a, b = safe_ev(t1, vs), safe_ev(t2, vs)
    if a.d != b.d:
        raise UnitError("left side is %s but right side is %s" % (dims_text(a.d), dims_text(b.d)))
    return a.v - b.v


def proportional(p, c, variables):
    """True when (c.left - c.right) is a constant non-zero multiple of (p.left - p.right)."""
    ratios, both_zero = [], 0
    for i in range(len(POINTS)):
        vs = point_vars(variables, i)
        try:
            fp, fc = eq_diff(p[0], p[1], vs), eq_diff(c[0], c[1], vs)
        except DomainError:
            continue
        except UnitError:
            return False
        zp, zc = is_zero(fp), is_zero(fc)
        if zp and zc:
            both_zero += 1
        elif zp or zc:
            return False
        else:
            ratios.append(fc / fp)
    if not ratios:
        return both_zero >= MIN_POINTS
    return len(ratios) >= 3 and all(same(r, ratios[0]) for r in ratios)


# ---------------------------------------------------------------- real-root search (one variable)

def find_roots(f):
    xs = [GRID_LO + (GRID_HI - GRID_LO) * i / GRID_N for i in range(GRID_N + 1)]
    ys = []
    for x in xs:
        try:
            ys.append(float(f(x)))
        except (DomainError, UnitError, ValueError, OverflowError, ZeroDivisionError):
            ys.append(None)
    valid = [y for y in ys if y is not None]
    if len(valid) < 10:
        return "nodomain", []
    if all(abs(y) <= 1e-7 for y in valid):
        return "identity", []
    roots = []

    def add(r):
        if all(abs(r - q) > CLOSE * max(1.0, abs(r)) for q in roots):
            roots.append(r)

    def safe(x):
        try:
            return abs(float(f(x)))
        except (DomainError, UnitError, ValueError, OverflowError, ZeroDivisionError):
            return None

    minima_runs = 0
    for i, y in enumerate(ys):
        if y is None:
            continue
        if abs(y) <= ZERO_TOL:
            add(xs[i])
        nxt = ys[i + 1] if i + 1 < len(ys) else None
        if nxt is not None and y * nxt < 0:
            lo, hi, flo = xs[i], xs[i + 1], y
            for _ in range(80):
                mid = (lo + hi) / 2
                fm = safe(mid)
                if fm is None:
                    break
                fv = float(f(mid))
                if fv == 0:
                    lo = hi = mid
                    break
                if (fv < 0) == (flo < 0):
                    lo, flo = mid, fv
                else:
                    hi = mid
            r = (lo + hi) / 2
            fr = safe(r)
            if fr is not None and fr <= 1e-6:  # a pole (1/x) flips sign but is not small
                add(r)
        prv = ys[i - 1] if i > 0 else None
        if prv is not None and nxt is not None and abs(y) < abs(prv) and abs(y) <= abs(nxt) and minima_runs < 60:
            minima_runs += 1
            lo, hi = xs[i - 1], xs[i + 1]
            for _ in range(100):
                m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
                f1, f2 = safe(m1), safe(m2)
                if f1 is None or f2 is None:
                    break
                if f1 < f2:
                    hi = m2
                else:
                    lo = m1
            m = (lo + hi) / 2
            fm = safe(m)
            if fm is not None and fm <= ZERO_TOL:
                add(m)
    return "roots", sorted(roots)


def diff_fn(pair, vname):
    key = "v_" + vname

    def f(x):
        vs = {key: Q(x)}
        return eq_diff(pair[0], pair[1], vs)
    return f


def fmt_root(vname, r):
    fr = Fraction(r).limit_denominator(1000)
    if abs(float(fr) - r) < 1e-7:
        return "%s = %s" % (vname, str(fr.numerator) if fr.denominator == 1 else "%d/%d" % (fr.numerator, fr.denominator))
    return "%s ~ %.6g" % (vname, r)


def close(a, b):
    return abs(a - b) <= CLOSE * max(1.0, abs(a), abs(b))


def diff_sets(prev, cur):
    added = [r for r in cur if not any(close(r, q) for q in prev)]
    lost = [q for q in prev if not any(close(q, r) for r in cur)]
    return added, lost


# ---------------------------------------------------------------- slip search (known wrong rewrites)

def is_sum(n):
    return isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub))


def bn(l, op, r):
    return ast.BinOp(left=l, op=op, right=r)


def local_slips(n):
    out = []
    if isinstance(n, ast.BinOp):
        l, r, op = n.left, n.right, n.op
        if isinstance(op, ast.Mult):
            if is_sum(r):
                out.append(("dropped_parenthesis", bn(bn(l, ast.Mult(), r.left), r.op, r.right)))
            if is_sum(l):
                out.append(("dropped_parenthesis", bn(bn(l.left, ast.Mult(), r), l.op, l.right)))
            if (isinstance(l, ast.BinOp) and isinstance(l.op, ast.Pow) and isinstance(r, ast.BinOp)
                    and isinstance(r.op, ast.Pow) and ast.dump(l.left) == ast.dump(r.left)):
                out.append(("exponent_rule", bn(l.left, ast.Pow(), bn(l.right, ast.Mult(), r.right))))
        if isinstance(op, ast.Div) and is_sum(l):
            out.append(("divide_only_one_term", bn(bn(l.left, ast.Div(), r), l.op, l.right)))
        if isinstance(op, ast.Sub) and is_sum(r):
            out.append(("distribute_negative", bn(bn(l, ast.Sub(), r.left), r.op, r.right)))
        if (isinstance(op, (ast.Add, ast.Sub)) and isinstance(l, ast.BinOp) and isinstance(l.op, ast.Div)
                and isinstance(r, ast.BinOp) and isinstance(r.op, ast.Div)):
            out.append(("fraction_no_common_denominator", bn(bn(l.left, op, r.left), ast.Div(), bn(l.right, op, r.right))))
            out.append(("fraction_no_common_denominator", bn(bn(l.left, op, r.left), ast.Div(), bn(l.right, ast.Mult(), r.right))))
        if isinstance(op, ast.Pow):
            if is_sum(l):
                out.append(("exponent_rule", bn(bn(l.left, ast.Pow(), r), l.op, bn(l.right, ast.Pow(), r))))
            if isinstance(l, ast.BinOp) and isinstance(l.op, ast.Pow):
                out.append(("exponent_rule", bn(l.left, ast.Pow(), bn(l.right, ast.Add(), r))))
    elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub) and is_sum(n.operand):
        o = n.operand
        out.append(("distribute_negative", bn(ast.UnaryOp(op=ast.USub(), operand=o.left), o.op, o.right)))
    elif isinstance(n, ast.Call) and n.func.id == "sqrt" and is_sum(n.args[0]):
        a = n.args[0]
        mk = lambda x: ast.Call(func=ast.Name(id="sqrt", ctx=ast.Load()), args=[x], keywords=[])
        out.append(("exponent_rule", bn(mk(a.left), a.op, mk(a.right))))
    return out


def alt_nodes(n):
    """Yield (slip name, tree) for each single wrong rewrite found anywhere inside n."""
    for item in local_slips(n):
        yield item
    if isinstance(n, ast.BinOp):
        for nm, nn in alt_nodes(n.left):
            yield nm, bn(nn, n.op, n.right)
        for nm, nn in alt_nodes(n.right):
            yield nm, bn(n.left, n.op, nn)
    elif isinstance(n, ast.UnaryOp):
        for nm, nn in alt_nodes(n.operand):
            yield nm, ast.UnaryOp(op=n.op, operand=nn)
    elif isinstance(n, ast.Call):
        for nm, nn in alt_nodes(n.args[0]):
            yield nm, ast.Call(func=n.func, args=[nn], keywords=[])


def flat_terms(n, sign=1):
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
        return flat_terms(n.left, sign) + flat_terms(n.right, sign)
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Sub):
        return flat_terms(n.left, sign) + flat_terms(n.right, -sign)
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
        return flat_terms(n.operand, -sign)
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.UAdd):
        return flat_terms(n.operand, sign)
    return [(sign, n)]


def build_sum(terms):
    acc = None
    for s, n in terms:
        if acc is None:
            acc = n if s > 0 else ast.UnaryOp(op=ast.USub(), operand=n)
        else:
            acc = bn(acc, ast.Add() if s > 0 else ast.Sub(), n)
    return acc if acc is not None else ast.Constant(value=0)


def expr_slip(prev_tree, cur_tree, variables):
    body = prev_tree.body if isinstance(prev_tree, ast.Expression) else prev_tree
    for name, cand in alt_nodes(body):
        try:
            verdict = trees_compare(cand, cur_tree, variables)[0]
        except (UnitError, DomainError, ParseError):
            continue
        if verdict == "equal":
            return name
    return None


def eq_slip(prev, cur, variables):
    """prev and cur are (left_tree, right_tree). Returns a slip name or None."""
    pl = prev[0].body if isinstance(prev[0], ast.Expression) else prev[0]
    pr = prev[1].body if isinstance(prev[1], ast.Expression) else prev[1]
    cands = []
    for name, new in alt_nodes(pl):
        cands.append((name, (new, pr)))
    for name, new in alt_nodes(pr):
        cands.append((name, (pl, new)))
    lt, rt = flat_terms(pl), flat_terms(pr)
    for i, (s, n) in enumerate(lt):  # move from left to right keeping the sign
        cands.append(("sign_when_moving_term", (build_sum(lt[:i] + lt[i + 1:]), build_sum(rt + [(s, n)]))))
    for i, (s, n) in enumerate(rt):
        cands.append(("sign_when_moving_term", (build_sum(lt + [(s, n)]), build_sum(rt[:i] + rt[i + 1:]))))
    consts = []
    for node in ast.walk(ast.Expression(body=bn(pl, ast.Add(), pr))):
        if isinstance(node, ast.Name) and node.id in NUMS:
            v = NUMS[node.id].v
            if v != 0 and v not in consts and -v not in consts:
                consts.append(v)
    for k in consts[:SLIP_CONSTANT_LIMIT]:
        kn = ast.Constant(value=k.numerator) if k.denominator == 1 else bn(ast.Constant(value=k.numerator), ast.Div(), ast.Constant(value=k.denominator))
        for mop in (ast.Mult(), ast.Div()):
            cands.append(("operation_on_one_side_only", (bn(pl, mop, kn), pr)))
            cands.append(("operation_on_one_side_only", (pl, bn(pr, mop, kn))))
    for name, cand in cands:
        try:
            if proportional(cand, cur, variables):
                return name
        except (ParseError, DomainError, UnitError):
            continue
    return None


# ---------------------------------------------------------------- rounding helpers

def round_half_up(x, d):
    f = Fraction(x)
    scale = Fraction(10) ** d
    s = f * scale
    r = Fraction(math.floor(abs(s) + Fraction(1, 2)))
    return (r if s >= 0 else -r) / scale


def truncate(x, d):
    f = Fraction(x)
    scale = Fraction(10) ** d
    s = f * scale
    r = Fraction(math.floor(abs(s)))
    return (r if s >= 0 else -r) / scale


def is_plain_number(expr):
    """True for 'number', '-number', 'number [unit]': the only shapes allowed right of a rounding sign."""
    if len(expr.literals) != 1 or expr.variables:
        return False
    for node in ast.walk(expr.tree):
        if isinstance(node, (ast.Call, ast.Pow, ast.Div, ast.Add, ast.Sub)):
            return False
    return True


def rel_error(exact, shown):
    d = abs(Fraction(exact) - Fraction(shown)) if isinstance(exact, Fraction) and isinstance(shown, Fraction) else abs(float(exact) - float(shown))
    return d / abs(exact) if not is_zero(exact) else d


def numeric_slip(a, b, lhs_tree):
    if not is_zero(a.v) and same(a.v, -b.v):
        return "sign_error"
    if not is_zero(a.v) and not is_zero(b.v) and isinstance(a.v, Fraction) and isinstance(b.v, Fraction) and a.d == b.d:
        ratio = b.v / a.v
        for k in range(1, 7):
            if ratio in (Fraction(10) ** k, Fraction(1, 10 ** k)):
                return "decimal_place" if a.d == ZERO_DIMS else "unit_conversion_factor"
        if a.d != ZERO_DIMS and ratio in (Fraction(60), Fraction(3600), Fraction(1, 60), Fraction(1, 3600)):
            return "unit_conversion_factor"
    for name, cand in alt_nodes(lhs_tree.body):
        try:
            c = safe_ev(cand, {})
        except (DomainError, UnitError, ParseError):
            continue
        if c.d == b.d and same(c.v, b.v):
            return name
    return None


# ---------------------------------------------------------------- the checker

def split_line(text, prev_last_text):
    t = text.replace("==", "=").replace("~=", "≈")
    parts = re.split("(=|≈)", t)
    sides, ops = parts[0::2], parts[1::2]
    if ops and not sides[0].strip():
        if prev_last_text is None:
            raise ParseError("a line starting with = continues the previous line, but there is nothing to continue (only expression and number lines can be continued)")
        sides[0] = prev_last_text
    for s in sides:
        if not s.strip():
            raise ParseError("one side of an = sign is empty")
    return sides, ops


class Checker:
    def __init__(self):
        self.prev_eq = None
        self.prev_roots = None
        self.prev_last = None
        self.prev_last_text = None
        self.extraneous = []
        self.rounded = []      # (shown Fraction, relative error, step)
        self.cum = Fraction(0)
        self.drift_flagged = False
        self.rounded_steps = 0

    def slip(self, name, extra=None):
        if name is None:
            return None
        expl = SLIPS[name] + ((" " + extra) if extra else "")
        return {"name": name, "explanation": expl}

    def note_drift(self, rec, exprs, step):
        """Add the relative error of every earlier rounded value that is reused in this line."""
        seen = set()
        for e in exprs:
            for val, _dec in e.literals:
                for shown, rel, from_step in self.rounded:
                    if val == shown and from_step != step and (from_step, val) not in seen:
                        seen.add((from_step, val))
                        self.cum += Fraction(rel) if isinstance(rel, Fraction) else Fraction(float(rel))
                        rec["notes"].append("uses %s, a rounded value from step %d (relative error %.4g)" % (fmt_num(val), from_step, float(rel)))
        if seen and self.cum >= DRIFT:
            rec["flags"].append("rounding_drift")
            rec["notes"].append("rounding errors reused so far add up to %.4g of the exact value; keep more digits until the last step" % float(self.cum))
            self.drift_flagged = True

    def register_rounded(self, rec, shown, rel, step):
        self.rounded.append((shown, rel, step))
        self.rounded_steps += 1
        if rel > DRIFT:
            rec["flags"].append("large_rounding_error")
            rec["notes"].append("rounding changes the value by more than 1 percent (%.4g)" % float(rel))

    # ----- numeric pair: a = b or a ~= b with no variables
    def numeric_pair(self, rec, lhs, rhs, op, step):
        try:
            a, b = safe_ev(lhs.tree, {}), safe_ev(rhs.tree, {})
        except UnitError as exc:
            return "unit_mismatch", ["%s" % exc]
        except DomainError as exc:
            if "too large" in str(exc):
                return "unchecked", ["%s" % exc]
            return "not_equivalent", ["a side is undefined: %s" % exc]
        if a.d != b.d:
            return "unit_mismatch", ["left side is %s but right side is %s" % (dims_text(a.d), dims_text(b.d))]
        if same(a.v, b.v):
            if op == "≈":
                return "equivalent", ["the two values are exactly equal; = would do"]
            return "equivalent", []
        plain = is_plain_number(rhs)
        if plain:
            lit, dec = rhs.literals[0]
            scale = abs(b.v) / lit if lit != 0 else Fraction(1)
            disp = a.v / scale
            shown = lit if b.v >= 0 else -lit
            if same(round_half_up(disp, dec), shown):
                rel = rel_error(a.v, b.v)
                self.register_rounded(rec, shown, rel, step)
                if op == "≈":
                    return "rounded", ["%s rounded to %d decimal place(s) is %s; error %.4g" % (fmt_num(disp), dec, fmt_num(shown), float(rel))]
                return "rounded_unmarked", ["left side is %s; the right side is that value rounded to %d decimal place(s), so write the rounding sign instead of =" % (fmt_num(disp), dec)]
            if same(truncate(disp, dec), shown):
                return "not_equivalent", ["%s cut to %d decimal place(s) gives %s, but rounding gives %s" % (fmt_num(disp), dec, fmt_num(shown), fmt_num(round_half_up(disp, dec)))], "truncated_not_rounded"
        elif op == "≈":
            return "unparseable", ["the right side of the rounding sign must be a single number, optionally with a [unit]"]
        notes = ["left side is %s, right side is %s" % (fmt_num(a.v), fmt_num(b.v))]
        if a.d != ZERO_DIMS:
            notes.append("quantities with units are compared in SI base units (metre, kilogram, second)")
        return "not_equivalent", notes, numeric_slip(a, b, lhs.tree)

    def link(self, rec, cur_expr, step):
        """Compare an expression-only line with the previous expression or last side."""
        prev = self.prev_last
        allv = sorted(prev.variables | cur_expr.variables)
        try:
            verdict, info = trees_compare(prev.tree, cur_expr.tree, allv)
        except UnitError as exc:
            return "unit_mismatch", [str(exc)], None
        if verdict == "unit":
            return "unit_mismatch", [info], None
        if verdict == "equal":
            notes = ["the two expressions agree at every tested point"]
            if info:
                notes.append("they are not defined at exactly the same points: check the domain")
            return "equivalent", notes, None
        if verdict == "insufficient":
            return "unchecked", ["too few points where both expressions are defined"], None
        return "not_equivalent", ["this line is not equal to the previous expression"], expr_slip(prev.tree, cur_expr.tree, allv)

    def domain_notes(self, rec, exprs, variables):
        if len(variables) != 1:
            return
        vname = variables[0]
        key = "v_" + vname
        for e in exprs:
            for node in ast.walk(e.tree):
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) and any(
                        isinstance(m, ast.Name) and m.id == key for m in ast.walk(node.right)):
                    kind, roots = find_roots(diff_fn((node.right, ast.Constant(value=0)), vname))
                    for r in roots[:3]:
                        rec["domain"].append("division by an expression that is zero at %s: %s is not allowed" % (fmt_root(vname, r), vname))
                if isinstance(node, ast.Call) and node.func.id == "sqrt" and any(
                        isinstance(m, ast.Name) and m.id == key for m in ast.walk(node.args[0])):
                    rec["domain"].append("a square root contains %s: its argument must be zero or positive, so check every candidate in the original equation" % vname)
        rec["domain"] = sorted(set(rec["domain"]))

    # ----- equation: exactly one = sign and at least one variable
    def equation(self, rec, left, right, step):
        variables = sorted(left.variables | right.variables)
        pair = (left.tree, right.tree)
        for i in range(len(POINTS)):
            try:
                eq_diff(pair[0], pair[1], point_vars(variables, i))
                break
            except UnitError as exc:
                rec["status"], rec["notes"] = "unit_mismatch", [str(exc)]
                return
            except DomainError:
                continue
        cur_roots = None
        if len(variables) == 1:
            cur_roots = find_roots(diff_fn(pair, variables[0]))
            kind, roots = cur_roots
            if kind == "identity":
                rec["solutions"] = ["all real %s" % variables[0]]
            elif kind == "roots":
                rec["solutions"] = [fmt_root(variables[0], r) for r in roots[:MAX_REPORTED_ROOTS]]
        self.domain_notes(rec, [left, right], variables)
        status, notes, slip = "given", [], None
        if self.prev_eq is not None:
            pe = self.prev_eq
            prev_pair = (pe[0].tree, pe[1].tree)
            allv = sorted(set(pe[0].variables) | set(pe[1].variables) | set(variables))
            if proportional(prev_pair, pair, allv):
                status = "equivalent"
                notes.append("same solutions as the previous equation")
            elif len(allv) == 1 and cur_roots is not None:
                prev_roots = self.prev_roots if self.prev_roots is not None else find_roots(diff_fn(prev_pair, allv[0]))
                status, notes, slip = self.compare_roots(prev_roots, cur_roots, allv[0], prev_pair, pair, allv)
            else:
                name = eq_slip(prev_pair, pair, allv)
                if name:
                    status, notes, slip = "not_equivalent", ["not equivalent to the previous equation"], name
                else:
                    status = "unchecked"
                    notes.append("several variables: only scalar-multiple rewrites can be proven; check this step by hand")
        rec["status"], rec["notes"], rec["suspected_slip"] = status, notes, self.slip(slip)
        self.prev_eq = (left, right)
        self.prev_roots = cur_roots
        self.prev_last = None
        self.prev_last_text = None

    def compare_roots(self, prev, cur, vname, prev_pair, pair, allv):
        pk, pr = prev
        ck, cr = cur
        if pk == "nodomain" or ck == "nodomain":
            return "unchecked", ["no points where the equation is defined in [-100, 100]"], None
        if pk == "identity" and ck == "identity":
            return "equivalent", ["both lines are true for every %s" % vname], None
        if pk == "identity" or ck == "identity":
            return "not_equivalent", ["one line is true for every %s and the other is not" % vname], None
        if not pr and not cr:
            return "unchecked", ["no real solution was found for either line in [-100, 100]"], None
        added, lost = diff_sets(pr, cr)
        if not added and not lost:
            return "equivalent", ["same solutions: %s" % ", ".join(fmt_root(vname, r) for r in cr[:MAX_REPORTED_ROOTS])], None
        if added and not lost:
            self.extraneous.extend(added)
            sq = ast.Constant(value=2)
            squared = (bn(prev_pair[0].body if isinstance(prev_pair[0], ast.Expression) else prev_pair[0], ast.Pow(), sq),
                       bn(prev_pair[1].body if isinstance(prev_pair[1], ast.Expression) else prev_pair[1], ast.Pow(), sq))
            how = "squaring both sides" if proportional(squared, pair, allv) else "multiplying by an expression that contains %s, or squaring" % vname
            return "possibly_extraneous", ["this line has new solution(s) %s that the previous line did not (typical cause: %s); test each candidate in the ORIGINAL equation" % (
                ", ".join(fmt_root(vname, r) for r in added[:MAX_REPORTED_ROOTS]), how)], None
        if lost and not added:
            if all(any(close(q, e) for e in self.extraneous) for q in lost):
                return "equivalent", ["drops %s, which entered earlier as an extra solution; correct only if it was rejected by checking in the original equation" % ", ".join(fmt_root(vname, q) for q in lost)], None
            return "solution_lost", ["solution(s) %s of the previous line are missing here" % ", ".join(fmt_root(vname, q) for q in lost[:MAX_REPORTED_ROOTS])], "divided_by_expression_that_can_be_zero"
        name = eq_slip(prev_pair, pair, allv)
        return "not_equivalent", ["the solutions changed: previous %s, now %s" % (
            ", ".join(fmt_root(vname, r) for r in pr[:MAX_REPORTED_ROOTS]) or "none found",
            ", ".join(fmt_root(vname, r) for r in cr[:MAX_REPORTED_ROOTS]) or "none found")], name

    # ----- one line
    def line(self, rec, text, step):
        sides, ops = split_line(text, self.prev_last_text)
        exprs = [parse_expr(s) for s in sides]
        variables = sorted(set().union(*[e.variables for e in exprs]))
        rec["notes"] = []
        if not ops:
            rec["kind"] = "expression"
            if self.prev_last is None:
                status, notes, name = "given", [], None
            else:
                status, notes, name = self.link(rec, exprs[0], step)
            rec["status"], rec["notes"], rec["suspected_slip"] = status, notes, self.slip(name)
            self.note_drift(rec, exprs, step)
            self.domain_notes(rec, exprs, variables)
            self.prev_last, self.prev_last_text, self.prev_eq = exprs[0], sides[0].strip(), None
            return
        if len(ops) == 1 and variables:
            if ops[0] != "=":
                raise ParseError("the rounding sign is only for lines with numbers only")
            rec["kind"] = "equation"
            self.equation(rec, exprs[0], exprs[1], step)
            self.note_drift(rec, exprs, step)
            return
        rec["kind"] = "chain" if variables else "arithmetic"
        statuses, notes, name = [], [], None
        for k, op in enumerate(ops):
            lhs, rhs = exprs[k], exprs[k + 1]
            if variables:
                if op != "=":
                    raise ParseError("the rounding sign is only for lines with numbers only")
                allv = sorted(lhs.variables | rhs.variables)
                try:
                    verdict, info = trees_compare(lhs.tree, rhs.tree, allv)
                except UnitError as exc:
                    res = ("unit_mismatch", [str(exc)], None)
                else:
                    if verdict == "unit":
                        res = ("unit_mismatch", [info], None)
                    elif verdict == "equal":
                        res = ("equivalent", [], None)
                    elif verdict == "insufficient":
                        res = ("unchecked", ["too few points where both sides are defined"], None)
                    else:
                        res = ("not_equivalent", ["side %d and side %d are not equal" % (k + 1, k + 2)], expr_slip(lhs.tree, rhs.tree, allv))
            else:
                res = self.numeric_pair(rec, lhs, rhs, op, step)
                if len(res) == 2:
                    res = (res[0], res[1], None)
            statuses.append(res[0])
            notes.extend(res[1])
            if name is None and res[2]:
                name = res[2]
        status = min(statuses, key=RANK.index)
        rec["status"], rec["notes"] = status, notes
        rec["suspected_slip"] = self.slip(name) if status in ERRORS else None
        self.note_drift(rec, exprs, step)
        if variables:
            self.domain_notes(rec, exprs, variables)
        self.prev_last, self.prev_last_text = exprs[-1], sides[-1].strip()
        if variables:
            self.prev_eq = None


def analyse(lines, label):
    NUMS.clear()
    chk = Checker()
    steps = []
    for lineno, raw in enumerate(lines, 1):
        text = raw.split("#", 1)[0].strip()
        if not text:
            continue
        rec = {"step": len(steps) + 1, "line": lineno, "text": text, "kind": "unknown", "status": "given",
               "notes": [], "suspected_slip": None, "domain": [], "solutions": [], "flags": []}
        steps.append(rec)
        try:
            if len(text) > MAX_LINE_CHARS:
                raise ParseError("line is longer than %d characters" % MAX_LINE_CHARS)
            chk.line(rec, text, rec["step"])
        except ParseError as exc:
            rec["status"], rec["notes"], rec["suspected_slip"] = "unparseable", [str(exc), "this line was skipped; the next line is compared with the last line that could be read"], None
        except (UnitError, DomainError) as exc:  # defensive: should have been handled inside
            rec["status"], rec["notes"] = "unchecked", ["could not evaluate: %s" % exc]
    counts = {}
    for s in steps:
        counts[s["status"]] = counts.get(s["status"], 0) + 1
    first = next((s for s in steps if s["status"] in ERRORS), None)
    return {
        "tool": "check_steps", "version": VERSION, "input": label, "step_count": len(steps),
        "steps": steps,
        "first_error": None if first is None else {
            "step": first["step"], "line": first["line"], "text": first["text"], "status": first["status"],
            "suspected_slip": first["suspected_slip"]["name"] if first["suspected_slip"] else None},
        "counts": counts,
        "rounding": {"rounded_steps": chk.rounded_steps, "cumulative_relative_error": round(float(chk.cum), 6),
                     "drift_threshold": float(DRIFT), "drift_flagged": chk.drift_flagged},
        "limits": LIMITS,
    }


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or argv[0] in ("-h", "--help"):
        sys.stderr.write("usage: python check_steps.py STEPS_FILE   (one step per line; '-' reads stdin)\n")
        return 2
    try:
        if argv[0] == "-":
            data = sys.stdin.buffer.read().decode("utf-8-sig")
        else:
            with open(argv[0], "rb") as fh:
                data = fh.read().decode("utf-8-sig")
    except OSError as exc:
        sys.stderr.write("cannot read %s: %s\n" % (argv[0], exc.strerror or exc))
        return 2
    except UnicodeDecodeError:
        sys.stderr.write("the file is not valid UTF-8; save it as UTF-8 and run again\n")
        return 2
    lines = data.splitlines()
    if not any(l.split("#", 1)[0].strip() for l in lines):
        sys.stderr.write("no steps found: write one step per line\n")
        return 2
    if len(lines) > MAX_LINES:
        sys.stderr.write("more than %d lines: split the solution into parts\n" % MAX_LINES)
        return 2
    report = analyse(lines, argv[0])
    out = json.dumps(report, indent=2, allow_nan=False)
    try:
        sys.stdout.buffer.write((out + "\n").encode("utf-8"))
    except AttributeError:
        sys.stdout.write(out + "\n")
    return 1 if report["first_error"] else 0


if __name__ == "__main__":
    sys.exit(main())
