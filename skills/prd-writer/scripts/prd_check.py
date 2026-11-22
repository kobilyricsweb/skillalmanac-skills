#!/usr/bin/env python3
"""Check a product requirements document (PRD) written in Markdown.

Standard library only. Reads the files it is given, prints a report, writes nothing.

    python prd_check.py PRD [--notes NOTES]

Checks:
  - the required sections exist (Problem, Users, Success metrics, Non-goals,
    Requirements, Open questions, Risks and assumptions);
  - every requirement has an ID (R1, R2 ...), a priority (Must, Should or Could)
    and an acceptance check introduced by "Accept:";
  - requirement lines do not rest on words nobody can test ("fast", "easy" ...);
  - every success metric carries a number, or the marker [needs data];
  - with --notes: every number in the PRD comes from the source notes, or sits
    on a line marked [proposed] or [assumption]. Single digits after "Accept:"
    are treated as test data and not checked.

Exit codes: 0 = no FAIL, 1 = at least one FAIL, 2 = usage or file error.
The script checks form and traceability. It cannot tell whether the product
decision is a good one.
"""
import re
import sys

SECTIONS = {
    "Problem": ("problem",),
    "Users": ("users", "audience", "who it is for", "personas"),
    "Success metrics": ("success metric", "goals", "success measure"),
    "Non-goals": ("non-goal", "non goal", "out of scope", "not in scope"),
    "Requirements": ("requirement",),
    "Open questions": ("open question",),
    "Risks and assumptions": ("risk", "assumption"),
}
# Words a tester cannot verify without a number or a named behaviour.
VAGUE = ("fast", "quick", "quickly", "easy", "easily", "simple", "simply", "intuitive", "user-friendly", "user friendly",
         "seamless", "seamlessly", "robust", "scalable", "flexible", "modern", "efficient", "efficiently", "smooth",
         "as needed", "if possible", "etc", "and so on", "best-in-class", "world-class", "state of the art",
         "appropriate", "reasonable", "minimal", "optimal", "improved", "better")
MARKED = re.compile(r"\[(proposed|assumption|needs data)\b", re.I)   # line-level markers for unconfirmed content
MIN_REQUIREMENTS = 3    # fewer than this is a feature note, not a PRD
MAX_WORDS = 1500        # past this length readers stop reading; split or cut
REQ_ID = re.compile(r"^\s*(?:[-*]\s*|\|\s*)?\**\s*((?:R|FR|NFR)-?\d+)\b")
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


def numbers(text):
    out = set()
    for m in NUM.findall(text):
        n = m.replace(",", "").rstrip(".")
        if "." in n:
            n = n.rstrip("0").rstrip(".")
        out.add(n)
    return out


def split_sections(text):
    out, current = [], None
    for line in text.split("\n"):
        m = re.match(r"^#{1,4}\s+(.*?)\s*#*$", line)
        if m:
            current = [re.sub(r"^\d+[.)]\s*", "", m.group(1)).lower(), []]
            out.append(current)
        elif current:
            current[1].append(line)
    return [(h, "\n".join(b)) for h, b in out]


