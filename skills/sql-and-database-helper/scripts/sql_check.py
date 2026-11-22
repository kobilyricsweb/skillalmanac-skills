#!/usr/bin/env python3
"""Static checker for a .sql file. No database connection, no network.

Usage:
    python sql_check.py check FILE.sql [--dialect generic|postgresql|mysql|sqlite]
                                       [--ignore RULE[,RULE...]] [--strict]
    python sql_check.py rules

What it reads: the one file given. What it writes: JSON on stdout, nothing else.
Exit codes: 0 no error-level finding (with --strict: no finding at all),
            1 at least one finding that fails the run, 2 unusable input.

Findings are regex- and token-based on masked text (comments blanked, string
and quoted-identifier contents replaced by 'x'). It is a review aid, not a SQL
parser: it can miss problems and it can flag legitimate SQL. Silence a finding
you have judged acceptable with a comment on the same or the previous line:
    -- sqlcheck: ignore select-star
or for the whole file:
    -- sqlcheck: ignore-file non-transactional-migration
Rule names or ids (SQL001) both work; "all" matches every rule.

Bodies of triggers, procedures, and dollar-quoted functions are not analysed.
"""
import argparse
import json
import os
import re
import sys

VERSION = "0.1.0"
MAX_BYTES = 5 * 1024 * 1024  # a larger file is almost certainly a data dump, not a migration
DIALECTS = ("generic", "postgresql", "mysql", "sqlite")

# id -> (name, severity, one-line summary)
RULES = {
    "SQL001": ("select-star", "warning", "SELECT * or RETURNING * instead of an explicit column list"),
    "SQL002": ("delete-without-where", "error", "DELETE with no WHERE clause"),
    "SQL003": ("update-without-where", "error", "UPDATE with no WHERE clause"),
    "SQL004": ("string-built-sql", "warning", "SQL text assembled by concatenation or string templating"),
    "SQL005": ("quoted-placeholder", "error", "a bind placeholder wrapped in quotes, so it is a literal string"),
    "SQL006": ("missing-limit", "warning", "plain SELECT with no LIMIT, no WHERE and no aggregation"),
    "SQL007": ("implicit-cross-join", "warning", "comma-separated tables in FROM (error when there is no WHERE)"),
    "SQL008": ("not-in-nullable", "warning", "NOT IN with a subquery that may return NULL (error for a literal NULL)"),
    "SQL009": ("non-transactional-migration", "warning", "two or more changes outside a transaction"),
    "SQL010": ("insert-without-columns", "warning", "INSERT with no column list"),
    "SQL011": ("null-comparison", "warning", "= NULL, <> NULL or != NULL is never true"),
    "SQL012": ("tautological-where", "error", "WHERE clause on UPDATE/DELETE that is always true"),
    "SQL013": ("concurrently-in-transaction", "error", "CREATE/DROP/REINDEX ... CONCURRENTLY inside a transaction"),
    "SQL014": ("ddl-autocommit-mysql", "info", "DDL inside a transaction on MySQL commits implicitly"),
    "SQL015": ("transaction-never-closed", "warning", "BEGIN with no COMMIT or ROLLBACK before the end of the file"),
}
NAME_TO_ID = {v[0]: k for k, v in RULES.items()}

SQL_FRAGMENT = re.compile(
    r"\b(select|insert\s+into|delete\s+from|update\s+\S+\s+set|where|from|order\s+by|group\s+by|values)\b", re.I)


