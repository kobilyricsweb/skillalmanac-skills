#!/usr/bin/env python3
"""Scan a folder of architecture decision records and print strict JSON.

Usage:
    python scripts/adr_scan.py scan <adr-folder> [--strict]

Reads every top-level *.md file in the folder (README, index and template files
are skipped). Writes nothing. Standard library only, no network.

Exit codes: 0 no errors (and no warnings with --strict), 1 findings,
2 bad usage or folder not found/empty of ADRs.

Output (one JSON object): command, dir, adr_count, numbers, findings
(file, line, rule, severity, message), counts_by_rule, errors, warnings, ok.
Rule names are listed in SKILL.md.
"""
import json
import os
import re
import sys

# A real consequence has at least one benefit and one cost, which is rarely
# under this many words. Shorter text is treated as empty.
MIN_CONSEQUENCE_WORDS = 15
# Options whose text carries none of these words probably list only upsides.
DOWNSIDE_RE = re.compile(
    r"\b(con|cons|downside|downsides|drawback|drawbacks|risk|risks|cost|costs|"
    r"expensive|slower|worse|trade-?offs?|however|but|lacks?|limit|limits|"
    r"limitation|limitations|harder|complex|complexity|lock-?in|against|"
    r"fails?|requires?|needs?|break|breaks|broken|weak|weaker|slow|slows|locks?|"
    r"overhead|brittle|fragile|unsupported|deprecated|manual)\b", re.I)
VALID_STATUS = ("proposed", "accepted", "rejected", "deprecated", "superseded")
SECTION_ALIASES = {
    "status": "status",
    "context": "context",
    "context and problem statement": "context",
    "problem statement": "context",
    "options": "options",
    "options considered": "options",
    "considered options": "options",
    "alternatives": "options",
    "alternatives considered": "options",
    "decision": "decision",
    "decision outcome": "decision",
    "consequences": "consequences",
}
REQUIRED = ("status", "context", "options", "decision", "consequences")
FILE_RE = re.compile(r"^(?:adr-)?(\d{3,5})-([a-z0-9][a-z0-9-]*)\.md$")
SKIP_RE = re.compile(r"^(readme|index|template.*|.*-template)\.md$", re.I)
TITLE_RE = re.compile(r"^#\s+(?:ADR[ -]?)?(\d+)\s*[.:\-]?\s*(.*?)\s*$", re.I)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LINK_LINE_RE = re.compile(
    r"^\s*(?:[-*]\s*)?[*_]*(supersedes|superseded[ -]by)[*_]*\s*:[*_]*\s*(.*)$", re.I)
STATUS_LINE_RE = re.compile(r"^\s*(?:[-*]\s*)?[*_]*status[*_]*\s*:[*_]*\s*(.+)$", re.I)
NUM_RE = re.compile(r"(?<![\w.-])(?:ADR[ -]?)?(\d{3,5})(?!\w)", re.I)
EXPLICIT_REF_RE = re.compile(r"\bADR[ -]?(\d{3,5})\b|(?<![\w.-])(\d{3,5})-[a-z0-9][a-z0-9-]*\.md\b", re.I)
PLACEHOLDER_RE = re.compile(
    r"\b(TBD|TODO|FIXME|lorem ipsum)\b|\{\{[^}\n]*\}\}|"
    r"<[^>\n]*(describe|fill in|your |option name|short title)[^>\n]*>", re.I)
URL_RE = re.compile(r"https?://\S+")


def mask(text):
    """Blank HTML comments and fenced code, keeping line numbers stable."""
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    text = re.sub(r"^(```|~~~).*?^(?:```|~~~)[ \t]*$", blank, text, flags=re.S | re.M)
    return text


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def words(lines):
    body = " ".join(lines)
    body = PLACEHOLDER_RE.sub(" ", body)
    return len(re.findall(r"[A-Za-z0-9][\w'-]*", body))


def nums_in(text):
    return [int(m.group(1)) for m in NUM_RE.finditer(URL_RE.sub(" ", text))]


