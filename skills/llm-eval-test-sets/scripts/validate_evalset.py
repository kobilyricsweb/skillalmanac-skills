#!/usr/bin/env python3
"""Validate an LLM eval set stored as JSONL, before any model is run on it.

Usage:
    python validate_evalset.py cases.jsonl
    python validate_evalset.py test.jsonl --against train.jsonl

Reads the given files, writes nothing, calls no model, uses no network.
Prints one strict JSON document on stdout (no NaN, no trailing text).
Exit codes: 0 no FAIL finding (WARN and INFO allowed), 1 at least one FAIL,
2 usage error or unreadable file.

Case format, one JSON object per line:
    id        required, unique string
    prompt    required, non-empty string
    grader    required: exact | contains | regex | numeric | set | abstain | judge
    expected  required for exact (string or number), contains (string or list of
              strings, all must appear), regex (pattern), numeric (number),
              set (non-empty list)
    tolerance required for numeric: absolute tolerance, number >= 0
    markers   for abstain: list of phrases that count as declining to answer
    rubric    required for judge: non-empty string
    tag       optional string, e.g. typical, edge, adversarial, unanswerable
    label     optional string, the class label for classification sets
    split     optional string, e.g. train, dev, test
    unanswerable  optional boolean
"""
import difflib
import json
import math
import re
import sys

GRADERS = ("exact", "contains", "regex", "numeric", "set", "abstain", "judge")

# Thresholds. Each value has a reason; change them only with a reason.
MIN_CASES = 30            # below this a pass rate has a Wilson 95% interval about 28 points wide or more (n=30, rate 80%)
MAX_SHARE_ONE_TAG = 0.70  # one tag holding more than 70% means the others are not really tested
MAX_SHARE_ONE_LABEL = 0.80  # a model that always says the majority label scores 80% on its own
MIN_UNANSWERABLE_SHARE = 0.10  # fewer than 1 in 10 makes a hallucination rate unmeasurable
NEAR_JACCARD = 0.80       # word 2-shingle overlap that reads as the same question reworded
NEAR_RATIO = 0.92         # character-level similarity that reads as a one-word edit
MIN_ANSWER_LEAK_CHARS = 4  # shorter expected strings appear in prompts by chance
SPREAD_RATIO_P90_MEDIAN = 5.0  # a long tail: p90 more than 5 times the median
UNIFORM_RATIO_MAX_MIN = 1.3    # every prompt nearly the same length: one template
MIN_PROMPT_CHARS = 5
MAX_PROMPT_CHARS = 8000
MAX_IDS_SHOWN = 20
MAX_PAIRS_FOR_NEAR = 4_000_000  # cap on pairwise comparisons so huge sets stay fast

FINDINGS = []


def add(severity, check, message, ids=None):
    entry = {"severity": severity, "check": check, "message": message}
    if ids:
        entry["case_ids"] = list(ids)[:MAX_IDS_SHOWN]
        if len(ids) > MAX_IDS_SHOWN:
            entry["more"] = len(ids) - MAX_IDS_SHOWN
    FINDINGS.append(entry)


def norm(text):
    return " ".join(re.findall(r"\w+", str(text).lower()))


def shingles(text):
    words = norm(text).split()
    if len(words) < 2:
        return set(words)
    return {" ".join(words[i:i + 2]) for i in range(len(words) - 1)}


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def load(path):
    """Return (cases, error). A case carries its line number in '_line'."""
    cases = []
    try:
        with open(path, encoding="utf-8-sig") as fh:
            for lineno, raw in enumerate(fh, 1):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except ValueError as exc:
                    add("FAIL", "json-parse", "line %d of %s is not valid JSON: %s" % (lineno, path, exc))
                    continue
                if not isinstance(obj, dict):
                    add("FAIL", "json-parse", "line %d of %s is not a JSON object" % (lineno, path))
                    continue
                obj["_line"] = lineno
                obj["_file"] = path
                cases.append(obj)
    except (OSError, UnicodeDecodeError) as exc:
        return None, "cannot read %s: %s" % (path, exc)
    return cases, None