# ----------------------------------------------------------------- masking
def mask(text, dialect, allow_dollar):
    """Return (code, nsc, strings). code: comments blanked and string/identifier
    contents replaced by x. nsc: comments blanked, strings intact. strings: list
    of (start, end) of single-quoted literals. All three keep the original length
    and newlines so offsets map to line numbers."""
    n = len(text)
    code = list(text)
    nsc = list(text)
    strings = []

    def blank(arr, a, b):
        for k in range(a, b):
            if arr[k] not in "\r\n":
                arr[k] = " "

    def fill(a, b):
        for k in range(a, b):
            if code[k] not in "\r\n":
                code[k] = "x"

    dollar = re.compile(r"\$([A-Za-z_]\w*)?\$")
    i = 0
    while i < n:
        c = text[i]
        two = text[i:i + 2]
        if two == "--" or (c == "#" and dialect == "mysql"):
            j = text.find("\n", i)
            j = n if j < 0 else j
            blank(code, i, j)
            blank(nsc, i, j)
            i = j
        elif two == "/*":
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            blank(code, i, j)
            blank(nsc, i, j)
            i = j
        elif c == "'":
            j = i + 1
            while j < n:
                if text[j] == "\\" and dialect == "mysql":
                    j += 2
                    continue
                if text[j] == "'":
                    if text[j + 1:j + 2] == "'":
                        j += 2
                        continue
                    break
                j += 1
            end = min(j + 1, n)
            strings.append((i, end))
            fill(i + 1, max(i + 1, end - 1))
            i = end
        elif c == '"' or c == "`":
            j = text.find(c, i + 1)
            end = n if j < 0 else j + 1
            fill(i + 1, max(i + 1, end - 1))
            i = end
        elif c == "$" and allow_dollar and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_")):
            m = dollar.match(text, i)
            if m:
                tag = m.group(0)
                j = text.find(tag, m.end())
                end = n if j < 0 else j + len(tag)
                fill(m.end(), max(m.end(), end - len(tag)))
                i = end
            else:
                i += 1
        elif c == "\\" and allow_dollar and (i == 0 or text[i - 1] == "\n"):
            j = text.find("\n", i)  # psql meta-command line
            j = n if j < 0 else j
            blank(code, i, j)
            blank(nsc, i, j)
            i = j
        else:
            i += 1
    return "".join(code), "".join(nsc), strings


# -------------------------------------------------------------- statements
COMPOUND_HEAD = re.compile(
    r"^\s*create\s+(?:or\s+replace\s+)?(?:(?:temp|temporary|definer\s*=\s*\S+)\s+)*(?:trigger|procedure|function|event)\b", re.I)
DELIM_RE = re.compile(r"[ \t]*delimiter[ \t]+(\S+)[ \t]*(?=\r?\n|$)", re.I)
END_WORD = re.compile(r"\bend\b(?!\s+(?:if|loop|while|repeat|for)\b)", re.I)
OPEN_WORD = re.compile(r"\b(?:begin|case)\b", re.I)


def compound_open(piece):
    if not COMPOUND_HEAD.match(piece):
        return False
    opens = len(OPEN_WORD.findall(piece))
    if not re.search(r"\bbegin\b", piece, re.I):
        return False
    return opens - len(END_WORD.findall(piece)) > 0


class Stmt:
    def __init__(self, code, start, end):
        lead = len(code) - len(code.lstrip())
        self.start = start + lead
        self.code = code.strip()
        self.end = end
        m = re.match(r"\(*\s*([A-Za-z_]+)", self.code)
        self.kw = m.group(1).lower() if m else ""
        self.compound = bool(COMPOUND_HEAD.match(self.code))
        d, depth = 0, []
        for ch in self.code:
            if ch == ")":
                d = max(0, d - 1)
            depth.append(d)
            if ch == "(":
                d += 1
        depth.append(d)
        self.depth = depth

    def top(self, regex, a=0, b=None):
        """Yield matches of regex at paren depth 0."""
        for m in regex.finditer(self.code, a, len(self.code) if b is None else b):
            if self.depth[m.start()] == 0:
                yield m

    @property
    def verb(self):
        if self.kw == "with":
            for m in self.top(re.compile(r"\b(select|insert|update|delete|merge)\b", re.I)):
                return m.group(1).lower()
        return self.kw


def split_statements(code, dialect, allow_delim):
    out, n, i, start, delim, empty = [], len(code), 0, 0, ";", True
    while i < n:
        if empty and allow_delim:
            m = DELIM_RE.match(code, i)
            if m:
                delim = m.group(1)
                i = start = m.end()
                continue
        if code.startswith(delim, i):
            piece = code[start:i]
            if delim == ";" and compound_open(piece):
                i += 1
                empty = False
                continue
            if piece.strip():
                out.append(Stmt(piece, start, i))
            i += len(delim)
            start = i
            empty = True
            continue
        if not code[i].isspace():
            empty = False
        i += 1
    tail = code[start:]
    if tail.strip():
        out.append(Stmt(tail, start, n))
    return out


