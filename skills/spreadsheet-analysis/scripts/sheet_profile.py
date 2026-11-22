#!/usr/bin/env python3
"""Profile a spreadsheet for data problems, then compute totals that say what was excluded.

Standard library only. Reads one .csv, .tsv or .xlsx file, prints a report, writes nothing.

    python sheet_profile.py FILE [--sheet N]
        Audit: header problems, column types, blanks, numbers stored as text,
        mixed date formats, spelling variants of the same category, exact
        duplicate rows, total/subtotal rows inside the data, extreme values.

    python sheet_profile.py FILE --sum COL [--by COL] [--unique-by COL]
    python sheet_profile.py FILE --mean COL [--by COL] [--unique-by COL]
    python sheet_profile.py FILE --count-distinct COL
        Compute on the data rows. Total rows and blank rows are always left out.
        The result is printed with exact duplicate rows kept and with them
        removed, so the difference is visible. --unique-by adds a third result
        that keeps one row per distinct value of that column (for example one
        row per email). Category values are grouped after trimming spaces and
        ignoring upper/lower case.

COL is a header name (case-insensitive) or a column letter such as C.
Exit codes: 0 = report printed, 2 = usage error or unreadable file.
Limits: .xlsx dates are stored as serial numbers and are shown as numbers;
formulas are read as their last saved value; merged cells are read as blanks.
"""
import csv
import io
import re
import statistics
import sys
import zipfile
from xml.etree import ElementTree

TOTAL_WORDS = ("total", "totals", "grand total", "subtotal", "sub-total", "sum", "overall")
TYPE_SHARE = 0.8        # a column is numeric/date when this share of filled cells parse as such
MAX_CATEGORIES = 40     # text columns with at most this many distinct values are listed in full
OUTLIER_FENCE = 3.0     # a value this many interquartile ranges beyond the quartiles is "extreme"
MIN_FOR_OUTLIERS = 8    # fewer values than this give no stable quartiles
DATE_PATTERNS = [
    ("YYYY-MM-DD", re.compile(r"^\d{4}-\d{1,2}-\d{1,2}([ T]\d{1,2}:\d{2}(:\d{2})?)?$")),
    ("N/N/YYYY", re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")),
    ("N.N.YYYY", re.compile(r"^\d{1,2}\.\d{1,2}\.\d{2,4}$")),
    ("N-N-YYYY", re.compile(r"^\d{1,2}-\d{1,2}-\d{2,4}$")),
    ("Mon D, YYYY", re.compile(r"^[A-Za-z]{3,9}\.? \d{1,2},? \d{4}$")),
    ("D Mon YYYY", re.compile(r"^\d{1,2}[ -][A-Za-z]{3,9}\.?[ -]\d{2,4}$")),
]
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "p": "http://schemas.openxmlformats.org/package/2006/relationships"}


def utf8_output():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def die(msg):
    print("ERROR: " + msg)
    sys.exit(2)