def case_name(c):
    cid = c.get("id")
    return str(cid) if isinstance(cid, str) and cid else "line%d" % c["_line"]


def check_fields(cases):
    seen = {}
    for c in cases:
        name = case_name(c)
        cid = c.get("id")
        if not isinstance(cid, str) or not cid.strip():
            add("FAIL", "id-missing", "case on line %d of %s has no string id" % (c["_line"], c["_file"]))
        else:
            seen.setdefault(cid, []).append(c)
        prompt = c.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            add("FAIL", "prompt-missing", "case %s has no prompt text" % name, [name])
        grader = c.get("grader")
        if grader is None:
            add("FAIL", "grader-missing", "case %s has no grader; every case needs one of %s" % (name, ", ".join(GRADERS)), [name])
            continue
        if grader not in GRADERS:
            add("FAIL", "grader-unknown", "case %s uses grader %r; allowed: %s" % (name, grader, ", ".join(GRADERS)), [name])
            continue
        exp = c.get("expected")
        if grader == "exact" and not ((isinstance(exp, str) and exp.strip()) or is_number(exp)):
            add("FAIL", "expected-missing", "case %s: exact grader needs a non-empty string or number in expected" % name, [name])
        elif grader == "contains":
            ok = (isinstance(exp, str) and exp.strip()) or (isinstance(exp, list) and exp and all(isinstance(x, str) and x.strip() for x in exp))
            if not ok:
                add("FAIL", "expected-missing", "case %s: contains grader needs a string or a non-empty list of strings in expected" % name, [name])
        elif grader == "regex":
            if not isinstance(exp, str) or not exp:
                add("FAIL", "expected-missing", "case %s: regex grader needs a pattern string in expected" % name, [name])
            else:
                try:
                    re.compile(exp)
                except re.error as exc:
                    add("FAIL", "regex-invalid", "case %s: expected is not a valid regex: %s" % (name, exc), [name])
        elif grader == "numeric":
            if not is_number(exp):
                add("FAIL", "expected-missing", "case %s: numeric grader needs a number in expected" % name, [name])
            tol = c.get("tolerance")
            if not is_number(tol) or tol < 0:
                add("FAIL", "tolerance-missing", "case %s: numeric grader needs tolerance (number >= 0); use 0 for exact" % name, [name])
        elif grader == "set":
            if not isinstance(exp, list) or not exp:
                add("FAIL", "expected-missing", "case %s: set grader needs a non-empty list in expected" % name, [name])
        elif grader == "abstain":
            markers = c.get("markers")
            if not (isinstance(markers, list) and markers and all(isinstance(m, str) and m.strip() for m in markers)):
                add("WARN", "abstain-marker-missing", "case %s: abstain grader has no markers list, so a refusal cannot be detected by string match" % name, [name])
        elif grader == "judge":
            rub = c.get("rubric")
            if not isinstance(rub, str) or not rub.strip():
                add("FAIL", "rubric-missing", "case %s: judge grader needs a rubric string saying what a pass looks like" % name, [name])
    dups = sorted(k for k, v in seen.items() if len(v) > 1)
    if dups:
        add("FAIL", "id-duplicate", "%d id(s) used more than once" % len(dups), dups)


def expected_key(c):
    return json.dumps(c.get("expected"), sort_keys=True) if "expected" in c else None


def check_duplicates(cases):
    by_norm = {}
    for c in cases:
        p = c.get("prompt")
        if isinstance(p, str) and p.strip():
            by_norm.setdefault(norm(p), []).append(c)
    conflict, same = [], []
    for group in by_norm.values():
        if len(group) < 2:
            continue
        keys = {expected_key(g) for g in group}
        (conflict if len(keys) > 1 else same).append([case_name(g) for g in group])
    if conflict:
        add("FAIL", "prompt-duplicate-conflict", "%d group(s) of identical prompts carry different expected answers; one of them is wrong" % len(conflict), [", ".join(g) for g in conflict])
    if same:
        add("WARN", "prompt-duplicate", "%d group(s) of identical prompts; they count twice and shrink the effective set size" % len(same), [", ".join(g) for g in same])
    return set(by_norm)