# ------------------------------------------------------------ select scopes
SET_OP = re.compile(r"\b(union|intersect|except)\b", re.I)
FROM_RE = re.compile(r"\bfrom\b", re.I)
FROM_END = re.compile(
    r"\b(where|group\s+by|having|order\s+by|limit|offset|fetch|window|qualify|returning)\b|\bfor\s+(?:update|share|no\s+key)\b", re.I)
WHERE_RE = re.compile(r"\bwhere\b", re.I)


def split_top(code, dep, a, b, d):
    parts, s = [], a
    for k in range(a, b):
        if code[k] == "," and dep[k] == d:
            parts.append((s, k))
            s = k + 1
    parts.append((s, b))
    return parts


def select_scopes(st):
    code, dep = st.code, st.depth
    out = []
    for m in re.finditer(r"\bselect\b", code, re.I):
        d = dep[m.start()]
        end = len(code)
        for j in range(m.end(), len(code)):
            if dep[j] < d:
                end = j
                break
        for so in SET_OP.finditer(code, m.end(), end):
            if dep[so.start()] == d:
                end = so.start()
                break
        from_kw = None
        for fm in FROM_RE.finditer(code, m.end(), end):
            if dep[fm.start()] != d:
                continue
            if code[max(0, fm.start() - 12):fm.start()].lower().rstrip().endswith("distinct"):
                continue
            from_kw = fm
            break
        list_end = from_kw.start() if from_kw else end
        from_a = from_end = None
        if from_kw:
            from_a = from_kw.end()
            from_end = end
            for em in FROM_END.finditer(code, from_a, end):
                if dep[em.start()] == d:
                    from_end = em.start()
                    break
        has_where = any(dep[w.start()] == d for w in WHERE_RE.finditer(code, m.end(), end))
        out.append(dict(pos=m.start(), d=d, list_a=m.end(), list_b=list_end, from_a=from_a,
                        from_b=from_end, end=end, where=has_where))
    return out


# ------------------------------------------------------------------ findings
class Finding:
    def __init__(self, offset, rule_id, message, fix):
        self.offset, self.rule_id, self.message, self.fix = offset, rule_id, message, fix


STAR_ITEM = re.compile(r"^(?:[\w\"`.\[\]]+\.)?\*(?:\s+(?:except|exclude|replace|ilike|rename)\b.*)?$", re.I | re.S)
SELECT_PREFIX = re.compile(
    r"^\s*(?:(?:all|distinct)\b(?:\s+on\s*\([^)]*\))?|top\s*\(?\s*\d+\s*\)?(?:\s+percent)?|sql_calc_found_rows|straight_join|high_priority)\s*",
    re.I)
AGGREGATE = re.compile(r"\b(count|sum|avg|min|max|bool_and|bool_or|array_agg|string_agg|group_concat)\s*\(", re.I)


def rule_select_star(st, dialect, scopes):
    res = []
    for sc in scopes:
        before = st.code[max(0, sc["pos"] - 30):sc["pos"]]
        if re.search(r"exists\s*\(\s*$", before, re.I):
            continue
        a = sc["list_a"]
        while True:
            m = SELECT_PREFIX.match(st.code[a:sc["list_b"]])
            if not m or m.end() == 0:
                break
            a += m.end()
        for (x, y) in split_top(st.code, st.depth, a, sc["list_b"], sc["d"]):
            item = st.code[x:y].strip()
            if STAR_ITEM.match(item):
                res.append(Finding(x + (len(st.code[x:y]) - len(st.code[x:y].lstrip())), "SQL001",
                                   "SELECT list uses '*', so the result changes whenever a column is added, "
                                   "reordered or dropped.",
                                   "Name the columns you need. Exempt: COUNT(*) and EXISTS (SELECT *)."))
    for m in re.finditer(r"\breturning\s+(\*)", st.code, re.I):
        res.append(Finding(m.start(1), "SQL001", "RETURNING * returns every column, including ones added later.",
                           "List the returned columns."))
    return res


def where_clause_span(st):
    for m in st.top(WHERE_RE):
        end = len(st.code)
        for em in st.top(re.compile(r"\b(returning|order\s+by|limit)\b", re.I), m.end()):
            end = em.start()
            break
        return m, end
    return None, None


