#!/usr/bin/env python3
"""Score a list of candidate brand names and print a ranked shortlist as strict JSON.

Usage:
    python score_names.py CANDIDATES [--competitors FILE] [--avoid FILE]
                          [--suffix .com] [--top 5] [--max-per-type 2]

CANDIDATES is a UTF-8 text file with one name per line (optional "name | type" where
type is descriptive, invented, compound, metaphor or acronym; "#" starts a comment)
or a JSON list of strings or {"name": ..., "type": ...} objects.
--competitors and --avoid are text files with one entry per line. --suffix may be
repeated (default ".com") and is only used to build domain-style slugs and to test
how the name reads when joined to the suffix.

Reads: only the files named on the command line. Writes: JSON on stdout. No network,
no subprocess, nothing is modified.
Exit codes: 0 shortlist complete; 1 fewer survivors than --top; 2 input problem.

It never checks whether a domain, handle or trademark is available. Every figure is a
heuristic for English-looking names.
"""
import argparse
import json
import re
import sys
import unicodedata

# Preferred length band in letters. 5 to 10 is easy to type and remember; the penalties
# below grow with distance from that band.
LEN_OK = (5, 10)
LEN_PENALTY = {1: 30, 2: 25, 3: 15, 4: 5, 11: 8, 12: 8, 13: 18, 14: 18, 15: 18}
LEN_FAR_PENALTY = 30  # 16 letters or more
SYLLABLE_PENALTY = {1: 5, 2: 0, 3: 0, 4: 8}  # 5 or more: SYLLABLE_FAR_PENALTY
SYLLABLE_FAR_PENALTY = 20
# Three-consonant runs that English readers handle without effort; other triples cost more.
COMMON_TRIPLES = {"str", "spr", "spl", "scr", "shr", "thr", "chr", "sch", "tch", "nth",
                  "rst", "nds", "nts", "lds", "rds", "rch", "rsh", "ght", "ngs", "nks",
                  "mps", "lst", "rts", "ngl", "ndr", "ntr", "mbl", "mbr"}
TRIPLE_PENALTY, TRIPLE_COMMON_PENALTY = 8, 3
QUAD_PENALTY, QUINT_PENALTY = 15, 25
VOWEL_RUN3_PENALTY, VOWEL_RUN4_PENALTY = 5, 10
AMBIG_PENALTY, AMBIG_CAP = 4, 16
DOUBLE_PENALTY, DOUBLE_CAP = 3, 6
NO_VOWEL_PENALTY = 30
Q_NO_U_PENALTY = 8
DIGIT_PENALTY, HYPHEN_PENALTY, NON_ASCII_PENALTY, MULTIWORD_PENALTY = 15, 10, 8, 3
# Competitor similarity: edit distance of 2 is the brief's limit; for names of 5 letters or
# fewer a distance of 2 matches unrelated words, so the limit drops to 1.
NEAR_LONG, NEAR_SHORT, NEAR_SHORT_MAX_LEN = 2, 1, 5
COMP_NEAR_PENALTY, COMP_SUBSTR_PENALTY, DUP_PENALTY = 25, 20, 5
SUBSTR_MIN_LEN = 4  # shorter strings are inside too many unrelated words
BUNDLED_4_PENALTY, BUNDLED_3_PENALTY = 15, 8
JOIN_PENALTY = 6
KEEP_MIN, REVIEW_MIN = 75, 50

TYPES = ("descriptive", "invented", "compound", "metaphor", "acronym")
VOWELS = set("aeiou")

# Short, deliberately incomplete list of vulgar or hateful strings. NOT EXHAUSTIVE: it
# misses other languages, slang, leetspeak and anything that is only unfortunate in
# context. Use --avoid for the audience's own languages.
BUNDLED_AVOID = ("shit", "fuck", "cunt", "dick", "cock", "tits", "porn", "rape", "nazi",
                 "slut", "whore", "bitch", "piss", "fart", "anal", "anus", "sex", "ass",
                 "cum", "poo", "kkk")

