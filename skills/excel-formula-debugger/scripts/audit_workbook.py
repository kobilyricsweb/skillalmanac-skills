#!/usr/bin/env python3
"""audit_workbook.py - read-only formula audit of an .xlsx or .xlsm workbook.

Usage:
    python audit_workbook.py <workbook.xlsx> [--max-per-category N]

Reads the workbook as a zip of XML files (standard library only), never opens
a spreadsheet application, never recalculates, never writes anything and uses
no network. It prints one strict JSON document (no NaN, ASCII only) to stdout.

Checks: formulas per sheet; error values stored in cells, traced to the root
cell; references to missing sheets, to #REF!, to other workbooks and to empty
ranges; hard-coded constants inside formulas; volatile functions and how many
cells depend on them; nested IF depth; circular references found in the
dependency graph; formulas that differ from their column or row neighbours;
numbers stored as text; functions that need a newer spreadsheet version.

Exit codes: 0 audit ran and found no error-severity finding; 1 audit ran and
found at least one error-severity finding; 2 the file could not be read as a
workbook (message on stderr, nothing on stdout).
"""
import bisect
import io
import json
import math
import os
import re
import sys
import zipfile
from collections import Counter, defaultdict, deque
import xml.etree.ElementTree as ET

VERSION = "1"
MAX_ROW = 1048576          # worksheet limit of the file format
MAX_COL = 16384            # column XFD
MAX_MEMBER_BYTES = 200 * 1024 * 1024   # refuse a single XML part larger than this (zip bomb guard)
MAX_EDGES = 3000000        # dependency edges kept; beyond this the graph is truncated and said so
IF_DEPTH_WARN = 4          # IF inside IF inside IF inside IF; three levels still read, four do not
IF_DEPTH_STRONG = 8        # far beyond any reader's patience; message gets stronger
CONSISTENCY_MIN_COLUMN = 4   # formulas needed in a column before a "dominant" pattern means anything
CONSISTENCY_SHARE_COLUMN = 0.6   # dominant pattern must cover at least this share of the column
CONSISTENCY_MIN_ROW = 5      # rows are noisier (each column often has its own formula), so stricter
CONSISTENCY_SHARE_ROW = 0.8
CONSISTENCY_MIN_DOMINANT = 3     # and at least this many cells share the pattern
DEFAULT_MAX_PER_CATEGORY = 200
BENIGN_ARITH = {0.0, 1.0, 2.0, 100.0}   # halves, doubles, percent conversion are not "magic numbers"
BENIGN_COMPARE = {0.0, 1.0}
# Functions whose small integer arguments are positions or digit counts, not business values.
POSITIONAL_FUNCS = {"VLOOKUP", "HLOOKUP", "INDEX", "MATCH", "XMATCH", "XLOOKUP", "ROUND", "ROUNDUP",
                    "ROUNDDOWN", "LEFT", "RIGHT", "MID", "OFFSET", "CHOOSE", "COLUMN", "ROW", "DATE",
                    "TIME", "LARGE", "SMALL", "RANK", "TEXT", "FIND", "SEARCH", "SUBSTITUTE", "REPT",
                    "ROWS", "COLUMNS", "SUBTOTAL", "WEEKDAY", "EOMONTH", "EDATE", "SEQUENCE", "TRUNC"}
AGGREGATES = {"SUM", "SUBTOTAL", "AVERAGE", "COUNT", "COUNTA", "MIN", "MAX"}