TAUTOLOGY = re.compile(r"^\(*\s*(?:true|(\d+)\s*=\s*\1|('[^']*')\s*=\s*\2)\s*\)*$", re.I)
OR_TRUE = re.compile(r"\bor\s+\(*\s*(?:true|(\d+)\s*=\s*\1|('[^']*')\s*=\s*\2)\s*\)*", re.I)


def rule_write_without_where(st, dialect, nsc):
    res = []
    verb = st.verb
    if verb not in ("update", "delete"):
        return res
    wm, wend = where_clause_span(st)
    if verb == "update" and not re.search(r"\bset\b", st.code, re.I):
        return res
    if wm is None:
        # DELETE ... USING / MySQL joins also need WHERE; no top-level WHERE at all is the finding.
        if verb == "delete":
            fix = {"mysql": "Add WHERE. For a staged delete use DELETE ... WHERE ... ORDER BY id LIMIT 1000 (MySQL allows LIMIT on single-table DELETE).",
                   "postgresql": "Add WHERE. To empty a table on purpose use TRUNCATE in its own reviewed step. PostgreSQL has no LIMIT on DELETE; batch with WHERE id IN (SELECT id ... LIMIT n).",
                   "sqlite": "Add WHERE. SQLite runs DELETE without WHERE as a full-table delete with no row count guard."}.get(dialect, "Add WHERE. To empty a table on purpose use TRUNCATE (or DELETE ... WHERE true with a comment) in its own reviewed step.")
            res.append(Finding(0, "SQL002", "DELETE has no WHERE clause and will remove every row.", fix))
        else:
            fix = {"mysql": "Add WHERE. Session variable sql_safe_updates=1 makes MySQL refuse UPDATE/DELETE without a key-column WHERE or LIMIT.",
                   "postgresql": "Add WHERE; PostgreSQL has no LIMIT on UPDATE, so batch with WHERE id IN (SELECT id ... LIMIT n).",
                   "sqlite": "Add WHERE; confirm the row count with SELECT count(*) and the same WHERE first."}.get(dialect, "Add WHERE and confirm the row count with SELECT count(*) and the same WHERE first.")
            res.append(Finding(0, "SQL003", "UPDATE has no WHERE clause and will change every row.", fix))
        return res
    raw = nsc[st.start + wm.end():st.start + wend].strip()
    if TAUTOLOGY.match(raw) or OR_TRUE.search(raw):
        res.append(Finding(wm.start(), "SQL012",
                           "WHERE clause is always true, so this %s touches every row." % verb.upper(),
                           "Replace it with a real condition, or remove it and state that a full-table change is intended."))
    return res


def rule_missing_limit(st, dialect, scopes):
    if st.verb != "select" or st.kw not in ("select", "with") and not st.code.startswith("("):
        return []
    if re.search(r"\binto\b", st.code[:st.code.lower().find("from")] if "from" in st.code.lower() else "", re.I) and st.kw == "select":
        return []
    top = [s for s in scopes if s["d"] == 0]
    if not top:
        return []
    main = top[-1] if st.kw == "with" else top[0]
    if main["from_a"] is None or re.search(r"\binto\b", st.code[main["list_a"]:main["list_b"]], re.I):
        return []
    if any(True for _ in st.top(re.compile(r"\blimit\b|\bfetch\s+(?:first|next)\b|\btop\s*\(?\s*\d", re.I))):
        return []
    if any(s["where"] for s in top):
        return []
    if any(True for _ in st.top(re.compile(r"\bgroup\s+by\b", re.I))):
        return []
    lst = st.code[main["list_a"]:main["list_b"]]
    if AGGREGATE.search(lst):
        return []
    return [Finding(main["pos"], "SQL006",
                    "SELECT has no LIMIT, no WHERE and no aggregation: on a large table it returns every row.",
                    "Add LIMIT n (or FETCH FIRST n ROWS ONLY on PostgreSQL) with an ORDER BY, or filter with WHERE. "
                    "Without ORDER BY the rows returned by LIMIT are arbitrary.")]


