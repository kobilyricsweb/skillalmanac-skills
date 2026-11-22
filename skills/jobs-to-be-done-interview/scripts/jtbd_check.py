#!/usr/bin/env python3
"""Validate a Jobs-to-be-Done study file: interview transcripts, force codes, job statements.

Usage:
    python jtbd_check.py <study.json> [--min-evidence N]

Reads the one JSON file given (see references/synthesis-contract.md for the shape).
Writes nothing to disk; prints one JSON object to stdout (UTF-8, always valid JSON).

Exit codes:
    0  ok: no error-severity findings
    1  not ok: at least one error-severity finding (warnings never fail)
    2  input problem (missing file, bad JSON, wrong top-level shape, bad option)
"""
import json
import re
import sys

# Four forces of progress. An interview must code or explicitly rule out each one.
FORCES = ("push", "pull", "anxiety", "habit")

# Participants should do most of the talking. Below 70% of words the interviewer is
# probably narrating, summarising or pitching. Working value, not a measured optimum.
MIN_PARTICIPANT_SHARE = 0.70

# A job statement needs support from at least this many different interviews
# (one story is an anecdote). Overridable with --min-evidence.
DEFAULT_MIN_EVIDENCE = 2

# A statement part under 3 words is a label ("faster"), not a situation or a motivation.
MIN_PART_WORDS = 3

# Question patterns: (rule, severity, regex). Matched case-insensitively against one
# interviewer question at a time. Errors fail the file; warnings are reported only.
QUESTION_RULES = [
    ("leading_tag", "error", r"\b(don't|doesn't|didn't|wouldn't|isn't|wasn't|aren't|weren't|shouldn't|couldn't|won't|can't) (you|it|that|they|there|we|this)\b"),
    ("leading_tag", "error", r",\s*(right|correct|yeah|no|isn't it|wasn't it|didn't you|don't you|wouldn't you)\s*\?\s*$"),
    ("leading_assumption", "error", r"\b(you must have|that must have|i imagine|i bet|you probably|so you (were|felt|got|decided)|obviously|surely)\b"),
    ("hypothetical", "error", r"\bwould you (use|buy|pay|switch|try|like|want|consider|recommend|subscribe|sign)\b"),
    ("hypothetical", "error", r"\b(will you|are you going to|how likely|how much would you|in the future|hypothetically|what if|imagine|if we (built|made|had|offered|launched|added))\b"),
    ("hypothetical", "error", r"\bwould (it|that|this) be (useful|helpful|valuable|good|great|nice|better)\b"),
    ("solution_priming", "error", r"\b(our|my|the) (product|app|tool|feature|platform|service|solution|software|prototype|idea|dashboard)\b"),
    ("opinion_seeking", "warn", r"\bdo you (think|feel|believe|like|love|hate|prefer|agree)\b|\bwhat do you think\b|\bhow do you feel about\b"),
    ("double_barreled", "warn", r"\b(and|or) (did|do|does|was|were|would|how|what|why|have|can|is|are|who|when|where)\b"),
    ("why_prompt", "warn", r"^\s*(and |so )?why\b"),
]

COMPILED = [(name, sev, re.compile(rx, re.IGNORECASE)) for name, sev, rx in QUESTION_RULES]

# Words that put a solution inside a job statement (the job is demand-side, not a feature).
SOLUTION_WORDS = re.compile(r"\b(app|tool|software|feature|platform|dashboard|integration|plugin|extension|subscription)\b", re.IGNORECASE)

SENTENCE_SPLIT = re.compile(r"(?<=[.?!])\s+")


class InputError(Exception):
    pass


def words(text):
    return re.findall(r"\S+", text or "")


def norm(text):
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def questions_in(text):
    return [s.strip() for s in SENTENCE_SPLIT.split(text or "") if s.strip().endswith("?")]