NOT_CHECKED = [
    "Domain, social handle, app-store and trademark availability (no network, no registry access)",
    "Meaning, slang and sound-alikes in other languages unless supplied with --avoid",
    "Whether the name is distinctive or protectable as a mark",
    "Search results for the name: what already ranks, and for what",
]
TO_VERIFY = [
    "Domain: look up {domains} at a registrar and read the whois result yourself",
    "Social handles on the platforms the project will use",
    "Trademark: search the registers of the countries and classes where you will trade; for anything beyond a hobby, ask a trademark professional",
    "Search the name alone and with the category word; read the first two pages",
    "Say it aloud to three people, then ask them to type it",
    "Ask a native speaker of each target language what it means or sounds like",
]


def fold(text):
    """Lowercase ASCII letters only, accents stripped."""
    base = unicodedata.normalize("NFKD", text)
    return "".join(c for c in base.lower() if "a" <= c <= "z")


def is_vowel(core, i):
    c = core[i]
    if c in VOWELS:
        return True
    if c == "y":
        return not (i == 0 and len(core) > 1 and core[1] in VOWELS)
    return False


def syllables(core):
    """Vowel-group count with a silent trailing 'e' removed. Rough for invented words."""
    groups, prev = 0, False
    for i in range(len(core)):
        v = is_vowel(core, i)
        if v and not prev:
            groups += 1
        prev = v
    if len(core) > 2 and core.endswith("e") and not is_vowel(core, len(core) - 2) \
            and not core.endswith(("le", "ee")) and groups > 1:
        groups -= 1
    return max(groups, 1)


def runs(core, want_vowel):
    out, cur = [], ""
    for i, c in enumerate(core):
        if is_vowel(core, i) == want_vowel:
            cur += c
        else:
            if cur:
                out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out


def levenshtein(a, b):
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def near_limit(a, b):
    return NEAR_SHORT if min(len(a), len(b)) <= NEAR_SHORT_MAX_LEN else NEAR_LONG


def ambiguity(core):
    found = []
    checks = [
        ("ph", "ph or f", lambda s: "ph" in s),
        ("gh", "gh may be silent or sound like f", lambda s: "gh" in s),
        ("ck", "ck or k", lambda s: "ck" in s),
        ("c_k", "hard c may be typed as k", lambda s: re.search(r"c(?![ehiy])", s) is not None),
        ("c_s", "soft c (ce, ci, cy) may be typed as s", lambda s: re.search(r"c[eiy]", s) is not None),
        ("ough", "ough has many pronunciations", lambda s: "ough" in s),
        ("silent_start", "silent first letters (kn, wr, ps, gn)", lambda s: s.startswith(("kn", "wr", "ps", "gn"))),
        ("ie_ei", "ie or ei order is easy to swap", lambda s: "ie" in s or "ei" in s),
    ]
    for code, detail, test in checks:
        if test(core):
            found.append((code, detail))
    return found


def parse_candidates(path):
    try:
        raw = open(path, encoding="utf-8-sig").read()
    except OSError as exc:
        raise ValueError(f"cannot read candidates file {path}: {exc}")
    if not raw.strip():
        raise ValueError(f"candidates file {path} is empty")
    items = []
    if raw.lstrip().startswith("["):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"candidates file is not valid JSON: {exc}")
        for entry in data:
            if isinstance(entry, str):
                items.append((entry.strip(), None))
            elif isinstance(entry, dict) and isinstance(entry.get("name"), str):
                items.append((entry["name"].strip(), entry.get("type")))
            else:
                raise ValueError("JSON candidates must be strings or objects with a 'name' string")
    else:
        for line in raw.splitlines():
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            if "|" in line:
                name, typ = [p.strip() for p in line.split("|", 1)]
                items.append((name, typ or None))
            else:
                items.append((line, None))
    items = [(n, t.lower() if isinstance(t, str) else None) for n, t in items if n]
    if not items:
        raise ValueError("no candidate names found")
    for n, t in items:
        if t is not None and t not in TYPES:
            raise ValueError(f"unknown type '{t}' for '{n}'; use one of {', '.join(TYPES)}")
    return items


def read_wordlist(path, label):
    if not path:
        return []
    try:
        lines = open(path, encoding="utf-8-sig").read().splitlines()
    except OSError as exc:
        raise ValueError(f"cannot read {label} file {path}: {exc}")
    return [l.split("#", 1)[0].strip() for l in lines if l.split("#", 1)[0].strip()]


