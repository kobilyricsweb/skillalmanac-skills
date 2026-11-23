"""Check that a translation uses the agreed glossary target term on each line.

Inputs: a glossary CSV with the header row source,target; a source text file;
and a translated text file. Lines are paired by line number. For every glossary
source term found in a source line, the paired translated line must contain the
agreed target term. A second glossary row for the same source term with a
different target defines a known variant; a variant found in the translated
line is reported as VARIANT. The script does not translate and does not write
any file. It reads inputs only, uses the standard library only, and makes no
network calls.

Exit codes: 0 no findings, 1 findings, 2 usage or input error.
"""
import argparse
import csv
import io
import json
import re
import sys

MAX_BYTES = 2 * 1024 * 1024


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        _fail("usage: " + message)


def _fail(message):
    sys.stderr.write(json.dumps({"error": message}, ensure_ascii=False) + "\n")
    sys.exit(2)


def read_text(path, label):
    try:
        with open(path, "rb") as fh:
            data = fh.read(MAX_BYTES + 1)
    except OSError as exc:
        _fail("cannot read %s file: %s" % (label, exc.strerror or "unknown error"))
    if len(data) > MAX_BYTES:
        _fail("%s file exceeds 2 MB" % label)
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        _fail("%s file is not valid UTF-8" % label)


def split_lines(text):
    if not text:
        return []
    lines = text.replace("\r\n", "\n").split("\n")
    if text.endswith("\n"):
        lines.pop()
    return lines


def parse_glossary(text):
    try:
        rows = [r for r in csv.reader(io.StringIO(text)) if any(c.strip() for c in r)]
    except csv.Error:
        _fail("glossary is not valid CSV")
    if not rows:
        _fail("glossary is empty")
    if [c.strip().lower() for c in rows[0]] != ["source", "target"]:
        _fail("glossary header must be source,target")
    agreed = {}
    variants = {}
    for n, row in enumerate(rows[1:], start=1):
        if len(row) != 2 or not row[0].strip() or not row[1].strip():
            _fail("glossary data row %d must have a non-empty source and target" % n)
        src_key = row[0].strip().casefold()
        target = row[1].strip()
        if src_key not in agreed:
            agreed[src_key] = (row[0].strip(), target)
            variants[src_key] = []
        elif target.casefold() != agreed[src_key][1].casefold():
            seen = [v.casefold() for v in variants[src_key]]
            if target.casefold() not in seen:
                variants[src_key].append(target)
    if not agreed:
        _fail("glossary has no data rows")
    return agreed, variants


def term_pattern(term):
    return re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)", re.IGNORECASE)


def run_check(agreed, variants, src_lines, tgt_lines):
    src_pat = {k: term_pattern(v[0]) for k, v in agreed.items()}
    tgt_pat = {k: term_pattern(v[1]) for k, v in agreed.items()}
    var_pat = {k: [(name, term_pattern(name)) for name in variants[k]] for k in agreed}
    findings = []
    occurrences = 0
    ok = 0
    for line_no, (src, tgt) in enumerate(zip(src_lines, tgt_lines), start=1):
        for key, (src_term, tgt_term) in agreed.items():
            if not src_pat[key].search(src):
                continue
            occurrences += 1
            hit = None
            for name, pat in var_pat[key]:
                if pat.search(tgt):
                    hit = name
                    break
            if hit is not None:
                findings.append({"line": line_no, "source_term": src_term,
                                 "agreed_target": tgt_term, "status": "VARIANT",
                                 "variant_found": hit})
            elif tgt_pat[key].search(tgt):
                ok += 1
            else:
                findings.append({"line": line_no, "source_term": src_term,
                                 "agreed_target": tgt_term, "status": "MISSING",
                                 "variant_found": None})
    return findings, occurrences, ok


def main(argv):
    parser = _Parser(description="Check glossary term consistency between a source and a translation.")
    parser.add_argument("--glossary", required=True, help="glossary CSV with header source,target")
    parser.add_argument("--source", required=True, help="source text file, one segment per line")
    parser.add_argument("--translated", required=True, help="translated text file, same line count")
    args = parser.parse_args(argv)

    agreed, variants = parse_glossary(read_text(args.glossary, "glossary"))
    src_lines = split_lines(read_text(args.source, "source"))
    tgt_lines = split_lines(read_text(args.translated, "translated"))
    if len(src_lines) != len(tgt_lines):
        _fail("line count mismatch: source has %d lines, translated has %d"
              % (len(src_lines), len(tgt_lines)))

    findings, occurrences, ok = run_check(agreed, variants, src_lines, tgt_lines)
    report = {
        "status": "findings" if findings else "ok",
        "source_lines": len(src_lines),
        "glossary_terms": len(agreed),
        "term_occurrences": occurrences,
        "ok_count": ok,
        "coverage_percent": round(100.0 * ok / occurrences, 1) if occurrences else None,
        "findings": findings,
    }
    sys.stdout.buffer.write((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