def main(argv):
    utf8_output()
    notes_path, args, i = None, [], 0
    while i < len(argv):
        if argv[i] == "--notes" and i + 1 < len(argv):
            notes_path = argv[i + 1]
            i += 2
        else:
            args.append(argv[i])
            i += 1
    if len(args) != 1:
        print(__doc__)
        return 2
    prd = read(args[0])
    fails, warns = [], []
    secs = split_sections(prd)

    found = {}
    for name, keys in SECTIONS.items():
        body = next((b for h, b in secs if any(k in h for k in keys)), None)
        if body is None:
            fails.append(f"section '{name}' is missing")
        elif not body.strip():
            fails.append(f"section '{name}' is empty (write 'None known' with a reason if that is the case)")
        found[name] = body or ""

    req_lines = [(n, l) for n, l in enumerate(prd.split("\n"), 1) if REQ_ID.match(l)]
    ids = [REQ_ID.match(l).group(1) for _, l in req_lines]
    if len(req_lines) < MIN_REQUIREMENTS:
        fails.append(f"{len(req_lines)} numbered requirement(s) found; write each as a line starting with an ID such as R1 (need at least {MIN_REQUIREMENTS})")
    for dup in sorted({x for x in ids if ids.count(x) > 1}):
        fails.append(f"requirement ID {dup} is used more than once")
    lines = prd.split("\n")
    for n, l in req_lines:
        rid = REQ_ID.match(l).group(1)
        block = l
        for nxt in lines[n:n + 4]:      # an indented Accept line may follow the requirement
            if REQ_ID.match(nxt) or nxt.startswith("#") or not nxt.strip():
                break
            block += " " + nxt
        if not re.search(r"\b(must|should|could|won't|p0|p1|p2)\b", block, re.I):
            fails.append(f"{rid} (line {n}): no priority (Must, Should or Could)")
        if not re.search(r"\baccept(ance)?\b[^:]{0,20}:", block, re.I):
            fails.append(f"{rid} (line {n}): no acceptance check; add 'Accept: <what a tester does and sees>'")
        low = " " + re.sub(r"[^a-z' -]", " ", block.lower()) + " "
        hits = [w for w in VAGUE if f" {w} " in low]
        if hits and not MARKED.search(block):
            warns.append(f"{rid} (line {n}): untestable word(s) {hits}; replace with a number or a named behaviour")

    metrics = [l for l in found["Success metrics"].split("\n") if re.match(r"^\s*(?:[-*]|\d+[.)]|\|)\s*\S", l) and not re.fullmatch(r"[\s|:-]+", l)]
    if found["Success metrics"].strip() and not metrics:
        fails.append("Success metrics has no list items; write one metric per bullet")
    for l in metrics:
        if l.strip().startswith("|") and re.search(r"\|\s*(metric|measure)\b", l, re.I):
            continue
        if not NUM.search(l) and not re.search(r"\[needs data\b", l, re.I):
            fails.append(f"success metric without a number or [needs data]: '{l.strip()[:70]}'")

    if notes_path:
        allowed = numbers(read(notes_path))
        for n, l in enumerate(lines, 1):
            if MARKED.search(l) or l.startswith("#"):
                continue
            body = REQ_ID.sub("", l)
            # Small example values inside an acceptance check ("save 3 items") are test data, not claims.
            head, sep, tail = body.partition("Accept:")
            body = head + sep + re.sub(r"(?<![\d.,])\d(?![\d%]|[.,]\d)", "", tail)
            body = re.sub(r"\b(?:R|FR|NFR)-?\d+\b", "", body)
            body = re.sub(r"^\s*\d+[.)]\s", "", body)
            body = re.sub(r"\bP[0-2]\b", "", body)
            new = sorted(numbers(body) - allowed)
            if new:
                fails.append(f"line {n}: number(s) {new} are not in the notes; take them from the notes, or mark the line [proposed] or [assumption]")

    n_words = len(re.findall(r"\w+", prd))
    if n_words > MAX_WORDS:
        warns.append(f"{n_words} words; over {MAX_WORDS} is rarely read in full")
    tbd = len(re.findall(r"\bTBD\b|\?\?\?", prd))
    if tbd:
        warns.append(f"{tbd} 'TBD' marker(s); move each to Open questions with an owner")
    if found["Open questions"].strip() and not re.search(r"\?", found["Open questions"]) and not re.search(r"\bnone\b", found["Open questions"], re.I):
        warns.append("Open questions contains no question mark; phrase each item as a question someone can answer")

    print("PRD CHECK")
    for f in fails:
        print("  FAIL  " + f)
    for w in warns:
        print("  WARN  " + w)
    if not fails:
        print(f"  OK    all sections present; {len(req_lines)} requirements with ID, priority and acceptance check" + ("; numbers trace to the notes or are marked" if notes_path else ""))
    print(f"\nRESULT: {'FAIL' if fails else 'PASS'} ({len(fails)} fail, {len(warns)} warn)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