VOLATILE = {
    "NOW": "recalculates at every calculation",
    "TODAY": "recalculates at every calculation",
    "RAND": "returns a new number at every calculation",
    "RANDBETWEEN": "returns a new number at every calculation",
    "RANDARRAY": "returns new numbers at every calculation",
    "OFFSET": "its target moves, so Excel cannot track what it depends on",
    "INDIRECT": "builds a reference from text, so Excel cannot track what it depends on",
    "INFO": "can change without any cell changing (some arguments)",
    "CELL": "volatile for some arguments (for example the filename or format)",
}
NEWER = {
    "IFS": "Excel 2019 and later", "SWITCH": "Excel 2019 and later", "CONCAT": "Excel 2019 and later",
    "TEXTJOIN": "Excel 2019 and later", "MAXIFS": "Excel 2019 and later", "MINIFS": "Excel 2019 and later",
    "XLOOKUP": "dynamic-array generation (Excel 2021 and Microsoft 365)",
    "XMATCH": "dynamic-array generation (Excel 2021 and Microsoft 365)",
    "FILTER": "dynamic-array generation (Excel 2021 and Microsoft 365)",
    "SORT": "dynamic-array generation (Excel 2021 and Microsoft 365)",
    "SORTBY": "dynamic-array generation (Excel 2021 and Microsoft 365)",
    "UNIQUE": "dynamic-array generation (Excel 2021 and Microsoft 365)",
    "SEQUENCE": "dynamic-array generation (Excel 2021 and Microsoft 365)",
    "RANDARRAY": "dynamic-array generation (Excel 2021 and Microsoft 365)",
    "LET": "dynamic-array generation (Excel 2021 and Microsoft 365)",
    "LAMBDA": "Microsoft 365 only", "TEXTSPLIT": "Microsoft 365 only", "TEXTBEFORE": "Microsoft 365 only",
    "TEXTAFTER": "Microsoft 365 only", "VSTACK": "Microsoft 365 only", "HSTACK": "Microsoft 365 only",
    "TAKE": "Microsoft 365 only", "DROP": "Microsoft 365 only", "TOCOL": "Microsoft 365 only",
    "TOROW": "Microsoft 365 only", "CHOOSECOLS": "Microsoft 365 only", "CHOOSEROWS": "Microsoft 365 only",
    "EXPAND": "Microsoft 365 only", "WRAPCOLS": "Microsoft 365 only", "WRAPROWS": "Microsoft 365 only",
}
ERROR_HINTS = {
    "#DIV/0!": "a divisor is zero or an empty cell; find which cell is the divisor, then decide whether blank should mean zero or no answer",
    "#N/A": "a lookup found no match (or NA() was typed); check exact-match mode, trailing spaces, text versus number, and the lookup range",
    "#NAME?": "a function or name is not recognised: a typo, an undefined name, text without quotes, or a function this spreadsheet version lacks",
    "#REF!": "a cell, row, column or sheet this formula pointed to was deleted, or a lookup column index is beyond the range",
    "#VALUE!": "an operand has the wrong type, for example text in arithmetic, or a range where a single value is expected",
    "#NUM!": "a number is invalid for the function: negative root, impossible date, result too large, or an iterative function that did not converge",
    "#NULL!": "a space between two references means intersection and the ranges do not overlap; a comma or colon was probably meant",
    "#SPILL!": "a dynamic array cannot spill because cells in its path are not empty or it sits in a table or merged cells",
    "#CALC!": "an array calculation returned an empty array or a LAMBDA is incomplete",
    "#GETTING_DATA": "an external data connection has not returned yet",
}
SUGGESTIONS = {
    "error_value": "Fix the root cell first; the cells that inherit its error clear by themselves. Do not wrap in IFERROR until the cause is known.",
    "broken_reference": "Rebuild the reference from the intended cell or range; the original target no longer exists.",
    "missing_sheet": "The sheet name does not exist in this workbook. Check spelling, quotes around names with spaces, or restore the deleted sheet.",
    "external_link": "Open Data > Edit Links, then either update the source or paste values. The numbers shown may be stale.",
    "empty_reference": "Confirm the cell or range is meant to be empty (an input not yet filled). If not, the reference is probably off by a row or column.",
    "undefined_name": "Define the name (Formulas > Name Manager), fix the spelling, or put text in quotes.",
    "hardcoded_constant": "Move the value to a labelled input cell and refer to it with an absolute reference such as $B$1.",
    "constant_formula": "A formula with no cell reference is a typed number in disguise. Type the value, or refer to the cells it came from.",
    "volatile_function": "Replace with a non-volatile form where one exists (INDEX instead of OFFSET or INDIRECT) or keep it on purpose and limit what depends on it.",
    "nested_if": "Use IFS or SWITCH where supported, or a lookup table with approximate-match XLOOKUP/VLOOKUP, or helper columns.",
    "circular_reference": "Break the loop: make one cell in the path a typed input or compute it from the inputs, not from its own result.",
    "inconsistent_formula": "Compare with the neighbours. If the difference is a mistake, refill the column from a correct cell; if deliberate, label the cell.",
    "hardcoded_value_in_formula_column": "A typed number sits inside a column of formulas. Restore the formula, or mark the cell as an override.",
    "number_stored_as_text": "Convert to numbers (Text to Columns, or multiply by 1 in a helper column); SUM skips text and comparisons treat it differently.",
    "newer_function": "Fine if every user has the stated version. Older versions show #NAME? for it.",
    "unparsed_formula": "The formula text could not be read; open the cell in the spreadsheet and check parentheses and quotes.",
}
SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}
CORE_NOT_CHECKED = [
    "Values are read from the results saved in the file; nothing is recalculated here, so a stale or never-calculated cell is shown as saved.",
    "INDIRECT and OFFSET targets, structured table references (Table1[Col]) and 3D sheet ranges are not followed in the dependency graph, so a circular path through them is not detected.",
    "Whether a formula is the right formula for the question is not judged; only structure, references and consistency are.",
    "Conditional-formatting rules, data-validation formulas and chart series are not read.",
    "Formula text is read as the file stores it, which always uses comma separators and English function names, whatever the locale of the author.",
]

_TOKEN_RE = re.compile(r"""
 (?P<str>"(?:[^"]|"")*")
|(?P<err>\#(?:REF|DIV/0|N/A|NAME|NULL|NUM|VALUE|SPILL|CALC|GETTING_DATA)[!?]?)
|(?P<struct>(?:[^\W\d]|\\)[\w.\\]*\[(?:[^\[\]]|\[[^\]]*\])*\])
|(?P<ref>(?P<pfx>(?:'(?:[^']|'')+'|\[\d+\](?:[^\W\d]|\\)[\w.]*|(?:[^\W\d]|\\)[\w.]*)!)?
   (?P<body>\$?[A-Za-z]{1,3}\$?\d+(?::\$?[A-Za-z]{1,3}\$?\d+)?|\$?[A-Za-z]{1,3}:\$?[A-Za-z]{1,3}|\$?\d+:\$?\d+)
   (?![\w.(\[]))
|(?P<func>(?:_xlfn\.|_xlws\.|_xlfn\._xlws\.)?(?:[^\W\d]|\\)[\w.]*(?=\())
|(?P<name>(?:[^\W\d]|\\)[\w.\\]*)
|(?P<num>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)
|(?P<op><>|<=|>=|[-+*/^&=<>:,;(){}%@#!])
|(?P<ws>\s+)
""", re.X)
_ENDPOINT_RE = re.compile(r"^(\$?)([A-Za-z]{1,3})?(\$?)(\d+)?$")


def col_to_num(letters):
    n = 0
    for ch in letters.upper():
        n = n * 26 + (ord(ch) - 64)
    return n


def num_to_col(n):
    out = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


def addr(row, col):
    return f"{num_to_col(col)}{row}"


def parse_addr(text):
    m = re.match(r"^([A-Za-z]{1,3})(\d+)$", text)
    return int(m.group(2)), col_to_num(m.group(1))


def local(tag):
    return tag.rsplit("}", 1)[-1]


# ----------------------------------------------------------------- formula text

