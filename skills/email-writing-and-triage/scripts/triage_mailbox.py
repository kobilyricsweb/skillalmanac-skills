#!/usr/bin/env python3
"""Classify an exported mailbox into triage categories and flag deadlines.

    python triage_mailbox.py triage <export> [--me a@x.com,b@y.com] [--today YYYY-MM-DD]
    python triage_mailbox.py check  <triage.json>

`triage` reads a JSON export (a list of messages, or {"messages": [...]}) or an
mbox-like text file (every message starts with a line beginning "From ", then
RFC 5322 headers, a blank line and the body). It prints one JSON object (the
triage table) to stdout. It reads the one file it is given, writes nothing,
uses no network and sends nothing. Message bodies are not copied to the output.

`check` validates a saved triage table against the strict contract below.

Exit codes
    triage: 0 = table produced; 2 = usage error, unreadable file, empty file,
            or no message could be parsed
    check:  0 = table is valid; 1 = table is invalid (errors listed in JSON);
            2 = usage error or unreadable file

JSON input fields per message (all optional except one of body/text):
    id, from, to (string or list), cc, subject, date, body | text,
    headers (object, any of: reply-to, bcc, list-unsubscribe, list-id,
    precedence, auto-submitted), attachments (list or count)

Output contract (schema_version 1)
    {"schema_version": 1, "command": "triage", "source": str,
     "format": "json" | "mbox", "me_known": bool,
     "reference_date": "YYYY-MM-DD" | null, "message_count": int,
     "counts_by_category": {category: int for every category},
     "messages": [{"id": str, "index": int, "from": str, "subject": str,
        "date": "YYYY-MM-DD" | null, "thread": str, "category": category,
        "reply_action": "draft" | "follow_up" | "do_not_reply" | "none",
        "flags": [flag], "reasons": [str],
        "deadlines": [{"text": str, "kind": "absolute" | "relative" |
            "weekday" | "window" | "immediate", "resolved_date":
            "YYYY-MM-DD" | null, "days_left": int | null}]}],
     "queue": [id], "quarantine": [id], "warnings": [str]}
    categories: suspicious automated urgent_reply reply fyi waiting_on_them sent
    The rules behind every category and flag are in references/triage-rules.md.
"""
import argparse
import calendar
import datetime as dt
import email
import email.header
import email.policy
import email.utils
import json
import re
import sys

SCHEMA_VERSION = 1
CATEGORIES = ("suspicious", "automated", "urgent_reply", "reply", "fyi", "waiting_on_them", "sent")
REPLY_ACTIONS = ("draft", "follow_up", "do_not_reply", "none")
KINDS = ("absolute", "relative", "weekday", "window", "immediate")
FLAGS = (
    "deadline", "overdue", "immediate", "money_mentioned", "reply_all_risk", "mass_recipient",
    "attachment", "bcc_header", "no_date", "stale_followup", "own_deadline_commitment",
)

# A deadline this close (calendar days from the reference date) makes a reply urgent.
# Two days lets a "by Thursday" mail on Tuesday surface before it becomes overdue.
URGENT_DAYS = 2
# A sent message that asked something and got no answer after this many days earns a follow-up.
STALE_FOLLOWUP_DAYS = 3
# More than this many To+Cc addresses marks a broadcast; reply-all there reaches strangers.
MASS_RECIPIENTS = 10
# Two or more other people on a thread is where reply-all leaks recipients by accident.
REPLY_ALL_OTHERS = 2
# Longest stretch before a date expression that may hold its cue word ("by", "before").
CUE_WINDOW = 40
# Suspicious needs a total weight of at least this: one strong signal or two weak ones.
SUSPICIOUS_SCORE = 2
MAX_DEADLINES = 5

MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MONTHS.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})
MONTHS["sept"] = 9
WEEKDAYS = {n.lower(): i for i, n in enumerate(calendar.day_name)}
_MONTH_ALT = "|".join(sorted(MONTHS, key=len, reverse=True))
_DAY_ALT = "|".join(WEEKDAYS)