def flag(code, severity, detail, penalty=0):
    return {"code": code, "severity": severity, "detail": detail, "penalty": penalty}


def bundled_hits(core, junction):
    """Return (word, where) for bundled strings.

    junction None: look inside the name itself (3-letter strings only at the start or end).
    junction set: look only for strings that straddle the dot between name and suffix.
    """
    hits = []
    for w in BUNDLED_AVOID:
        start = core.find(w)
        while start != -1:
            end = start + len(w)
            if junction is None:
                if len(w) >= 4 or start == 0 or end == len(core):
                    hits.append((w, "inside"))
            elif start < junction < end:
                hits.append((w, "joined"))
            start = core.find(w, start + 1)
    return hits


def analyse(name, typ, competitors, avoid, suffixes):
    core = fold(name)
    flags = []
    acronym = typ == "acronym"
    n = len(core)
    if n == 0:
        return core, flags, 0, 0
    # Length
    if n > 15:
        pen = LEN_FAR_PENALTY
    elif LEN_OK[0] <= n <= LEN_OK[1]:
        pen = 0
    else:
        pen = LEN_PENALTY.get(n, 0)
    if acronym and n <= 5:
        pen = 0
    if pen:
        flags.append(flag("length", "warn", f"{n} letters; preferred {LEN_OK[0]} to {LEN_OK[1]}", pen))
    syl = syllables(core)
    if not acronym:
        spen = SYLLABLE_FAR_PENALTY if syl >= 5 else SYLLABLE_PENALTY.get(syl, 0)
        if spen:
            flags.append(flag("syllables", "warn", f"about {syl} syllables; preferred 2 to 3", spen))
    # Characters that are hard to say or type
    if re.search(r"\d", name):
        flags.append(flag("digit", "warn", "contains a digit; people cannot type it after hearing it once", DIGIT_PENALTY))
    if "-" in name:
        flags.append(flag("hyphen", "warn", "contains a hyphen; it is dropped when spoken", HYPHEN_PENALTY))
    if any(ord(c) > 127 and c.isalpha() for c in name):
        flags.append(flag("non_ascii", "warn", "accented or non-Latin letters are hard to type and break handles", NON_ASCII_PENALTY))
    if " " in name:
        flags.append(flag("multi_word", "info", "multi-word name; slugs join the words", MULTIWORD_PENALTY))
    # Pronounceability (skipped for acronyms, which are spelled out)
    if not acronym:
        if not any(is_vowel(core, i) for i in range(n)):
            flags.append(flag("no_vowel", "warn", "no vowel; cannot be pronounced as a word", NO_VOWEL_PENALTY))
        cons = runs(core, False)
        for r in cons:
            if len(r) == 3:
                common = r in COMMON_TRIPLES
                flags.append(flag("consonant_cluster", "info" if common else "warn",
                                  f"three consonants in a row: '{r}'", TRIPLE_COMMON_PENALTY if common else TRIPLE_PENALTY))
            elif len(r) == 4:
                flags.append(flag("consonant_cluster", "warn", f"four consonants in a row: '{r}'", QUAD_PENALTY))
            elif len(r) >= 5:
                flags.append(flag("consonant_cluster", "warn", f"{len(r)} consonants in a row: '{r}'", QUINT_PENALTY))
        for r in runs(core, True):
            if len(r) == 3:
                flags.append(flag("vowel_run", "warn", f"three vowels in a row: '{r}'", VOWEL_RUN3_PENALTY))
            elif len(r) >= 4:
                flags.append(flag("vowel_run", "warn", f"{len(r)} vowels in a row: '{r}'", VOWEL_RUN4_PENALTY))
        if re.search(r"q(?!u)", core):
            flags.append(flag("q_without_u", "warn", "q without u is read several ways", Q_NO_U_PENALTY))
    # Ambiguous spellings
    amb = ambiguity(core)
    if amb:
        pen = min(AMBIG_PENALTY * len(amb), AMBIG_CAP)
        flags.append(flag("ambiguous_spelling", "warn", "; ".join(d for _, d in amb), pen))
    doubles = sorted({m.group(0) for m in re.finditer(r"(.)\1", core)})
    if doubles:
        pen = min(DOUBLE_PENALTY * len(doubles), DOUBLE_CAP)
        flags.append(flag("doubled_letter", "warn", "doubled letters: " + ", ".join(doubles) + "; people may type one", pen))
    # Offensive substrings
    for w, where in bundled_hits(core, None):
        if len(w) >= 5:
            flags.append(flag("bundled_offensive", "block", f"contains '{w}' (bundled list, not exhaustive)", 0))
        elif len(w) == 4:
            flags.append(flag("bundled_offensive", "warn", f"contains '{w}' (bundled list, not exhaustive); check it is not read that way", BUNDLED_4_PENALTY))
        else:
            flags.append(flag("bundled_offensive", "warn", f"starts or ends with '{w}' (bundled list, not exhaustive)", BUNDLED_3_PENALTY))
    for word in avoid:
        w = fold(word)
        if w and w in core:
            flags.append(flag("avoid_word", "block", f"contains '{word}' from your avoid list", 0))
    # Competitors
    for comp in competitors:
        c = fold(comp)
        if not c:
            continue
        if c == core:
            flags.append(flag("competitor_exact", "block", f"identical to competitor '{comp}'", 0))
            continue
        if len(c) >= SUBSTR_MIN_LEN and c in core:
            flags.append(flag("competitor_substring", "warn", f"contains competitor '{comp}'", COMP_SUBSTR_PENALTY))
        elif len(core) >= SUBSTR_MIN_LEN and core in c:
            flags.append(flag("competitor_substring", "warn", f"is contained in competitor '{comp}'", COMP_SUBSTR_PENALTY))
        else:
            d = levenshtein(core, c)
            if d <= near_limit(core, c):
                flags.append(flag("competitor_near", "warn", f"edit distance {d} from competitor '{comp}'", COMP_NEAR_PENALTY))
    # Joined to a suffix
    for suf in suffixes:
        label = fold(suf)
        joined = core + label
        j = len(core)
        probs = []
        if re.search(r"(.)\1\1", joined):
            probs.append("three identical letters in a row")
        left = re.search(r"[^aeiouy]*$", core).group(0)
        right = re.match(r"[^aeiouy]*", label).group(0) if label else ""
        if len(left) + len(right) >= 4 and left and right:
            probs.append(f"consonant pile-up '{left}|{right}'")
        if core and label and core[-1] == label[0]:
            probs.append(f"'{core[-1]}' doubles at the dot, easy to mistype")
        for w, where in bundled_hits(joined, j):
            if where == "joined":
                probs.append(f"reads as '{w}' across the dot (bundled list, not exhaustive)")
        if core.endswith(label) and label:
            probs.append(f"name already ends in '{label}'")
        if probs:
            flags.append(flag("suffix_join", "warn", f"{core}{suf}: " + "; ".join(probs), JOIN_PENALTY))
    return core, flags, n, syl