def near_pairs(a_cases, b_cases=None):
    """Near-duplicate prompt pairs within a_cases, or across a_cases and b_cases."""
    def prep(cs):
        out = []
        for c in cs:
            p = c.get("prompt")
            if isinstance(p, str) and p.strip():
                out.append((c, norm(p), shingles(p)))
        return out
    A = prep(a_cases)
    B = prep(b_cases) if b_cases is not None else A
    pairs, count = [], 0
    for i, (ca, na, sa) in enumerate(A):
        start = 0 if b_cases is not None else i + 1
        for cb, nb, sb in B[start:]:
            count += 1
            if count > MAX_PAIRS_FOR_NEAR:
                return pairs, True
            if na == nb:
                continue  # exact duplicates are reported separately
            union = len(sa | sb)
            jac = len(sa & sb) / union if union else 0.0
            near = jac >= NEAR_JACCARD
            if not near and jac >= 0.5:
                near = difflib.SequenceMatcher(None, na, nb).ratio() >= NEAR_RATIO
            if near:
                pairs.append((case_name(ca), case_name(cb)))
    return pairs, False


def check_near(cases):
    pairs, capped = near_pairs(cases)
    if pairs:
        add("WARN", "prompt-near-duplicate", "%d pair(s) of prompts are near-identical (word 2-shingle overlap >= %.2f or character similarity >= %.2f); in a templated set this is expected, otherwise merge or rewrite" % (len(pairs), NEAR_JACCARD, NEAR_RATIO), ["%s ~ %s" % p for p in pairs])
    if capped:
        add("INFO", "near-duplicate-capped", "near-duplicate search stopped after %d comparisons; split the file to check the rest" % MAX_PAIRS_FOR_NEAR)


def is_unanswerable(c):
    return c.get("unanswerable") is True or c.get("tag") == "unanswerable" or c.get("grader") == "abstain"


def check_balance(cases, stats):
    n = len(cases)
    tags = {}
    for c in cases:
        t = c.get("tag")
        tags.setdefault(t if isinstance(t, str) and t else "(none)", []).append(case_name(c))
    stats["by_tag"] = {k: len(v) for k, v in sorted(tags.items())}
    if n and "(none)" in tags and len(tags) == 1:
        add("WARN", "tags-missing", "no case has a tag; per-tag breakdowns will be empty (use typical, edge, adversarial, unanswerable)")
    elif n and len(tags) == 1:
        add("WARN", "tags-single", "every case has the same tag %r, so the set tests one kind of input" % next(iter(tags)))
    elif n:
        top, ids = max(tags.items(), key=lambda kv: len(kv[1]))
        if len(ids) / n > MAX_SHARE_ONE_TAG:
            add("WARN", "tag-imbalance", "tag %r holds %d of %d cases (%.0f%%, limit %.0f%%)" % (top, len(ids), n, 100.0 * len(ids) / n, 100 * MAX_SHARE_ONE_TAG))
    unans = [case_name(c) for c in cases if is_unanswerable(c)]
    stats["unanswerable"] = len(unans)
    if n >= 10 and len(unans) / n < MIN_UNANSWERABLE_SHARE:
        add("WARN", "unanswerable-share", "%d of %d cases (%.0f%%) are unanswerable probes; below %.0f%% a hallucination rate cannot be measured" % (len(unans), n, 100.0 * len(unans) / n, 100 * MIN_UNANSWERABLE_SHARE))
    for c in cases:
        if (c.get("tag") == "unanswerable" or c.get("unanswerable") is True) and c.get("grader") not in ("abstain", "judge"):
            add("WARN", "unanswerable-grader", "case %s is marked unanswerable but graded by %r; use abstain (or judge with a rubric)" % (case_name(c), c.get("grader")), [case_name(c)])
    labels = {}
    for c in cases:
        lab = c.get("label")
        if lab is None and c.get("grader") == "exact" and isinstance(c.get("expected"), str):
            lab = c["expected"]
        if isinstance(lab, str):
            labels.setdefault(lab, []).append(case_name(c))
    if labels and len(labels) <= 12 and sum(len(v) for v in labels.values()) >= 10:
        stats["by_label"] = {k: len(v) for k, v in sorted(labels.items())}
        total = sum(len(v) for v in labels.values())
        top, ids = max(labels.items(), key=lambda kv: len(kv[1]))
        if len(labels) == 1:
            add("WARN", "label-single", "every labelled case has the label %r; a constant answer scores 100%%" % top)
        elif len(ids) / total > MAX_SHARE_ONE_LABEL:
            add("WARN", "label-imbalance", "label %r holds %d of %d labelled cases (%.0f%%, limit %.0f%%); always answering it would score that much" % (top, len(ids), total, 100.0 * len(ids) / total, 100 * MAX_SHARE_ONE_LABEL))
    if n < MIN_CASES:
        add("WARN", "set-small", "%d cases; under %d the Wilson 95%% interval on a pass rate is about 28 points wide or more" % (n, MIN_CASES))