def rule_cross_join(st, dialect, scopes):
    res = []
    for sc in scopes:
        if sc["from_a"] is None:
            continue
        items = [st.code[x:y].strip() for (x, y) in split_top(st.code, st.depth, sc["from_a"], sc["from_b"], sc["d"])]
        items = [it for it in items if it]
        tables = [it for it in items if not re.match(r"^(?:lateral\b|[\w.\"`]+\s*\()", it, re.I)]
        if len(items) > 1 and len(tables) >= 2:
            sev_error = not sc["where"]
            res.append(Finding(sc["from_a"], "SQL007",
                               ("FROM lists %d tables separated by commas and the query has no WHERE: this is a "
                                "cartesian product." % len(tables)) if sev_error else
                               ("FROM lists %d tables separated by commas; if any join condition is missing from "
                                "WHERE the result is a cartesian product." % len(tables)),
                               "Write JOIN ... ON for each pair. Use CROSS JOIN when a product is really intended."))
            res[-1].severity = "error" if sev_error else "warning"
    return res


def matching_paren(st, open_idx):
    d = st.depth[open_idx]
    for j in range(open_idx + 1, len(st.code)):
        if st.code[j] == ")" and st.depth[j] == d:
            return j
    return len(st.code)


def rule_not_in(st, dialect):
    res = []
    for m in re.finditer(r"\bnot\s+in\s*\(", st.code, re.I):
        op = m.end() - 1
        cl = matching_paren(st, op)
        inner = st.code[op + 1:cl]
        if re.match(r"\s*(select|with)\b", inner, re.I):
            if re.search(r"\bis\s+not\s+null\b", inner, re.I):
                continue
            res.append(Finding(m.start(), "SQL008",
                               "NOT IN (subquery) returns no rows at all if the subquery yields a single NULL.",
                               "Use NOT EXISTS (SELECT 1 FROM ... WHERE inner.col = outer.col), or add "
                               "WHERE col IS NOT NULL inside the subquery."))
        elif re.search(r"\bnull\b", inner, re.I):
            f = Finding(m.start(), "SQL008", "NOT IN list contains NULL: the condition is never true.",
                        "Remove NULL from the list and test IS NOT NULL separately.")
            f.severity = "error"
            res.append(f)
    return res


def rule_null_comparison(st, dialect):
    res = []
    for m in re.finditer(r"(?:<>|!=)\s*null\b", st.code, re.I):
        res.append(Finding(m.start(), "SQL011", "Comparison to NULL with <> or != yields NULL, never true.",
                           "Use IS NOT NULL (or IS DISTINCT FROM; MySQL spells the null-safe form <=>)."))
    wh = re.search(r"\b(where|having|when)\b", st.code, re.I)
    for m in re.finditer(r"(?<![<>!:=])=\s*null\b", st.code, re.I):
        if wh and m.start() > wh.start() or st.verb == "select":
            res.append(Finding(m.start(), "SQL011", "= NULL yields NULL, never true.",
                               "Use IS NULL. (SET col = NULL in UPDATE is fine and is not flagged.)"))
    return res


INSERT_NO_COLS = re.compile(
    r"^(?:insert|replace)\s+(?:or\s+\w+\s+|ignore\s+|low_priority\s+|delayed\s+|high_priority\s+)*(?:into\s+)?"
    r"[\w.\"`\[\]]+\s+(?:values|value|select|with|default\s+values|table)\b", re.I)


def rule_insert_columns(st, dialect):
    if st.kw in ("insert", "replace") and INSERT_NO_COLS.match(st.code):
        return [Finding(0, "SQL010", "INSERT has no column list, so it depends on the table's current column order.",
                        "Write INSERT INTO t (a, b, c) VALUES (...).")]
    return []


SIMPLE_PLACEHOLDER = re.compile(r"^(?:\?|%s|%d|%\(\w+\)[sd]|:\w+|\$\d+|\{[A-Za-z_]\w*\})$")
EXEC_CONTEXT = re.compile(r"^(?:exec|execute|prepare|call)\b|\bsp_executesql\b|\bexecute\s+immediate\b", re.I)
OPERAND = re.compile(r"[@A-Za-z_][\w.]*|\$[A-Za-z_]\w*")


