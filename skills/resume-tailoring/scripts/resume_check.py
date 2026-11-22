#!/usr/bin/env python3
"""Check a tailored resume against the original resume and a job posting.

Standard library only. Reads the files it is given, prints a report, writes nothing.

    python resume_check.py match RESUME JOB
        Lists the job posting's terms and whether the resume contains each one.

    python resume_check.py compare ORIGINAL TAILORED [--job JOB] [--confirmed FILE]
        Flags anything in TAILORED that is not backed by ORIGINAL (or by FILE, a
        plain-text list of facts the candidate confirmed in conversation):
        new numbers, new named tools or skills, terms copied from the job posting.
        Also checks the layout rules that keep a resume readable by parsers.

Exit codes: 0 = no FAIL, 1 = at least one FAIL (an unbacked fact), 2 = usage or file error.
The checks compare words and numbers. They cannot judge whether a sentence is true.
"""
import re
import sys

# Words that carry no hiring signal; never reported as job terms.
STOP = set("""a about above across after all also an and any are as at be been being both but by can could
day days do does each etc for from full get had has have he her high how i if in into is it its job join
just know like looking make may more most must my need new no not of on one or other our out over own per
plus role she should so some such than that the their them then there these they this those through time
to up us use using very was we well were what when where which while who will with within work working
would year years you your ability able including include includes strong excellent experience experienced
required requirements preferred responsibilities responsible qualifications candidate ideal team teams
company position apply application applicants equal opportunity employer benefits salary""".split())
MIN_REPEAT = 2          # a lower-case term must appear this often in the posting to count as a term
MAX_TERMS = 45          # enough to cover a posting without burying the report
MAX_WORDS = 900         # about two pages; longer resumes are flagged, not failed
MAX_BULLET_WORDS = 35   # a bullet longer than this reads as a paragraph
SECTION_WORDS = {
    "experience": ("experience", "employment", "work history"),
    "education": ("education",),
    "skills": ("skills", "technical skills", "core competencies"),
}
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
        print(f"ERROR: {path} is empty. Save the text into the file first.")
        sys.exit(2)
    return text.replace("\r\n", "\n")


def stem(word):
    """Very light stemming so 'managed', 'managing' and 'manages' match."""
    w = word.lower()
    for suffix in ("ments", "ment", "ings", "ing", "ions", "ion", "ers", "er", "ed", "es", "s"):
        if w.endswith(suffix) and len(w) - len(suffix) >= 4:
            return w[: -len(suffix)]
    return w


def words(text):
    return re.findall(r"[A-Za-z][A-Za-z0-9+#./&-]*[A-Za-z0-9+#]|[A-Za-z]", text)


def numbers(text):
    out = set()
    for m in NUM.findall(text):
        n = m.replace(",", "").rstrip(".")
        if "." in n:
            n = n.rstrip("0").rstrip(".")
        out.add(n)
    return out


def hard_terms(text):
    """Named things: tools, certifications, acronyms. Capitalised or symbol-bearing
    tokens that are not simply the first word of a sentence or bullet."""
    found = {}
    for line in text.split("\n"):
        line = re.sub(r"^[\s>*#\-•\d.)]+", "", line)
        toks = words(line)
        for i, tok in enumerate(toks):
            acronym = len(tok) >= 2 and tok.isupper()
            symbol = bool(re.search(r"[+#]|\d", tok)) and len(tok) >= 2
            capital = tok[0].isupper() and i > 0 and not toks[i - 1].endswith((".", ":"))
            if (acronym or symbol or capital) and tok.lower() not in STOP:
                found.setdefault(tok.lower(), tok)
    return found


def job_terms(job):
    """Terms worth matching: named things, plus ordinary words and two-word
    phrases the posting repeats."""
    hard = hard_terms(job)
    toks = [w.lower() for w in words(job)]
    counts = {}
    for i, w in enumerate(toks):
        if w not in STOP and len(w) > 2:
            counts[stem(w)] = counts.get(stem(w), 0) + 1
    soft = [w for w, c in sorted(counts.items(), key=lambda kv: -kv[1]) if c >= MIN_REPEAT and w not in {stem(h) for h in hard}]
    return hard, soft[: max(0, MAX_TERMS - len(hard))]


def stems_of(text):
    return {stem(w) for w in words(text)}


def has_term(term, text_lower, text_stems):
    if re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text_lower):
        return True
    return stem(term) in text_stems