def check_interview(iv, idx):
    """Return the per-interview report. Findings are dicts with where/rule/severity/text."""
    iid = str(iv.get("id", f"interview-{idx + 1}"))
    findings = []
    turns = iv.get("turns")
    if not isinstance(turns, list) or not turns:
        findings.append({"where": iid, "rule": "no_turns", "severity": "error", "text": "interview has no turns"})
        turns = []
    by_n = {}
    interviewer_words = participant_words = 0
    n_questions = n_leading = 0
    for pos, t in enumerate(turns):
        if not isinstance(t, dict):
            findings.append({"where": f"{iid} turn#{pos + 1}", "rule": "bad_turn", "severity": "error", "text": "turn is not an object"})
            continue
        n = t.get("n", pos + 1)
        speaker = str(t.get("speaker", "")).lower()
        text = str(t.get("text", ""))
        by_n[n] = (speaker, text)
        if speaker not in ("interviewer", "participant"):
            findings.append({"where": f"{iid} turn {n}", "rule": "bad_speaker", "severity": "error", "text": f"speaker {speaker!r} must be interviewer or participant"})
            continue
        if speaker == "interviewer":
            interviewer_words += len(words(text))
            for q in questions_in(text):
                n_questions += 1
                hit_error = False
                seen = set()
                for name, sev, rx in COMPILED:
                    if name in seen or not rx.search(q):
                        continue
                    seen.add(name)
                    hit_error = hit_error or sev == "error"
                    findings.append({"where": f"{iid} turn {n}", "rule": name, "severity": sev, "text": q})
                n_leading += 1 if hit_error else 0
        else:
            participant_words += len(words(text))

    total = interviewer_words + participant_words
    share = round(participant_words / total, 3) if total else 0.0
    if total and share < MIN_PARTICIPANT_SHARE:
        findings.append({"where": iid, "rule": "interviewer_dominates", "severity": "warn",
                         "text": f"participant speaks {share:.0%} of words; target at least {MIN_PARTICIPANT_SHARE:.0%}"})

    counts = {f: 0 for f in FORCES}
    ruled_out = set()
    codes = iv.get("codes", [])
    if not isinstance(codes, list):
        findings.append({"where": iid, "rule": "bad_codes", "severity": "error", "text": "codes must be a list"})
        codes = []
    for c in codes:
        if not isinstance(c, dict):
            findings.append({"where": iid, "rule": "bad_code", "severity": "error", "text": "code is not an object"})
            continue
        force = str(c.get("force", "")).lower()
        if force not in FORCES:
            findings.append({"where": iid, "rule": "unknown_force", "severity": "error", "text": f"force {force!r} must be one of {', '.join(FORCES)}"})
            continue
        if c.get("none_found"):
            if len(words(str(c.get("note", "")))) < 4:
                findings.append({"where": iid, "rule": "none_found_without_note", "severity": "error",
                                 "text": f"{force}: none_found needs a note of at least 4 words saying what was probed"})
            else:
                ruled_out.add(force)
            continue
        turn_no = c.get("turn")
        where = f"{iid} turn {turn_no}"
        if turn_no not in by_n:
            findings.append({"where": where, "rule": "code_turn_missing", "severity": "error", "text": f"{force}: no such turn"})
            continue
        speaker, text = by_n[turn_no]
        if speaker != "participant":
            findings.append({"where": where, "rule": "code_on_interviewer_turn", "severity": "error", "text": f"{force}: forces are coded only on participant turns"})
            continue
        quote = norm(str(c.get("quote", "")))
        if not quote or quote not in norm(text):
            findings.append({"where": where, "rule": "quote_not_in_turn", "severity": "error", "text": f"{force}: quote is empty or not a verbatim part of the turn"})
            continue
        counts[force] += 1

    missing = [f for f in FORCES if counts[f] == 0 and f not in ruled_out]
    for f in missing:
        findings.append({"where": iid, "rule": "force_not_covered", "severity": "error", "text": f"{f}: no coded quote and no none_found note"})

    return {
        "id": iid,
        "turns": len(turns),
        "interviewer_questions": n_questions,
        "leading_questions": n_leading,
        "leading_rate": round(n_leading / n_questions, 3) if n_questions else 0.0,
        "participant_word_share": share,
        "forces": counts,
        "forces_ruled_out": sorted(ruled_out),
        "forces_missing": missing,
        "findings": findings,
    }, {iid: by_n}


