#!/usr/bin/env python3
"""Validate a finished research report and its source log.

    python validate_research.py REPORT.md SOURCES.md [--today YYYY-MM-DD]
                                [--reply REPLY.txt --max-words N]

With --reply and --max-words the script also counts the words of the chat
reply file and reports an error if it exceeds N (user word limits are hard).

Reads the two files; writes nothing; no network. Prints one JSON object to
stdout. Exit codes: 0 no errors (warnings allowed), 1 at least one error,
2 usage problem (missing, unreadable or empty file).

Formats are defined in references/templates.md. In short:
  SOURCES.md  a table with columns  id | title | url | accessed | quote
  REPORT.md   sections  Question, Summary, Findings, Claim table,
              Contradictions, Gaps; the claim table has columns
              claim_id | claim | source_ids | quote | confidence;
              paragraphs under Summary and Findings cite claims as [C1] or [C1, C2].
"""
import datetime
import json
import re
import sys

# Confidence is a probability-like score; values outside this range are errors.
CONF_MIN, CONF_MAX = 0.0, 1.0
# A lone source rarely justifies near-certainty; warn above this value.
SINGLE_SOURCE_CONF_WARN = 0.8
# Logged quotes are evidence snippets, not copied passages; warn above this.
LONG_QUOTE_CHARS = 300
REQUIRED_SECTIONS = ["question", "summary", "findings", "claim table", "contradictions", "gaps"]
CITED_SECTIONS = ("summary", "findings")

SOURCE_ID = re.compile(r"^S\d+$")
CLAIM_ID = re.compile(r"^C\d+$")
CITATION = re.compile(r"\[\s*(C\d+(?:\s*[,;]\s*C\d+)*)\s*\]")
URL = re.compile(r"^https?://[^\s/$.?#][^\s]*$", re.I)
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def error(self, code, where, message):
        self.errors.append({"code": code, "where": where, "message": message})

    def warn(self, code, where, message):
        self.warnings.append({"code": code, "where": where, "message": message})


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        sys.stderr.write(f"cannot read {path}: {exc}\n")
        sys.exit(2)
    if not text.strip():
        sys.stderr.write(f"{path} is empty; write the file first\n")
        sys.exit(2)
    return text


