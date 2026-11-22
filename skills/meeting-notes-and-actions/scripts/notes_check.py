#!/usr/bin/env python3
"""Check meeting notes against the transcript they were written from.

Standard library only. Reads two files, prints a report, writes nothing.

    python notes_check.py TRANSCRIPT NOTES

What it checks in NOTES (Markdown):
  - the sections Decisions, Action items and Open questions exist;
  - the action table has the columns Owner, Action, Due, Source, and every row
    has an owner (a person named in the transcript, or "Unassigned") and a due
    value (a date backed by the transcript, or "No date set");
  - every number, quotation and person name in the notes also appears in the
    transcript.

Exit codes: 0 = no FAIL, 1 = at least one FAIL, 2 = usage or file error.
The checks compare words and numbers. They cannot tell whether a decision was
really made; that needs a read of the transcript.
"""
import re
import sys

REQUIRED_SECTIONS = ("decisions", "action items", "open questions")
ACTION_COLUMNS = ("owner", "action", "due", "source")
UNASSIGNED = ("unassigned", "no owner", "not assigned")
NO_DATE = ("no date set", "no date", "none set", "not set")
MIN_QUOTE_WORDS = 4      # shorter quoted fragments are usually terms, not quotations
# Capitalised words that are not people; never reported as unknown names.
NOT_NAMES = set("""Decisions Decision Action Actions Items Item Open Questions Question Owner Due Source Notes Meeting
Summary Attendees Unassigned No Date Set The A An This That These Those It We They He She I If In On At By For To
From With And Or But Not As Is Are Was Were Will Would Should Could Can May Monday Tuesday Wednesday Thursday Friday
Saturday Sunday January February March April May June July August September October November December Jan Feb Mar
Apr Jun Jul Aug Sep Sept Oct Nov Dec Q1 Q2 Q3 Q4 Discussed Decided Parked Risks Risk Next Steps Step Follow Up
Purpose Outcome Outcomes Context Topic Topics Agenda Yes None TBD Who What When Why How All Each Both After Before
Until Once Send Review Draft Update Confirm Check Prepare Schedule Share Create Write Ask Get Set Add Fix Call Email
Book Finish Complete Investigate Decide Present Report Reported Raised Not Still Pending Corrected Reversed Final
Earlier Later Changed Agreed Proposed Proposal Replaces Replaced Raised Requested Recorded Moved Noted Stated Said
Asked Answered Confirmed Parked Unowned Undated Supersedes Superseded Corrections Correction Check Needs Confirming""".split())
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def utf8_output():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def read(path):
    try:
        raw = open(path, "rb").read()
    except OSError as err:
        print(f"ERROR: cannot read {path}: {err.strerror}. Check the path.")
        sys.exit(2)
    for enc in ("utf-8-sig", "cp1252"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if not text.strip():
        print(f"ERROR: {path} is empty.")
        sys.exit(2)
    return text.replace("\r\n", "\n")


def norm(text):
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip().lower()


def numbers(text):
    out = set()
    for m in NUM.findall(text):
        n = m.replace(",", "").rstrip(".")
        if "." in n:
            n = n.rstrip("0").rstrip(".")
        out.add(n.lstrip("0") or "0")
    return out


def sections(notes):
    """Map lower-case heading text to the body under it."""
    out, current = {}, None
    for line in notes.split("\n"):
        m = re.match(r"^#{1,4}\s+(.*?)\s*#*$", line) or re.match(r"^\*\*(.+?)\*\*:?\s*$", line)
        if m:
            current = m.group(1).strip().strip(":").lower()
            out[current] = []
        elif current is not None:
            out[current].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def find_section(secs, name):
    for key, body in secs.items():
        if key.startswith(name) or name in key:
            return body
    return None


def table_rows(body):
    rows = []
    for line in body.split("\n"):
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c) and any(cells):
                continue
            rows.append(cells)
    return rows


