#!/usr/bin/env python3
"""Validate a tagged-notes file and, optionally, a themes file for a research synthesis.

Usage:
    python synthesis_check.py NOTES.json [THEMES.json]
        [--min-quotes N] [--min-participants M] [--max-share F] [--strict]

Reads the files you name and prints ONE strict JSON object to stdout. Writes nothing,
uses no network.

Exit codes: 0 = no errors (and, with --strict, no warnings); 1 = at least one error
(or a warning under --strict); 2 = a file is missing, empty or not valid JSON, or the
arguments are wrong (the JSON object then has "fatal" set).

Notes file:  {"participants": ["P01", ...]  (optional),
              "codebook": ["tag", ...]      (optional),
              "notes": [{"id": "N001", "participant": "P01", "kind": "quote"|"observation",
                         "text": "verbatim words", "tags": ["tag"]}]}
Themes file: {"thresholds": {"min_quotes": 3, "min_participants": 3, "max_share": 0.5},
              "themes": [{"id": "T1", "title": "...", "statement": "...",
                          "confidence": "high"|"medium"|"low",
                          "quotes": [{"participant": "P01", "note": "N001", "text": "..."}],
                          "contradictions": [ same shape as quotes, may be empty ]}]}
"""
import argparse
import json
import math
import os
import re
import sys

# Evidence rule defaults: a theme needs this many distinct notes from this many distinct people.
# 3 and 3 is the smallest pattern a reader can tell from one person's habit.
DEFAULT_MIN_QUOTES = 3
DEFAULT_MIN_PARTICIPANTS = 3
# Below 2 people there is no cross-interview pattern at all, so thresholds cannot go lower.
FLOOR = 2
# One person may supply at most half of a theme's quotes before the theme is that person's story.
DEFAULT_MAX_SHARE = 0.5
# Corpus level: one person owning over 30 percent of all notes skews every count (needs 4+ people to be meaningful).
NOTE_SHARE_LIMIT = 0.30
NOTE_SHARE_MIN_PARTICIPANTS = 4
# Confidence ladder (see SKILL.md): participants and share of all participants.
MEDIUM_MIN_P, MEDIUM_MIN_SHARE = 4, 0.25
HIGH_MIN_P, HIGH_MIN_SHARE = 5, 0.40
# A quote shorter than this carries too little to show what the person meant.
SHORT_QUOTE_WORDS = 4
CONFIDENCE_ORDER = {"low": 1, "medium": 2, "high": 3}
KINDS = ("quote", "observation")
VAGUE = re.compile(r"\b(most|many|majority|minority|few|several|everyone|everybody|nobody|always|never|often|usually|typically|generally)\b", re.I)
COUNT_CLAIM = re.compile(r"\b(\d+)\s+of\s+(?:the\s+)?(\d+)\s+(?:participants|people|interviewees|users)\b", re.I)
ELISION = re.compile(r"\s*(?:\[\s*(?:\.\.\.|…)\s*\]|\.\.\.|…)\s*")
SEV_ORDER = {"error": 0, "warning": 1}


class Fatal(Exception):
    pass


class Findings:
    def __init__(self):
        self.items = []

    def add(self, severity, code, where, message):
        self.items.append({"severity": severity, "code": code, "where": where, "message": message})

    def error(self, code, where, message):
        self.add("error", code, where, message)

    def warn(self, code, where, message):
        self.add("warning", code, where, message)

    def count(self, severity):
        return sum(1 for f in self.items if f["severity"] == severity)