def split_row(line):
    """Split a Markdown table row on unescaped pipes."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    cells = re.split(r"(?<!\\)\|", line)
    return [c.replace("\\|", "|").strip() for c in cells]


def is_separator(cells):
    return all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c != "") and any(cells)


def find_tables(lines):
    """Return list of (header_cells_lowercase, rows, first_line_no) for each table."""
    tables, i = [], 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and lines[i + 1].lstrip().startswith("|"):
            header = [c.lower() for c in split_row(lines[i])]
            if is_separator(split_row(lines[i + 1])):
                rows, j = [], i + 2
                while j < len(lines) and lines[j].lstrip().startswith("|"):
                    rows.append((j + 1, split_row(lines[j])))
                    j += 1
                tables.append((header, rows, i + 1))
                i = j
                continue
        i += 1
    return tables


def table_with(tables, required):
    for header, rows, line_no in tables:
        if all(col in header for col in required):
            return header, rows, line_no
    return None


def norm(text):
    """Lowercase, unify quotes and dashes, collapse whitespace for quote matching."""
    text = text.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-").replace("…", "...")
    text = text.strip().strip('"\'').strip()
    return re.sub(r"\s+", " ", text).lower()


def cell(header, row, name):
    idx = header.index(name)
    return row[idx] if idx < len(row) else ""


def parse_sources(text, rep, today):
    tables = find_tables(text.splitlines())
    found = table_with(tables, ["id", "url", "accessed", "quote"])
    sources = {}
    if not found:
        rep.error("sources_table_missing", "SOURCES", "no table with columns id | url | accessed | quote")
        return sources
    header, rows, _ = found
    for line_no, row in rows:
        where = f"SOURCES line {line_no}"
        sid = cell(header, row, "id")
        if not SOURCE_ID.match(sid):
            rep.error("source_id_invalid", where, f"id '{sid}' must look like S1, S2, ...")
            continue
        if sid in sources:
            rep.error("source_id_duplicate", where, f"id {sid} appears more than once")
            continue
        url = cell(header, row, "url")
        if not URL.match(url):
            rep.error("source_url_invalid", where, f"{sid}: url '{url}' is not an http(s) URL")
        accessed = cell(header, row, "accessed")
        if not DATE.match(accessed):
            rep.error("source_date_invalid", where, f"{sid}: accessed '{accessed}' must be YYYY-MM-DD")
        else:
            try:
                parsed = datetime.date.fromisoformat(accessed)
                if parsed > today:
                    rep.error("source_date_future", where, f"{sid}: accessed {accessed} is after {today}")
            except ValueError:
                rep.error("source_date_invalid", where, f"{sid}: accessed '{accessed}' is not a real date")
        quote = cell(header, row, "quote")
        if not quote.strip(' "\''):
            rep.error("source_quote_missing", where, f"{sid}: no quote logged; copy the passage you relied on")
        elif len(quote) > LONG_QUOTE_CHARS:
            rep.warn("source_quote_long", where, f"{sid}: quote is {len(quote)} chars; keep to the sentence needed")
        sources[sid] = norm(quote)
    if not sources:
        rep.error("sources_empty", "SOURCES", "the source table has no valid rows")
    return sources


def parse_sections(lines):
    """Map each line index to the lower-case level-2 section name it sits in."""
    current, names, order = None, [], []
    for line in lines:
        m = re.match(r"^##\s+(.+?)\s*#*\s*$", line)
        if m and not line.startswith("###"):
            current = m.group(1).strip().lower()
            order.append(current)
        names.append(current)
    return names, order


def paragraphs(lines, names, section_names):
    """Yield (first_line_no, text) for prose blocks and list items in the chosen sections."""
    block, start, in_code = [], 0, False

    def flush():
        nonlocal block
        if block:
            yield_list.append((start, " ".join(block)))
        block = []

    yield_list = []
    for idx, line in enumerate(lines):
        if line.strip().startswith("```"):
            flush()
            in_code = not in_code
            continue
        if in_code or names[idx] not in section_names:
            flush()
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("|") or stripped.startswith(">") \
                or re.fullmatch(r"[-*_]{3,}", stripped):
            flush()
            continue
        if LIST_ITEM.match(line):
            flush()
            start = idx + 1
            block = [stripped]
        else:
            if not block:
                start = idx + 1
            block.append(stripped)
    flush()
    return yield_list


def main(argv):
    args, today = [], datetime.date.today()
    reply, max_words = None, None
    it = iter(argv)
    for arg in it:
        if arg == "--today":
            try:
                today = datetime.date.fromisoformat(next(it))
            except (StopIteration, ValueError):
                sys.stderr.write("--today needs a date like 2026-11-21\n")
                return 2
        elif arg == "--reply":
            reply = next(it, None)
        elif arg == "--max-words":
            try:
                max_words = int(next(it))
            except (StopIteration, ValueError):
                sys.stderr.write("--max-words needs an integer"+chr(92)+"n")
                return 2
        else:
            args.append(arg)
    if len(args) != 2 or (reply is None) != (max_words is None):
        sys.stderr.write("usage: validate_research.py REPORT.md SOURCES.md [--today YYYY-MM-DD]\n")
        return 2
    report_text, sources_text = read_text(args[0]), read_text(args[1])
    rep = Report()
    sources = parse_sources(sources_text, rep, today)

    lines = report_text.splitlines()
    names, order = parse_sections(lines)
    for section in REQUIRED_SECTIONS:
        if section not in order:
            rep.error("section_missing", "REPORT", f"missing section '## {section.title()}'")

    tables = find_tables(lines)
    claims, used_sources = {}, set()
    found = table_with(tables, ["claim_id", "claim", "source_ids", "quote", "confidence"])
    if not found:
        rep.error("claim_table_missing", "REPORT", "no table with columns claim_id | claim | source_ids | quote | confidence")
    else:
        header, rows, _ = found
        for line_no, row in rows:
            where = f"REPORT line {line_no}"
            cid = cell(header, row, "claim_id")
            if not CLAIM_ID.match(cid):
                rep.error("claim_id_invalid", where, f"claim_id '{cid}' must look like C1, C2, ...")
                continue
            if cid in claims:
                rep.error("claim_id_duplicate", where, f"{cid} appears more than once")
                continue
            claims[cid] = {"sources": []}
            if not cell(header, row, "claim").strip():
                rep.error("claim_text_missing", where, f"{cid}: claim text is empty")
            ids = [s for s in re.split(r"[\s,;]+", cell(header, row, "source_ids")) if s]
            if not ids:
                rep.error("claim_no_source", where, f"{cid}: no source id; add one or delete the claim")
            for sid in ids:
                if sid not in sources:
                    rep.error("claim_unknown_source", where, f"{cid}: source {sid} is not in the source log")
                else:
                    used_sources.add(sid)
                    claims[cid]["sources"].append(sid)
            quote = cell(header, row, "quote")
            nq = norm(quote)
            if not nq:
                rep.error("claim_quote_missing", where, f"{cid}: no supporting quote")
            elif claims[cid]["sources"] and not any(nq in sources[s] for s in claims[cid]["sources"]):
                rep.error("claim_quote_not_in_source", where,
                          f"{cid}: quote does not appear in the logged quote of {', '.join(claims[cid]['sources'])}")
            conf_raw = cell(header, row, "confidence")
            try:
                conf = float(conf_raw)
                if not (CONF_MIN <= conf <= CONF_MAX) or conf != conf:
                    raise ValueError
                if len(set(ids)) == 1 and conf > SINGLE_SOURCE_CONF_WARN:
                    rep.warn("single_source_high_confidence", where,
                             f"{cid}: confidence {conf} above {SINGLE_SOURCE_CONF_WARN} with one source")
            except ValueError:
                rep.error("confidence_out_of_range", where,
                          f"{cid}: confidence '{conf_raw}' must be a number from {CONF_MIN} to {CONF_MAX}")
        if not claims:
            rep.error("claim_table_empty", "REPORT", "the claim table has no valid rows")

    for sid in sorted(sources, key=lambda s: int(s[1:])):
        if sid not in used_sources:
            rep.error("source_unused", "SOURCES", f"{sid} is logged but no claim uses it; cite it or remove it")

    cited = set()
    for line_no, text in paragraphs(lines, names, CITED_SECTIONS):
        refs = CITATION.findall(text)
        if not refs:
            rep.error("paragraph_uncited", f"REPORT line {line_no}", "paragraph has no [C#] citation: " + text[:60])
        for group in refs:
            for cid in re.split(r"[,;\s]+", group):
                if cid in claims:
                    cited.add(cid)
                else:
                    rep.error("citation_unknown_claim", f"REPORT line {line_no}", f"{cid} is not in the claim table")
    for cid in claims:
        if cid not in cited:
            rep.warn("claim_not_cited_in_text", "REPORT", f"{cid} is in the claim table but no paragraph cites it")

    contra = table_with(tables, ["topic", "claim_ids", "resolution"])
    contradictions = 0
    if contra:
        header, rows, _ = contra
        for line_no, row in rows:
            contradictions += 1
            where = f"REPORT line {line_no}"
            ids = [c for c in re.split(r"[\s,;]+", cell(header, row, "claim_ids")) if c]
            if len(ids) < 2:
                rep.error("contradiction_needs_two_claims", where, "list at least two claim ids that conflict")
            for cid in ids:
                if cid not in claims:
                    rep.error("contradiction_unknown_claim", where, f"{cid} is not in the claim table")
            if not cell(header, row, "resolution").strip():
                rep.error("contradiction_no_resolution", where, "state how it was resolved, or write 'unresolved'")

    reply_words = None
    if reply is not None:
        reply_words = len(read_text(reply).split())
        if reply_words > max_words:
            rep.error("reply_too_long", "REPLY", f"{reply_words} words; the limit is {max_words}; cut {reply_words - max_words}")

    out = {
        "ok": not rep.errors,
        "counts": {"sources": len(sources), "claims": len(claims), "contradictions": contradictions,
                   "errors": len(rep.errors), "warnings": len(rep.warnings),
                   "reply_words": reply_words},
        "errors": rep.errors,
        "warnings": rep.warnings,
    }
    sys.stdout.write(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main(sys.argv[1:]))