def parse_endpoint(text):
    m = _ENDPOINT_RE.match(text)
    g1, col, g3, row = m.group(1), m.group(2), m.group(3), m.group(4)
    if col is None:
        return (False, None, g1 == "$", int(row))
    cnum = col_to_num(col)
    if cnum > MAX_COL:
        return None
    return (g1 == "$", cnum, g3 == "$", int(row) if row else None)


def tokenize(formula):
    """Return a list of token dicts. Raises ValueError with a plain message."""
    tokens, pos = [], 0
    while pos < len(formula):
        m = _TOKEN_RE.match(formula, pos)
        if not m or m.end() == pos:
            raise ValueError(f"unexpected character {formula[pos]!r} at position {pos + 1}")
        kind = m.lastgroup
        text = m.group(0)
        pos = m.end()
        if kind in ("pfx", "body"):
            kind = "ref"
        if kind == "ws":
            continue
        tok = {"k": kind, "t": text}
        if kind == "ref":
            pfx = m.group("pfx")
            body = m.group("body")
            parts = body.split(":")
            e1 = parse_endpoint(parts[0])
            e2 = parse_endpoint(parts[1]) if len(parts) == 2 else None
            if e1 is None or (len(parts) == 2 and e2 is None):
                tok["k"] = "name"
            else:
                tok["pfx"] = pfx or ""
                tok["e1"], tok["e2"] = e1, e2
        tokens.append(tok)
    return tokens


def sheet_of_prefix(pfx):
    """Return (sheet_name or None, is_external) for a prefix such as 'My Sheet'! or [1]Sheet1!."""
    if not pfx:
        return None, False
    raw = pfx[:-1]
    if raw.startswith("'") and raw.endswith("'"):
        raw = raw[1:-1].replace("''", "'")
    if re.match(r"^\[\d+\]", raw):
        return raw, True
    return raw, False


def bounds(tok):
    e1, e2 = tok["e1"], tok["e2"]
    eps = [e for e in (e1, e2) if e is not None]
    cols = [e[1] for e in eps if e[1] is not None]
    rows = [e[3] for e in eps if e[3] is not None]
    c_lo, c_hi = (min(cols), max(cols)) if cols else (1, MAX_COL)
    r_lo, r_hi = (min(rows), max(rows)) if rows else (1, MAX_ROW)
    if e1[1] is None or (e2 is not None and e2[1] is None):
        c_lo, c_hi = 1, MAX_COL
    if e1[3] is None or (e2 is not None and e2[3] is None):
        r_lo, r_hi = 1, MAX_ROW
    return r_lo, c_lo, r_hi, c_hi


def is_whole_line(tok):
    return any(e is not None and (e[1] is None or e[3] is None) for e in (tok["e1"], tok["e2"]))


def fmt_endpoint(ep):
    cabs, col, rabs, row = ep
    return (("$" if cabs else "") + num_to_col(col) if col else "") + (("$" if rabs else "") + str(row) if row else "")


def shift_endpoint(ep, dr, dc):
    cabs, col, rabs, row = ep
    if col is not None and not cabs:
        col += dc
    if row is not None and not rabs:
        row += dr
    if (col is not None and not 1 <= col <= MAX_COL) or (row is not None and not 1 <= row <= MAX_ROW):
        return None
    return (cabs, col, rabs, row)


def shift_formula(tokens, dr, dc):
    """Rebuild formula text with relative references moved by (dr, dc)."""
    out = []
    for tok in tokens:
        if tok["k"] != "ref":
            out.append(tok["t"])
            continue
        e1 = shift_endpoint(tok["e1"], dr, dc)
        e2 = shift_endpoint(tok["e2"], dr, dc) if tok["e2"] else None
        if e1 is None or (tok["e2"] and e2 is None):
            out.append("#REF!")
            continue
        body = fmt_endpoint(e1) + (":" + fmt_endpoint(e2) if e2 else "")
        out.append(tok["pfx"] + body)
    return "".join(out)


def normalise(tokens, row, col):
    """Relative-offset form of the formula: equal for cells filled from one another."""
    out = []
    for tok in tokens:
        if tok["k"] == "ref":
            parts = []
            for ep in (tok["e1"], tok["e2"]):
                if ep is None:
                    continue
                cabs, c, rabs, r = ep
                rs = "" if r is None else (f"R{r}" if rabs else f"R[{r - row}]")
                cs = "" if c is None else (f"C{c}" if cabs else f"C[{c - col}]")
                parts.append(rs + cs)
            out.append(tok["pfx"].lower() + ":".join(parts))
        elif tok["k"] in ("func", "name"):
            out.append(tok["t"].upper())
        else:
            out.append(tok["t"])
    return "".join(out)


def func_name(tok):
    name = tok["t"]
    for p in ("_xlfn._xlws.", "_xlfn.", "_xlws."):
        if name.startswith(p):
            name = name[len(p):]
    return name.upper()