def rule_string_built(st, dialect, strings, nsc, text):
    res = []
    base = st.start
    lim = base + len(st.code)
    in_stmt = [(a, b) for (a, b) in strings if base <= a < lim]
    for (a, b) in in_stmt:
        content = text[a + 1:b - 1]
        if SIMPLE_PLACEHOLDER.match(content.strip()):
            res.append(Finding(a - base, "SQL005",
                               "'%s' is a quoted string, not a bind placeholder: the driver will not bind it." % content.strip(),
                               "Remove the quotes. Placeholders: PostgreSQL protocol $1, psycopg and MySQL connectors %s, "
                               "SQLite and JDBC ?, named :name."))
    for m in re.finditer(r"\$\{[^}]*\}|#\{[^}]*\}", nsc[base:lim]):
        res.append(Finding(m.start(), "SQL004", "Template interpolation (%s) puts a value into the SQL text." % m.group(0),
                           "Bind the value as a parameter instead of interpolating it."))
    for m in re.finditer(r"(?<![$#])\{[A-Za-z_0-9]*\}", st.code):
        res.append(Finding(m.start(), "SQL004", "Brace placeholder %s is string formatting, not a bind parameter." % m.group(0),
                           "Use the driver's bind placeholder; identifiers need an allow-list, not formatting."))
    exec_ctx = bool(EXEC_CONTEXT.search(st.code))
    hit = None
    for (a, b) in in_stmt:
        content = text[a + 1:b - 1]
        if not SQL_FRAGMENT.search(content):
            continue
        after = st.code[b - base:b - base + 40]
        m = re.match(r"\s*(\|\||\+)\s*(\S)", after)
        if m and m.group(2) != "'" and OPERAND.match(after[m.end() - 1:] or ""):
            hit = a - base
        before = st.code[max(0, a - base - 40):a - base]
        m2 = re.search(r"([@\w.$]+)\s*(\|\||\+)\s*$", before)
        if m2 and not before.rstrip().endswith("'") and OPERAND.fullmatch(m2.group(1)):
            hit = a - base
        if hit is not None:
            break
    if hit is None:
        for cm in re.finditer(r"\bconcat(?:_ws)?\s*\(", st.code, re.I):
            op = cm.end() - 1
            cl = matching_paren(st, op)
            parts = split_top(st.code, st.depth, op + 1, cl, st.depth[op] + 1)
            has_sql = any(st.code[x:y].strip().startswith("'") and SQL_FRAGMENT.search(text[base + x + st.code[x:y].find("'") + 1:base + y - 1]) for (x, y) in parts)
            has_var = any(re.fullmatch(r"[@$]?[A-Za-z_][\w.]*", st.code[x:y].strip()) for (x, y) in parts)
            if has_sql and has_var:
                hit = cm.start()
                break
    if hit is not None:
        res.append(Finding(hit, "SQL004",
                           "SQL text is built by concatenating a variable into a SQL string"
                           + (" and passed to dynamic execution." if exec_ctx else "."),
                           {"postgresql": "Use EXECUTE ... USING for values, and format() with %I (identifier) or %L (literal) instead of %s.",
                            "mysql": "Use PREPARE ... USING @v for values; validate identifiers against an allow-list before CONCAT.",
                            "sqlite": "SQLite has no dynamic SQL in SQL itself: build the text in the application and bind values with ?."}.get(
                               dialect, "Bind values as parameters; allow-list any identifier that must vary.")))
        res[-1].severity = "error" if exec_ctx else "warning"
    for (a, b) in in_stmt:
        content = text[a + 1:b - 1]
        if "%s" in content and re.search(r"%s(?![A-Za-z])", content) and SQL_FRAGMENT.search(content) and re.search(r"\bformat\s*\(", st.code, re.I):
            res.append(Finding(a - base, "SQL004", "format() with %s inlines raw text into SQL.",
                               "Use %I for identifiers and %L for literals, or pass values with USING."))
            break
    return res


MODIFY_VERBS = ("create", "alter", "drop", "truncate", "rename", "insert", "update", "delete", "merge", "replace",
                "grant", "revoke", "comment")