RE_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
RE_MONTH_DAY = re.compile(r"\b(" + _MONTH_ALT + r")\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?\b")
RE_DAY_MONTH = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(" + _MONTH_ALT + r")\b(?:,?\s+(\d{4}))?")
RE_REL_DAY = re.compile(r"\b(today|tonight|tomorrow)\b")
RE_WEEKDAY = re.compile(r"\b(?:(next|this|coming)\s+)?(" + _DAY_ALT + r")\b")
RE_END_OF = re.compile(r"\b(?:end of (?:the )?(week|month)|(eow|eom))\b")
RE_EOD = re.compile(r"\b(eod|cob|end of (?:the )?(?:business )?day|close of business|end of business)\b")
RE_WITHIN = re.compile(r"\bwithin\s+(\d{1,3})\s+(business days?|working days?|days?|hours?|weeks?)\b")
RE_IMMEDIATE = re.compile(r"\b(asap|as soon as possible|urgent(?:ly)?|time[- ]sensitive)\b")
RE_CUE = re.compile(r"\b(by|before|until|till|due(?! to)|deadline|no later than|on or before|expires?|closes?|cut-?off|latest)\b")
RE_CUE_AFTER = re.compile(r"\W{0,3}(?:at the latest|is the (?:deadline|cut-?off)|is due|deadline)")

RE_QUESTION = re.compile(r"\?(?:\s|$)")
REQUEST_PHRASES = (
    "can you", "could you", "would you", "will you", "are you able", "do you have", "let me know",
    "need you to", "need your", "send me", "send over", "kindly", "get back to me", "your thoughts",
    "waiting for your", "action required", "please confirm", "reply by", "please reply", "please send",
)
RE_PLEASE = re.compile(r"\bplease\b(?!\s+(?:find|see|note|be advised|disregard|ignore))")

STRONG_SUSPICIOUS = (
    ("gift_card", re.compile(r"\bgift ?cards?\b")),
    ("bank_details_change", re.compile(r"(?:new|updated|changed|change of) (?:bank|account|payment) (?:details|number|information)|bank details (?:have )?changed")),
    ("credential_request", re.compile(
        r"\b(?:send|reply with|share|provide|confirm|enter|verify|update|log ?in|sign ?in)\b.{0,40}\b(?:password|passcode|credentials|one[- ]time code|verification code|2fa code)\b"
        r"|\b(?:password|passcode|credentials|one[- ]time code|verification code|2fa code)\b.{0,40}\b(?:send|reply|share|provide|confirm|enter|verify|update)\b")),
    ("crypto_payment", re.compile(r"\b(?:bitcoin|crypto(?:currency)?|usdt)\b.{0,40}\b(?:pay|send|transfer)\b")),
    ("urgent_wire", re.compile(r"\bwire\b.{0,30}\b(?:today|urgent|immediately|asap)\b")),
)
WEAK_SUSPICIOUS = (
    ("account_locked", re.compile(r"account (?:has been |will be |is )?(?:suspended|locked|disabled|closed)")),
    ("verify_account", re.compile(r"verify your (?:account|identity|email)")),
    ("click_link", re.compile(r"click (?:the |this )?(?:link|here)")),
    ("pressure", re.compile(r"\bact now\b|within 24 hours|final notice|last warning")),
)
RE_AUTOMATED_LOCAL = re.compile(
    r"(?:no[-_.]?reply|do[-_.]?not[-_.]?reply|notifications?|mailer-daemon|postmaster|newsletters?|alerts?|digest|bounces?|automated)(?:[-_.+].*)?$")
RE_MONEY = re.compile(r"[$€£₪]\s?\d|\b\d[\d,.]*\s?(?:usd|eur|gbp|nis|dollars|euros|shekels)\b|\b(?:invoice|quote|pricing|price|refund|discount|budget|payment)\b")
RE_ATTACH = re.compile(r"\b(?:attached|attachment|enclosed)\b")
RE_SUBJECT_PREFIX = re.compile(r"^\s*(?:(?:re|fw|fwd|aw|sv)\s*:\s*)+", re.I)
RE_ON_WROTE = re.compile(r"^on .{5,}wrote:\s*$")
RE_ORIGINAL = re.compile(r"^(?:-{2,}\s*(?:original|forwarded) message\s*-{2,}|_{10,})\s*$")


class InputError(Exception):
    """Raised for problems the user must fix (unreadable file, empty input)."""


