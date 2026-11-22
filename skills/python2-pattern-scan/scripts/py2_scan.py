"""Scan one Python file for Python 2 only constructs and report each with its Python 3 replacement.

Read-only: the input is opened for reading and never rewritten; no output file is written.
Strings and comments are masked with tokenize before pattern checks, so text inside them is
not reported. When the file parses under the running Python 3, name checks use the ast;
otherwise they use the masked text. If tokenize cannot read the file, masking is skipped and
the output says so with "masking": "none".

Usage: python -I py2_scan.py <input-file>
Exit codes: 0 no findings, 1 findings reported, 2 usage or input error.
Stdout: one JSON object. Stderr: one-line JSON error object on exit 2.
"""
import ast
import io
import json
import os
import re
import sys
import tokenize
import warnings

MAX_BYTES = 2 * 1024 * 1024
TOOL_VERSION = "0.1.0"

# name -> (rule code, construct label, Python 3 replacement)
NAME_MAP = {
    "xrange": ("PY2-006", "xrange", "range"),
    "raw_input": ("PY2-007", "raw_input", "input"),
    "unicode": ("PY2-008", "unicode type", "str"),
    "long": ("PY2-008", "long type", "int"),
    "basestring": ("PY2-008", "basestring type", "str"),
}
NAME_RE = re.compile(r"(?<![\w.])(?P<name>xrange|raw_input|unicode|long|basestring)\b")

# (rule code, construct label, compiled regex on masked code, replacement template)
RULES = [
    ("PY2-001", "print statement",
     re.compile(r"(?:^\s*|[;:]\s*)print(?:\s*>>|\s+(?![=.,:)\]\(]))"),
     "print(...) function call"),
    ("PY2-002", "except clause with comma",
     re.compile(r"\bexcept\s+(?P<exc>[^:]*?)\s*,\s*(?P<name>[A-Za-z_]\w*)\s*:"),
     "except {exc} as {name}:"),
    ("PY2-003", "backtick repr",
     re.compile(r"`(?P<inner>[^`]*)`"),
     "repr({inner})"),
    ("PY2-004", "exec statement",
     re.compile(r"(?:^\s*|[;:]\s*)exec\s+(?![=.,:)\]\(])"),
     "exec(code, namespace) function call"),
    ("PY2-005", "dict.has_key() call",
     re.compile(r"\.has_key\s*\("),
     "key in mapping"),
    ("PY2-008", "long literal suffix L",
     re.compile(r"(?<![\w.])\d+[lL](?!\w)"),
     "drop the L suffix"),
    ("PY2-009", "integer division risk (working heuristic)",
     re.compile(r"(?<![\w.])(?:\d+|len\([^()]*\)|int\([^()]*\))\s*/(?![/=])\s*"
                r"(?:\d+|len\([^()]*\)|int\([^()]*\))(?![\w.])"),
     "use // for floor division, or float(a) / b for true division"),
    ("PY2-010", "old-style octal literal",
     re.compile(r"(?<![\w.])0+(?P<digits>[1-7][0-7]*)(?![\w.])"),
     "0o{digits}"),
]

IMPORT_RE = re.compile(r"^\s*import\s+(?P<mod>[A-Za-z_]\w*)")
FROM_RE = re.compile(r"^\s*from\s+(?P<mod>[A-Za-z_]\w*)\s+import\b")
FUTURE_ABS_RE = re.compile(r"^\s*from\s+__future__\s+import\s+.*\babsolute_import\b", re.M)


def fail(code, message):
    sys.stderr.write(json.dumps({"error": code, "message": message}) + "\n")
    sys.exit(2)


def read_source(path):
    base = os.path.basename(path)
    if not os.path.isfile(path):
        fail("file_missing", "not a readable file: " + base)
    if not path.lower().endswith(".py"):
        fail("not_python_file", "input must end in .py: " + base)
    try:
        with open(path, "rb") as handle:
            data = handle.read(MAX_BYTES + 1)
    except OSError:
        fail("file_unreadable", "cannot open: " + base)
    if len(data) > MAX_BYTES:
        fail("too_large", "input exceeds 2 MB: " + base)
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
        return data.decode(encoding)
    except (SyntaxError, LookupError, UnicodeDecodeError):
        fail("not_decodable", "cannot decode as UTF-8 or the declared coding: " + base)


def mask_code(text):
    """Return the lines with string and comment spans replaced by spaces, or None if tokenize fails."""
    grid = [list(line) for line in text.split("\n")]
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError):
        return None
    for tok in tokens:
        if tok.type not in (tokenize.STRING, tokenize.COMMENT):
            continue
        (start_row, start_col), (end_row, end_col) = tok.start, tok.end
        for row in range(start_row, end_row + 1):
            line = grid[row - 1]
            first = start_col if row == start_row else 0
            last = end_col if row == end_row else len(line)
            for col in range(first, min(last, len(line))):
                line[col] = " "
    return ["".join(line) for line in grid]


def parse_tree(text):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            return ast.parse(text)
        except (SyntaxError, ValueError, RecursionError, MemoryError):
            return None


def is_local_module(folder, name):
    return (os.path.isfile(os.path.join(folder, name + ".py"))
            or os.path.isfile(os.path.join(folder, name, "__init__.py")))


def scan(text, folder, base):
    masked = mask_code(text)
    masking = "tokenize" if masked is not None else "none"
    code_lines = masked if masked is not None else text.split("\n")
    code = "\n".join(code_lines)
    tree = parse_tree(text)
    findings = []

    def add(line, rule_code, construct, replacement):
        findings.append({"line": line, "code": rule_code,
                         "construct": construct, "replacement": replacement})

    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in NAME_MAP:
                rule_code, construct, replacement = NAME_MAP[node.id]
                add(node.lineno, rule_code, construct, replacement)

    for lineno, line in enumerate(code_lines, start=1):
        for rule_code, construct, regex, template in RULES:
            for match in regex.finditer(line):
                add(lineno, rule_code, construct, template.format(**match.groupdict()))
        if tree is None:
            for match in NAME_RE.finditer(line):
                rule_code, construct, replacement = NAME_MAP[match.group("name")]
                add(lineno, rule_code, construct, replacement)

    if not FUTURE_ABS_RE.search(code):
        for lineno, line in enumerate(code_lines, start=1):
            match = IMPORT_RE.match(line)
            if match and is_local_module(folder, match.group("mod")):
                mod = match.group("mod")
                add(lineno, "PY2-011", "implicit relative import",
                    "from . import " + mod)
                continue
            match = FROM_RE.match(line)
            if match and is_local_module(folder, match.group("mod")):
                mod = match.group("mod")
                add(lineno, "PY2-011", "implicit relative import",
                    "from ." + mod + " import ...")

    findings.sort(key=lambda item: (item["line"], item["code"]))
    return {
        "tool": "py2_scan",
        "version": TOOL_VERSION,
        "file": base,
        "ast_parsed": tree is not None,
        "masking": masking,
        "count": len(findings),
        "findings": findings,
    }


def main(argv):
    if len(argv) != 2:
        fail("usage", "usage: py2_scan.py <input-file>")
    path = argv[1]
    text = read_source(path)
    folder = os.path.dirname(os.path.abspath(path))
    result = scan(text, folder, os.path.basename(path))
    sys.stdout.write(json.dumps(result, ensure_ascii=True) + "\n")
    return 1 if result["count"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