def percentile(sorted_vals, q):
    k = max(0, math.ceil(q * len(sorted_vals)) - 1)
    return sorted_vals[k]


def check_lengths(cases, stats):
    pairs = [(case_name(c), c["prompt"]) for c in cases if isinstance(c.get("prompt"), str) and c["prompt"].strip()]
    if not pairs:
        return
    chars = sorted(len(p) for _, p in pairs)
    words = sorted(len(p.split()) for _, p in pairs)
    med = percentile(chars, 0.5)
    stats["prompt_chars"] = {"min": chars[0], "median": med, "p90": percentile(chars, 0.9), "max": chars[-1]}
    stats["prompt_words"] = {"min": words[0], "median": percentile(words, 0.5), "p90": percentile(words, 0.9), "max": words[-1]}
    short = [i for i, p in pairs if len(p) < MIN_PROMPT_CHARS]
    long_ = [i for i, p in pairs if len(p) > MAX_PROMPT_CHARS]
    if short:
        add("WARN", "prompt-too-short", "%d prompt(s) under %d characters" % (len(short), MIN_PROMPT_CHARS), short)
    if long_:
        add("WARN", "prompt-too-long", "%d prompt(s) over %d characters; check they fit the model context together with the system prompt" % (len(long_), MAX_PROMPT_CHARS), long_)
    if len(chars) >= 10 and med > 0 and stats["prompt_chars"]["p90"] / med > SPREAD_RATIO_P90_MEDIAN:
        add("WARN", "length-tail", "p90 length is %.1f times the median; a few long prompts dominate the cost and may behave differently" % (stats["prompt_chars"]["p90"] / med))
    if len(chars) >= 10 and chars[0] > 0 and chars[-1] / chars[0] < UNIFORM_RATIO_MAX_MIN:
        add("WARN", "length-uniform", "longest prompt is under %.1f times the shortest; the set looks like one template and may not cover real input lengths" % UNIFORM_RATIO_MAX_MIN)


def answer_strings(c):
    exp = c.get("expected")
    out = []
    if c.get("grader") in ("exact", "contains", "set"):
        for x in (exp if isinstance(exp, list) else [exp]):
            if isinstance(x, str) and len(norm(x)) >= MIN_ANSWER_LEAK_CHARS:
                out.append(norm(x))
    return out