DDL_VERBS = ("create", "alter", "drop", "truncate", "rename", "comment", "grant", "revoke")
TXN_START = re.compile(r"^(?:begin\b(?!\s*(?:atomic)\b)|start\s+transaction\b)", re.I)
TXN_END = re.compile(r"^(?:commit\b|end\b(?:\s+(?:transaction|work))?\s*$|rollback\b(?!\s+to\b))", re.I)
CONCURRENTLY = re.compile(r"\bconcurrently\b", re.I)


def transaction_findings(stmts, dialect):
    res, in_txn, txn_at, outside, ddl_in_txn = [], False, None, [], []
    for st in stmts:
        if st.compound:
            if st.kw == "create":
                (ddl_in_txn if in_txn else outside).append(st)
            continue
        if TXN_START.match(st.code):
            in_txn, txn_at = True, st
            continue
        if TXN_END.match(st.code):
            in_txn = False
            continue
        verb = st.verb
        if verb not in MODIFY_VERBS:
            continue
        if CONCURRENTLY.search(st.code):
            if in_txn:
                res.append(Finding(st.start, "SQL013",
                                   "CONCURRENTLY cannot run inside a transaction block; PostgreSQL rejects it.",
                                   "Run this statement on its own, outside BEGIN/COMMIT, and drop an INVALID index left by a failed attempt before retrying."))
            continue
        if in_txn:
            if verb in DDL_VERBS:
                ddl_in_txn.append(st)
        else:
            outside.append(st)
    if len(outside) >= 2:
        first = outside[0]
        msgs = {"mysql": ("MySQL commits DDL implicitly, so BEGIN/COMMIT does not make DDL atomic. "
                          "Make each step idempotent (IF NOT EXISTS / IF EXISTS), or keep one DDL statement per migration, and wrap only the DML in a transaction."),
                "postgresql": "Wrap the file in BEGIN; ... COMMIT; PostgreSQL DDL is transactional. Leave CONCURRENTLY statements out of the block.",
                "sqlite": "Wrap the file in BEGIN; ... COMMIT; SQLite DDL is transactional (use BEGIN IMMEDIATE to take the write lock at once)."}
        res.append(Finding(first.start, "SQL009",
                           "%d data or schema changes run outside a transaction; a failure part-way leaves the database half-migrated." % len(outside),
                           msgs.get(dialect, "Wrap the changes in BEGIN; ... COMMIT; where the engine supports transactional DDL (PostgreSQL, SQLite). "
                                              "MySQL commits DDL implicitly; use idempotent steps there. Ignore this finding if the migration runner already wraps each file.")))
    if in_txn and txn_at is not None:
        res.append(Finding(txn_at.start, "SQL015", "Transaction opened here is never committed or rolled back in this file.",
                           "End the file with COMMIT; (or ROLLBACK; for a dry run)."))
    if dialect == "mysql" and ddl_in_txn:
        res.append(Finding(ddl_in_txn[0].start, "SQL014",
                           "%d DDL statement(s) inside a transaction: MySQL commits implicitly at each, so a later failure does not undo them." % len(ddl_in_txn),
                           "Split DDL from DML, make DDL idempotent."))
    return res


# --------------------------------------------------------------------- main
IGNORE_RE = re.compile(r"sqlcheck:\s*ignore(-file)?\s+([\w,\s-]+)", re.I)


def parse_ignores(lines):
    line_ign, file_ign = {}, set()
    for ln, raw in enumerate(lines, 1):
        m = IGNORE_RE.search(raw)
        if not m:
            continue
        names = {t.lower() for t in re.split(r"[,\s]+", m.group(2).strip()) if t}
        if m.group(1):
            file_ign |= names
        else:
            line_ign[ln] = names
    return line_ign, file_ign


def matches(names, rule_id):
    return "all" in names or RULES[rule_id][0] in names or rule_id.lower() in names


