#!/usr/bin/env python3
"""Validate an automated email sequence described in JSON and print a timeline.

Usage:
    python scripts/sequence_check.py validate <sequence.json> [--strict] [--min-gap DAYS]

Reads the one JSON file given. Writes nothing. No network, standard library only.
Stdout is always one strict JSON document (no NaN, ASCII only).

Exit codes:
    0  no FAIL findings (with --strict: no FAIL and no WARN findings)
    1  at least one FAIL finding (with --strict: or a WARN finding)
    2  usage error, missing/empty file, or the file is not a JSON object

Input shape (all fields are described in references/sequence_schema.md):
    {"sequence": {"name", "type", "trigger", "goal", "consent_basis", "sender": {...},
                  "exit_conditions": [...], "min_gap_days"?, "consent_evidence"?, "regions"?},
     "emails":   [{"id", "day", "job", "subject", "preheader", "cta": {"label", "url"},
                   "unsubscribe", "list_unsubscribe_header"?, "transactional"?,
                   "exit_conditions"?, "sender"?}]}

This script checks structure and surface patterns only. It cannot judge consent,
legal compliance, or whether the copy is any good.
"""
import json
import re
import sys

# Subject length. 78 is the line length RFC 5322 recommends for a header line, used here as the
# hard cap; 60 is a working value after which mobile inbox lists usually cut the subject.
SUBJECT_WARN = 60
SUBJECT_FAIL = 78
# Preheader text beyond about 100-130 characters is cut by most clients; 130 is a working value.
PREHEADER_WARN = 130
# Minimum days between consecutive emails per sequence type. Working values, not measured optima.
MIN_GAP = {"onboarding": 1.0, "nurture": 2.0, "winback": 3.0, "other": 2.0}
# A gap this long makes the recipient forget why they are receiving the email.
MAX_GAP_WARN = 30.0
# More than this many emails inside the first 7 days is a burst.
BURST_LIMIT = 4
# Very long sequences are rarely finished by anyone; working value.
LENGTH_WARN = 10

TYPES = ("onboarding", "nurture", "winback", "other")
CONSENT_BASES = ("express_consent", "double_opt_in", "existing_customer",
                 "legitimate_interest", "other")
BAD_BASES = ("purchased_list", "rented_list", "scraped", "unknown")
GOAL_WORDS = re.compile(r"purchas|bought|convert|book|upgrad|activat|complet|repl(y|ie)|paid|goal|order|renew|redeem|signed up", re.I)

# (code, pattern, level, message). Patterns are matched case-insensitively against the subject.
SPAM_PATTERNS = [
    ("subject-fake-reply", r"^\s*(re|fwd?)\s*:", "FAIL",
     "subject starts with Re:/Fwd: which fakes a prior conversation (deceptive subject)"),
    ("subject-money-symbols", r"\${2,}|\bmake money\b|\bearn \$|\bcash bonus\b", "WARN",
     "money-promise wording common in spam filters"),
    ("subject-urgency", r"\bact now\b|\bapply now\b|\bbuy now\b|\burgent\b|\blast chance\b|\bdon'?t miss\b|\bhurry\b", "WARN",
     "pressure wording common in spam filters"),
    ("subject-free-claims", r"\b100% free\b|\brisk[- ]free\b|\bno obligation\b|\bno strings\b|\bfree gift\b|\bfree money\b", "WARN",
     "free/no-risk claim wording common in spam filters"),
    ("subject-prize", r"\bwinner\b|\bcongratulations\b|\byou('ve| have) been selected\b|\bonce in a lifetime\b", "WARN",
     "prize wording common in spam filters"),
    ("subject-click-here", r"\bclick here\b|\bthis isn'?t spam\b|\bdear friend\b", "WARN",
     "stock spam phrase"),
    ("subject-guarantee", r"\bguarantee(d)?\b", "WARN",
     "guarantee wording: also a claim you must be able to back up"),
]


def finding(level, code, message, email=None):
    item = {"level": level, "code": code, "message": message}
    if email is not None:
        item["email"] = email
    return item