def check_leakage(cases, stats):
    splits = {}
    for c in cases:
        s = c.get("split") if isinstance(c.get("split"), str) and c.get("split") else c["_default_split"]
        c["_split"] = s
        splits.setdefault(s, []).append(c)
    stats["splits"] = {k: len(v) for k, v in sorted(splits.items())}
    # An answer sitting inside its own prompt is leakage within a case.
    own = []
    for c in cases:
        p = norm(c.get("prompt", ""))
        if any(a in p for a in answer_strings(c)):
            own.append(case_name(c))
    if own:
        add("WARN", "answer-in-prompt", "%d case(s) have the expected answer text inside their own prompt; a model can pass by copying (real for open answers, often harmless for class labels)" % len(own), own)
    if len(splits) < 2:
        add("INFO", "leakage-skipped", "only one split present; pass --against train.jsonl or add a split field to check train/test leakage")
        return
    names = sorted(splits)
    exact_hits, near_hits, answer_hits = [], [], []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            A, B = splits[names[i]], splits[names[j]]
            normA = {}
            for c in A:
                if isinstance(c.get("prompt"), str):
                    normA.setdefault(norm(c["prompt"]), []).append(c)
            for c in B:
                if isinstance(c.get("prompt"), str):
                    for m in normA.get(norm(c["prompt"]), []):
                        exact_hits.append("%s:%s = %s:%s" % (names[i], case_name(m), names[j], case_name(c)))
            pairs, _ = near_pairs(A, B)
            near_hits += ["%s:%s ~ %s:%s" % (names[i], a, names[j], b) for a, b in pairs]
            for src, dst, sn, dn in ((A, B, names[i], names[j]), (B, A, names[j], names[i])):
                for c in src:
                    ans = answer_strings(c)
                    if not ans:
                        continue
                    for d in dst:
                        dp = norm(d.get("prompt", ""))
                        if any(a in dp for a in ans):
                            answer_hits.append("%s:%s answer inside %s:%s prompt" % (sn, case_name(c), dn, case_name(d)))
                            break
    if exact_hits:
        add("FAIL", "split-leakage-exact", "%d prompt(s) appear in more than one split; the test score is inflated by memory" % len(exact_hits), exact_hits)
    if near_hits:
        add("FAIL", "split-leakage-near", "%d near-identical prompt pair(s) across splits" % len(near_hits), near_hits)
    if answer_hits:
        add("WARN", "split-leakage-answer", "%d case(s) whose expected answer is spelled out in another split's prompt (for example as a few-shot example)" % len(answer_hits), answer_hits)


def validate(paths, against):
    del FINDINGS[:]
    stats = {}
    cases, err = load(paths)
    if err:
        return None, err
    extra = []
    if against:
        extra, err = load(against)
        if err:
            return None, err
    for c in cases:
        c["_default_split"] = "test" if against else "main"
    for c in extra:
        c["_default_split"] = "train"
    allc = cases + extra
    stats["cases"] = len(cases)
    if against:
        stats["against_cases"] = len(extra)
    if not cases:
        add("FAIL", "empty", "no cases found in %s" % paths)
    check_fields(allc)
    check_duplicates(cases)
    check_near(cases)
    check_balance(cases, stats)
    check_lengths(cases, stats)
    gr = {}
    for c in cases:
        g = c.get("grader")
        gr[g if isinstance(g, str) else "(none)"] = gr.get(g if isinstance(g, str) else "(none)", 0) + 1
    stats["by_grader"] = dict(sorted(gr.items()))
    check_leakage(allc, stats)
    counts = {"FAIL": 0, "WARN": 0, "INFO": 0}
    for f in FINDINGS:
        counts[f["severity"]] += 1
    report = {
        "tool": "validate_evalset",
        "file": paths,
        "ok": counts["FAIL"] == 0,
        "counts": counts,
        "stats": stats,
        "findings": FINDINGS,
    }
    return report, None


def main(argv):
    args = list(argv)
    against = None
    if "--against" in args:
        i = args.index("--against")
        if i + 1 >= len(args):
            print("usage: validate_evalset.py cases.jsonl [--against train.jsonl]", file=sys.stderr)
            return 2
        against = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1 or args[0].startswith("-"):
        print("usage: validate_evalset.py cases.jsonl [--against train.jsonl]", file=sys.stderr)
        return 2
    report, err = validate(args[0], against)
    if err:
        print(err, file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main(sys.argv[1:]))
