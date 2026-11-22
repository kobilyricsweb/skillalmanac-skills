#!/usr/bin/env python3
"""Check discovery-call notes and, optionally, the follow-up email drafted from them.

    python scripts/call_check.py NOTES [FOLLOWUP] [--min-coverage N] [--pretty]

NOTES     Markdown (.md/.txt) or JSON (.json) call notes. See SKILL.md for the layout.
FOLLOWUP  Markdown/plain text, or JSON {"subject": "...", "body": "..."}. Optional;
          without it only the notes are checked (use this before the call to check
          the plan, after the call to check the notes).

Reads only the files given. Writes nothing. No network. Prints ONE strict JSON object
on stdout (no NaN, no trailing text). Exit codes: 0 no error-level finding,
1 at least one error-level finding, 2 usage or unreadable input (JSON with "error").

What it checks:
  * every follow-up sentence that promises something ("I'll send", "we can", "you will")
    is backed by a line in the notes commitments or next-step section
  * every price, percentage, count-with-unit, calendar date and weekday in the follow-up
    also appears in the notes
  * the next step has an action, ONE named owner and a calendar date, and the follow-up
    repeats the date and the owner
  * which of the five discovery fields (situation, problem, impact, decision process,
    next step) are unanswered, and a 0-100 question-plan coverage score
"""
import argparse
import datetime
import json
import os
import re
import sys

VERSION = "1.0.0"
STAGES = ["situation", "problem", "impact", "decision_process", "next_step"]

# Heading / label aliases, matched after lower-casing and replacing non-letters with spaces.
ALIASES = {
    "situation": "situation", "current situation": "situation", "current state": "situation",
    "background": "situation", "context": "situation",
    "problem": "problem", "problems": "problem", "pain": "problem", "pain points": "problem",
    "challenge": "problem", "challenges": "problem",
    "impact": "impact", "implication": "impact", "implications": "impact",
    "business impact": "impact", "cost of problem": "impact", "cost": "impact",
    "decision process": "decision_process", "decision": "decision_process",
    "buying process": "decision_process", "decision making": "decision_process",
    "decision criteria": "decision_process",
    "next step": "next_step", "next steps": "next_step", "agreed next step": "next_step",
    "question plan": "question_plan", "questions": "question_plan", "call plan": "question_plan",
    "commitments": "commitments", "commitments made": "commitments", "promises": "commitments",
    "action items": "commitments",
}

# A field with fewer words than this is treated as unanswered: "Slow." answers nothing.
MIN_FIELD_WORDS = 3
PLACEHOLDER = re.compile(
    r"^(tbd|tbc|n/?a|none|unknown|todo|to do|\?+|-+|\.+|not (asked|discussed|covered|answered|sure)|didn'?t ask|no answer)\.?$",
    re.I,
)
# Coverage points per stage: planned 1, asked 1, answered 2 (max 4 per stage, 20 total).
POINTS_PLANNED, POINTS_ASKED, POINTS_ANSWERED = 1, 1, 2
# Follow-ups over this many words stop being read; warn (it is advice, not an error).
MAX_FOLLOWUP_WORDS = 200

MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august",
          "september", "october", "november", "december"]
MONTH_NUM = {}
for _i, _m in enumerate(MONTHS, 1):
    MONTH_NUM[_m] = _i
    MONTH_NUM[_m[:3]] = _i
MONTH_NUM["sept"] = 9
_MON_RE = "|".join(sorted(MONTH_NUM, key=len, reverse=True))
ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
MONTH_DAY = re.compile(r"\b(" + _MON_RE + r")\.?\s+(\d{1,2})(?:st|nd|rd|th)?\b(?!\s*(?:%|days?|weeks?|users?|seats?))", re.I)
DAY_MONTH = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(" + _MON_RE + r")\b", re.I)
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
WEEKDAY_RE = re.compile(r"\b(" + "|".join(WEEKDAYS) + r")\b", re.I)

