#!/usr/bin/env python3
"""Validate a social content calendar (JSON or CSV) and print strict JSON.

Usage:
    python calendar_check.py <calendar.json|calendar.csv> [--limits limits.json]
                             [--dup-days N] [--min-gap-minutes N] [--max-gap-days N]
                             [--rules]

Reads: the calendar file, and the optional limits override file. Writes: JSON to
stdout only. Network: none. Nothing on disk is modified.

Calendar fields per post (CSV header or JSON keys):
    id            required, unique string
    platform      required: x, linkedin, instagram, facebook, threads, bluesky, tiktok, youtube
    scheduled_at  required, ISO 8601 (2026-12-01T09:30:00+02:00 or ...Z). A missing offset is a warning.
    text          required, the full post text as it will be published
    sponsored     optional true/false (yes/no/1/0); blank means false
    disclosure    optional: "platform_label" when the platform's paid-partnership label is switched on
    hashtags      optional extra hashtags not written in the text (space or comma separated)

Exit codes: 0 no error-level findings (warnings allowed); 1 at least one error-level
finding; 2 unreadable or malformed input file, or bad arguments.
"""
import argparse
import csv
import io
import json
import re
import sys
from datetime import datetime, timedelta, timezone

VERSION = "1.0.0"
LIMITS_AS_OF = "2026-11-21"

# Per-platform defaults. Every number is a working value stated as of LIMITS_AS_OF;
# see references/platform_limits.md for confidence and sources. Override with --limits.
#   max_chars        hard cap on post text (code points; URLs counted at full length unless url_weight set)
#   url_weight       fixed length every URL counts as (X wraps links); None = real length
#   hashtags_max     error above this
#   hashtags_rec     warning above this (house recommendation, not a platform rule)
#   fold             characters shown before a "more" cut; the hook must end before it. None = no fold
#   min_gap_minutes  two posts on the same platform closer than this are flagged (feed crowding)
DEFAULT_LIMITS = {
    "x":         {"max_chars": 280,   "url_weight": 23, "hashtags_max": 10, "hashtags_rec": 2, "fold": None, "min_gap_minutes": 120},
    "linkedin":  {"max_chars": 3000,  "url_weight": None, "hashtags_max": 30, "hashtags_rec": 5, "fold": 210, "min_gap_minutes": 720},
    "instagram": {"max_chars": 2200,  "url_weight": None, "hashtags_max": 30, "hashtags_rec": 5, "fold": 125, "min_gap_minutes": 480},
    "facebook":  {"max_chars": 63206, "url_weight": None, "hashtags_max": 30, "hashtags_rec": 3, "fold": 125, "min_gap_minutes": 480},
    "threads":   {"max_chars": 500,   "url_weight": None, "hashtags_max": 1,  "hashtags_rec": 1, "fold": None, "min_gap_minutes": 180},
    "bluesky":   {"max_chars": 300,   "url_weight": None, "hashtags_max": 8,  "hashtags_rec": 2, "fold": None, "min_gap_minutes": 120},
    "tiktok":    {"max_chars": 4000,  "url_weight": None, "hashtags_max": 30, "hashtags_rec": 5, "fold": 90, "min_gap_minutes": 480},
    "youtube":   {"max_chars": 5000,  "url_weight": None, "hashtags_max": 15, "hashtags_rec": 3, "fold": 100, "min_gap_minutes": 1440},
}
# Platforms with a native paid-partnership label that may stand in for a text marker.
LABEL_PLATFORMS = {"instagram", "facebook", "tiktok", "youtube"}
DEFAULT_FOLD = 140  # fallback visibility window for the disclosure position check
DEFAULT_DUP_DAYS = 14  # same platform, same message inside two weeks reads as spam
DEFAULT_MAX_GAP_DAYS = 10  # a platform silent this long inside the calendar span looks abandoned
SIMILARITY = 0.8  # word-set Jaccard at or above this counts as a duplicate
MIN_WORDS_FOR_SIMILARITY = 6  # shorter posts only match when exactly equal

# Clear disclosures a reader notices; matched case-insensitively on word boundaries.
STRONG = [r"#ad\b", r"#sponsored\b", r"#paidpartnership\b", r"#paidpromotion\b", r"#advertisement\b",
          r"\bsponsored\b", r"\bpaid partnership\b", r"\bpaid promotion\b", r"\badvertisement\b",
          r"\[ad\]", r"\(ad\)", r"^\s*ad\s*[:\-|]", r"\bin paid partnership with\b", r"\bpaid for by\b"]