def analyse_tokens(tokens):
    """Per-formula facts: functions, max IF depth, constants, parenthesis balance, refs."""
    funcs, stack, if_depth = [], [], 0
    depth_paren, in_brace = 0, 0
    consts_arith, consts_other = [], []
    prev = None
    n = len(tokens)
    has_ref = False
    balanced = True
    for i, tok in enumerate(tokens):
        k, t = tok["k"], tok["t"]
        nxt = tokens[i + 1] if i + 1 < n else None
        if k == "ref" or k == "struct" or k == "name":
            has_ref = has_ref or k != "name"
        if k == "func":
            fn = func_name(tok)
            funcs.append(fn)
            if fn == "IF":
                if_depth = max(if_depth, 1 + sum(1 for s in stack if s == "IF"))
        elif k == "op":
            if t == "(":
                depth_paren += 1
                stack.append(func_name(prev) if prev is not None and prev["k"] == "func" else "")
            elif t == ")":
                depth_paren -= 1
                if stack:
                    stack.pop()
                if depth_paren < 0:
                    balanced = False
            elif t == "{":
                in_brace += 1
            elif t == "}":
                in_brace -= 1
        elif k == "num" and in_brace == 0:
            try:
                val = float(t)
            except ValueError:
                val = 0.0
            p_t = prev["t"] if prev is not None and prev["k"] == "op" else None
            n_t = nxt["t"] if nxt is not None and nxt["k"] == "op" else None
            standalone = p_t in ("(", ",", ";") and n_t in (",", ")", ";")
            if standalone:
                top = stack[-1] if stack else ""
                if top in POSITIONAL_FUNCS and val == int(val) and -1 <= val <= 20:
                    pass
                elif val not in BENIGN_ARITH:
                    consts_other.append(t)
            elif p_t in ("+", "-", "*", "/", "^") or n_t in ("+", "-", "*", "/", "^"):
                if val not in BENIGN_ARITH:
                    consts_arith.append(t)
            elif p_t in ("=", "<>", "<", ">", "<=", ">=") or n_t in ("=", "<>", "<", ">", "<=", ">="):
                if val not in BENIGN_COMPARE:
                    consts_other.append(t)
        prev = tok
    if depth_paren != 0 or in_brace != 0:
        balanced = False
    return {"funcs": funcs, "if_depth": if_depth, "arith": consts_arith, "other": consts_other,
            "has_ref": has_ref, "balanced": balanced}


# ----------------------------------------------------------------- workbook reading

class WorkbookError(Exception):
    pass


def read_member(zf, name):
    try:
        info = zf.getinfo(name)
    except KeyError:
        return None
    if info.file_size > MAX_MEMBER_BYTES:
        raise WorkbookError(f"part {name} is larger than {MAX_MEMBER_BYTES // (1024 * 1024)} MB; refusing to read it")
    data = zf.read(name)
    if b"<!ENTITY" in data[:20000]:
        raise WorkbookError(f"part {name} declares XML entities; refusing to parse it")
    return data


def parse_shared_strings(data):
    if data is None:
        return []
    out = []
    for _ev, el in ET.iterparse(io.BytesIO(data), events=("end",)):
        if local(el.tag) == "si":
            parts = []
            for node in el.iter():
                if local(node.tag) == "t":
                    parts.append(node.text or "")
            out.append("".join(parts))
            el.clear()
    return out


def parse_sheet(data, shared):
    cells = {}
    cur_row, col_counter = 0, 0
    for ev, el in ET.iterparse(io.BytesIO(data), events=("start", "end")):
        tag = local(el.tag)
        if ev == "start":
            if tag == "row":
                cur_row = int(el.get("r") or cur_row + 1)
                col_counter = 0
            continue
        if tag != "c":
            continue
        ref = el.get("r")
        if ref:
            row, col = parse_addr(ref)
        else:
            row, col = cur_row, col_counter + 1
        col_counter = col
        t = el.get("t") or "n"
        f_el = v_el = is_el = None
        for child in el:
            ct = local(child.tag)
            if ct == "f":
                f_el = child
            elif ct == "v":
                v_el = child
            elif ct == "is":
                is_el = child
        rec = {"t": t, "f": None}
        raw = v_el.text if v_el is not None else None
        if is_el is not None:
            rec["value"] = "".join((n.text or "") for n in is_el.iter() if local(n.tag) == "t")
            rec["kind"] = "text"
        elif raw is None or raw == "":
            rec["value"], rec["kind"] = None, "empty"
        elif t == "s":
            idx = int(raw)
            rec["value"] = shared[idx] if 0 <= idx < len(shared) else ""
            rec["kind"] = "text"
        elif t == "e":
            rec["value"], rec["kind"] = raw, "error"
        elif t in ("str",):
            rec["value"], rec["kind"] = raw, "text"
        elif t == "b":
            rec["value"], rec["kind"] = raw == "1", "bool"
        else:
            try:
                rec["value"], rec["kind"] = float(raw), "number"
            except ValueError:
                rec["value"], rec["kind"] = raw, "text"
        if f_el is not None:
            rec["f"] = f_el.text or ""
            rec["ft"] = f_el.get("t") or "normal"
            rec["si"] = f_el.get("si")
        cells[(row, col)] = rec
        el.clear()
    # expand shared formulas: followers carry only an index
    masters = {}
    for (r, c), rec in cells.items():
        if rec["f"] and rec.get("ft") == "shared" and rec["f"] != "":
            masters[rec["si"]] = (r, c, rec["f"])
    for (r, c), rec in cells.items():
        if rec.get("ft") == "shared" and rec["f"] == "" and rec["si"] in masters:
            mr, mc, text = masters[rec["si"]]
            try:
                rec["f"] = shift_formula(tokenize(text), r - mr, c - mc)
            except ValueError:
                rec["f"] = text
    return cells


def resolve_target(target):
    target = target.replace("\\", "/")
    if target.startswith("/"):
        return target[1:]
    return "xl/" + target


