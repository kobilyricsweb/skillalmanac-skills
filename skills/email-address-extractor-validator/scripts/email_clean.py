#!/usr/bin/env python3
"""Extract, syntax-check and de-duplicate email addresses in a plain text file.

Usage:
    python -I scripts/email_clean.py <input-file> [--out <output-file>]

Behavior:
    - Reads one UTF-8 text file (max 2 MB). The input is never modified.
    - Candidate regex: a run of characters that are not whitespace, angle
      brackets, quotes, parentheses, commas, semicolons, colons or square
      brackets, containing at least one "@". One trailing "." is stripped.
    - Each candidate is checked against the syntax rules in validate().
    - Valid addresses are compared case-insensitively; repeats are DUPLICATE.
    - Role-looking local parts (info, sales, support, ...) are counted for
      information only and do not affect the exit code.
    - No DNS lookup, no network, no subprocess. Addresses are masked in the
      JSON report; only line numbers and codes are printed in full.
    - With --out, the unique valid addresses (first-seen order, original
      casing of the first occurrence) are written to a NEW file. The script
      refuses (exit 2) if the output path already exists, so it never
      overwrites, and it never writes to the input path.

Exit codes:
    0  no invalid addresses and no duplicates
    1  findings present (at least one invalid address or duplicate)
    2  usage or input error (one-line JSON error on stderr)
"""

import json
import os
import re
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_ADDRESS_LEN = 254
MAX_LOCAL_LEN = 64

CANDIDATE_RE = re.compile(r"[^\s<>\"'(),;:\[\]]*@[^\s<>\"'(),;:\[\]]*")
LOCAL_ATOM = r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
LOCAL_RE = re.compile(LOCAL_ATOM + r"(?:\." + LOCAL_ATOM + r")*")
LABEL_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?")
TLD_RE = re.compile(r"[A-Za-z]{2,}")

ROLE_LOCALS = {
    "abuse", "admin", "billing", "contact", "help", "hello", "hostmaster",
    "info", "noreply", "no-reply", "postmaster", "sales", "support", "team",
    "webmaster",
}

USAGE = "python -I scripts/email_clean.py <input-file> [--out <output-file>]"


def fail(code, detail):
    """Print a one-line JSON error on stderr and exit 2."""
    sys.stderr.write(json.dumps({"error": code, "detail": detail}) + "\n")
    sys.exit(2)


def validate(addr):
    """Return None when addr is syntactically valid, else an error code."""
    if len(addr) > MAX_ADDRESS_LEN:
        return "TOO_LONG"
    if addr.count("@") > 1:
        return "MULTIPLE_AT"
    local, domain = addr.split("@")
    if not local:
        return "EMPTY_LOCAL"
    if not domain:
        return "EMPTY_DOMAIN"
    if len(local) > MAX_LOCAL_LEN:
        return "LOCAL_TOO_LONG"
    if ".." in addr:
        return "CONSECUTIVE_DOTS"
    if local.startswith(".") or local.endswith("."):
        return "LOCAL_EDGE_DOT"
    if not LOCAL_RE.fullmatch(local):
        return "LOCAL_BAD_CHAR"
    if "." not in domain:
        return "DOMAIN_NO_DOT"
    labels = domain.split(".")
    for label in labels:
        if not LABEL_RE.fullmatch(label):
            return "DOMAIN_BAD_LABEL"
    if not TLD_RE.fullmatch(labels[-1]):
        return "TLD_INVALID"
    return None


def mask(addr):
    """Mask the local part for the JSON report: first character plus ***."""
    local, _, domain = addr.partition("@")
    return (local[:1] + "***" if local else "***") + "@" + domain


def read_input(path):
    if not os.path.exists(path):
        fail("file_not_found", "input file does not exist")
    if not os.path.isfile(path):
        fail("not_a_file", "input path is not a regular file")
    try:
        with open(path, "rb") as fh:
            data = fh.read(MAX_INPUT_BYTES + 1)
    except OSError:
        fail("read_failed", "input file could not be read")
    if len(data) > MAX_INPUT_BYTES:
        fail("input_too_large", "input exceeds 2097152 bytes")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("invalid_utf8", "input is not valid UTF-8")


def main(argv):
    out_path = None
    args = list(argv)
    if "--out" in args:
        idx = args.index("--out")
        if idx + 1 >= len(args):
            fail("usage", USAGE)
        out_path = args[idx + 1]
        del args[idx:idx + 2]
    if len(args) != 1 or args[0].startswith("--"):
        fail("usage", USAGE)
    input_path = args[0]

    text = read_input(input_path)
    if out_path is not None and os.path.exists(out_path):
        fail("output_exists", "output path already exists; choose a new file name")

    lines = text.splitlines()
    candidates = 0
    valid_occurrences = 0
    role_count = 0
    invalid_items = []
    duplicate_items = []
    seen = {}      # lowercased address -> first line number
    unique = []    # (first-seen original address) for --out

    for lineno, line in enumerate(lines, start=1):
        for match in CANDIDATE_RE.finditer(line):
            candidates += 1
            addr = match.group(0).rstrip(".")
            code = validate(addr)
            if code is not None:
                invalid_items.append({"line": lineno, "code": code})
                continue
            valid_occurrences += 1
            local = addr.split("@")[0].lower()
            if local in ROLE_LOCALS:
                role_count += 1
            key = addr.lower()
            if key in seen:
                duplicate_items.append({
                    "line": lineno,
                    "first_line": seen[key],
                    "value_masked": mask(addr),
                })
            else:
                seen[key] = lineno
                unique.append(addr)

    report = {
        "status": "findings" if (invalid_items or duplicate_items) else "ok",
        "lines_scanned": len(lines),
        "candidates": candidates,
        "valid_occurrences": valid_occurrences,
        "unique_valid": len(unique),
        "invalid": len(invalid_items),
        "duplicates": len(duplicate_items),
        "role_addresses": role_count,
        "invalid_items": invalid_items,
        "duplicate_items": duplicate_items,
    }

    if out_path is not None:
        try:
            with open(out_path, "x", encoding="utf-8", newline="\n") as fh:
                for addr in unique:
                    fh.write(addr + "\n")
        except FileExistsError:
            fail("output_exists", "output path already exists; choose a new file name")
        except OSError:
            fail("output_write_failed", "output file could not be created")
        report["written_unique"] = len(unique)

    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    sys.exit(1 if report["status"] == "findings" else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