VAGUE_DATE = re.compile(
    r"\b(next week|this week|soon|asap|sometime|later|in a few days|a couple of days|"
    r"end of (?:the )?(?:week|month|quarter)|early next|after the holidays|when (?:you|they|we) can|tbd)\b",
    re.I,
)
NON_OWNER = {"both", "we", "team", "tbd", "?", "unknown", "someone", "everyone", "all", "n/a", "none"}
OWNER_STOP = {"us", "them", "we", "me", "prospect", "customer", "buyer", "seller", "our", "their", "team",
              "from", "at", "of", "the", "and", "rep", "client", "to", "for"}

# Phrases that sound like promises but commit to nothing specific; skipped by the commitment check.
BENIGN = re.compile(
    r"(be in touch|keep you posted|let you know|happy to (?:help|answer|clarify)|look forward|reach out|"
    r"see you|talk soon|speak soon|thank|appreciate|will be brief|can help|can answer)",
    re.I,
)
CUE_FIRST = re.compile(
    r"\b(?:i|we)(?:'ll| will| shall| can| promise| guarantee| commit)\b|\blet me (?:send|arrange|set up|get)\b|"
    r"\bwill (?:send|share|follow|set up|provide|get|loop|schedule|introduce|connect|arrange|have|include|"
    r"deliver|cover|waive|extend|match|confirm)\b|\b(?:guarantee[sd]?|promise[sd]?)\b",
    re.I,
)
PRON_FIRST = re.compile(r"\b(?:i|we)(?:'ll| will| shall| can| promise| guarantee| commit)\b|\blet me\b", re.I)
CUE_SECOND = re.compile(r"\byou(?:'ll| will)\b", re.I)
FIRST_PERSON_OWNER = re.compile(r"\b(?:i|we)(?:'ll| will)\b", re.I)
SECOND_PERSON_OWNER = re.compile(r"\byou(?:'ll| will| to)\b|\byour team\b", re.I)
RISKY = re.compile(
    r"\b(guarantee[sd]?|free of charge|free trial|free|discount|waive[sd]?|unlimited|no risk|"
    r"lowest price|best price|price match|roadmap|exclusive)\b",
    re.I,
)

# Words ignored when matching a follow-up promise against a notes commitment.
STOP = set("""the and for with will can you your our that this have has from they them their also would should
please then just over about into out are was been were shall per any all one but not who how what let know
get got its it's i'll we'll you'll there here some more very can't won't""".split())

CURRENCY = re.compile(r"[$€£]\s?\d[\d,]*(?:\.\d+)?\s?[kKmM]?\b")
PERCENT = re.compile(r"\b\d+(?:\.\d+)?\s?%")
QUANTITY = re.compile(
    r"\b(\d[\d,]*(?:\.\d+)?)\s?(days?|weeks?|months?|hours?|minutes?|users?|seats?|licen[sc]es?|people|reps|"
    r"employees|customers|accounts)\b",
    re.I,
)


class InputError(Exception):
    pass


def read_text(path, what):
    if not os.path.isfile(path):
        raise InputError("%s file not found: %s" % (what, path))
    raw = open(path, "rb").read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    text = text.replace("’", "'").replace("‘", "'")
    if not text.strip():
        raise InputError("%s file is empty: %s" % (what, path))
    return text


def stage_key(label):
    return ALIASES.get(re.sub(r"[^a-z]+", " ", label.lower()).strip())


def words(text):
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'%$.,/-]*", text)


def is_unanswered(text):
    flat = re.sub(r"[*_`>#\-\s]+", " ", text).strip()
    if not flat or PLACEHOLDER.match(flat):
        return "empty or placeholder"
    if len(words(flat)) < MIN_FIELD_WORDS:
        return "fewer than %d words" % MIN_FIELD_WORDS
    return None


# ---------- notes parsing ----------