def cmd_match(resume_path, job_path):
    resume, job = read(resume_path), read(job_path)
    hard, soft = job_terms(job)
    low, stems = resume.lower(), stems_of(resume)
    have_h = sorted(v for k, v in hard.items() if has_term(k, low, stems))
    miss_h = sorted(v for k, v in hard.items() if not has_term(k, low, stems))
    have_s = [t for t in soft if t in stems]
    miss_s = [t for t in soft if t not in stems]
    total = len(hard) + len(soft)
    print("JOB TERM COVERAGE")
    print(f"  {len(have_h) + len(have_s)} of {total} posting terms appear in the resume")
    print(f"  Named tools, skills, credentials found   : {', '.join(have_h) or '-'}")
    print(f"  Named tools, skills, credentials MISSING : {', '.join(miss_h) or '-'}")
    print(f"  Repeated posting words found             : {', '.join(have_s) or '-'}")
    print(f"  Repeated posting words missing           : {', '.join(miss_s) or '-'}")
    print("\nA missing term is a question for the candidate, not something to add.")
    print("Word stems are compared, so 'managed' matches 'management'. Some terms are company names or noise; ignore those.")
    return 0


def layout_findings(text):
    warn = []
    lines = text.split("\n")
    table_lines = [l for l in lines if l.strip().startswith("|") or re.fullmatch(r"[\s|:-]{5,}", l)]
    if len(table_lines) >= 2:   # a contact line with | separators is not a table
        warn.append("table found (lines with | columns); parsers often scramble tables - use plain lines")
    if any("\t" in line.strip() for line in lines):
        warn.append("tab characters inside lines suggest a multi-column layout; use one column")
    if re.search(r"!\[[^\]]*\]\(", text) or re.search(r"<img\b", text, re.I):
        warn.append("image found; text inside images is not read")
    heads = " \n".join(l.strip("#* :\t").lower() for l in lines if l.strip() and (l.startswith("#") or l.strip().isupper() or re.match(r"^\*\*[^*]+\*\*$", l.strip())))
    for name, variants in SECTION_WORDS.items():
        if not any(v in heads for v in variants):
            warn.append(f"no standard '{name}' heading found (use a plain heading such as '{variants[0].title()}')")
    if not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text):
        warn.append("no email address found in the resume")
    if re.search(r"\b(I|my|me)\b", re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "", text)):
        warn.append("first-person pronoun (I, my, me) found; resume bullets normally drop them")
    n_words = len(words(text))
    if n_words > MAX_WORDS:
        warn.append(f"{n_words} words; over about {MAX_WORDS} usually means more than two pages")
    for l in lines:
        if re.match(r"^\s*[-*•]\s", l) and len(words(l)) > MAX_BULLET_WORDS:
            warn.append(f"bullet longer than {MAX_BULLET_WORDS} words: '{l.strip()[:60]}...'")
    return warn


def cmd_compare(orig_path, new_path, job_path, confirmed_path):
    orig, new = read(orig_path), read(new_path)
    backing = orig + ("\n" + read(confirmed_path) if confirmed_path else "")
    fails, warns = [], []

    new_nums = sorted(numbers(new) - numbers(backing), key=lambda s: (len(s), s))
    for n in new_nums:
        fails.append(f"NEW NUMBER '{n}' is not in the original resume or the confirmed facts")
    lost_years = sorted(y for y in numbers(orig) - numbers(new) if re.fullmatch(r"(19|20)\d\d", y))
    if lost_years:
        warns.append("years in the original that are gone: " + ", ".join(lost_years) + " (a dropped job or date; tell the candidate)")

    back_low, back_stems = backing.lower(), stems_of(backing)
    new_low, new_stems = new.lower(), stems_of(new)
    job_hard, job_soft = job_terms(read(job_path)) if job_path else ({}, [])
    for key, shown in sorted(hard_terms(new).items()):
        if has_term(key, back_low, back_stems):
            continue
        if key in job_hard:
            fails.append(f"ADDED FROM JOB POSTING '{shown}': named in the posting, not in the original resume")
        else:
            warns.append(f"new capitalised term '{shown}' (check it is a real fact from the candidate, or a heading)")
    copied = [t for t in job_soft if t in new_stems and t not in back_stems]
    if copied:
        warns.append("posting words now used that the original did not use: " + ", ".join(copied) + " (fine as wording; not fine as a new claim)")

    warns.extend(layout_findings(new))
    print("RESUME FACT CHECK")
    for f in fails:
        print("  FAIL  " + f)
    for w in warns:
        print("  WARN  " + w)
    if not fails:
        print("  OK    no new numbers and no named skills beyond the original" + (" and the confirmed facts" if confirmed_path else ""))
    print(f"\nRESULT: {'FAIL' if fails else 'PASS'} ({len(fails)} fail, {len(warns)} warn)")
    if fails:
        print("Fix: remove each FAIL item, or ask the candidate; if they confirm it, add their answer to the confirmed-facts file and re-run.")
    return 1 if fails else 0


def main(argv):
    utf8_output()
    opts = {"--job": None, "--confirmed": None}
    args, i = [], 0
    while i < len(argv):
        if argv[i] in opts and i + 1 < len(argv):
            opts[argv[i]] = argv[i + 1]
            i += 2
        else:
            args.append(argv[i])
            i += 1
    if len(args) == 3 and args[0] == "match":
        return cmd_match(args[1], args[2])
    if len(args) == 3 and args[0] == "compare":
        return cmd_compare(args[1], args[2], opts["--job"], opts["--confirmed"])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