def front_matter(lines):
    """Return (dict, index of first line after the block)."""
    if not lines or lines[0].strip() != "---":
        return {}, 0
    data = {}
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return data, i + 1
        m = re.match(r"^([A-Za-z_-]+)\s*:\s*(.*)$", lines[i])
        if m:
            data[m.group(1).lower().replace("_", "-")] = m.group(2).strip().strip("\"'")
    return {}, 0


def parse(path, name):
    raw = open(path, "rb").read().decode("utf-8", errors="replace").lstrip(chr(0xFEFF))
    lines = mask(raw).split("\n")
    fm, start = front_matter(lines)
    doc = {"name": name, "fm": fm, "title": None, "title_line": 0, "number": None,
           "sections": {}, "section_line": {}, "status": None, "status_line": 0,
           "supersedes": [], "superseded_by": [], "link_problems": [], "refs": [],
           "lines": lines}
    m = FILE_RE.match(name)
    doc["file_number"] = int(m.group(1)) if m else None
    current = None
    for i in range(start, len(lines)):
        line = lines[i]
        h = HEADING_RE.match(line)
        if h and len(h.group(1)) == 1 and doc["title"] is None:
            t = TITLE_RE.match(line)
            doc["title_line"] = i + 1
            if t:
                doc["number"] = int(t.group(1))
                doc["title"] = t.group(2)
            else:
                doc["title"] = ""
            continue
        if h and len(h.group(1)) == 2:
            key = re.sub(r"^\d+[.)]\s*", "", h.group(2)).strip().rstrip(":").lower()
            current = SECTION_ALIASES.get(key)
            if current and current not in doc["sections"]:
                doc["sections"][current] = []
                doc["section_line"][current] = i + 1
            else:
                current = None
            continue
        if current:
            doc["sections"][current].append((i + 1, line))
        lm = LINK_LINE_RE.match(line)
        if lm:
            kind = "supersedes" if lm.group(1).lower() == "supersedes" else "superseded_by"
            value = lm.group(2).strip()
            found = nums_in(value)
            if found:
                doc[kind].extend((n, i + 1) for n in found)
            elif value and not re.match(r"^[*_\s]*(none|n/?a|-|—)[*_\s]*$", value, re.I):
                doc["link_problems"].append((i + 1, value))
            continue
        for rm in EXPLICIT_REF_RE.finditer(URL_RE.sub(" ", line)):
            doc["refs"].append((int(rm.group(1) or rm.group(2)), i + 1))
    for key, kind in (("supersedes", "supersedes"), ("superseded-by", "superseded_by")):
        if fm.get(key):
            doc[kind].extend((n, 1) for n in nums_in(fm[key]))
    # status: front matter, then a "Status:" line, then first line of the section
    status_text, sline = fm.get("status"), 1
    if status_text is None:
        for i in range(start, min(len(lines), start + 25)):
            sm = STATUS_LINE_RE.match(lines[i])
            if sm:
                status_text, sline = sm.group(1), i + 1
                break
    if status_text is None and "status" in doc["sections"]:
        for ln, text in doc["sections"]["status"]:
            if text.strip():
                status_text, sline = text, ln
                break
    if status_text is not None:
        clean = re.sub(r"[*_`]", "", status_text).strip()
        w = re.match(r"([A-Za-z]+)", clean)
        doc["status"] = w.group(1).lower() if w else ""
        doc["status_line"] = sline
        for km in re.finditer(r"(supersedes|superseded[ -]by)\s*:?\s*([^.;]*)", clean, re.I):
            kind = "supersedes" if km.group(1).lower() == "supersedes" else "superseded_by"
            doc[kind].extend((n, sline) for n in nums_in(km.group(2)))
    return doc


def split_options(body):
    """Return list of (name, text_lines) option blocks from the options section."""
    heads = [i for i, (_, t) in enumerate(body) if re.match(r"^###\s+\S", t)]
    blocks = []
    if heads:
        for k, i in enumerate(heads):
            end = heads[k + 1] if k + 1 < len(heads) else len(body)
            blocks.append((re.sub(r"^###\s+", "", body[i][1]).strip(),
                           [t for _, t in body[i:end]]))
        return blocks
    start = None
    for i, (_, t) in enumerate(body):
        if re.match(r"^(?:[-*]|\d+[.)])\s+\S", t):
            if start is not None:
                blocks.append(start)
            start = (t.strip(), [t])
        elif start is not None and t.strip():
            start[1].append(t)
    if start is not None:
        blocks.append(start)
    return blocks