def check_statement(st, idx, transcripts, min_evidence):
    sid = str(st.get("id", f"J{idx + 1}")) if isinstance(st, dict) else f"J{idx + 1}"
    findings = []
    if not isinstance(st, dict):
        return {"id": sid, "missing_parts": ["situation", "motivation", "outcome"],
                "findings": [{"where": sid, "rule": "bad_statement", "severity": "error", "text": "statement is not an object"}]}
    parts = {k: str(st.get(k, "")).strip() for k in ("situation", "motivation", "outcome")}
    missing = [k for k, v in parts.items() if len(words(v)) < MIN_PART_WORDS]
    for k in missing:
        findings.append({"where": sid, "rule": "missing_part", "severity": "error",
                         "text": f"{k} is empty or shorter than {MIN_PART_WORDS} words"})
    text = str(st.get("text", "")).strip()
    low = text.lower()
    if not (low.startswith("when ") and "i want to" in low and "so i can" in low):
        findings.append({"where": sid, "rule": "text_not_in_form", "severity": "error",
                         "text": "text must read 'When <situation>, I want to <motivation>, so I can <outcome>'"})
    else:
        for k, v in parts.items():
            if v and norm(v).rstrip(".,") not in norm(text):
                findings.append({"where": sid, "rule": "part_not_in_text", "severity": "error",
                                 "text": f"the {k} part does not appear in the statement text"})
    if SOLUTION_WORDS.search(text):
        findings.append({"where": sid, "rule": "solution_in_statement", "severity": "warn",
                         "text": "statement names a solution type; a job should be solution-free"})
    ev = st.get("evidence", [])
    cited = set()
    if not isinstance(ev, list):
        ev = []
    for e in ev:
        if not isinstance(e, dict) or str(e.get("interview")) not in transcripts or e.get("turn") not in transcripts[str(e.get("interview"))]:
            findings.append({"where": sid, "rule": "bad_evidence_ref", "severity": "error",
                             "text": f"evidence {e!r} does not point to an existing interview turn"})
            continue
        cited.add(str(e["interview"]))
    if len(cited) < min_evidence:
        findings.append({"where": sid, "rule": "thin_evidence", "severity": "error",
                         "text": f"cites {len(cited)} interview(s); need at least {min_evidence}"})
    return {"id": sid, "missing_parts": missing, "evidence_interviews": sorted(cited), "findings": findings}


def validate(data, min_evidence):
    if not isinstance(data, dict) or not isinstance(data.get("interviews"), list):
        raise InputError("top level must be an object with an 'interviews' list")
    reports, transcripts = [], {}
    for i, iv in enumerate(data["interviews"]):
        if not isinstance(iv, dict):
            raise InputError(f"interviews[{i}] is not an object")
        rep, by = check_interview(iv, i)
        reports.append(rep)
        transcripts.update(by)
    statements = data.get("job_statements", [])
    if not isinstance(statements, list):
        raise InputError("'job_statements' must be a list")
    st_reports = [check_statement(s, i, transcripts, min_evidence) for i, s in enumerate(statements)]
    if not statements:
        st_reports_note = [{"where": "study", "rule": "no_job_statements", "severity": "warn", "text": "no job_statements yet; synthesis not started"}]
    else:
        st_reports_note = []

    all_findings = [f for r in reports for f in r["findings"]] + [f for r in st_reports for f in r["findings"]] + st_reports_note
    errors = [f for f in all_findings if f["severity"] == "error"]
    q = sum(r["interviewer_questions"] for r in reports)
    lead = sum(r["leading_questions"] for r in reports)
    summary = {
        "interviews": len(reports),
        "interviewer_questions": q,
        "leading_questions": lead,
        "leading_rate": round(lead / q, 3) if q else 0.0,
        "interviews_missing_forces": [r["id"] for r in reports if r["forces_missing"]],
        "statements": len(st_reports),
        "statements_missing_parts": [r["id"] for r in st_reports if r["missing_parts"]],
        "errors": len(errors),
        "warnings": len(all_findings) - len(errors),
    }
    return {"ok": not errors, "command": "validate", "summary": summary,
            "interviews": reports, "statements": st_reports, "study_findings": st_reports_note}


def emit(obj):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n")


def main(argv):
    min_evidence = DEFAULT_MIN_EVIDENCE
    args = list(argv)
    path = None
    try:
        while args:
            a = args.pop(0)
            if a == "--min-evidence":
                min_evidence = int(args.pop(0))
                if min_evidence < 1:
                    raise ValueError
            elif a.startswith("-"):
                raise InputError(f"unknown option {a}")
            elif path is None:
                path = a
            else:
                raise InputError("only one file may be given")
        if path is None:
            raise InputError("usage: jtbd_check.py <study.json> [--min-evidence N]")
    except (ValueError, IndexError):
        emit({"ok": False, "error": "--min-evidence needs a whole number of at least 1"})
        return 2
    except InputError as exc:
        emit({"ok": False, "error": str(exc)})
        return 2
    try:
        with open(path, encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        emit({"ok": False, "error": f"file not found: {path}"})
        return 2
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        emit({"ok": False, "error": f"not valid UTF-8 JSON: {exc}"})
        return 2
    except RecursionError:
        emit({"ok": False, "error": "nesting_too_deep: the JSON is nested too deeply to read"})
        return 2
    except ValueError as exc:
        # json.load raises a plain ValueError for an integer with more than about 4300 digits
        emit({"ok": False, "error": f"invalid_number: {str(exc)[:120]}"})
        return 2
    try:
        report = validate(data, min_evidence)
    except InputError as exc:
        emit({"ok": False, "error": str(exc)})
        return 2
    emit(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