def parse_notes_markdown(text):
    sections, plan, commitments = {}, [], []
    current = None
    heading = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
    plan_line = re.compile(r"^\s*[-*]\s*(?:\[([ xX])\]\s*)?([A-Za-z_ ]+?)\s*:\s*(.+)$")
    commit_line = re.compile(r"^\s*[-*]\s*[\[(]?(us|we|me|them|prospect|customer|buyer|both)[\])]?\s*:?\s+(.+)$", re.I)
    unknown_plan = []
    for n, line in enumerate(text.splitlines(), 1):
        m = heading.match(line)
        if m:
            current = stage_key(m.group(1)) or "other"
            sections.setdefault(current, [])
            continue
        if current is None:
            continue
        sections.setdefault(current, []).append(line)
        if current == "question_plan":
            pm = plan_line.match(line)
            if pm:
                stage = stage_key(pm.group(2))
                if stage in STAGES:
                    plan.append({"stage": stage, "asked": (pm.group(1) or " ").lower() == "x", "question": pm.group(3).strip(), "line": n})
                else:
                    unknown_plan.append(n)
        elif current == "commitments":
            cm = commit_line.match(line)
            if cm:
                commitments.append({"party": cm.group(1).lower(), "text": cm.group(2).strip(), "line": n})
            elif line.strip().startswith(("-", "*")):
                commitments.append({"party": "unknown", "text": line.strip().lstrip("-* ").strip(), "line": n})
    return {"sections": {k: "\n".join(v).strip() for k, v in sections.items()},
            "plan": plan, "commitments": commitments, "unknown_plan_lines": unknown_plan, "full_text": text}


def parse_notes_json(text):
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise InputError("notes JSON is not valid: %s" % exc)
    if not isinstance(data, dict):
        raise InputError("notes JSON must be an object")
    fields = data.get("fields") or {}
    sections = {}
    for key in STAGES:
        value = fields.get(key, "")
        sections[key] = value if isinstance(value, str) else json.dumps(value)
    ns = data.get("next_step")
    if isinstance(ns, dict):
        sections["next_step"] = "\n".join("%s: %s" % (k.capitalize(), ns[k]) for k in ("action", "owner", "date") if ns.get(k))
    plan = []
    for i, item in enumerate(data.get("question_plan") or [], 1):
        stage = stage_key(str(item.get("stage", ""))) if isinstance(item, dict) else None
        if stage in STAGES:
            plan.append({"stage": stage, "asked": bool(item.get("asked")), "question": str(item.get("question", "")), "line": i})
    commitments = []
    for i, item in enumerate(data.get("commitments") or [], 1):
        if isinstance(item, dict):
            commitments.append({"party": str(item.get("party", "unknown")).lower(), "text": str(item.get("text", "")), "line": i})
    flat = []

    def walk(v):
        if isinstance(v, str):
            flat.append(v)
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(data)
    return {"sections": sections, "plan": plan, "commitments": commitments, "unknown_plan_lines": [], "full_text": "\n".join(flat)}


def load_notes(path):
    text = read_text(path, "notes")
    if path.lower().endswith(".json"):
        return parse_notes_json(text)
    return parse_notes_markdown(text)


def load_followup(path):
    text = read_text(path, "follow-up")
    if path.lower().endswith(".json"):
        try:
            data = json.loads(text)
        except ValueError as exc:
            raise InputError("follow-up JSON is not valid: %s" % exc)
        if isinstance(data, dict):
            text = "%s\n%s" % (data.get("subject", ""), data.get("body", ""))
        elif isinstance(data, str):
            text = data
        else:
            raise InputError("follow-up JSON must be an object with subject/body or a string")
    return text


# ---------- dates and figures ----------

def date_keys(text):
    """Return (valid MM-DD keys, invalid raw strings, ISO dates as date objects)."""
    keys, invalid, isos = set(), [], []

    def add(month, day, raw, year=None):
        try:
            datetime.date(year or 2000, month, day)
        except ValueError:
            invalid.append(raw)
            return
        keys.add("%02d-%02d" % (month, day))
        if year:
            isos.append(datetime.date(year, month, day))

    for m in ISO_DATE.finditer(text):
        add(int(m.group(2)), int(m.group(3)), m.group(0), int(m.group(1)))
    for m in MONTH_DAY.finditer(text):
        add(MONTH_NUM[m.group(1).lower()], int(m.group(2)), m.group(0))
    for m in DAY_MONTH.finditer(text):
        add(MONTH_NUM[m.group(2).lower()], int(m.group(1)), m.group(0))
    return keys, invalid, isos