# Tags regulators and ad bodies have found unclear on their own.
WEAK = [r"#sp\b", r"#spon\b", r"#collab\b", r"#partner\b", r"#ambassador\b", r"#gifted\b",
        r"#thanks\w*\b", r"#sponsor\b", r"#promo\b", r"#affiliate\b"]
# Prompts that trade an action for reach; checked on the full text.
BAIT = [r"\blike (this )?(post )?if\b", r"\blike and share\b", r"\bshare (this )?if\b", r"\btag (a|your|2|3|two|three) (friend|mate|colleague|someone)",
        r"\bcomment (yes|below|\"?\w+\"? below|\"?\w+\"? to get)\b", r"\bretweet if\b", r"\brt if\b", r"\bfollow (me |us )?for (more|part)",
        r"\bdouble.?tap if\b", r"\bsmash that\b", r"\bgiveaway\b.*\b(like|follow|share|tag)\b", r"\bwho else\b.{0,20}\?$"]

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
HASHTAG_RE = re.compile(r"(?<![\w&/#])#([^\W\d_][\w]*|\d+[^\W\d_][\w]*)", re.U)
TRUE_WORDS = {"true", "yes", "y", "1"}
FALSE_WORDS = {"false", "no", "n", "0", ""}


def finding(sev, code, post, message, **detail):
    return {"severity": sev, "code": code, "post_id": post.get("id") if post else None,
            "platform": post.get("platform") if post else None, "message": message, "detail": detail}


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    s = str(value).strip().lower()
    if s in TRUE_WORDS:
        return True
    if s in FALSE_WORDS:
        return False
    raise ValueError(value)


def parse_dt(value):
    s = str(value).strip()
    if s.endswith(("Z", "z")):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)  # raises ValueError


def load_posts(path):
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as fh:
            raw = fh.read()
    except OSError as exc:
        raise SystemExit(f"cannot read {path}: {exc}")
    if not raw.strip():
        raise SystemExit(f"{path} is empty")
    if path.lower().endswith(".csv"):
        rows = list(csv.DictReader(io.StringIO(raw)))
        if not rows:
            raise SystemExit("CSV has a header but no rows, or no header")
        return [{(k or "").strip().lower(): v for k, v in r.items()} for r in rows]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} is not valid JSON: {exc}")
    if isinstance(data, dict):
        data = data.get("posts")
    if not isinstance(data, list) or not all(isinstance(p, dict) for p in data):
        raise SystemExit("JSON must be a list of post objects or an object with a 'posts' list")
    if not data:
        raise SystemExit("calendar has no posts")
    return data


def merged_limits(override_path):
    limits = {k: dict(v) for k, v in DEFAULT_LIMITS.items()}
    if override_path:
        try:
            with open(override_path, "r", encoding="utf-8-sig") as fh:
                extra = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"cannot use limits file {override_path}: {exc}")
        if not isinstance(extra, dict):
            raise SystemExit("limits file must be a JSON object keyed by platform")
        for plat, vals in extra.items():
            if not isinstance(vals, dict):
                raise SystemExit(f"limits for {plat} must be an object")
            limits.setdefault(plat, {"max_chars": 100000, "url_weight": None, "hashtags_max": 30, "hashtags_rec": 30,
                                     "fold": None, "min_gap_minutes": 0}).update(vals)
    return limits


def effective_length(text, url_weight):
    if not url_weight:
        return len(text)
    urls = URL_RE.findall(text)
    return len(URL_RE.sub("", text)) + url_weight * len(urls)


def hashtags_of(text, extra):
    tags = {m.group(1).lower() for m in HASHTAG_RE.finditer(URL_RE.sub(" ", text))}
    for t in re.split(r"[\s,]+", extra or ""):
        t = t.strip().lstrip("#").lower()
        if t:
            tags.add(t)
    return tags


def normalise(text):
    t = URL_RE.sub(" ", text.lower())
    t = HASHTAG_RE.sub(" ", t)
    t = re.sub(r"[^\w\s]", " ", t, flags=re.U)
    return " ".join(t.split())