# --------------------------------------------------------------------------- input

def read_text(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc.strerror or exc}")
    text = raw.decode("utf-8-sig", errors="replace")
    if not text.strip():
        raise InputError(f"{path} is empty")
    return text


def parse_date(value):
    """Return a date from an ISO string or an RFC 5322 date; None when unparseable."""
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    try:
        return email.utils.parsedate_to_datetime(value).date()
    except (TypeError, ValueError, IndexError):
        return None


def addresses(value):
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    out = []
    for _, addr in email.utils.getaddresses([str(i) for i in items]):
        addr = addr.strip().lower()
        if "@" in addr and addr not in out:
            out.append(addr)
    return out


def decode_header_value(value):
    if value is None:
        return ""
    try:
        return str(email.header.make_header(email.header.decode_header(str(value))))
    except (ValueError, LookupError):
        return str(value)


def normalize_message(raw, index, warnings):
    headers = {str(k).lower(): str(v) for k, v in (raw.get("headers") or {}).items()}
    body = raw.get("body", raw.get("text"))
    if not isinstance(body, str):
        body = ""
        warnings.append(f"message {index}: no body or text field; treated as empty")
    from_raw = str(raw.get("from") or "")
    attachments = raw.get("attachments")
    count = len(attachments) if isinstance(attachments, list) else (attachments if isinstance(attachments, int) else 0)
    date = parse_date(raw.get("date"))
    return {
        "id": str(raw.get("id") or ""), "index": index, "from_raw": from_raw,
        "from": (addresses(from_raw) or [""])[0], "to": addresses(raw.get("to")), "cc": addresses(raw.get("cc")),
        "subject": str(raw.get("subject") or ""), "date": date, "body": body, "headers": headers,
        "attachment_count": count,
    }


def load_json(text, warnings):
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise InputError(f"input looks like JSON but does not parse: {exc}")
    if isinstance(data, dict):
        data = data.get("messages")
    if not isinstance(data, list):
        raise InputError('JSON input must be a list of messages or {"messages": [...]}')
    out = []
    for i, raw in enumerate(data, 1):
        if not isinstance(raw, dict):
            warnings.append(f"message {i}: not an object; skipped")
            continue
        out.append(normalize_message(raw, i, warnings))
    return out


def mbox_body(msg):
    try:
        part = msg.get_body(preferencelist=("plain",))
        if part is not None:
            return part.get_content()
    except (LookupError, ValueError, KeyError):
        pass
    payload = msg.get_payload()
    return payload if isinstance(payload, str) else ""


def load_mbox(text, warnings):
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("From ") and (i == 0 or not lines[i - 1].strip())]
    if not starts or starts[0] != 0:
        raise InputError('mbox-like input must start each message with a line beginning "From "')
    starts.append(len(lines))
    out = []
    for n, (a, b) in enumerate(zip(starts, starts[1:]), 1):
        chunk = "\n".join(l[1:] if l.startswith(">From ") else l for l in lines[a + 1:b])
        try:
            msg = email.message_from_string(chunk, policy=email.policy.default)
        except Exception as exc:  # the stdlib parser is lenient; this is a last guard
            warnings.append(f"message {n}: could not parse headers ({exc.__class__.__name__}); skipped")
            continue
        raw = {
            "id": (msg.get("message-id") or "").strip().strip("<>"), "from": decode_header_value(msg.get("from")),
            "to": [decode_header_value(h) for h in msg.get_all("to", [])],
            "cc": [decode_header_value(h) for h in msg.get_all("cc", [])],
            "subject": decode_header_value(msg.get("subject")), "date": msg.get("date"), "body": mbox_body(msg),
            "headers": {k: str(msg.get(k)) for k in ("reply-to", "bcc", "list-unsubscribe", "list-id", "precedence", "auto-submitted") if msg.get(k)},
            "attachments": sum(1 for p in msg.walk() if p.get_content_disposition() == "attachment"),
        }
        out.append(normalize_message(raw, n, warnings))
    return out


# --------------------------------------------------------------------------- text helpers