def is_num(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value == value \
        and value not in (float("inf"), float("-inf"))


def nonempty_str(value):
    return isinstance(value, str) and value.strip() != ""


def check_sender(sender, where, out, email=None):
    """Return True when the sender block is complete."""
    if not isinstance(sender, dict):
        out.append(finding("FAIL", "sender-missing", where + " has no sender block", email))
        return False
    ok = True
    for key, why in (("from_name", "recipients must see who the mail is from"),
                     ("from_email", "a real, monitored From address is required"),
                     ("postal_address", "a valid physical postal address is required by CAN-SPAM; verify with counsel")):
        if not nonempty_str(sender.get(key)):
            out.append(finding("FAIL", "sender-field-missing",
                               where + " sender." + key + " is missing or empty (" + why + ")", email))
            ok = False
    addr = sender.get("from_email")
    if nonempty_str(addr) and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", addr.strip()):
        out.append(finding("FAIL", "sender-email-invalid", where + " sender.from_email is not an email address", email))
        ok = False
    if nonempty_str(addr) and re.match(r"^(no-?reply|donotreply|do-not-reply)@", addr.strip(), re.I):
        out.append(finding("WARN", "sender-noreply",
                           where + " uses a no-reply From address; replies are a positive engagement signal", email))
    return ok


def check_subject(email_id, subject, out):
    if not nonempty_str(subject):
        out.append(finding("FAIL", "subject-missing", "subject is missing or empty", email_id))
        return
    n = len(subject.strip())
    if n > SUBJECT_FAIL:
        out.append(finding("FAIL", "subject-too-long",
                           "subject is %d characters; the cap is %d" % (n, SUBJECT_FAIL), email_id))
    elif n > SUBJECT_WARN:
        out.append(finding("WARN", "subject-long",
                           "subject is %d characters; over %d is usually cut on mobile" % (n, SUBJECT_WARN), email_id))
    if subject != subject.strip():
        out.append(finding("WARN", "subject-whitespace", "subject has leading or trailing spaces", email_id))
    for code, pattern, level, message in SPAM_PATTERNS:
        if re.search(pattern, subject, re.I):
            out.append(finding(level, code, message, email_id))
    caps = [w for w in re.findall(r"[A-Za-z]{4,}", subject) if w.isupper()]
    if caps:
        out.append(finding("WARN", "subject-all-caps",
                           "all-caps word(s): " + ", ".join(caps[:3]), email_id))
    if subject.count("!") > 1:
        out.append(finding("WARN", "subject-exclamations", "more than one exclamation mark", email_id))


def validate(doc, min_gap_arg=None):
    out = []
    timeline = []
    seq = doc.get("sequence")
    emails = doc.get("emails")
    if not isinstance(seq, dict):
        out.append(finding("FAIL", "schema-sequence", "top-level 'sequence' object is missing"))
        seq = {}
    if not isinstance(emails, list) or not emails:
        out.append(finding("FAIL", "schema-emails", "top-level 'emails' must be a non-empty list"))
        return out, timeline, 0
    # ---- sequence contract
    stype = seq.get("type")
    if stype not in TYPES:
        out.append(finding("FAIL", "sequence-type", "sequence.type must be one of " + ", ".join(TYPES)))
        stype = "other"
    for key in ("name", "trigger", "goal"):
        if not nonempty_str(seq.get(key)):
            out.append(finding("FAIL", "sequence-" + key + "-missing", "sequence." + key + " is missing or empty"))
    basis = seq.get("consent_basis")
    if basis in BAD_BASES:
        out.append(finding("FAIL", "consent-basis-unacceptable",
                           "consent_basis '%s' is not a basis to send marketing mail on; verify with counsel" % basis))
    elif basis not in CONSENT_BASES:
        out.append(finding("FAIL", "consent-basis-missing",
                           "sequence.consent_basis must be one of " + ", ".join(CONSENT_BASES)))
    elif basis in ("express_consent", "double_opt_in") and not nonempty_str(seq.get("consent_evidence")):
        out.append(finding("WARN", "consent-evidence-missing",
                           "no sequence.consent_evidence (where, when and how consent is recorded)"))
    regions = seq.get("regions")
    if isinstance(regions, list) and basis == "legitimate_interest" and \
            any(isinstance(r, str) and r.upper() in ("EU", "EEA", "UK", "GDPR") for r in regions):
        out.append(finding("WARN", "legitimate-interest-eu-uk",
                           "legitimate_interest with EU/UK recipients needs a documented balancing test; verify with counsel"))
    seq_sender_ok = check_sender(seq.get("sender"), "sequence", out)
    seq_exits = seq.get("exit_conditions")
    seq_exits_ok = isinstance(seq_exits, list) and any(nonempty_str(x) for x in seq_exits)
    if seq_exits_ok and not any(GOAL_WORDS.search(x) for x in seq_exits if isinstance(x, str)):
        out.append(finding("WARN", "exit-no-goal",
                           "no exit condition mentions the goal being reached; recipients who already converted keep getting emails"))
    # ---- cadence settings
    gap_min = MIN_GAP[stype]
    override = seq.get("min_gap_days", min_gap_arg)
    if min_gap_arg is not None and "min_gap_days" not in seq:
        override = min_gap_arg
    if override is not None:
        if is_num(override) and override >= 0:
            if override < MIN_GAP[stype]:
                out.append(finding("WARN", "min-gap-lowered",
                                   "minimum gap lowered to %s days from the %s default of %s" % (override, stype, MIN_GAP[stype])))
            gap_min = float(override)
        else:
            out.append(finding("FAIL", "min-gap-invalid", "min_gap_days must be a number of days, 0 or more"))
    # ---- emails
    seen_ids, seen_urls, seen_labels, seen_subjects = {}, {}, {}, {}
    prev_day = None
    in_first_week = 0
    if len(emails) > LENGTH_WARN:
        out.append(finding("WARN", "sequence-long", "%d emails; over %d is rarely finished by recipients" % (len(emails), LENGTH_WARN)))
    for idx, em in enumerate(emails):
        if not isinstance(em, dict):
            out.append(finding("FAIL", "schema-email", "emails[%d] is not an object" % idx))
            continue
        eid = em.get("id") if nonempty_str(em.get("id")) else "emails[%d]" % idx
        if not nonempty_str(em.get("id")):
            out.append(finding("FAIL", "email-id-missing", "email has no id", eid))
        elif eid in seen_ids:
            out.append(finding("FAIL", "email-id-duplicate", "id also used by emails[%d]" % seen_ids[eid], eid))
        else:
            seen_ids[eid] = idx
        day = em.get("day")
        if not is_num(day) or day < 0:
            out.append(finding("FAIL", "day-invalid", "day must be a number of days after the trigger, 0 or more", eid))
            day = None
        gap = None
        if day is not None:
            if prev_day is not None:
                gap = day - prev_day
                if gap < 0:
                    out.append(finding("FAIL", "order-wrong", "email is listed before an earlier one: day %s after day %s" % (day, prev_day), eid))
                elif gap < gap_min:
                    out.append(finding("FAIL", "gap-too-short",
                                       "%s days after the previous email; the %s minimum is %s" % (round(gap, 3), stype, gap_min), eid))
                elif gap > MAX_GAP_WARN:
                    out.append(finding("WARN", "gap-too-long", "%s days after the previous email; over %d days loses context" % (round(gap, 3), int(MAX_GAP_WARN)), eid))
            if day < 7:
                in_first_week += 1
            prev_day = day
        if not nonempty_str(em.get("job")):
            out.append(finding("FAIL", "job-missing", "email has no 'job' (the one thing it must do)", eid))
        elif re.search(r"\band\b.*\band\b|;|\bplus\b", em["job"], re.I):
            out.append(finding("WARN", "job-multiple", "job reads like more than one job; split the email or cut one", eid))
        check_subject(eid, em.get("subject"), out)
        subj = em.get("subject")
        if nonempty_str(subj):
            key = subj.strip().lower()
            if key in seen_subjects:
                out.append(finding("WARN", "subject-duplicate", "same subject as %s" % seen_subjects[key], eid))
            else:
                seen_subjects[key] = eid
        pre = em.get("preheader")
        if not nonempty_str(pre):
            out.append(finding("WARN", "preheader-missing", "no preheader; clients will show the first body text instead", eid))
        else:
            if len(pre.strip()) > PREHEADER_WARN:
                out.append(finding("WARN", "preheader-long", "preheader is %d characters; over %d is cut" % (len(pre.strip()), PREHEADER_WARN), eid))
            if nonempty_str(subj) and pre.strip().lower() == subj.strip().lower():
                out.append(finding("WARN", "preheader-repeats-subject", "preheader repeats the subject", eid))
        cta = em.get("cta")
        cta_label = None
        if em.get("ctas") is not None:
            out.append(finding("WARN", "cta-multiple", "'ctas' list found; an email gets one primary CTA", eid))
        if not isinstance(cta, dict) or not nonempty_str(cta.get("label")) or not nonempty_str(cta.get("url")):
            out.append(finding("FAIL", "cta-missing", "email needs cta.label and cta.url", eid))
        else:
            cta_label = cta["label"].strip()
            url = cta["url"].strip()
            if not re.match(r"^https://", url, re.I):
                out.append(finding("WARN", "cta-not-https", "CTA url is not https", eid))
            if re.search(r"^(click here|here|read more|learn more|submit)$", cta_label, re.I):
                out.append(finding("WARN", "cta-label-vague", "CTA label '%s' says nothing about the action" % cta_label, eid))
            url_key = url.split("#")[0].split("?")[0].rstrip("/").lower()
            if url_key in seen_urls:
                out.append(finding("WARN", "cta-duplicate-url", "same CTA destination as %s" % seen_urls[url_key], eid))
            else:
                seen_urls[url_key] = eid
            label_key = cta_label.lower()
            if label_key in seen_labels:
                out.append(finding("WARN", "cta-duplicate-label", "same CTA label as %s" % seen_labels[label_key], eid))
            else:
                seen_labels[label_key] = eid
        # unsubscribe
        transactional = em.get("transactional") is True
        if not transactional:
            if em.get("unsubscribe") is not True:
                out.append(finding("FAIL", "unsubscribe-missing", "marketing email must carry a working unsubscribe link (unsubscribe: true)", eid))
            if em.get("list_unsubscribe_header") is not True:
                out.append(finding("WARN", "list-unsubscribe-header", "no List-Unsubscribe header (one-click) declared; large senders need it; verify current mailbox-provider rules", eid))
        # sender
        if "sender" in em:
            check_sender(em.get("sender"), "email", out, eid)
        elif not seq_sender_ok:
            out.append(finding("FAIL", "sender-missing", "no usable sender on the email or on the sequence", eid))
        # exits
        own = em.get("exit_conditions")
        own_ok = isinstance(own, list) and any(nonempty_str(x) for x in own)
        if "exit_conditions" in em and not own_ok and not isinstance(own, list):
            out.append(finding("FAIL", "exit-invalid", "exit_conditions must be a list of strings", eid))
        elif not own_ok and not seq_exits_ok:
            out.append(finding("FAIL", "exit-missing", "no exit condition on the email or on the sequence", eid))
        timeline.append({
            "day": day,
            "gap_days": None if gap is None else round(gap, 3),
            "id": eid,
            "subject": subj if isinstance(subj, str) else None,
            "cta": cta_label,
            "job": em.get("job") if isinstance(em.get("job"), str) else None,
            "exits": "own" if own_ok else ("sequence" if seq_exits_ok else "none"),
        })
    if in_first_week > BURST_LIMIT:
        out.append(finding("WARN", "burst", "%d emails in the first 7 days; more than %d reads as a burst" % (in_first_week, BURST_LIMIT)))
    return out, timeline, len(emails)


def report(payload):
    sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=True, allow_nan=False) + "\n")