def load_workbook(path):
    if not os.path.isfile(path):
        raise WorkbookError(f"file not found: {path}")
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        raise WorkbookError("not an .xlsx/.xlsm file (it is not a zip archive). Older .xls and .xlsb files, and password-protected files, "
                            "cannot be read: open the file in the spreadsheet app, remove the password, and save as .xlsx")
    with zf:
        wb = read_member(zf, "xl/workbook.xml")
        if wb is None:
            raise WorkbookError("no xl/workbook.xml inside the archive: this is not a spreadsheet workbook")
        rels_raw = read_member(zf, "xl/_rels/workbook.xml.rels")
        rels = {}
        if rels_raw:
            for el in ET.fromstring(rels_raw):
                rels[el.get("Id")] = (el.get("Target") or "", el.get("Type") or "")
        shared = parse_shared_strings(read_member(zf, "xl/sharedStrings.xml"))
        root = ET.fromstring(wb)
        sheets, defined, iterate = [], {}, False
        for el in root.iter():
            tag = local(el.tag)
            if tag == "sheet":
                rid = None
                for key, val in el.attrib.items():
                    if local(key) == "id":
                        rid = val
                target, rtype = rels.get(rid, ("", ""))
                sheets.append({"name": el.get("name") or "", "state": el.get("state") or "visible",
                               "target": resolve_target(target) if target else None, "type": rtype})
            elif tag == "definedName":
                defined[(el.get("name") or "").upper()] = (el.text or "").strip()
            elif tag == "calcPr":
                iterate = (el.get("iterate") or "") in ("1", "true")
        table_names = set()
        external_links = 0
        for info in zf.infolist():
            if re.match(r"^xl/tables/[^/]+\.xml$", info.filename):
                data = read_member(zf, info.filename)
                try:
                    table_names.add((ET.fromstring(data).get("displayName") or "").upper())
                except ET.ParseError:
                    pass
            elif info.filename.startswith("xl/externalLinks/") and info.filename.endswith(".xml"):
                external_links += 1
        parsed = []
        for sh in sheets:
            if sh["target"] is None or "chartsheet" in sh["type"] or "dialogsheet" in sh["type"]:
                parsed.append(None)
                continue
            data = read_member(zf, sh["target"])
            parsed.append(parse_sheet(data, shared) if data is not None else {})
    return {"sheets": sheets, "cells": parsed, "defined": defined, "iterate": iterate,
            "tables": table_names, "external_links": external_links}


# ----------------------------------------------------------------- the audit

class Findings:
    def __init__(self, cap):
        self.cap = cap
        self.items = []
        self.counts = Counter()
        self.kept = Counter()

    def add(self, severity, category, sheet, cell, message, **extra):
        self.counts[category] += 1
        if self.kept[category] >= self.cap:
            return
        self.kept[category] += 1
        item = {"severity": severity, "category": category, "sheet": sheet, "cell": cell,
                "message": message, "suggestion": SUGGESTIONS.get(category, "")}
        item.update(extra)
        self.items.append(item)


def find_cycles(adj):
    index, low, onstack, stack, result = {}, {}, set(), [], []
    counter = 0
    for root in adj:
        if root in index:
            continue
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        onstack.add(root)
        work = [(root, iter(adj[root]))]
        while work:
            node, it = work[-1]
            advanced = False
            for nxt in it:
                if nxt not in adj:
                    continue
                if nxt not in index:
                    index[nxt] = low[nxt] = counter
                    counter += 1
                    stack.append(nxt)
                    onstack.add(nxt)
                    work.append((nxt, iter(adj[nxt])))
                    advanced = True
                    break
                if nxt in onstack:
                    low[node] = min(low[node], index[nxt])
            if advanced:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index[node]:
                comp = []
                while True:
                    w = stack.pop()
                    onstack.discard(w)
                    comp.append(w)
                    if w == node:
                        break
                if len(comp) > 1 or node in adj[node]:
                    result.append(comp)
    return result


def cycle_path(start, comp, adj):
    """Shortest path from start back to start inside the component."""
    members = set(comp)
    queue = deque([(start, [start])])
    seen = set()
    while queue:
        node, path = queue.popleft()
        for nxt in sorted(adj[node]):
            if nxt not in members:
                continue
            if nxt == start:
                return path + [start]
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, path + [nxt]))
    return [start]