def slugs(name, core, suffixes):
    words = [fold(w) for w in re.split(r"[\s_\-]+", name) if fold(w)]
    flat = "".join(words) or core
    out = {"handle": flat, "handle_underscore": "_".join(words) or flat,
           "handle_hyphen": "-".join(words) or flat}
    out["domains"] = [flat + (s if s.startswith(".") else "." + s) for s in suffixes]
    return out


def build_reason(entry):
    bits = [f"{entry['length']} letters", f"about {entry['syllables']} syllables"]
    codes = {f["code"] for f in entry["flags"]}
    if "ambiguous_spelling" not in codes and "doubled_letter" not in codes:
        bits.append("no ambiguous spellings")
    if "consonant_cluster" not in codes and "vowel_run" not in codes:
        bits.append("easy letter pattern")
    if not codes & {"competitor_exact", "competitor_substring", "competitor_near"}:
        bits.append("no collision with the competitor list")
    if "near_duplicate" not in codes:
        bits.append("distinct within the list")
    return ", ".join(bits)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Score candidate brand names; strict JSON out.")
    ap.add_argument("candidates")
    ap.add_argument("--competitors")
    ap.add_argument("--avoid")
    ap.add_argument("--suffix", action="append")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--max-per-type", type=int, default=2)
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    suffixes = args.suffix or [".com"]
    if args.top < 1 or args.max_per_type < 1:
        print("error: --top and --max-per-type must be at least 1", file=sys.stderr)
        return 2
    try:
        cands = parse_candidates(args.candidates)
        competitors = read_wordlist(args.competitors, "competitors")
        avoid = read_wordlist(args.avoid, "avoid")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    entries, seen = [], {}
    for name, typ in cands:
        core, flags, n, syl = analyse(name, typ, competitors, avoid, suffixes)
        if not core:
            flags = [flag("no_letters", "block", "contains no a-z letters", 0)]
        elif core in seen:
            flags.append(flag("exact_duplicate", "block", f"same letters as '{seen[core]}' earlier in the list", 0))
        else:
            seen[core] = name
        entries.append({"name": name, "type": typ, "core": core, "length": n,
                        "syllables": syl, "flags": flags, "slugs": slugs(name, core, suffixes)})

    # Near-duplicates inside the list
    pairs = []
    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            a, b = entries[i]["core"], entries[j]["core"]
            if a and b and a != b:
                d = levenshtein(a, b)
                if d <= near_limit(a, b):
                    pairs.append({"a": entries[i]["name"], "b": entries[j]["name"], "distance": d})
                    for e, other in ((entries[i], entries[j]), (entries[j], entries[i])):
                        e["flags"].append(flag("near_duplicate", "info",
                                               f"edit distance {d} from '{other['name']}' in this list", DUP_PENALTY))

    for e in entries:
        pen = sum(f["penalty"] for f in e["flags"])
        e["score"] = max(0, 100 - pen)
        blocked = any(f["severity"] == "block" for f in e["flags"])
        warn_pile = sum(1 for f in e["flags"] if f["severity"] == "warn")
        if blocked or e["score"] < REVIEW_MIN:
            e["verdict"] = "cut"
        elif e["score"] < KEEP_MIN or warn_pile >= 3:
            e["verdict"] = "review"
        else:
            e["verdict"] = "keep"

    entries.sort(key=lambda e: (-e["score"], e["name"].lower()))
    shortlist, per_type = [], {}
    for e in entries:
        if e["verdict"] == "cut" or len(shortlist) >= args.top:
            continue
        if any(levenshtein(e["core"], s["core"]) <= near_limit(e["core"], s["core"]) for s in shortlist):
            continue
        key = e["type"] or "untyped"
        if e["type"] and per_type.get(key, 0) >= args.max_per_type:
            continue
        per_type[key] = per_type.get(key, 0) + 1
        shortlist.append(e)

    out_rank = []
    for rank, e in enumerate(entries, 1):
        out_rank.append({
            "rank": rank, "name": e["name"], "type": e["type"], "score": e["score"],
            "verdict": e["verdict"], "length": e["length"], "syllables": e["syllables"],
            "flags": [{k: f[k] for k in ("code", "severity", "detail")} for f in e["flags"]],
            "slugs": e["slugs"]})
    out_short = []
    for e in shortlist:
        watch = [f["detail"] for f in e["flags"] if f["severity"] in ("warn", "info")]
        domains = ", ".join(e["slugs"]["domains"])
        out_short.append({
            "name": e["name"], "type": e["type"], "score": e["score"],
            "reasons": [build_reason(e)], "watch": watch,
            "to_verify": [t.format(domains=domains) for t in TO_VERIFY]})
    report = {
        "tool": "score_names", "schema_version": 1,
        "input": {"candidates": len(entries), "competitors": len(competitors),
                  "avoid_words": len(avoid), "suffixes": suffixes, "top": args.top,
                  "max_per_type": args.max_per_type},
        "thresholds": {"keep_min_score": KEEP_MIN, "review_min_score": REVIEW_MIN,
                       "preferred_letters": list(LEN_OK), "preferred_syllables": [2, 3]},
        "ranking": out_rank, "shortlist": out_short, "near_duplicate_pairs": pairs,
        "shortlist_shortfall": len(shortlist) < args.top,
        "not_checked": NOT_CHECKED,
        "notes": ["Scores are heuristics for English-looking names, not measurements of quality.",
                  "The bundled offensive-substring list is short and not exhaustive.",
                  "No name here has been checked for availability or trademark conflict."],
    }
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    return 1 if report["shortlist_shortfall"] else 0


if __name__ == "__main__":
    sys.exit(main())