def figures(text):
    """Normalised figures: price, percent, quantity+unit, date (d:MM-DD), weekday (wd:name)."""
    found = {}
    for m in CURRENCY.finditer(text):
        found["amount:" + re.sub(r"[\s,]", "", m.group(0)).lower()] = m.group(0).strip()
    for m in PERCENT.finditer(text):
        found["percent:" + re.sub(r"\s", "", m.group(0))] = m.group(0).strip()
    for m in QUANTITY.finditer(text):
        found["qty:%s %s" % (m.group(1).replace(",", ""), m.group(2).lower().rstrip("s"))] = m.group(0).strip()
    keys, _, isos = date_keys(text)
    for k in keys:
        found["date:" + k] = "%s %d" % (MONTHS[int(k[:2]) - 1][:3].title(), int(k[3:]))
    for m in WEEKDAY_RE.finditer(text):
        found["weekday:" + m.group(1).lower()] = m.group(1)
    for d in isos:
        found["weekday:" + WEEKDAYS[d.weekday()]] = WEEKDAYS[d.weekday()]
    return found


def figures_label(key, raw):
    return raw if not key.startswith("date:") else "date " + raw


# ---------- sentence and token helpers ----------

def sentences(text):
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith(">") or re.match(r"^(subject|to|from|cc)\s*:", line, re.I):
            continue
        line = re.sub(r"^[-*\d.)\s]+", "", line)
        for part in re.split(r"(?<=[.!?])\s+", line):
            part = part.strip()
            if part:
                out.append((n, part))
    return out


def content_tokens(text):
    text = ISO_DATE.sub(" ", text)
    text = MONTH_DAY.sub(" ", text)
    text = DAY_MONTH.sub(" ", text)
    text = WEEKDAY_RE.sub(" ", text)
    toks = set()
    for w in re.findall(r"[a-z][a-z']+", text.lower()):
        if w in STOP or w in MONTH_NUM or len(w) < 3:
            continue
        toks.add(w[:5])
    return toks


def party_side(party):
    if party in ("us", "we", "me"):
        return "us"
    if party in ("them", "prospect", "customer", "buyer"):
        return "them"
    return "any"


# ---------- checks ----------

def finding(sev, code, message, **extra):
    f = {"severity": sev, "code": code, "message": message}
    f.update(extra)
    return f


def check_fields(notes, findings):
    unanswered, detail = [], {}
    for stage in STAGES:
        reason = is_unanswered(notes["sections"].get(stage, ""))
        detail[stage] = "answered" if reason is None else "unanswered (%s)" % reason
        if reason:
            unanswered.append(stage)
            findings.append(finding("warn", "unanswered_field", "Discovery field '%s' is unanswered: %s." % (stage, reason), field=stage))
    impact = notes["sections"].get("impact", "")
    if "impact" not in unanswered and not re.search(r"\d", impact):
        findings.append(finding("warn", "impact_not_quantified",
                                "Impact has no number (money, hours, deals, headcount). Record the figure or write who could supply it.", field="impact"))
    dp = notes["sections"].get("decision_process", "")
    if "decision_process" not in unanswered:
        gaps = []
        if not re.search(r"\b(decide[sr]?|approv\w*|sign\w*|sponsor|cfo|ceo|cto|vp|director|head of|committee|board|procurement|legal|security review)\b", dp, re.I):
            gaps.append("who decides or approves")
        if not re.search(r"\b(by|before|quarter|q[1-4]|month|week|date|deadline|renewal|\d{4}-\d{2}-\d{2})\b", dp, re.I):
            gaps.append("timeline")
        if not re.search(r"\b(budget|funded|funding|approved|spend|price|cost|\$|procurement)\b", dp, re.I):
            gaps.append("budget or paperwork")
        for g in gaps:
            findings.append(finding("warn", "decision_process_gap", "Decision process says nothing about %s." % g, field="decision_process"))
    return unanswered, detail