def main(argv):
    utf8_output()
    if len(argv) != 2:
        print(__doc__)
        return 2
    transcript, notes = read(argv[0]), read(argv[1])
    t_norm, t_nums = norm(transcript), numbers(transcript)
    t_words = set(re.findall(r"[a-z][a-z'-]+", t_norm))
    fails, warns = [], []

    secs = sections(notes)
    for name in REQUIRED_SECTIONS:
        if find_section(secs, name) is None:
            fails.append(f"section '{name.title()}' is missing (use it as a heading; write 'None' under it if empty)")

    due_cells = []
    actions = find_section(secs, "action items")
    if actions is not None:
        rows = table_rows(actions)
        if not rows:
            if not re.search(r"\bnone\b", actions, re.I):
                fails.append("Action items has no table (columns: Owner | Action | Due | Source)")
        else:
            header = [c.lower() for c in rows[0]]
            missing = [c for c in ACTION_COLUMNS if not any(h.startswith(c) for h in header)]
            if missing:
                fails.append("action table lacks column(s): " + ", ".join(missing))
            else:
                idx = {c: next(i for i, h in enumerate(header) if h.startswith(c)) for c in ACTION_COLUMNS}
                for n, row in enumerate(rows[1:], 1):
                    row = row + [""] * (len(header) - len(row))
                    owner, action, due = row[idx["owner"]], row[idx["action"]], row[idx["due"]]
                    due_cells.append(due)
                    if not owner:
                        fails.append(f"action {n}: no owner (write 'Unassigned' if nobody took it)")
                    elif owner.lower() not in UNASSIGNED:
                        for person in re.split(r"\s*(?:,|/|&|\band\b)\s*", owner):
                            first = re.sub(r"[^A-Za-z' -]", "", person).strip().split(" ")[0].lower()
                            if first and first not in t_words:
                                fails.append(f"action {n}: owner '{person}' does not appear in the transcript")
                    if len(action.split()) < 3:
                        warns.append(f"action {n}: '{action}' is too short to act on (verb + object + enough detail)")
                    if not due:
                        fails.append(f"action {n}: Due is empty (write 'No date set' if no date was said)")
                    elif due.lower() not in NO_DATE:
                        quoted = re.findall(r'"([^"]+)"', due.replace("“", '"').replace("”", '"'))
                        if quoted:
                            for q in quoted:
                                if norm(q) not in t_norm:
                                    fails.append(f"action {n}: due phrase \"{q}\" is not in the transcript")
                        elif not (numbers(due) and numbers(due) <= t_nums) and norm(due) not in t_norm:
                            fails.append(f"action {n}: due '{due}' cannot be traced; give the date as said, or a computed date followed by the spoken phrase in double quotes")
                    if not row[idx["source"]]:
                        warns.append(f"action {n}: Source is empty (speaker and time or line)")

    body_for_numbers = notes
    for cell in due_cells:
        if cell:        # replacing an empty string would insert a space between every character
            body_for_numbers = body_for_numbers.replace(cell, " ")
    title_line = notes.split("\n", 1)[0] if notes.lstrip().startswith("#") else ""
    for n in sorted(numbers(body_for_numbers.replace(title_line, " ")) - t_nums, key=lambda s: (len(s), s)):
        if len(n) == 1 and re.search(rf"(^|\n)\s*{n}[.)]\s", notes):
            continue  # list numbering
        fails.append(f"NEW NUMBER '{n}' is in the notes but not in the transcript")

    plain = notes.replace("“", '"').replace("”", '"')
    for q in re.findall(r'"([^"\n]+)"', plain):
        if len(q.split()) >= MIN_QUOTE_WORDS and norm(q).rstrip(".,!?") not in t_norm:
            fails.append(f"quotation not found word for word in the transcript: \"{q[:70]}\"")

    seen = set()
    for line in notes.split("\n"):
        if line.startswith("#"):
            continue
        toks = re.findall(r"[A-Za-z][A-Za-z'-]*", line)
        for i, tok in enumerate(toks):
            if tok[0].isupper() and tok[1:].islower() and len(tok) > 2 and tok not in NOT_NAMES and i > 0:
                if tok.lower() not in t_words and tok not in seen:
                    seen.add(tok)
                    warns.append(f"capitalised word '{tok}' is not in the transcript (a new name? check it)")

    print("MEETING NOTES CHECK")
    for f in fails:
        print("  FAIL  " + f)
    for w in warns:
        print("  WARN  " + w)
    if not fails:
        print("  OK    structure complete; owners, dates, numbers and quotations trace to the transcript")
    print(f"\nRESULT: {'FAIL' if fails else 'PASS'} ({len(fails)} fail, {len(warns)} warn)")
    print("Not checked by this script: whether each decision was really agreed, and whether an action was missed. Read the transcript end to end for those.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