def norm(text):
    """Make whitespace and typographic quote marks comparable; keeps case and words."""
    for old, new in (("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"'),
                     ("–", "-"), ("—", "-"), (" ", " ")):
        text = text.replace(old, new)
    return " ".join(text.split())


def quote_found(quote, note_text):
    """True when every segment of the quote (split at elisions) occurs in order in the note."""
    hay = norm(note_text)
    segments = [s.strip(' "') for s in ELISION.split(norm(quote))]
    segments = [s for s in segments if s]
    if not segments:
        return False
    pos = 0
    for seg in segments:
        idx = hay.find(seg, pos)
        if idx < 0:
            return False
        pos = idx + len(seg)
    return True


def load_json(path):
    if not os.path.isfile(path):
        raise Fatal("file not found: %s" % path)
    try:
        with open(path, encoding="utf-8-sig") as fh:
            raw = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise Fatal("cannot read %s as UTF-8 text: %s" % (path, exc))
    if not raw.strip():
        raise Fatal("file is empty: %s" % path)
    try:
        return json.loads(raw)
    except ValueError as exc:
        raise Fatal("not valid JSON: %s (%s)" % (path, exc))


def check_notes(data, f):
    """Returns (notes_by_id, participant_ids). Validates structure and tagging."""
    if not isinstance(data, dict) or not isinstance(data.get("notes"), list) or not data["notes"]:
        raise Fatal('notes file must be an object with a non-empty "notes" list')
    declared = data.get("participants")
    declared_ids = None
    if declared is not None:
        if not isinstance(declared, list):
            raise Fatal('"participants" must be a list of ids')
        declared_ids = []
        for item in declared:
            pid = item.get("id") if isinstance(item, dict) else item
            if isinstance(pid, str) and pid.strip():
                declared_ids.append(pid.strip())
        if len(set(declared_ids)) != len(declared_ids):
            f.error("duplicate_participant", "participants", "participant ids are not unique")
    codebook = data.get("codebook")
    codebook_set = set(codebook) if isinstance(codebook, list) else None

    notes, order = {}, []
    for i, note in enumerate(data["notes"]):
        where = "notes[%d]" % i
        if not isinstance(note, dict):
            f.error("bad_note", where, "note is not an object")
            continue
        nid, pid, text = note.get("id"), note.get("participant"), note.get("text")
        if not isinstance(nid, str) or not nid.strip():
            f.error("bad_note", where, "note has no string id")
            continue
        where = "note %s" % nid
        if nid in notes:
            f.error("duplicate_note_id", where, "note id used more than once")
            continue
        if not isinstance(pid, str) or not pid.strip():
            f.error("note_without_participant", where, "note has no participant id")
            continue
        if not isinstance(text, str) or not text.strip():
            f.error("empty_note", where, "note text is empty")
            continue
        kind = note.get("kind", "quote")
        if kind not in KINDS:
            f.error("bad_kind", where, "kind must be one of %s, got %r" % (list(KINDS), kind))
            kind = "quote"
        tags = note.get("tags")
        tags = [t for t in tags if isinstance(t, str) and t.strip()] if isinstance(tags, list) else []
        if not tags:
            f.warn("untagged_note", where, "note has no tags; tag it or mark it out of scope in the report")
        elif codebook_set is not None:
            for t in tags:
                if t not in codebook_set:
                    f.error("unknown_tag", where, "tag %r is not in the codebook" % t)
        if declared_ids is not None and pid.strip() not in declared_ids:
            f.error("unknown_participant", where, "participant %s is not in the participants list" % pid)
        notes[nid] = {"participant": pid.strip(), "text": text, "kind": kind, "tags": tags}
        order.append(nid)

    pids = declared_ids if declared_ids is not None else sorted({n["participant"] for n in notes.values()})
    counts = {}
    for n in notes.values():
        counts[n["participant"]] = counts.get(n["participant"], 0) + 1
    total = len(notes)
    if len(pids) >= NOTE_SHARE_MIN_PARTICIPANTS and total:
        for pid in sorted(counts):
            if counts[pid] / total > NOTE_SHARE_LIMIT:
                f.warn("participant_over_represented_in_notes", "participant %s" % pid,
                       "%d of %d notes (%.0f%%) come from this person; counts of notes overstate their weight"
                       % (counts[pid], total, 100.0 * counts[pid] / total))
    if declared_ids is not None:
        for pid in declared_ids:
            if pid not in counts:
                f.warn("participant_without_notes", "participant %s" % pid, "declared but has no notes")
    return notes, pids


def check_evidence_list(items, label, notes, f, where, need_unique):
    """Validate quote objects; returns list of (participant, note_id) for the valid ones."""
    valid, seen = [], set()
    if not isinstance(items, list):
        f.error("bad_%s_list" % label, where, "%ss must be a list" % label)
        return valid
    for j, q in enumerate(items):
        w = "%s %s[%d]" % (where, label, j)
        if not isinstance(q, dict):
            f.error("bad_quote", w, "%s is not an object" % label)
            continue
        nid, pid, text = q.get("note"), q.get("participant"), q.get("text")
        if not isinstance(text, str) or not text.strip() or not isinstance(nid, str) or not isinstance(pid, str):
            f.error("bad_quote", w, "%s needs string fields participant, note and text" % label)
            continue
        note = notes.get(nid)
        if note is None:
            f.error("quote_note_unknown", w, "note %s does not exist in the notes file" % nid)
            continue
        if note["participant"] != pid:
            f.error("quote_participant_mismatch", w,
                    "cites %s but note %s belongs to %s" % (pid, nid, note["participant"]))
            continue
        if note["kind"] != "quote":
            f.error("quote_from_observation", w, "note %s is a researcher observation, not participant words" % nid)
            continue
        if not quote_found(text, note["text"]):
            f.error("quote_not_found", w, "text is not a verbatim excerpt of note %s" % nid)
            continue
        if nid in seen:
            if need_unique:
                f.error("duplicate_quote", w, "note %s is cited twice in this theme; it counts once" % nid)
            continue
        seen.add(nid)
        if len(norm(text).split()) < SHORT_QUOTE_WORDS:
            f.warn("short_quote", w, "quote has under %d words; cite more of what the person said" % SHORT_QUOTE_WORDS)
        valid.append((pid, nid))
    return valid


def max_confidence(p, total_p, contra_p, min_p, min_q, n_quotes):
    if p < min_p or n_quotes < min_q:
        return None
    share = p / total_p if total_p else 0.0
    if p >= HIGH_MIN_P and share >= HIGH_MIN_SHARE:
        level = "high"
    elif p >= MEDIUM_MIN_P and share >= MEDIUM_MIN_SHARE:
        level = "medium"
    else:
        level = "low"
    if contra_p >= 1 and level == "high":
        level = "medium"          # any contradicting person caps at medium
    if contra_p >= 1 and 2 * contra_p >= p:
        level = "low"             # contradicted by half as many people as support it
    return level


def check_themes(data, notes, pids, args, f):
    if not isinstance(data, dict) or not isinstance(data.get("themes"), list) or not data["themes"]:
        raise Fatal('themes file must be an object with a non-empty "themes" list')
    th = data.get("thresholds") if isinstance(data.get("thresholds"), dict) else {}
    min_q = args.min_quotes if args.min_quotes is not None else th.get("min_quotes", DEFAULT_MIN_QUOTES)
    min_p = args.min_participants if args.min_participants is not None else th.get("min_participants", DEFAULT_MIN_PARTICIPANTS)
    max_share = args.max_share if args.max_share is not None else th.get("max_share", DEFAULT_MAX_SHARE)
    if not (isinstance(min_q, int) and isinstance(min_p, int) and isinstance(max_share, (int, float))):
        raise Fatal("thresholds must be integers (min_quotes, min_participants) and a number (max_share)")
    if min_q < FLOOR or min_p < FLOOR or min_q < min_p or not 0 < max_share <= 1:
        raise Fatal("invalid thresholds: need min_quotes >= min_participants >= %d and 0 < max_share <= 1" % FLOOR)
    if min_q < DEFAULT_MIN_QUOTES or min_p < DEFAULT_MIN_PARTICIPANTS:
        f.warn("threshold_lowered", "thresholds",
               "below the default %d quotes / %d participants; state why in the report" % (DEFAULT_MIN_QUOTES, DEFAULT_MIN_PARTICIPANTS))
    total_p = len(pids)
    seen_ids, cited, out = set(), set(), []
    for i, th_obj in enumerate(data["themes"]):
        if not isinstance(th_obj, dict):
            f.error("bad_theme", "themes[%d]" % i, "theme is not an object")
            continue
        tid = th_obj.get("id") if isinstance(th_obj.get("id"), str) and th_obj.get("id").strip() else None
        where = "theme %s" % (tid or "[%d]" % i)
        if tid is None:
            f.error("bad_theme", where, "theme has no string id")
        elif tid in seen_ids:
            f.error("duplicate_theme_id", where, "theme id used more than once")
        else:
            seen_ids.add(tid)
        for field in ("title", "statement"):
            if not isinstance(th_obj.get(field), str) or not th_obj[field].strip():
                f.error("missing_" + field, where, "theme has no %s" % field)
        declared = th_obj.get("confidence")
        if declared not in CONFIDENCE_ORDER:
            f.error("bad_confidence", where, "confidence must be high, medium or low, got %r" % (declared,))
        if "contradictions" not in th_obj:
            f.error("missing_contradictions_field", where,
                    'add "contradictions" (an empty list is allowed once you searched the notes for counter-evidence)')
        support = check_evidence_list(th_obj.get("quotes"), "quote", notes, f, where, True)
        contra = check_evidence_list(th_obj.get("contradictions", []), "contradiction", notes, f, where, False)
        sup_p = sorted({p for p, _ in support})
        con_p = sorted({p for p, _ in contra})
        n_quotes = len(support)
        if n_quotes < min_q or len(sup_p) < min_p:
            f.error("below_threshold", where,
                    "%d valid quotes from %d participants; needs at least %d quotes from %d participants"
                    % (n_quotes, len(sup_p), min_q, min_p))
        if n_quotes >= 3:
            for pid in sup_p:
                c = sum(1 for p, _ in support if p == pid)
                if c / n_quotes > max_share:
                    f.warn("participant_dominates_theme", where,
                           "%s supplies %d of %d quotes (%.0f%%, limit %.0f%%)"
                           % (pid, c, n_quotes, 100.0 * c / n_quotes, 100.0 * max_share))
        ceiling = max_confidence(len(sup_p), total_p, len(con_p), min_p, min_q, n_quotes)
        if ceiling and declared in CONFIDENCE_ORDER and CONFIDENCE_ORDER[declared] > CONFIDENCE_ORDER[ceiling]:
            f.error("confidence_overstated", where,
                    "declared %s but the evidence supports at most %s (%d of %d participants, %d contradicting)"
                    % (declared, ceiling, len(sup_p), total_p, len(con_p)))
        for field in ("title", "statement"):
            text = th_obj.get(field)
            if not isinstance(text, str):
                continue
            for m in COUNT_CLAIM.finditer(text):
                if (int(m.group(1)), int(m.group(2))) != (len(sup_p), total_p):
                    f.error("count_claim_mismatch", where,
                            "%s says %s of %s but the quotes show %d of %d participants"
                            % (field, m.group(1), m.group(2), len(sup_p), total_p))
            vague = VAGUE.search(text)
            if vague:
                f.warn("vague_quantifier", where,
                       "%s uses %r; state a count such as '%d of %d participants'" % (field, vague.group(0), len(sup_p), total_p))
        cited.update(p for p, _ in support)
        out.append({"id": tid, "quotes": n_quotes, "participants": sup_p, "contradicting_participants": con_p,
                    "declared_confidence": declared if declared in CONFIDENCE_ORDER else None,
                    "max_confidence": ceiling})
    return out, sorted(cited), {"min_quotes": min_q, "min_participants": min_p, "max_share": max_share}


def build_parser():
    ap = argparse.ArgumentParser(description="Validate tagged notes and a themes file; prints strict JSON.")
    ap.add_argument("notes")
    ap.add_argument("themes", nargs="?")
    ap.add_argument("--min-quotes", type=int)
    ap.add_argument("--min-participants", type=int)
    ap.add_argument("--max-share", type=float)
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    return ap


def emit(obj):
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        emit({"ok": False, "fatal": "bad arguments; see the usage in the script docstring"})
        return 2
    f = Findings()
    try:
        notes, pids = check_notes(load_json(args.notes), f)
        themes_out, cited, used = [], [], None
        if args.themes:
            themes_out, cited, used = check_themes(load_json(args.themes), notes, pids, args, f)
    except Fatal as exc:
        emit({"ok": False, "fatal": str(exc)})
        return 2
    f.items.sort(key=lambda x: SEV_ORDER[x["severity"]])
    errors, warnings = f.count("error"), f.count("warning")
    ok = errors == 0 and (warnings == 0 or not args.strict)
    emit({
        "ok": ok,
        "strict": bool(args.strict),
        "summary": {
            "notes": len(notes),
            "participants": len(pids),
            "untagged_notes": sum(1 for x in f.items if x["code"] == "untagged_note"),
            "themes": len(themes_out),
            "participants_never_cited": sorted(set(pids) - set(cited)) if args.themes else None,
            "errors": errors,
            "warnings": warnings,
            "thresholds": used,
        },
        "themes": themes_out,
        "findings": f.items,
    })
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