def audit(path, max_per_category=DEFAULT_MAX_PER_CATEGORY):
    wb = load_workbook(path)
    sheets, cells_by_sheet = wb["sheets"], wb["cells"]
    names_lower = {s["name"].lower(): i for i, s in enumerate(sheets)}
    findings = Findings(max_per_category)
    not_checked = list(CORE_NOT_CHECKED)

    # occupancy and formula indexes -------------------------------------------------
    occ_cols = []   # per sheet: col -> sorted rows of non-empty cells
    f_cols = []     # per sheet: col -> sorted rows of formula cells
    for cells in cells_by_sheet:
        oc, fc = defaultdict(list), defaultdict(list)
        for (r, c), rec in (cells or {}).items():
            if rec["f"] is not None:
                fc[c].append(r)
                oc[c].append(r)
            elif rec["kind"] != "empty":
                oc[c].append(r)
        for d in (oc, fc):
            for c in d:
                d[c].sort()
        occ_cols.append(dict(oc))
        f_cols.append(dict(fc))
    f_col_lists = [sorted(d) for d in f_cols]
    occ_col_lists = [sorted(d) for d in occ_cols]

    def any_in(cols_map, col_list, r1, c1, r2, c2):
        lo = bisect.bisect_left(col_list, c1)
        hi = bisect.bisect_right(col_list, c2)
        for c in col_list[lo:hi]:
            rows = cols_map[c]
            j = bisect.bisect_left(rows, r1)
            if j < len(rows) and rows[j] <= r2:
                return True
        return False

    def formula_nodes_in(si, r1, c1, r2, c2):
        cols_map, col_list = f_cols[si], f_col_lists[si]
        lo = bisect.bisect_left(col_list, c1)
        hi = bisect.bisect_right(col_list, c2)
        for c in col_list[lo:hi]:
            rows = cols_map[c]
            a = bisect.bisect_left(rows, r1)
            b = bisect.bisect_right(rows, r2)
            for r in rows[a:b]:
                yield (si, r, c)

    # defined names that are a plain reference ---------------------------------------
    name_refs = {}
    for nm, text in wb["defined"].items():
        try:
            toks = tokenize(text)
        except ValueError:
            continue
        if len(toks) == 1 and toks[0]["k"] == "ref":
            name_refs[nm] = toks[0]
    known_names = set(wb["defined"]) | wb["tables"] | {"TRUE", "FALSE"}

    # pass 1: tokenise and analyse every formula --------------------------------------
    info = {}   # node -> dict
    sheet_stats = []
    for si, sh in enumerate(sheets):
        cells = cells_by_sheet[si]
        stats = {"name": sh["name"], "state": sh["state"], "formula_cells": 0, "value_cells": 0,
                 "error_cells": 0, "volatile_cells": 0, "max_if_depth": 0, "cross_sheet_targets": Counter(),
                 "used_range": None, "readable": cells is not None}
        sheet_stats.append(stats)
        if cells is None:
            continue
        occupied = [rc for rc, rec in cells.items() if rec["kind"] != "empty" or rec["f"] is not None]
        if occupied:
            rs = [r for r, _ in occupied]
            cs = [c for _, c in occupied]
            stats["used_range"] = f"{addr(min(rs), min(cs))}:{addr(max(rs), max(cs))}"
        for (r, c), rec in cells.items():
            if rec["f"] is None:
                if rec["kind"] != "empty":
                    stats["value_cells"] += 1
                if rec["kind"] == "error":
                    stats["error_cells"] += 1
                    findings.add("warning", "error_value", sh["name"], addr(r, c),
                                 f"{rec['value']} is stored as a typed or pasted value, not a formula result",
                                 error=rec["value"], root_cause=True, formula=None)
                continue
            stats["formula_cells"] += 1
            text = rec["f"]
            node = (si, r, c)
            try:
                toks = tokenize(text)
                facts = analyse_tokens(toks)
                if not facts["balanced"]:
                    raise ValueError("parentheses or braces are not balanced")
            except ValueError as exc:
                findings.add("warning", "unparsed_formula", sh["name"], addr(r, c),
                             f"formula could not be read: {exc}", formula="=" + text)
                info[node] = {"toks": [], "facts": None, "text": text}
                continue
            info[node] = {"toks": toks, "facts": facts, "text": text}

    # dependency graph ----------------------------------------------------------------
    adj, edge_count, truncated = {}, 0, False
    for node, d in info.items():
        adj[node] = set()
    for node, d in info.items():
        si, r, c = node
        if d["facts"] is None:
            continue
        for tok in d["toks"]:
            target = None
            if tok["k"] == "ref":
                name, ext = sheet_of_prefix(tok["pfx"])
                if ext:
                    continue
                if name is None:
                    tsi = si
                else:
                    tsi = names_lower.get(name.lower())
                    if tsi is None:
                        continue
                target = (tsi, tok)
            elif tok["k"] == "name" and tok["t"].upper() in name_refs:
                rt = name_refs[tok["t"].upper()]
                name, ext = sheet_of_prefix(rt["pfx"])
                tsi = names_lower.get(name.lower()) if name else si
                if tsi is None or ext:
                    continue
                target = (tsi, rt)
            if target is None:
                continue
            tsi, rt = target
            if cells_by_sheet[tsi] is None:
                continue
            r1, c1, r2, c2 = bounds(rt)
            for dep in formula_nodes_in(tsi, r1, c1, r2, c2):
                if dep not in adj[node]:
                    adj[node].add(dep)
                    edge_count += 1
            if edge_count > MAX_EDGES:
                truncated = True
                break
        if truncated:
            break
    if truncated:
        not_checked.append(f"The dependency graph was cut off after {MAX_EDGES} edges (very large ranges); circular references and error tracing are incomplete.")
    reverse = defaultdict(set)
    for node, deps in adj.items():
        for dep in deps:
            reverse[dep].add(node)

    # pass 2: per-formula checks --------------------------------------------------------
    any_cached = False
    volatile_cells = set()
    newer_seen = defaultdict(list)
    volatile_seen = defaultdict(list)
    for node, d in sorted(info.items()):
        si, r, c = node
        sname = sheets[si]["name"]
        cell = addr(r, c)
        rec = cells_by_sheet[si][(r, c)]
        if rec["kind"] != "empty":
            any_cached = True
        facts = d["facts"]
        formula_text = "=" + re.sub(r"_xlfn\.|_xlws\.", "", d["text"])
        # error values
        if rec["kind"] == "error":
            sheet_stats[si]["error_cells"] += 1
            err = rec["value"]
            precedents = sorted(addr(p[1], p[2]) if p[0] == si else f"{sheets[p[0]]['name']}!{addr(p[1], p[2])}"
                                for p in adj.get(node, ())
                                if cells_by_sheet[p[0]][(p[1], p[2])]["kind"] == "error")
            hint = ERROR_HINTS.get(err, "an error value")
            if precedents:
                findings.add("info", "error_value", sname, cell,
                             f"{err} inherited from {', '.join(precedents[:5])}; fix those first", error=err,
                             root_cause=False, inherited_from=precedents[:5], formula=formula_text)
            else:
                findings.add("error", "error_value", sname, cell, f"{err}: {hint}", error=err,
                             root_cause=True, formula=formula_text)
        if facts is None:
            continue
        # references
        for tok in d["toks"]:
            if tok["k"] == "err" and tok["t"].upper().startswith("#REF"):
                findings.add("error", "broken_reference", sname, cell,
                             "formula contains #REF!: a reference was deleted", formula=formula_text)
            if tok["k"] == "name":
                up = tok["t"].upper()
                if (up not in known_names and not up.startswith("_XLPM.")
                        and not ({"LET", "LAMBDA"} & set(facts["funcs"]))):
                    findings.add("warning", "undefined_name", sname, cell,
                                 f"name '{tok['t']}' is not defined in this workbook", formula=formula_text)
            if tok["k"] != "ref":
                continue
            name, ext = sheet_of_prefix(tok["pfx"])
            if ext:
                findings.add("warning", "external_link", sname, cell,
                             f"refers to another workbook ({tok['pfx'][:-1]})", formula=formula_text)
                continue
            if name is None:
                tsi = si
            else:
                tsi = names_lower.get(name.lower())
                if tsi is None:
                    findings.add("error", "missing_sheet", sname, cell,
                                 f"sheet '{name}' does not exist in this workbook", formula=formula_text)
                    continue
                if tsi != si:
                    sheet_stats[si]["cross_sheet_targets"][sheets[tsi]["name"]] += 1
            if cells_by_sheet[tsi] is None or is_whole_line(tok):
                continue
            r1, c1, r2, c2 = bounds(tok)
            if not any_in(occ_cols[tsi], occ_col_lists[tsi], r1, c1, r2, c2):
                rng = addr(r1, c1) + (f":{addr(r2, c2)}" if (r2, c2) != (r1, c1) else "")
                where = rng if tsi == si else f"{sheets[tsi]['name']}!{rng}"
                findings.add("warning" if (r1, c1) == (r2, c2) else "info", "empty_reference", sname, cell,
                             f"refers to {where}, which holds nothing", target=where, formula=formula_text)
        # constants
        if facts["arith"] or facts["other"]:
            if not facts["has_ref"]:
                findings.add("info", "constant_formula", sname, cell,
                             "formula has no cell reference; it is a typed value", formula=formula_text)
            else:
                values = list(dict.fromkeys(facts["arith"] + facts["other"]))
                findings.add("warning" if facts["arith"] else "info", "hardcoded_constant", sname, cell,
                             "constants inside the formula: " + ", ".join(values[:8]), values=values[:8],
                             formula=formula_text)
        # volatile and newer functions
        for fn in facts["funcs"]:
            if fn in VOLATILE:
                volatile_cells.add(node)
                volatile_seen[(si, fn)].append(cell)
            if fn in NEWER:
                newer_seen[(si, fn)].append(cell)
        if facts["if_depth"] >= IF_DEPTH_WARN:
            sheet_stats[si]["max_if_depth"] = max(sheet_stats[si]["max_if_depth"], facts["if_depth"])
            msg = f"IF nested {facts['if_depth']} levels deep"
            if facts["if_depth"] >= IF_DEPTH_STRONG:
                msg += " (far beyond what a reader can follow)"
            findings.add("warning", "nested_if", sname, cell, msg, depth=facts["if_depth"], formula=formula_text)
        elif facts["if_depth"]:
            sheet_stats[si]["max_if_depth"] = max(sheet_stats[si]["max_if_depth"], facts["if_depth"])
    for si, st in enumerate(sheet_stats):
        st["volatile_cells"] = sum(1 for n in volatile_cells if n[0] == si)
    for (si, fn), cell_list in sorted(volatile_seen.items()):
        findings.add("info", "volatile_function", sheets[si]["name"], cell_list[0],
                     f"{fn} is volatile: {VOLATILE[fn]} ({len(cell_list)} cell(s))", function=fn,
                     count=len(cell_list), cells=cell_list[:20])
    for (si, fn), cell_list in sorted(newer_seen.items()):
        findings.add("info", "newer_function", sheets[si]["name"], cell_list[0],
                     f"{fn} needs {NEWER[fn]} ({len(cell_list)} cell(s))", function=fn,
                     count=len(cell_list), cells=cell_list[:20])
    downstream = set()
    queue = deque(volatile_cells)
    while queue:
        cur = queue.popleft()
        for nxt in reverse.get(cur, ()):
            if nxt not in downstream:
                downstream.add(nxt)
                queue.append(nxt)
    downstream -= volatile_cells

    # circular references -----------------------------------------------------------------
    cycles = find_cycles(adj)
    for comp in sorted(cycles, key=lambda comp: min(comp)):
        start = min(comp)
        cyc = cycle_path(start, comp, adj)

        def label(n):
            return addr(n[1], n[2]) if n[0] == start[0] else f"{sheets[n[0]]['name']}!{addr(n[1], n[2])}"
        shown = [label(n) for n in cyc]
        sev = "info" if wb["iterate"] else "error"
        note = " Iterative calculation is on in this workbook, so Excel will not warn." if wb["iterate"] else ""
        if len(comp) == 1:
            msg = f"{shown[0]} refers to itself.{note}"
        else:
            msg = f"circular chain of {len(comp)} cells: {' -> '.join(shown)}.{note}"
        findings.add(sev, "circular_reference", sheets[start[0]]["name"], addr(start[1], start[2]), msg,
                     path=shown, size=len(comp))

    # consistency across columns and rows ----------------------------------------------------
    flagged = set()

    def check_group(members, axis, min_n, share):
        # members: list of (position, node) sorted by position; position is row for columns, col for rows
        if len(members) < min_n:
            return
        patterns = []
        for pos, node in members:
            d = info[node]
            if d["facts"] is None:
                patterns.append(None)
            else:
                patterns.append(normalise(d["toks"], node[1], node[2]))
        counted = Counter(p for p in patterns if p is not None)
        if not counted:
            return
        dom, dom_n = counted.most_common(1)[0]
        if dom_n < CONSISTENCY_MIN_DOMINANT or dom_n / len(members) < share or len(counted) < 2:
            return
        rep = next(node for (pos, node), p in zip(members, patterns) if p == dom)
        last = members[-1][1]
        for (pos, node), p in zip(members, patterns):
            if p is None or p == dom or node in flagged:
                continue
            d = info[node]
            top = d["facts"]["funcs"][0] if d["facts"]["funcs"] else ""
            if node == last and top in AGGREGATES and d["toks"] and d["toks"][0]["k"] == "func":
                continue    # a closing total row is expected to differ
            flagged.add(node)
            expected = "=" + shift_formula(info[rep]["toks"], node[1] - rep[1], node[2] - rep[2])
            where = "column" if axis == "col" else "row"
            findings.add("warning", "inconsistent_formula", sheets[node[0]]["name"], addr(node[1], node[2]),
                         f"differs from the pattern shared by {dom_n} of {len(members)} formulas in its {where}; that pattern would give {expected}",
                         formula="=" + re.sub(r"_xlfn\.|_xlws\.", "", d["text"]), expected=expected)

    for si in range(len(sheets)):
        by_col = defaultdict(list)
        by_row = defaultdict(list)
        for node in info:
            if node[0] == si:
                by_col[node[2]].append((node[1], node))
                by_row[node[1]].append((node[2], node))
        for col, members in by_col.items():
            members.sort()
            check_group(members, "col", CONSISTENCY_MIN_COLUMN, CONSISTENCY_SHARE_COLUMN)
        for row, members in by_row.items():
            members.sort()
            check_group(members, "row", CONSISTENCY_MIN_ROW, CONSISTENCY_SHARE_ROW)
        # typed numbers inside a formula column, and numbers stored as text
        cells = cells_by_sheet[si] or {}
        for col, members in by_col.items():
            members.sort()
            if len(members) < CONSISTENCY_MIN_COLUMN:
                continue
            pats = {}
            for pos, node in members:
                d = info[node]
                pats[pos] = normalise(d["toks"], node[1], node[2]) if d["facts"] is not None else None
            counted = Counter(p for p in pats.values() if p is not None)
            if not counted:
                continue
            dom, dom_n = counted.most_common(1)[0]
            if dom_n < CONSISTENCY_MIN_DOMINANT or dom_n / len(members) < CONSISTENCY_SHARE_COLUMN:
                continue
            rows = [pos for pos, _ in members]
            for (r, c), rec in sorted(cells.items(), key=lambda kv: kv[0]):
                if c != col or rec["f"] is not None or rec["kind"] != "number":
                    continue
                k = bisect.bisect_left(rows, r)
                if 0 < k < len(rows) and pats[rows[k - 1]] == dom and pats[rows[k]] == dom:
                    val = rec["value"] if math.isfinite(rec["value"]) else str(rec["value"])
                    findings.add("warning", "hardcoded_value_in_formula_column", sheets[si]["name"], addr(r, c),
                                 f"typed number {val:g} sits between formulas that follow one pattern" if isinstance(val, float)
                                 else f"typed number {val} sits between formulas that follow one pattern", value=val)
        text_by_col = defaultdict(list)
        num_rows = defaultdict(list)
        for (r, c), rec in cells.items():
            if rec["f"] is not None:
                continue
            if rec["kind"] == "number":
                num_rows[c].append(r)
            elif rec["kind"] == "text" and re.match(r"^\s*[-+]?(\d[\d,]*\.?\d*|\.\d+)%?\s*$", rec["value"] or ""):
                text_by_col[c].append(r)
        for c, rows_ in sorted(text_by_col.items()):
            if len(num_rows.get(c, [])) < 3:
                continue
            first_num = min(num_rows[c])
            bad = sorted(r for r in rows_ if r > first_num)
            if bad:
                findings.add("warning", "number_stored_as_text", sheets[si]["name"], addr(bad[0], c),
                             f"{len(bad)} cell(s) in column {num_to_col(c)} hold numbers as text", count=len(bad),
                             cells=[addr(r, c) for r in bad[:20]])

    if info and not any_cached:
        not_checked.append("No formula in this file has a saved result (typical of files written by scripts). Error values and stale values cannot be checked; open and save the file in the spreadsheet app, then re-run.")
    if wb["external_links"]:
        not_checked.append(f"{wb['external_links']} external link part(s) exist; the linked workbooks were not opened.")
    findings.items.sort(key=lambda f: (SEVERITY_ORDER[f["severity"]], f["sheet"], f["category"], f["cell"]))
    total_by_sev = Counter()
    for f in findings.items:
        total_by_sev[f["severity"]] += 1
    sheet_out = []
    for st in sheet_stats:
        out = dict(st)
        out["cross_sheet_targets"] = dict(sorted(st["cross_sheet_targets"].items()))
        sheet_out.append(out)
    truncated_cats = {c: n for c, n in findings.counts.items() if n > findings.kept[c]}
    report = {
        "tool": "audit_workbook",
        "version": VERSION,
        "file": os.path.basename(path),
        "ok": total_by_sev["error"] == 0,
        "workbook": {
            "sheets": len(sheets),
            "formula_cells": sum(s["formula_cells"] for s in sheet_stats),
            "cached_values_present": any_cached if info else None,
            "iterative_calculation": wb["iterate"],
            "defined_names": len(wb["defined"]),
            "external_link_parts": wb["external_links"],
            "volatile_cells": len(volatile_cells),
            "volatile_downstream_cells": len(downstream),
        },
        "sheets": sheet_out,
        "counts_by_category": dict(sorted(findings.counts.items())),
        "counts_by_severity": {k: total_by_sev[k] for k in ("error", "warning", "info")},
        "truncated_categories": dict(sorted(truncated_cats.items())),
        "findings": findings.items,
        "not_checked": not_checked,
    }
    return report


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cap = DEFAULT_MAX_PER_CATEGORY
    if "--max-per-category" in argv:
        i = argv.index("--max-per-category")
        try:
            cap = int(argv[i + 1])
            del argv[i:i + 2]
        except (IndexError, ValueError):
            print("error: --max-per-category needs a whole number", file=sys.stderr)
            return 2
    if len(argv) != 1 or argv[0] in ("-h", "--help"):
        print("usage: audit_workbook.py <workbook.xlsx> [--max-per-category N]", file=sys.stderr)
        return 2
    try:
        report = audit(argv[0], cap)
    except WorkbookError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (ET.ParseError, zipfile.BadZipFile, KeyError, ValueError) as exc:
        print(f"error: the workbook XML could not be read ({exc.__class__.__name__}: {exc})", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(report, ensure_ascii=True, allow_nan=False, indent=2) + "\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