def main(argv):
    args = list(argv)
    strict = False
    min_gap = None
    try:
        if "--strict" in args:
            strict = True
            args.remove("--strict")
        if "--min-gap" in args:
            i = args.index("--min-gap")
            min_gap = float(args[i + 1])
            del args[i:i + 2]
    except (IndexError, ValueError):
        report({"command": "validate", "ok": False, "error": "--min-gap needs a number of days"})
        return 2
    if len(args) != 2 or args[0] != "validate":
        report({"command": "validate", "ok": False,
                "error": "usage: sequence_check.py validate <sequence.json> [--strict] [--min-gap DAYS]"})
        return 2
    path = args[1]
    try:
        with open(path, encoding="utf-8-sig") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        report({"command": "validate", "file": path, "ok": False, "error": "cannot read file: " + str(exc)})
        return 2
    if not text.strip():
        report({"command": "validate", "file": path, "ok": False, "error": "file is empty"})
        return 2
    try:
        doc = json.loads(text)
    except ValueError as exc:
        report({"command": "validate", "file": path, "ok": False, "error": "not valid JSON: " + str(exc)})
        return 2
    if not isinstance(doc, dict):
        report({"command": "validate", "file": path, "ok": False, "error": "top level must be a JSON object with 'sequence' and 'emails'"})
        return 2
    findings, timeline, count = validate(doc, min_gap)
    fails = sum(1 for f in findings if f["level"] == "FAIL")
    warns = sum(1 for f in findings if f["level"] == "WARN")
    ok = fails == 0 and (warns == 0 or not strict)
    report({
        "command": "validate",
        "file": path,
        "ok": ok,
        "strict": strict,
        "summary": {"emails": count, "fail": fails, "warn": warns},
        "findings": findings,
        "timeline": timeline,
        "not_checked": ["consent actually obtained", "legal compliance in any jurisdiction",
                        "copy quality", "rendering and deliverability in real inboxes"],
    })
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