def clean_body(body):
    """Keep only what the sender wrote new: drop quoted lines, the quoted tail and the signature."""
    kept = []
    for line in body.replace("\r\n", "\n").split("\n"):
        stripped = line.strip()
        low = stripped.lower()
        if RE_ON_WROTE.match(low) or RE_ORIGINAL.match(low) or stripped == "--" or line.startswith("-- "):
            break
        if stripped.startswith(">"):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def thread_key(subject):
    return re.sub(r"\s+", " ", RE_SUBJECT_PREFIX.sub("", subject)).strip().lower()


def add_business_days(day, n):
    while n > 0:
        day += dt.timedelta(days=1)
        if day.weekday() < 5:
            n -= 1
    return day


def safe_date(y, m, d):
    try:
        return dt.date(y, m, d)
    except ValueError:
        return None


# --------------------------------------------------------------------------- deadlines

def has_cue(low, start, end):
    sent_start = max(low.rfind(c, 0, start) for c in ".!?\n") + 1
    if RE_CUE.search(low[max(sent_start, start - CUE_WINDOW):start]):
        return True
    return bool(RE_CUE_AFTER.match(low[end:end + 30]))


def find_deadlines(text, msg_date):
    """Return deadline mentions as dicts without days_left; see references/triage-rules.md section 4."""
    low = text.lower()
    cands = []  # (start, end, kind, resolved, self_contained, is_eod)

    def add(m, kind, resolved, selfc=False, eod=False):
        cands.append((m.start(), m.end(), kind, resolved, selfc, eod))

    for m in RE_ISO.finditer(low):
        add(m, "absolute", safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
    for rx, mi, di, yi in ((RE_MONTH_DAY, 1, 2, 3), (RE_DAY_MONTH, 2, 1, 3)):
        for m in rx.finditer(low):
            month, day = MONTHS[m.group(mi)], int(m.group(di))
            if m.group(yi):
                resolved = safe_date(int(m.group(yi)), month, day)
            elif msg_date:
                resolved = safe_date(msg_date.year, month, day)
                # A date more than 30 days behind the message means next year ("by 5 Jan" sent in December).
                if resolved and resolved < msg_date - dt.timedelta(days=30):
                    resolved = safe_date(msg_date.year + 1, month, day)
            else:
                resolved = None
            add(m, "absolute", resolved)
    for m in RE_REL_DAY.finditer(low):
        word = m.group(1)
        resolved = None if not msg_date else msg_date + dt.timedelta(days=1 if word == "tomorrow" else 0)
        add(m, "relative", resolved)
    for m in RE_WEEKDAY.finditer(low):
        resolved = None
        if msg_date:
            target = WEEKDAYS[m.group(2)]
            if m.group(1) == "next":
                resolved = msg_date + dt.timedelta(days=(target - msg_date.weekday() - 1) % 7 + 1)
                if resolved.isocalendar()[:2] == msg_date.isocalendar()[:2]:
                    resolved += dt.timedelta(days=7)
            else:
                resolved = msg_date + dt.timedelta(days=(target - msg_date.weekday()) % 7)
        add(m, "weekday", resolved)
    for m in RE_END_OF.finditer(low):
        resolved = None
        if msg_date:
            if (m.group(1) or "") == "month" or m.group(2) == "eom":
                resolved = msg_date.replace(day=calendar.monthrange(msg_date.year, msg_date.month)[1])
            else:
                resolved = msg_date + dt.timedelta(days=(4 - msg_date.weekday()) % 7 if msg_date.weekday() <= 4 else 7 - msg_date.weekday() + 4)
        add(m, "relative", resolved)
    for m in RE_EOD.finditer(low):
        add(m, "relative", msg_date, selfc=True, eod=True)
    for m in RE_WITHIN.finditer(low):
        n, unit = int(m.group(1)), m.group(2)
        resolved = None
        if msg_date:
            if unit.startswith(("business", "working")):
                resolved = add_business_days(msg_date, n)
            elif unit.startswith("hour"):
                resolved = msg_date + dt.timedelta(days=n // 24)
            elif unit.startswith("week"):
                resolved = msg_date + dt.timedelta(days=7 * n)
            else:
                resolved = msg_date + dt.timedelta(days=n)
        add(m, "window", resolved, selfc=True)
    for m in RE_IMMEDIATE.finditer(low):
        add(m, "immediate", None, selfc=True)

    # "by eod tomorrow" is one deadline (tomorrow); drop an eod token that touches another date token.
    others = [c for c in cands if not c[5]]
    cands = [c for c in cands if not c[5] or not any(o[0] - c[1] in range(0, 5) or c[0] - o[1] in range(0, 5) for o in others)]
    cands = [c for c in cands if c[4] or has_cue(low, c[0], c[1])]
    cands.sort(key=lambda c: (c[0], -(c[1] - c[0])))
    found, last_end, seen = [], -1, set()
    for start, end, kind, resolved, _, _ in cands:
        key = (text[start:end].lower(), resolved)
        if start < last_end or key in seen:  # overlap, or the same mention again (subject and body)
            continue
        last_end = end
        seen.add(key)
        found.append({"text": text[start:end], "kind": kind, "resolved_date": resolved})
    return found[:MAX_DEADLINES]


# --------------------------------------------------------------------------- classification

def needs_response(text):
    """Return (bool, reason) from the unquoted body of one message."""
    low = text.lower()
    if RE_QUESTION.search(low):
        return True, "question_mark"
    for phrase in REQUEST_PHRASES:
        if phrase in low:
            return True, f"request_phrase:{phrase}"
    if RE_PLEASE.search(low):
        return True, "request_phrase:please"
    return False, ""


def suspicious_score(low, msg, known_domains=None):
    score, reasons = 0, []
    for name, rx in STRONG_SUSPICIOUS:
        if rx.search(low):
            score += 2
            reasons.append(f"suspicious:{name}")
    for name, rx in WEAK_SUSPICIOUS:
        if rx.search(low):
            score += 1
            reasons.append(f"suspicious:{name}")
    reply_to = addresses(msg["headers"].get("reply-to"))
    if reply_to and msg["from"] and reply_to[0].split("@")[-1] != msg["from"].split("@")[-1]:
        score += 1
        reasons.append("suspicious:reply_to_domain_differs")
    if RE_SHORTENER.search(low):
        score += 1
        reasons.append("suspicious:url_shortener")
    if msg["from"] and lookalike_domain(msg["from"].split("@")[-1], known_domains or ()):
        score += 2
        reasons.append("suspicious:lookalike_sender_domain")
    if RE_URGENCY.search(low) and "suspicious:credential_request" in reasons:
        score += 1
        reasons.append("suspicious:urgency_with_credential_request")
    return score, reasons


RE_SHORTENER = re.compile(
    r"https?://(?:www\.)?(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|ow\.ly|is\.gd|buff\.ly|rebrand\.ly|cutt\.ly|shorturl\.at|tiny\.cc)/")
RE_URGENCY = re.compile(r"\bwithin \d+ hours?\b|\bact now\b|\bimmediately\b|\burgent(?:ly)?\b|\bfinal notice\b|\blast warning\b|\bexpires? (?:today|soon)\b")
# Brands whose names are often faked. A sender domain containing one of these (after undoing digit
# swaps) whose registrable name is not exactly the brand is treated as a lookalike.
IMPERSONATED_BRANDS = ("paypal", "microsoft", "google", "apple", "amazon", "docusign", "netflix", "dropbox", "linkedin", "dhl", "fedex")
DIGIT_SWAPS = str.maketrans({"0": "o", "1": "l", "3": "e", "5": "s", "4": "a", "7": "t"})


def _registrable(domain):
    parts = domain.lower().strip(".").split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else domain.lower()


def _edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def lookalike_domain(domain, known):
    """True when `domain` is not a known sender domain but imitates one (edit distance 1 or 2 on the
    registrable name, or digit-for-letter swap) or imitates a commonly faked brand."""
    reg = _registrable(domain)
    known_reg = {_registrable(k) for k in known}
    if reg in known_reg:
        return False
    name = reg.split(".")[0]
    for k in known_reg:
        kn = k.split(".")[0]
        if len(kn) >= 4 and (name.translate(DIGIT_SWAPS) == kn.translate(DIGIT_SWAPS) or _edit_distance(name, kn) <= 2) and name != kn:
            return True
    plain = domain.lower().translate(DIGIT_SWAPS).replace("-", "")
    for brand in IMPERSONATED_BRANDS:
        if brand in plain and reg != brand + ".com":
            # Sub-domains of the real brand (mail.google.com) have reg == brand.com and are skipped above.
            return True
    return False


def automated_reason(msg, body):
    local = msg["from"].split("@")[0]
    if RE_AUTOMATED_LOCAL.match(local):
        return "automated_sender"
    h = msg["headers"]
    if "list-unsubscribe" in h or "list-id" in h:
        return "list_header"
    if h.get("precedence", "").strip().lower() in ("bulk", "list", "junk"):
        return "precedence_bulk"
    auto = h.get("auto-submitted", "no").strip().lower()
    if auto and auto != "no":
        return "auto_submitted"
    tail = [l for l in body.lower().split("\n") if l.strip()][-12:]
    if any("unsubscribe" in l for l in tail):
        return "unsubscribe_footer"
    return ""


def classify(messages, me, today, warnings):
    me_set = set(me)
    # Known domains: yours, plus every domain you wrote to or copied (people you already deal with).
    known_domains = {a.split("@")[-1] for a in me_set}
    for m in messages:
        if m["from"] in me_set:
            known_domains |= {a.split("@")[-1] for a in list(m["to"]) + list(m["cc"])}
    threads = {}
    for m in messages:
        threads.setdefault(thread_key(m["subject"]), []).append(m)
    latest = {k: max(v, key=lambda m: (m["date"] or dt.date.min, m["index"])) for k, v in threads.items()}
    rows = []
    for m in messages:
        body = clean_body(m["body"])
        low = body.lower() + "\n" + m["subject"].lower()
        flags, reasons = [], []
        deadlines = find_deadlines(body + "\n" + m["subject"], m["date"])
        for d in deadlines:
            d["days_left"] = (d["resolved_date"] - today).days if d["resolved_date"] and today else None
        if m["date"] is None:
            flags.append("no_date")
        if deadlines:
            flags.append("deadline")
        if any(d["kind"] == "immediate" for d in deadlines):
            flags.append("immediate")
        if any(d["days_left"] is not None and d["days_left"] < 0 for d in deadlines):
            flags.append("overdue")
        if RE_MONEY.search(low):
            flags.append("money_mentioned")
        if RE_ATTACH.search(low) or m["attachment_count"]:
            flags.append("attachment")
        if "bcc" in m["headers"]:
            flags.append("bcc_header")
        recipients = set(m["to"]) | set(m["cc"])
        others = recipients - {m["from"]} - me_set
        if len(others) >= REPLY_ALL_OTHERS:
            flags.append("reply_all_risk")
        if len(recipients) > MASS_RECIPIENTS:
            flags.append("mass_recipient")

        asks, ask_reason = needs_response(body)
        from_me = bool(me_set) and m["from"] in me_set
        close = [d for d in deadlines if d["kind"] == "immediate" or (d["days_left"] is not None and d["days_left"] <= URGENT_DAYS)]
        if from_me:
            if deadlines:
                flags.append("own_deadline_commitment")
            is_latest = latest[thread_key(m["subject"])] is m
            if is_latest and asks:
                category, reasons = "waiting_on_them", ["from_me_latest_in_thread", ask_reason]
                if m["date"] and today and (today - m["date"]).days >= STALE_FOLLOWUP_DAYS:
                    flags.append("stale_followup")
            else:
                category, reasons = "sent", ["from_me" + ("" if is_latest else "_not_latest")]
        else:
            score, sus = suspicious_score(low, m, known_domains)
            auto = automated_reason(m, body)
            if score >= SUSPICIOUS_SCORE:
                category, reasons = "suspicious", sus
            elif auto:
                category, reasons = "automated", [auto]
            elif me_set and m["from"] not in me_set and not (me_set & set(m["to"])):
                category = "fyi"
                reasons = ["cc_only" if me_set & set(m["cc"]) else "not_addressed_to_me"]
            elif asks and close:
                category, reasons = "urgent_reply", [ask_reason, "deadline_within_%d_days" % URGENT_DAYS]
            elif asks:
                category, reasons = "reply", [ask_reason]
            else:
                category, reasons = "fyi", ["no_question_or_request"]
        if category == "suspicious":
            action = "do_not_reply"
        elif category in ("urgent_reply", "reply"):
            action = "draft"
        elif category == "waiting_on_them" and "stale_followup" in flags:
            action = "follow_up"
        else:
            action = "none"
        rows.append({
            "id": m["id"], "index": m["index"], "from": m["from"], "subject": m["subject"],
            "date": m["date"].isoformat() if m["date"] else None, "thread": thread_key(m["subject"]),
            "category": category, "reply_action": action,
            "flags": [f for f in FLAGS if f in flags], "reasons": reasons,
            "deadlines": [{"text": d["text"], "kind": d["kind"],
                           "resolved_date": d["resolved_date"].isoformat() if d["resolved_date"] else None,
                           "days_left": d["days_left"]} for d in deadlines],
        })
    seen = {}
    for r in rows:
        base = r["id"] or f"m{r['index']}"
        seen[base] = seen.get(base, 0) + 1
        r["id"] = base if seen[base] == 1 else f"{base}#{seen[base]}"
        if seen[base] > 1:
            warnings.append(f"duplicate id {base!r}; later copies renamed with #n")
    return rows


def urgency(row):
    days = [0 if d["kind"] == "immediate" else d["days_left"] for d in row["deadlines"] if d["kind"] == "immediate" or d["days_left"] is not None]
    return min(days) if days else 9999


def build_queue(rows):
    keyed = []
    for r in rows:
        if r["category"] == "urgent_reply":
            keyed.append(((0, urgency(r), r["index"]), r["id"]))
        elif r["category"] == "reply":
            keyed.append(((1, urgency(r), r["index"]), r["id"]))
        elif r["reply_action"] == "follow_up":
            keyed.append(((2, r["index"], 0), r["id"]))
    return [i for _, i in sorted(keyed)]


def run_triage(path, me, today_arg):
    text = read_text(path)
    warnings = []
    fmt = "json" if text.lstrip().startswith(("[", "{")) else "mbox"
    messages = load_json(text, warnings) if fmt == "json" else load_mbox(text, warnings)
    if not messages:
        raise InputError("no message could be parsed from the input")
    today = None
    if today_arg:
        today = parse_date(today_arg)
        if today is None:
            raise InputError("--today must look like YYYY-MM-DD")
    else:
        dated = [m["date"] for m in messages if m["date"]]
        today = max(dated) if dated else None
    if today is None:
        warnings.append("no message has a parseable date and --today was not given; days_left is null everywhere")
    rows = classify(messages, addresses(me), today, warnings)
    counts = {c: 0 for c in CATEGORIES}
    for r in rows:
        counts[r["category"]] += 1
    return {
        "schema_version": SCHEMA_VERSION, "command": "triage", "source": path.replace("\\", "/").split("/")[-1],
        "format": fmt, "me_known": bool(addresses(me)), "reference_date": today.isoformat() if today else None,
        "message_count": len(rows), "counts_by_category": counts, "messages": rows,
        "queue": build_queue(rows), "quarantine": [r["id"] for r in rows if r["category"] == "suspicious"],
        "warnings": warnings,
    }


# --------------------------------------------------------------------------- check

TOP_KEYS = {"schema_version", "command", "source", "format", "me_known", "reference_date", "message_count",
            "counts_by_category", "messages", "queue", "quarantine", "warnings"}
ROW_KEYS = {"id", "index", "from", "subject", "date", "thread", "category", "reply_action", "flags", "reasons", "deadlines"}
DEADLINE_KEYS = {"text", "kind", "resolved_date", "days_left"}
RE_ISO_FULL = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate(table):
    errors = []
    if not isinstance(table, dict):
        return ["top level is not an object"]
    if set(table) != TOP_KEYS:
        errors.append(f"top-level keys differ: missing {sorted(TOP_KEYS - set(table))}, extra {sorted(set(table) - TOP_KEYS)}")
        return errors
    if table["schema_version"] != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if table["command"] != "triage":
        errors.append('command must be "triage"')
    if table["format"] not in ("json", "mbox"):
        errors.append('format must be "json" or "mbox"')
    if not isinstance(table["me_known"], bool):
        errors.append("me_known must be a boolean")
    ref = table["reference_date"]
    if ref is not None and not (isinstance(ref, str) and RE_ISO_FULL.match(ref)):
        errors.append("reference_date must be YYYY-MM-DD or null")
    rows = table["messages"]
    if not isinstance(rows, list):
        return errors + ["messages must be a list"]
    if table["message_count"] != len(rows):
        errors.append("message_count does not equal the number of messages")
    counts = {c: 0 for c in CATEGORIES}
    ids = set()
    for i, r in enumerate(rows):
        where = f"messages[{i}]"
        if not isinstance(r, dict) or set(r) != ROW_KEYS:
            errors.append(f"{where}: keys must be exactly {sorted(ROW_KEYS)}")
            continue
        if r["category"] not in CATEGORIES:
            errors.append(f"{where}: unknown category {r['category']!r}")
        else:
            counts[r["category"]] += 1
        if r["reply_action"] not in REPLY_ACTIONS:
            errors.append(f"{where}: unknown reply_action {r['reply_action']!r}")
        if r["id"] in ids:
            errors.append(f"{where}: duplicate id {r['id']!r}")
        ids.add(r["id"])
        if r["date"] is not None and not (isinstance(r["date"], str) and RE_ISO_FULL.match(r["date"])):
            errors.append(f"{where}: date must be YYYY-MM-DD or null")
        if not isinstance(r["flags"], list) or any(f not in FLAGS for f in r["flags"]):
            errors.append(f"{where}: flags must be a list drawn from the documented flag names")
        if not isinstance(r["reasons"], list) or not all(isinstance(x, str) for x in r["reasons"]):
            errors.append(f"{where}: reasons must be a list of strings")
        if (r["category"] == "suspicious") != (r["reply_action"] == "do_not_reply"):
            errors.append(f"{where}: do_not_reply is used for suspicious messages and only for them")
        if r["category"] in ("urgent_reply", "reply") and r["reply_action"] != "draft":
            errors.append(f"{where}: urgent_reply and reply must have reply_action draft")
        if isinstance(r["deadlines"], list):
            if bool(r["deadlines"]) != ("deadline" in r["flags"]):
                errors.append(f"{where}: the deadline flag must be present exactly when deadlines is not empty")
            for d in r["deadlines"]:
                if not isinstance(d, dict) or set(d) != DEADLINE_KEYS or d["kind"] not in KINDS:
                    errors.append(f"{where}: a deadline entry has wrong keys or kind")
        else:
            errors.append(f"{where}: deadlines must be a list")
    if table["counts_by_category"] != counts:
        errors.append("counts_by_category does not match the messages")
    by_id = {r["id"]: r for r in rows if isinstance(r, dict) and "id" in r}
    for qid in table["queue"] if isinstance(table["queue"], list) else []:
        row = by_id.get(qid)
        if row is None or row["reply_action"] not in ("draft", "follow_up"):
            errors.append(f"queue entry {qid!r} is missing or not actionable")
    if table["quarantine"] != [r["id"] for r in rows if isinstance(r, dict) and r.get("category") == "suspicious"]:
        errors.append("quarantine must list exactly the suspicious message ids in order")
    if not isinstance(table["warnings"], list):
        errors.append("warnings must be a list")
    return errors


# --------------------------------------------------------------------------- cli

def main(argv=None):
    parser = argparse.ArgumentParser(prog="triage_mailbox.py", description="Triage an exported mailbox. Reads only; sends nothing.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("triage", help="classify messages and flag deadlines")
    t.add_argument("export", help="JSON export or mbox-like text file")
    t.add_argument("--me", default="", help="comma-separated addresses that belong to the mailbox owner")
    t.add_argument("--today", default="", help="reference date YYYY-MM-DD (default: latest message date)")
    c = sub.add_parser("check", help="validate a saved triage table")
    c.add_argument("table", help="JSON file produced by the triage command")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        if args.cmd == "triage":
            result = run_triage(args.export, args.me, args.today)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
        try:
            table = json.loads(read_text(args.table))
        except ValueError as exc:
            print(json.dumps({"ok": False, "errors": [f"not valid JSON: {exc}"]}, indent=2))
            return 1
        errors = validate(table)
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2, ensure_ascii=False))
        return 1 if errors else 0
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