def check_coverage(notes, findings):
    per_stage, total = {}, 0
    for stage in STAGES:
        items = [p for p in notes["plan"] if p["stage"] == stage]
        planned = bool(items)
        asked = any(p["asked"] for p in items)
        answered = is_unanswered(notes["sections"].get(stage, "")) is None
        pts = (POINTS_PLANNED if planned else 0) + (POINTS_ASKED if asked else 0) + (POINTS_ANSWERED if answered else 0)
        total += pts
        per_stage[stage] = {"planned": planned, "asked": asked, "answered": answered, "points": pts}
        if not planned:
            findings.append(finding("warn", "no_plan_for_stage", "No planned question for stage '%s'." % stage, field=stage))
    for n in notes["unknown_plan_lines"]:
        findings.append(finding("warn", "plan_line_unrecognized",
                                "Question-plan line is not '- [x] stage: question' with a known stage.", line=n))
    max_pts = (POINTS_PLANNED + POINTS_ASKED + POINTS_ANSWERED) * len(STAGES)
    return round(100.0 * total / max_pts, 1), per_stage


def check_next_step(notes, findings):
    text = notes["sections"].get("next_step", "")
    info = {"action": None, "owner": None, "date": None, "owner_side": "any"}
    if is_unanswered(text):
        findings.append(finding("error", "next_step_missing", "No next step is recorded. End every call with an action, one owner and a calendar date."))
        return info, None
    lab = lambda names: re.search(r"(?im)^\s*(?:[-*]\s*)?(?:%s)\s*:\s*(.+)$" % names, text)
    a, o, d = lab("action|what"), lab("owner|who"), lab("date|when|due|by")
    info["action"] = a.group(1).strip() if a else text.strip().splitlines()[0].strip("-* ")
    owner = o.group(1).strip() if o else None
    if not owner:
        fm = re.search(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+(?:to|will)\b", text)
        owner = fm.group(1) if fm else None
    info["owner"] = owner
    date_text = d.group(1) if d else text
    info["date"] = date_text.strip() if d else None
    if not owner or owner.lower().strip(" .") in NON_OWNER:
        findings.append(finding("error", "next_step_no_owner", "Next step has no single named owner (found: %r)." % owner, field="next_step"))
    else:
        low = owner.lower()
        if re.search(r"\b(us|me|we|our|seller|rep)\b", low):
            info["owner_side"] = "us"
        elif re.search(r"\b(them|prospect|customer|buyer|their|client)\b", low):
            info["owner_side"] = "them"
    keys, invalid, _ = date_keys(date_text)
    for raw in invalid:
        findings.append(finding("error", "next_step_invalid_date", "Next step date %r is not a real calendar date." % raw, field="next_step"))
    if not keys and not invalid:
        vague = VAGUE_DATE.search(text)
        weekday = WEEKDAY_RE.search(date_text)
        why = "vague wording %r" % vague.group(0) if vague else ("weekday %r without a calendar date" % weekday.group(0) if weekday else "no date found")
        findings.append(finding("error", "next_step_no_date", "Next step has no calendar date (%s). Use YYYY-MM-DD or 'Nov 19'." % why, field="next_step"))
    return info, keys


def check_followup(notes, followup, ns_info, ns_keys, findings):
    words_n = len(words(followup))
    if words_n < 15:
        findings.append(finding("error", "followup_empty", "Follow-up has %d words; there is nothing to check or send." % words_n))
    if words_n > MAX_FOLLOWUP_WORDS:
        findings.append(finding("warn", "followup_too_long", "Follow-up is %d words; keep it under %d." % (words_n, MAX_FOLLOWUP_WORDS)))
    notes_fig = figures(notes["full_text"])
    for key, raw in sorted(figures(followup).items()):
        if key not in notes_fig:
            findings.append(finding("error", "figure_not_in_notes", "Follow-up states %s, which is not in the notes." % figures_label(key, raw), figure=raw))
    notes_low = notes["full_text"].lower()
    cleaned = re.sub(r"feel free", " ", followup, flags=re.I)
    seen = set()
    for m in RISKY.finditer(cleaned):
        term = m.group(1).lower()
        if term not in seen and term not in notes_low:
            seen.add(term)
            findings.append(finding("warn", "risky_term_not_in_notes", "Follow-up uses %r; the notes never mention it." % term, term=term))
    sources = list(notes["commitments"])
    ns_text = notes["sections"].get("next_step", "")
    if ns_text.strip():
        sources.append({"party": ns_info.get("owner_side", "any"), "text": ns_text, "line": 0})
    if not notes["commitments"]:
        findings.append(finding("warn", "commitments_section_empty", "Notes have no '## Commitments made' list; promises can only be matched against the next step."))
    for n, sent in sentences(followup):
        if sent.endswith("?") or BENIGN.search(sent):
            continue
        first, second = bool(CUE_FIRST.search(sent)), bool(CUE_SECOND.search(sent))
        if not (first or second):
            continue
        # Whose promise is it? "you will" is the prospect's; "I'll/we can" is ours; anything else matches either side.
        pron_first = bool(PRON_FIRST.search(sent))
        side = "them" if second and not pron_first else ("us" if pron_first and not second else "any")
        toks = content_tokens(sent)
        if not toks:
            continue
        best = 0.0
        for src in sources:
            ps = party_side(src["party"]) if src["party"] != "unknown" else "any"
            if "any" not in (ps, side) and ps != side:
                continue
            overlap = len(toks & content_tokens(src["text"])) / float(len(toks))
            best = max(best, overlap)
        if best < 0.5:
            findings.append(finding("error", "commitment_not_in_notes",
                                    "Follow-up commits to something the notes do not record (best match %.0f%%)." % (100 * best),
                                    line=n, text=sent))
    low = followup.lower()
    if ns_keys:
        fkeys, _, _ = date_keys(followup)
        if not (ns_keys & fkeys):
            findings.append(finding("error", "followup_missing_next_step_date", "Follow-up does not repeat the agreed next-step date."))
    owner = ns_info.get("owner")
    if owner:
        toks = [t for t in re.findall(r"[a-z]{2,}", owner.lower()) if t not in OWNER_STOP]
        named = any(re.search(r"\b%s\b" % re.escape(t), low) for t in toks)
        side = ns_info.get("owner_side", "any")
        pronoun = (side == "us" and FIRST_PERSON_OWNER.search(followup)) or (side == "them" and SECOND_PERSON_OWNER.search(followup))
        if (toks or side != "any") and not (named or pronoun):
            findings.append(finding("error", "followup_missing_next_step_owner", "Follow-up does not say who owns the next step (%s)." % owner))


def run(notes_path, followup_path, min_coverage):
    notes = load_notes(notes_path)
    followup = load_followup(followup_path) if followup_path else None
    findings = []
    unanswered, field_detail = check_fields(notes, findings)
    score, per_stage = check_coverage(notes, findings)
    if score < min_coverage:
        findings.append(finding("error", "coverage_below_min", "Question-plan coverage %.1f is below the required %.1f." % (score, min_coverage)))
    ns_info, ns_keys = check_next_step(notes, findings)
    if followup is not None:
        check_followup(notes, followup, ns_info, ns_keys or set(), findings)
    errors = sum(1 for f in findings if f["severity"] == "error")
    warns = len(findings) - errors
    return {
        "tool": "call_check", "version": VERSION, "ok": errors == 0,
        "verdict": "pass" if errors == 0 else "needs_work",
        "followup_checked": followup is not None,
        "coverage_score": score, "coverage_by_stage": per_stage,
        "fields": field_detail, "unanswered_fields": unanswered,
        "next_step": {"action": ns_info["action"], "owner": ns_info["owner"], "date": ns_info["date"]},
        "counts": {"error": errors, "warn": warns},
        "findings": findings,
    }


def emit(obj, pretty):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, allow_nan=False, indent=2 if pretty else None, sort_keys=True) + "\n")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass
    parser = argparse.ArgumentParser(description="Check call notes and a follow-up draft.")
    parser.add_argument("notes")
    parser.add_argument("followup", nargs="?")
    parser.add_argument("--min-coverage", type=float, default=0.0, help="error if coverage score is lower (0-100)")
    parser.add_argument("--pretty", action="store_true")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code:
            emit({"tool": "call_check", "ok": False, "error": "usage: call_check.py NOTES [FOLLOWUP] [--min-coverage N] [--pretty]"}, False)
            return 2
        return 0
    try:
        report = run(args.notes, args.followup, args.min_coverage)
    except InputError as exc:
        emit({"tool": "call_check", "ok": False, "error": str(exc)}, False)
        return 2
    emit(report, args.pretty)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