def analyse(text, dialect, ignore):
    allow_delim = dialect in ("mysql", "generic") and bool(re.search(r"^[ \t]*delimiter\b", text, re.I | re.M))
    allow_dollar = dialect in ("postgresql", "generic") and not allow_delim
    code, nsc, strings = mask(text, dialect, allow_dollar)
    stmts = split_statements(code, dialect, allow_delim)
    findings = []
    for st in stmts:
        if st.compound:
            continue
        scopes = select_scopes(st)
        found = []
        found += rule_select_star(st, dialect, scopes)
        found += rule_write_without_where(st, dialect, nsc)
        found += rule_missing_limit(st, dialect, scopes)
        found += rule_cross_join(st, dialect, scopes)
        found += rule_not_in(st, dialect)
        found += rule_null_comparison(st, dialect)
        found += rule_insert_columns(st, dialect)
        found += rule_string_built(st, dialect, strings, nsc, text)
        for f in found:
            f.offset += st.start
        findings += found
    findings += transaction_findings(stmts, dialect)

    lines = text.splitlines()
    line_ign, file_ign = parse_ignores(lines)
    starts = [0]
    for m in re.finditer(r"\n", text):
        starts.append(m.end())
    import bisect
    out, suppressed = [], 0
    for f in findings:
        ln = bisect.bisect_right(starts, f.offset)
        col = f.offset - starts[ln - 1] + 1
        names = set(file_ign) | set(ignore)
        names |= line_ign.get(ln, set()) | line_ign.get(ln - 1, set())
        if matches(names, f.rule_id):
            suppressed += 1
            continue
        sev = getattr(f, "severity", RULES[f.rule_id][1])
        snippet = lines[ln - 1].strip() if ln - 1 < len(lines) else ""
        out.append({"line": ln, "column": col, "id": f.rule_id, "rule": RULES[f.rule_id][0], "severity": sev,
                    "message": f.message, "fix": f.fix, "snippet": snippet[:140]})
    out.sort(key=lambda d: (d["line"], d["column"], d["id"]))
    return len(stmts), out, suppressed


def cmd_check(args):
    path = args.file
    if not os.path.isfile(path):
        print("sql_check: file not found: %s" % path, file=sys.stderr)
        return 2
    if os.path.getsize(path) == 0:
        print("sql_check: file is empty: %s" % path, file=sys.stderr)
        return 2
    if os.path.getsize(path) > MAX_BYTES:
        print("sql_check: file is larger than %d bytes; split it or check the migration, not the dump." % MAX_BYTES, file=sys.stderr)
        return 2
    with open(path, "rb") as fh:
        raw = fh.read()
    note = None
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
        note = "file is not valid UTF-8; decoded as latin-1"
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    ignore = set()
    for tok in (args.ignore or "").split(","):
        tok = tok.strip().lower()
        if tok:
            if tok not in NAME_TO_ID and tok.upper() not in RULES and tok != "all":
                print("sql_check: unknown rule in --ignore: %s (run 'rules' to list them)" % tok, file=sys.stderr)
                return 2
            ignore.add(tok)
    n_stmts, findings, suppressed = analyse(text, args.dialect, ignore)
    counts = {"error": 0, "warning": 0, "info": 0}
    for f in findings:
        counts[f["severity"]] += 1
    failed = counts["error"] > 0 or (args.strict and len(findings) > 0)
    verdict = "fail" if counts["error"] else ("review" if findings else "clean")
    report = {"tool": "sql_check", "version": VERSION, "command": "check", "file": os.path.basename(path),
              "dialect": args.dialect, "statements": n_stmts, "counts": counts, "suppressed": suppressed,
              "verdict": verdict, "findings": findings}
    if note:
        report["note"] = note
    print(json.dumps(report, indent=2, allow_nan=False))
    return 1 if failed else 0


def cmd_rules(_args):
    print(json.dumps({"tool": "sql_check", "version": VERSION, "command": "rules",
                      "rules": [{"id": k, "rule": v[0], "severity": v[1], "summary": v[2]} for k, v in RULES.items()]},
                     indent=2, allow_nan=False))
    return 0


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="sql_check", description="Static checks for a .sql file (no database connection).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check one .sql file")
    c.add_argument("file")
    c.add_argument("--dialect", choices=DIALECTS, default="generic")
    c.add_argument("--ignore", default="", help="comma-separated rule names or ids to skip")
    c.add_argument("--strict", action="store_true", help="exit 1 on any finding, not only errors")
    c.set_defaults(fn=cmd_check)
    r = sub.add_parser("rules", help="list the rules as JSON")
    r.set_defaults(fn=cmd_rules)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