def read_delimited(path):
    try:
        raw = open(path, "rb").read()
    except OSError as err:
        die(f"cannot read {path}: {err.strerror}. Check the path.")
    text = None
    for enc in ("utf-8-sig", "cp1252"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if not text.strip():
        die(f"{path} is empty.")
    sample = text[:5000]
    counts = {d: sample.count(d) for d in (",", ";", "\t", "|")}
    delim = "\t" if path.lower().endswith(".tsv") else max(counts, key=counts.get)
    return [row for row in csv.reader(io.StringIO(text), delimiter=delim)], f"delimiter {delim!r}"


def col_index(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_xlsx(path, sheet_no):
    try:
        z = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile):
        die(f"{path} is not a readable .xlsx file. Old .xls files must be saved as .xlsx or .csv first.")
    names = z.namelist()
    shared = []
    if "xl/sharedStrings.xml" in names:
        for si in ElementTree.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    wb = ElementTree.fromstring(z.read("xl/workbook.xml"))
    sheets = wb.findall("m:sheets/m:sheet", NS)
    if not 1 <= sheet_no <= len(sheets):
        die(f"--sheet {sheet_no} does not exist; the workbook has {len(sheets)} sheet(s): " + ", ".join(s.get("name") for s in sheets))
    rid = sheets[sheet_no - 1].get("{%s}id" % NS["r"])
    rels = ElementTree.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = next(r.get("Target") for r in rels.findall("p:Relationship", NS) if r.get("Id") == rid)
    target = target.lstrip("/") if target.startswith("/") else "xl/" + target
    rows = []
    for row in ElementTree.fromstring(z.read(target)).findall("m:sheetData/m:row", NS):
        cells = []
        for c in row.findall("m:c", NS):
            i = col_index(c.get("r")) if c.get("r") else len(cells)
            kind, v = c.get("t"), c.find("m:v", NS)
            if kind == "inlineStr":
                val = "".join(t.text or "" for t in c.iter("{%s}t" % NS["m"]))
            elif v is None or v.text is None:
                val = ""
            elif kind == "s":
                val = shared[int(v.text)]
            elif kind == "b":
                val = "TRUE" if v.text == "1" else "FALSE"
            else:
                val = v.text
                if re.fullmatch(r"-?\d+\.0+", val):
                    val = val.split(".")[0]
            while len(cells) < i:
                cells.append("")
            cells.append(val)
        rows.append(cells)
    note = f"sheet {sheet_no} of {len(sheets)} ('{sheets[sheet_no - 1].get('name')}')"
    if len(sheets) > 1:
        note += "; other sheets: " + ", ".join(s.get("name") for i, s in enumerate(sheets) if i != sheet_no - 1)
    return rows, note


def parse_number(cell):
    """Return (value, plain) where plain is False when the cell needed cleaning
    (currency sign, thousands separator, percent, brackets, spaces)."""
    s = cell.strip()
    if not s:
        return None, True
    if re.fullmatch(r"-?\d+(\.\d+)?([eE][-+]?\d+)?", s):
        return float(s), s == cell
    t = re.sub(r"[\s $€£₪]", "", s)
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").rstrip("%")
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", t) or re.fullmatch(r"-?\d+(\.\d+)?", t):
        val = float(t.replace(",", ""))
        return (-val if neg else val), False
    return None, True


def date_format(cell):
    s = cell.strip()
    for label, rx in DATE_PATTERNS:
        if rx.match(s):
            return label
    return None


def fmt(x):
    return f"{x:,.2f}".rstrip("0").rstrip(".") if abs(x - round(x)) > 1e-9 else f"{int(round(x)):,}"


class Table:
    def __init__(self, rows):
        self.notes = []
        rows = [[c if isinstance(c, str) else str(c) for c in r] for r in rows]
        first = next((i for i, r in enumerate(rows) if sum(1 for c in r if c.strip()) >= 2), None)
        if first is None:
            die("no row with at least two filled cells was found; nothing to analyse.")
        if first > 0:
            self.notes.append(f"header taken from file row {first + 1}; {first} row(s) above it were skipped")
        width = max(len(r) for r in rows[first:])
        self.header = [(c.strip() or f"(blank header {i + 1})") for i, c in enumerate(rows[first] + [""] * (width - len(rows[first])))]
        if any(h.startswith("(blank header") for h in self.header):
            self.notes.append("one or more header cells are blank")
        low = [h.lower() for h in self.header]
        dup = sorted({h for h in low if low.count(h) > 1})
        if dup:
            self.notes.append("duplicate header names: " + ", ".join(dup))
        if all(parse_number(h)[0] is not None for h in self.header):
            self.notes.append("the first row looks like data, not headers; the file may have no header row")
        self.first_data_row = first + 2
        self.rows, self.blank_rows, self.total_rows = [], [], []
        for n, r in enumerate(rows[first + 1:], first + 2):
            r = r + [""] * (width - len(r))
            if not any(c.strip() for c in r):
                self.blank_rows.append(n)
            elif any(c.strip().lower().rstrip(":") in TOTAL_WORDS or re.match(r"^(grand |sub)?total\b", c.strip().lower()) for c in r):
                self.total_rows.append(n)
            else:
                self.rows.append((n, r))
        seen, self.duplicate_rows = {}, []
        for n, r in self.rows:
            key = tuple(c.strip() for c in r)
            if key in seen:
                self.duplicate_rows.append((n, seen[key]))
            else:
                seen[key] = n

    def column(self, name):
        if re.fullmatch(r"[A-Za-z]{1,2}", name) and name.lower() not in [h.lower() for h in self.header]:
            i = col_index(name.upper())
            if i < len(self.header):
                return i
        for i, h in enumerate(self.header):
            if h.lower() == name.lower():
                return i
        die(f"column '{name}' not found. Columns: " + ", ".join(self.header))

    def unique_rows(self):
        dups = {n for n, _ in self.duplicate_rows}
        return [(n, r) for n, r in self.rows if n not in dups]


def audit(table, source_note):
    t = table
    print("SPREADSHEET AUDIT")
    print(f"  Source: {source_note}")
    print(f"  {len(t.rows)} data rows, {len(t.header)} columns; data starts at file row {t.first_data_row}")
    issues = list(t.notes)
    if t.blank_rows:
        issues.append(f"{len(t.blank_rows)} fully blank row(s) at file rows {t.blank_rows[:8]}")
    if t.total_rows:
        issues.append(f"TOTAL ROWS inside the data at file rows {t.total_rows}: summing the column counts these twice")
    if t.duplicate_rows:
        shown = ", ".join(f"{n} (same as {m})" for n, m in t.duplicate_rows[:8])
        issues.append(f"{len(t.duplicate_rows)} EXACT DUPLICATE row(s): file rows {shown}. Ask whether they are real repeats or copy errors")
    print("\nCOLUMNS")
    for i, h in enumerate(t.header):
        cells = [(n, r[i]) for n, r in t.rows]
        filled = [(n, c) for n, c in cells if c.strip()]
        blanks = len(cells) - len(filled)
        nums = [(n, c, parse_number(c)) for n, c in filled]
        numeric = [(n, v) for n, c, (v, plain) in nums if v is not None]
        dates = [(n, date_format(c)) for n, c in filled if date_format(c)]
        distinct = len({c for _, c in filled})
        letter = chr(65 + i) if i < 26 else f"col{i + 1}"
        if filled and len(dates) >= TYPE_SHARE * len(filled):
            formats = {}
            for n, f in dates:
                formats.setdefault(f, []).append(n)
            print(f"  {letter} '{h}': date, {len(filled)} filled, {blanks} blank, formats: " + "; ".join(f"{k} x{len(v)}" for k, v in formats.items()))
            if len(formats) > 1:
                issues.append(f"column '{h}': MIXED DATE FORMATS " + "; ".join(f"{k} (e.g. row {v[0]})" for k, v in formats.items()))
            if any(k.startswith("N") for k in formats):
                issues.append(f"column '{h}': numeric dates such as 03/04/2026 can mean 3 April or March 4; confirm day/month order before grouping by month")
            not_dates = [n for n, c in filled if not date_format(c)]
            if not_dates:
                issues.append(f"column '{h}': {len(not_dates)} value(s) are not dates, rows {not_dates[:5]}")
        elif filled and len(numeric) >= TYPE_SHARE * len(filled):
            vals = [v for _, v in numeric]
            line = f"  {letter} '{h}': number, {len(numeric)} values, {blanks} blank, min {fmt(min(vals))}, max {fmt(max(vals))}, sum {fmt(sum(vals))}, mean {fmt(statistics.mean(vals))}"
            print(line)
            texty = [n for n, c, (v, plain) in nums if v is not None and not plain]
            if texty:
                issues.append(f"column '{h}': {len(texty)} NUMBER(S) STORED AS TEXT (currency sign, comma, percent, brackets or spaces), e.g. row {texty[0]}; a plain spreadsheet SUM skips or misreads these")
            bad = [(n, c) for n, c, (v, plain) in nums if v is None]
            if bad:
                issues.append(f"column '{h}': {len(bad)} non-numeric value(s): " + ", ".join(f"row {n} '{c.strip()}'" for n, c in bad[:5]))
            if blanks:
                issues.append(f"column '{h}': {blanks} blank cell(s); decide whether blank means zero or unknown before averaging")
            if len(vals) >= MIN_FOR_OUTLIERS:
                q = statistics.quantiles(vals, n=4)
                spread = q[2] - q[0]
                if spread > 0:
                    extreme = [(n, v) for n, v in numeric if v < q[0] - OUTLIER_FENCE * spread or v > q[2] + OUTLIER_FENCE * spread]
                    if extreme:
                        issues.append(f"column '{h}': EXTREME value(s) " + ", ".join(f"row {n} = {fmt(v)}" for n, v in extreme[:5]) + f" (typical range {fmt(q[0])} to {fmt(q[2])}); a typo or a real exception?")
            if any(v < 0 for v in vals):
                issues.append(f"column '{h}': {sum(1 for v in vals if v < 0)} negative value(s) (refunds or corrections?)")
        else:
            print(f"  {letter} '{h}': text, {len(filled)} filled, {blanks} blank, {distinct} distinct")
            groups = {}
            for n, c in filled:
                groups.setdefault(re.sub(r"\s+", " ", c.strip()).casefold(), {}).setdefault(c, []).append(n)
            variants = {k: v for k, v in groups.items() if len(v) > 1}
            listed = len(groups) <= MAX_CATEGORIES and len(groups) * 2 <= len(filled)
            if listed:
                print("      values: " + "; ".join(f"{max(v, key=lambda x: len(v[x])).strip()} x{sum(len(r) for r in v.values())}" for k, v in sorted(groups.items())))
            if variants:
                issues.append(f"column '{h}': SPELLING VARIANTS of the same value (case or spaces): " + "; ".join(" / ".join(repr(x) for x in v) for v in list(variants.values())[:6]) + ". Grouping on the raw text splits these")
            repeated = {k: sorted(n for rows in v.values() for n in rows) for k, v in groups.items() if sum(len(r) for r in v.values()) > 1}
            if repeated and not listed:
                shown = "; ".join(f"'{k}' at rows {rows}" for k, rows in list(repeated.items())[:8])
                issues.append(f"column '{h}': mostly unique, but {len(repeated)} value(s) REPEAT after ignoring case and spaces ({len(groups)} distinct of {len(filled)}): {shown}. If this column should be unique per row, these are double entries")
            if blanks and blanks * 2 <= len(cells):   # a mostly empty notes column is not a finding
                issues.append(f"column '{h}': {blanks} blank cell(s)")
    print("\nDATA PROBLEMS" + (" (none found)" if not issues else ""))
    for n, issue in enumerate(issues, 1):
        print(f"  {n}. {issue}")
    print("\nNot checked: whether values are true, near-duplicates that differ by a typo, units, and anything on other sheets.")


def compute(table, op, col, by, unique_by):
    t = table
    ci = t.column(col)
    bi = t.column(by) if by and op != "count-distinct" else None
    by = by if bi is not None else None
    views = [("duplicates kept", t.rows), ("exact duplicates removed", t.unique_rows())]
    if unique_by:
        ui, seen, firsts = t.column(unique_by), set(), []
        for n, r in t.rows:
            key = re.sub(r"\s+", " ", r[ui].strip()).casefold()
            if key and key in seen:
                continue
            seen.add(key)
            firsts.append((n, r))
        views.append((f"one row per distinct '{t.header[ui]}' (case and spaces ignored, first row kept)", firsts))
    excluded = f"left out: {len(t.total_rows)} total row(s), {len(t.blank_rows)} blank row(s)"
    print(f"COMPUTE {op} of '{t.header[ci]}'" + (f" by '{t.header[bi]}'" if by else "") + f"  [{excluded}]")
    for label, rows in views:
        print(f"\n  -- {label}: {len(rows)} rows --")
        if op == "count-distinct":
            raw = {r[ci] for _, r in rows if r[ci].strip()}
            cleaned = {re.sub(r"\s+", " ", r[ci].strip()).casefold() for _, r in rows if r[ci].strip()}
            print(f"  distinct values as typed: {len(raw)}; after trimming spaces and ignoring case: {len(cleaned)}; blank cells: {sum(1 for _, r in rows if not r[ci].strip())}")
            continue
        groups, labels, skipped = {}, {}, []
        for n, r in rows:
            v, _ = parse_number(r[ci])
            if v is None:
                skipped.append(n)
                continue
            key = re.sub(r"\s+", " ", r[bi].strip()).casefold() if by else ""
            groups.setdefault(key, []).append(v)
            if by:
                labels.setdefault(key, {}).setdefault(r[bi].strip(), 0)
                labels[key][r[bi].strip()] += 1
        for key in sorted(groups):
            vals = groups[key]
            name = (max(labels[key], key=labels[key].get) or "(blank)") if by else "all rows"
            res = sum(vals) if op == "sum" else statistics.mean(vals)
            print(f"  {name}: {fmt(res)}  (n={len(vals)})")
        if by:
            allv = [v for vals in groups.values() for v in vals]
            if allv:
                print(f"  ALL: {fmt(sum(allv) if op == 'sum' else statistics.mean(allv))}  (n={len(allv)})")
        if skipped:
            print(f"  skipped {len(skipped)} row(s) with a blank or non-numeric '{t.header[ci]}': file rows {skipped[:10]}")
    print("\nReport which of these figures you used and why.")


def main(argv):
    utf8_output()
    opts = {"--sheet": "1", "--sum": None, "--mean": None, "--count-distinct": None, "--by": None, "--unique-by": None}
    args, i = [], 0
    while i < len(argv):
        if argv[i] in opts and i + 1 < len(argv):
            opts[argv[i]] = argv[i + 1]
            i += 2
        else:
            args.append(argv[i])
            i += 1
    if len(args) != 1 or args[0].startswith("--") or not opts["--sheet"].isdigit():
        print(__doc__)
        return 2
    path = args[0]
    if path.lower().endswith((".xlsx", ".xlsm")):
        rows, note = read_xlsx(path, int(opts["--sheet"]))
    elif path.lower().endswith(".xls"):
        die("old .xls files are not supported; save the file as .xlsx or .csv first.")
    else:
        rows, note = read_delimited(path)
    table = Table(rows)
    ops = [(k[2:], v) for k, v in opts.items() if k in ("--sum", "--mean", "--count-distinct") and v]
    if not ops:
        audit(table, note)
    for op, col in ops:
        compute(table, op, col, opts["--by"], opts["--unique-by"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