def similar(a, b):
    if a == b:
        return True
    wa, wb = set(a.split()), set(b.split())
    if min(len(wa), len(wb)) < MIN_WORDS_FOR_SIMILARITY:
        return False
    return len(wa & wb) / len(wa | wb) >= SIMILARITY


def first_match(patterns, text, flags=re.I | re.M):
    best = None
    for p in patterns:
        m = re.search(p, text, flags)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), m.group(0))
    return best


def check(posts_raw, limits, dup_days, min_gap_override, max_gap_days):
    findings, posts = [], []
    seen_ids = set()
    for i, raw in enumerate(posts_raw, 1):
        p = {"id": str(raw.get("id") or "").strip(), "platform": str(raw.get("platform") or "").strip().lower(),
             "text": raw.get("text") if isinstance(raw.get("text"), str) else ("" if raw.get("text") is None else str(raw.get("text"))),
             "row": i}
        ref = {"id": p["id"] or f"row{i}", "platform": p["platform"] or None}
        if not p["id"]:
            findings.append(finding("error", "missing_field", ref, "post has no id", field="id", row=i))
            p["id"] = ref["id"]
        elif p["id"] in seen_ids:
            findings.append(finding("error", "duplicate_id", ref, "id used more than once", row=i))
        seen_ids.add(p["id"])
        if p["platform"] not in limits:
            findings.append(finding("error", "unknown_platform", ref, "platform not in the limits table; add it with --limits", known=sorted(limits)))
            continue
        if not p["text"].strip():
            findings.append(finding("error", "missing_field", ref, "post has no text", field="text"))
            continue
        try:
            p["sponsored"] = parse_bool(raw.get("sponsored"))
        except ValueError:
            findings.append(finding("error", "bad_sponsored_value", ref, "sponsored must be true or false", value=str(raw.get("sponsored"))))
            continue
        p["disclosure"] = str(raw.get("disclosure") or "").strip().lower()
        p["extra_tags"] = raw.get("hashtags") if isinstance(raw.get("hashtags"), str) else " ".join(raw.get("hashtags") or []) if isinstance(raw.get("hashtags"), list) else ""
        try:
            p["when"] = parse_dt(raw.get("scheduled_at"))
        except (ValueError, TypeError):
            findings.append(finding("error", "bad_datetime", ref, "scheduled_at must be ISO 8601, e.g. 2026-12-01T09:30:00+02:00", value=str(raw.get("scheduled_at"))))
            continue
        p["naive"] = p["when"].tzinfo is None
        if p["naive"]:
            findings.append(finding("warning", "no_timezone", ref, "scheduled_at has no UTC offset; treated as UTC for gap and duplicate maths"))
            p["when"] = p["when"].replace(tzinfo=timezone.utc)
        posts.append(p)

    for p in posts:
        lim = limits[p["platform"]]
        length = effective_length(p["text"], lim.get("url_weight"))
        if length > lim["max_chars"]:
            findings.append(finding("error", "over_limit", p, f"{length} characters, limit {lim['max_chars']}", length=length, limit=lim["max_chars"]))
        tags = hashtags_of(p["text"], p["extra_tags"])
        if len(tags) > lim["hashtags_max"]:
            findings.append(finding("error", "hashtag_count", p, f"{len(tags)} hashtags, maximum {lim['hashtags_max']}", count=len(tags), maximum=lim["hashtags_max"]))
        elif len(tags) > lim["hashtags_rec"]:
            findings.append(finding("warning", "hashtag_count_high", p, f"{len(tags)} hashtags, recommended at most {lim['hashtags_rec']}", count=len(tags), recommended=lim["hashtags_rec"]))
        fold = lim.get("fold")
        if fold:
            first = p["text"].strip().splitlines()[0]
            if len(first) > fold and not re.search(r"[.!?:]\s", first[:fold]):
                findings.append(finding("warning", "hook_past_fold", p, f"first line is {len(first)} characters with no sentence end before the {fold}-character fold; the hook may be cut", fold=fold))
        bait = first_match(BAIT, p["text"])
        if bait:
            findings.append(finding("warning", "engagement_bait", p, "text trades an action for reach", match=bait[1]))
        strong = first_match(STRONG, p["text"])
        weak = first_match(WEAK, p["text"])
        if p["sponsored"]:
            label_ok = p["disclosure"] == "platform_label" and p["platform"] in LABEL_PLATFORMS
            if not strong and not label_ok:
                why = "only an unclear tag (" + weak[1] + ")" if weak else "no marker found"
                findings.append(finding("error", "missing_disclosure", p, "sponsored post has no clear disclosure: " + why, weak_tag=weak[1] if weak else None))
            elif strong:
                window = fold or DEFAULT_FOLD
                if strong[0] > window and not label_ok:
                    findings.append(finding("warning", "disclosure_not_upfront", p, f"disclosure starts at character {strong[0]}, after the {window}-character visible window", position=strong[0]))
        elif strong and re.search(r"#ad\b|#sponsored\b|#paidpartnership\b", p["text"], re.I):
            findings.append(finding("warning", "undeclared_sponsored", p, "text carries a paid-content tag but sponsored is not true; fix the flag or the text"))

    by_platform = {}
    for p in posts:
        by_platform.setdefault(p["platform"], []).append(p)
    for plat, group in by_platform.items():
        group.sort(key=lambda q: q["when"])
        min_gap = limits[plat]["min_gap_minutes"] if min_gap_override is None else min_gap_override
        for a, b in zip(group, group[1:]):
            gap = b["when"] - a["when"]
            if gap < timedelta(minutes=min_gap):
                findings.append(finding("warning", "gap_too_short", b, f"{int(gap.total_seconds() // 60)} min after {a['id']} on {plat}; minimum {min_gap}", previous=a["id"], minutes=int(gap.total_seconds() // 60), minimum=min_gap))
            if gap > timedelta(days=max_gap_days):
                findings.append(finding("warning", "gap_too_long", b, f"{gap.days} days since {a['id']} on {plat}; limit {max_gap_days}", previous=a["id"], days=gap.days, limit=max_gap_days))
        norms = [(q, normalise(q["text"])) for q in group]
        for idx, (b, nb) in enumerate(norms):
            for a, na in norms[:idx]:
                if b["when"] - a["when"] <= timedelta(days=dup_days) and similar(na, nb):
                    findings.append(finding("error", "duplicate_post", b, f"same message as {a['id']} within {dup_days} days on {plat}", other=a["id"]))
                    break

    cross = {}
    for p in posts:
        cross.setdefault(normalise(p["text"]), []).append(p)
    for norm, group in cross.items():
        plats = {q["platform"] for q in group}
        if norm and len(plats) > 1:
            first = group[0]
            for q in group[1:]:
                if q["platform"] != first["platform"]:
                    findings.append(finding("warning", "unadapted_cross_post", q, f"text identical to {first['id']} on {first['platform']}; adapt it to the platform", other=first["id"]))
    order = {"error": 0, "warning": 1}
    findings.sort(key=lambda f: (order[f["severity"]], str(f["post_id"]), f["code"]))
    return findings, len(posts_raw)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate a social content calendar and print JSON.")
    ap.add_argument("calendar", nargs="?")
    ap.add_argument("--limits")
    ap.add_argument("--dup-days", type=int, default=DEFAULT_DUP_DAYS)
    ap.add_argument("--min-gap-minutes", type=int, default=None)
    ap.add_argument("--max-gap-days", type=int, default=DEFAULT_MAX_GAP_DAYS)
    ap.add_argument("--rules", action="store_true", help="print the limits table in use and exit")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code not in (0, None) else 0
    for name in ("dup_days", "max_gap_days"):
        if getattr(args, name) < 0:
            print("numeric options must not be negative", file=sys.stderr)
            return 2
    try:
        limits = merged_limits(args.limits)
        if args.rules:
            out = {"tool": "calendar_check", "version": VERSION, "limits_as_of": LIMITS_AS_OF, "limits": limits}
        else:
            if not args.calendar:
                print("calendar file required", file=sys.stderr)
                return 2
            findings, n = check(load_posts(args.calendar), limits, args.dup_days, args.min_gap_minutes, args.max_gap_days)
            errors = sum(f["severity"] == "error" for f in findings)
            out = {"tool": "calendar_check", "version": VERSION, "limits_as_of": LIMITS_AS_OF, "file": args.calendar.replace("\\", "/").split("/")[-1],
                   "posts": n, "ok": errors == 0, "errors": errors, "warnings": len(findings) - errors, "findings": findings}
    except SystemExit as exc:
        print(str(exc.code), file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(out, indent=2, ensure_ascii=True, allow_nan=False) + "\n")
    return 0 if args.rules or out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