def scan(folder, strict):
    findings = []

    def add(file, line, rule, severity, message):
        findings.append({"file": file, "line": line, "rule": rule,
                         "severity": severity, "message": message})

    names = sorted(n for n in os.listdir(folder)
                   if n.lower().endswith(".md") and os.path.isfile(os.path.join(folder, n))
                   and not SKIP_RE.match(n))
    docs = []
    for n in names:
        if not FILE_RE.match(n):
            add(n, None, "bad-filename", "warning",
                "file name should look like 0007-short-slug.md (3 to 5 digits, lowercase slug)")
            continue
        docs.append(parse(os.path.join(folder, n), n))

    by_number = {}
    for d in docs:
        by_number.setdefault(d["file_number"], []).append(d)
    for num, group in sorted(by_number.items()):
        if len(group) > 1:
            for d in group:
                add(d["name"], None, "duplicate-number", "error",
                    "number %d is used by %s" % (num, ", ".join(g["name"] for g in group)))
    numbers = sorted(by_number)
    if numbers:
        have = set(numbers)
        gaps = [n for n in range(numbers[0], numbers[-1] + 1) if n not in have]
        if gaps:
            add(None, None, "numbering-gap", "warning",
                "missing numbers between %d and %d: %s" % (
                    numbers[0], numbers[-1], ", ".join(str(g) for g in gaps[:20])
                    + (" ..." if len(gaps) > 20 else "")))

    titles = {}
    for d in docs:
        nm = d["name"]
        if not d["title_line"] or not d["title"]:
            add(nm, d["title_line"] or None, "bad-title", "error",
                "first line must be an H1 like '# 0007. Title' or '# ADR-0007: Title'")
        else:
            if d["number"] != d["file_number"]:
                add(nm, d["title_line"], "title-number-mismatch", "error",
                    "title says %s, file name says %d" % (d["number"], d["file_number"]))
            titles.setdefault(norm_title(d["title"]), []).append(d)

        status = d["status"]
        if status is None:
            add(nm, None, "missing-status", "error",
                "no status found (front matter, a 'Status:' line, or a '## Status' section)")
        elif status not in VALID_STATUS:
            add(nm, d["status_line"], "bad-status", "error",
                "status '%s' is not one of %s" % (status, ", ".join(VALID_STATUS)))

        for sec in REQUIRED:
            if sec == "status":
                continue
            if sec not in d["sections"]:
                add(nm, None, "missing-section", "error", "no '## %s' section" % sec.capitalize()
                    if sec != "options" else "no '## Options considered' section")
            elif sec == "consequences" and status in ("accepted", "superseded"):
                continue  # reported as accepted-no-consequences instead
            elif words([t for _, t in d["sections"][sec]]) == 0:
                add(nm, d["section_line"][sec], "empty-section", "error",
                    "'%s' section has no text" % sec)

        if "options" in d["sections"]:
            blocks = split_options(d["sections"]["options"])
            if len(blocks) < 2:
                add(nm, d["section_line"]["options"], "few-options", "error",
                    "%d option listed; a decision needs at least 2 real options" % len(blocks))
            else:
                for name, block in blocks:
                    if not DOWNSIDE_RE.search(" ".join(block)):
                        add(nm, None, "option-no-downside", "warning",
                            "option '%s' states no cost or downside (heuristic)" % name[:60])

        if "consequences" in d["sections"] and status in ("accepted", "superseded"):
            n = words([t for _, t in d["sections"]["consequences"]])
            if 0 < n < MIN_CONSEQUENCE_WORDS:
                add(nm, d["section_line"]["consequences"], "accepted-no-consequences", "error",
                    "%s ADR has only %d words of consequences (minimum %d)" % (status, n, MIN_CONSEQUENCE_WORDS))
            elif n == 0 and "consequences" in d["sections"]:
                add(nm, d["section_line"]["consequences"], "accepted-no-consequences", "error",
                    "%s ADR has an empty consequences section" % status)
        elif "consequences" in d["sections"] and status == "proposed":
            n = words([t for _, t in d["sections"]["consequences"]])
            if 0 < n < MIN_CONSEQUENCE_WORDS:
                add(nm, d["section_line"]["consequences"], "thin-consequences", "warning",
                    "only %d words of consequences; fill before accepting" % n)

        for i, text in enumerate(d["lines"]):
            if PLACEHOLDER_RE.search(text):
                add(nm, i + 1, "placeholder-text", "warning" if status == "proposed" else "error",
                    "template or TODO text left in the record")
                break

        for ln, value in d["link_problems"]:
            add(nm, ln, "unparsable-link", "error",
                "no ADR number found in link value '%s'" % value[:40])

    for key, group in sorted(titles.items()):
        if len(group) > 1:
            for d in group:
                add(d["name"], d["title_line"], "duplicate-title", "warning",
                    "same title as %s" % ", ".join(g["name"] for g in group if g is not d))

    exist = {d["file_number"]: d for d in docs}
    for d in docs:
        nm = d["name"]
        for kind in ("supersedes", "superseded_by"):
            seen = set()
            for num, ln in d[kind]:
                if num in seen:
                    continue
                seen.add(num)
                if num == d["file_number"]:
                    add(nm, ln, "self-reference", "error", "%s points at itself" % kind)
                elif num not in exist:
                    add(nm, ln, "broken-link", "error",
                        "%s %04d, but no such ADR file exists" % (kind.replace("_", " "), num))
                else:
                    other = exist[num]
                    back = "superseded_by" if kind == "supersedes" else "supersedes"
                    if d["file_number"] not in [n for n, _ in other[back]]:
                        add(nm, ln, "missing-backlink", "error",
                            "%s says %s %04d, but %s does not point back" % (
                                nm, kind.replace("_", " "), num, other["name"]))
                    if kind == "superseded_by" and other["status"] not in (None, "accepted", "superseded"):
                        add(nm, ln, "successor-not-accepted", "warning",
                            "superseded by %s whose status is '%s'" % (other["name"], other["status"]))
        if d["status"] == "superseded" and not d["superseded_by"]:
            add(nm, d["status_line"], "superseded-without-successor", "error",
                "status is superseded but no 'Superseded by: NNNN' link")
        if d["superseded_by"] and d["status"] not in (None, "superseded"):
            add(nm, d["superseded_by"][0][1], "successor-status-mismatch", "error",
                "has a Superseded by link but status is '%s'" % d["status"])
        linked = {n for k in ("supersedes", "superseded_by") for n, _ in d[k]}
        for num, ln in d["refs"]:
            if num not in exist and num not in linked:
                add(nm, ln, "broken-link", "error", "reference to ADR %04d, but no such ADR file exists" % num)

    findings.sort(key=lambda f: (f["file"] or "", f["line"] or 0, f["rule"], f["message"]))
    counts = {}
    for f in findings:
        counts[f["rule"]] = counts.get(f["rule"], 0) + 1
    errors = sum(1 for f in findings if f["severity"] == "error")
    warnings = len(findings) - errors
    ok = errors == 0 and not (strict and warnings)
    return {"command": "scan", "dir": folder.replace("\\", "/"), "adr_count": len(docs),
            "numbers": numbers, "findings": findings,
            "counts_by_rule": dict(sorted(counts.items())),
            "errors": errors, "warnings": warnings, "ok": ok}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    strict = "--strict" in argv
    args = [a for a in argv if a != "--strict"]
    if len(args) != 2 or args[0] != "scan":
        print("usage: adr_scan.py scan <adr-folder> [--strict]", file=sys.stderr)
        return 2
    if not os.path.isdir(args[1]):
        print("error: folder not found: %s (pass the folder that holds the ADR files)" % args[1], file=sys.stderr)
        return 2
    report = scan(args[1], strict)
    if report["adr_count"] == 0 and not report["findings"]:
        print("error: no ADR files (NNNN-slug.md) in %s" % args[1], file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
