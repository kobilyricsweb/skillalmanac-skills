#!/usr/bin/env python3
"""Validate a video package (script plus publishing metadata) given as JSON.

Usage:
    python scripts/video_check.py <package.json>
    python scripts/video_check.py -          (read JSON from standard input)

Reads the file you name and prints one JSON report to standard output. Writes
nothing, uses no network. Output is always strict JSON, including errors.

Exit codes: 0 no FAIL findings (WARN allowed), 1 at least one FAIL,
2 the input could not be read or is not the expected shape.

Input fields (all optional except title; a missing field is reported, not guessed):
  title                  string
  hook                   string, the spoken opening line(s)
  script                 string, the full spoken script (used for disclosure and keyword checks)
  description            string
  primary_keyword        string, the phrase the video is about
  tags                   list of strings
  chapters               list of {"time": "M:SS" or "H:MM:SS", "title": string}
  duration_s             number, total runtime in seconds
  pattern_breaks         list of numbers, seconds at which the visual or pacing changes
  sponsored              boolean
  disclosure             object: {"paid_promotion_toggle": bool}
"""
import json
import re
import sys

# Spoken pace used to turn the 15-second hook rule into words: 150 words per
# minute is a normal conversational delivery, so 15 s is about 37 words.
WORDS_PER_SECOND = 2.5
HOOK_MAX_SECONDS = 15
HOOK_FAIL_WORDS = int(HOOK_MAX_SECONDS * WORDS_PER_SECOND)  # 37
HOOK_WARN_WORDS = 30  # leaves a few seconds of air for the first visual

# YouTube hard limits (title 100 characters, description 5,000, tags 500 in total).
TITLE_FAIL = 100
# Search results and suggested rows cut long titles; about 60 characters is the
# usual safe visible length, used here as a stated heuristic.
TITLE_WARN = 60
DESC_FAIL = 5000
DESC_PREVIEW = 150  # characters shown before "more" in most surfaces; a heuristic
TAGS_TOTAL_FAIL = 500
TAGS_WARN_COUNT = 15  # tags carry little ranking weight; more is noise
TAG_MIN_COUNT = 3

# Chapters: YouTube needs a first chapter at 0:00, at least 3 chapters and at
# least 10 seconds per chapter.
CHAPTER_MIN = 3
CHAPTER_MIN_GAP_S = 10

# Heuristic: a visual or pacing change at least every 30 seconds. It is a
# working value, not a measured optimum; change it in the report if the user
# states another interval.
PATTERN_BREAK_MAX_GAP_S = 30

CLICKBAIT_PHRASES = [
    "you won't believe", "you wont believe", "shocking", "gone wrong",
    "they don't want you to know", "they dont want you to know",
    "will blow your mind", "doctors hate", "nobody is talking about",
    "the truth about", "number 1 secret", "secret trick", "destroyed",
]

DISCLOSURE_TERMS = [
    "sponsored", "paid promotion", "paid partnership", "#ad", "ad:", "advertisement",
    "in partnership with", "paid for by", "brought to you by",
]

TS_RE = re.compile(r"^(?:(\d{1,2}):)?(\d{1,2}):(\d{2})$")
URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)


class Report:
    def __init__(self):
        self.findings = []

    def add(self, severity, check, message):
        self.findings.append({"severity": severity, "check": check, "message": message})

    def fail(self, check, message):
        self.add("FAIL", check, message)

    def warn(self, check, message):
        self.add("WARN", check, message)


def words(text):
    return re.findall(r"\S+", text)


def has_term(text, terms):
    low = text.lower()
    return [t for t in terms if t in low]


def parse_ts(value):
    """Return seconds for 'M:SS' or 'H:MM:SS', or None if the format is wrong."""
    if not isinstance(value, str):
        return None
    m = TS_RE.match(value.strip())
    if not m:
        return None
    h, mi, s = m.group(1), int(m.group(2)), int(m.group(3))
    if s > 59 or (h is not None and mi > 59):
        return None
    return (int(h) if h else 0) * 3600 + mi * 60 + s


def check_title(pkg, rep):
    title = pkg.get("title")
    if not isinstance(title, str) or not title.strip():
        rep.fail("title-missing", "title is missing or empty")
        return
    n = len(title)
    if n > TITLE_FAIL:
        rep.fail("title-length", f"title is {n} characters; the limit is {TITLE_FAIL}")
    elif n > TITLE_WARN:
        rep.warn("title-length", f"title is {n} characters; about {TITLE_WARN} is the safe visible length, put the promise first")
    letters = [c for c in title if c.isalpha()]
    if len(letters) >= 8 and sum(c.isupper() for c in letters) / len(letters) > 0.6:
        rep.warn("title-caps", "title is mostly capital letters; write it in normal case")
    hits = has_term(title, CLICKBAIT_PHRASES)
    if hits:
        rep.warn("title-clickbait", "title contains clickbait phrase(s): " + ", ".join(hits) + "; state the real promise instead")
    kw = pkg.get("primary_keyword")
    if isinstance(kw, str) and kw.strip() and kw.lower() not in title.lower():
        rep.warn("title-keyword", f"primary keyword '{kw}' is not in the title")


def check_hook(pkg, rep):
    hook = pkg.get("hook")
    if not isinstance(hook, str) or not hook.strip():
        rep.fail("hook-missing", "hook is missing or empty")
        return
    n = len(words(hook))
    seconds = round(n / WORDS_PER_SECOND, 1)
    if n > HOOK_FAIL_WORDS:
        rep.fail("hook-length", f"hook is {n} words (about {seconds} s at {WORDS_PER_SECOND} words/s); the limit is {HOOK_FAIL_WORDS} words for {HOOK_MAX_SECONDS} s")
    elif n > HOOK_WARN_WORDS:
        rep.warn("hook-length", f"hook is {n} words (about {seconds} s); over {HOOK_WARN_WORDS} leaves no room for a first visual")
    hits = has_term(hook, CLICKBAIT_PHRASES)
    if hits:
        rep.warn("hook-clickbait", "hook contains clickbait phrase(s): " + ", ".join(hits))


def check_chapters(pkg, rep):
    chapters = pkg.get("chapters")
    if not isinstance(chapters, list):
        rep.fail("chapters-missing", "chapters is missing or not a list")
        return
    if len(chapters) < CHAPTER_MIN:
        rep.fail("chapters-count", f"{len(chapters)} chapters; at least {CHAPTER_MIN} are required")
    prev = None
    for i, ch in enumerate(chapters, start=1):
        if not isinstance(ch, dict):
            rep.fail("chapter-shape", f"chapter {i} is not an object with time and title")
            continue
        sec = parse_ts(ch.get("time"))
        if sec is None:
            rep.fail("chapter-timestamp", f"chapter {i} time {ch.get('time')!r} is not M:SS or H:MM:SS")
            continue
        if i == 1 and sec != 0:
            rep.fail("chapter-first", f"first chapter starts at {ch.get('time')}; it must be 0:00")
        if prev is not None:
            if sec <= prev:
                rep.fail("chapter-order", f"chapter {i} at {ch.get('time')} is not after the previous chapter")
            elif sec - prev < CHAPTER_MIN_GAP_S:
                rep.fail("chapter-gap", f"chapter {i-1} is only {sec - prev} s long; the minimum is {CHAPTER_MIN_GAP_S} s")
        title = ch.get("title")
        if not isinstance(title, str) or not title.strip():
            rep.fail("chapter-title", f"chapter {i} has no title")
        prev = sec
    dur = pkg.get("duration_s")
    if isinstance(dur, (int, float)) and prev is not None and prev >= dur:
        rep.fail("chapter-beyond-end", f"last chapter starts at {prev} s but duration_s is {dur}")


def check_description(pkg, rep):
    desc = pkg.get("description")
    if not isinstance(desc, str) or not desc.strip():
        rep.fail("description-missing", "description is missing or empty")
        return
    if len(desc) > DESC_FAIL:
        rep.fail("description-length", f"description is {len(desc)} characters; the limit is {DESC_FAIL}")
    head = desc[:DESC_PREVIEW]
    if len(desc) < DESC_PREVIEW:
        rep.warn("description-short", f"description is {len(desc)} characters; the first {DESC_PREVIEW} are the preview, use them")
    kw = pkg.get("primary_keyword")
    if isinstance(kw, str) and kw.strip() and kw.lower() not in head.lower():
        rep.fail("description-keyword", f"primary keyword '{kw}' is not in the first {DESC_PREVIEW} characters")
    if URL_RE.search(head):
        rep.warn("description-url-first", f"a link sits inside the first {DESC_PREVIEW} characters; lead with the promise, links later")
    low = head.lower()
    if low.startswith(("subscribe", "like and", "follow me", "hey guys", "hi guys")):
        rep.warn("description-opener", "description opens with a request instead of what the viewer gets")


def check_tags(pkg, rep):
    tags = pkg.get("tags")
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        rep.fail("tags-missing", "tags is missing or not a list of strings")
        return
    if len(tags) < TAG_MIN_COUNT:
        rep.warn("tags-few", f"{len(tags)} tags; at least {TAG_MIN_COUNT} are useful (include misspellings of hard names)")
    if len(tags) > TAGS_WARN_COUNT:
        rep.warn("tags-count", f"{len(tags)} tags; more than {TAGS_WARN_COUNT} is noise")
    total = sum(len(t) for t in tags) + max(len(tags) - 1, 0)
    if total > TAGS_TOTAL_FAIL:
        rep.fail("tags-total-length", f"tags total {total} characters; the limit is {TAGS_TOTAL_FAIL}")
    seen = set()
    for t in tags:
        key = t.strip().lower()
        if key in seen:
            rep.warn("tags-duplicate", f"tag '{t}' is repeated")
        seen.add(key)
    if any(t.startswith("#") for t in tags):
        rep.warn("tags-hash", "tags should not carry a leading '#'; hashtags belong in the description")


def check_disclosure(pkg, rep):
    sponsored = pkg.get("sponsored")
    if sponsored is not True:
        return
    desc = pkg.get("description") if isinstance(pkg.get("description"), str) else ""
    script = pkg.get("script") if isinstance(pkg.get("script"), str) else ""
    if not has_term(desc, DISCLOSURE_TERMS):
        rep.fail("disclosure-description", "video is sponsored but the description has no disclosure wording (for example 'Sponsored by', 'Paid promotion', '#ad')")
    elif not has_term(desc[:DESC_PREVIEW], DISCLOSURE_TERMS):
        rep.warn("disclosure-position", f"disclosure is not inside the first {DESC_PREVIEW} characters of the description")
    if not script.strip():
        rep.fail("disclosure-spoken", "video is sponsored but no script was supplied to check for a spoken disclosure")
    elif not has_term(script, DISCLOSURE_TERMS):
        rep.fail("disclosure-spoken", "video is sponsored but the script has no spoken or on-screen disclosure wording")
    toggle = pkg.get("disclosure")
    if not (isinstance(toggle, dict) and toggle.get("paid_promotion_toggle") is True):
        rep.fail("disclosure-toggle", "video is sponsored but disclosure.paid_promotion_toggle is not true (the platform's paid-promotion setting)")


def check_pacing(pkg, rep):
    breaks = pkg.get("pattern_breaks")
    dur = pkg.get("duration_s")
    if breaks is None:
        rep.warn("pattern-breaks-missing", "no pattern_breaks supplied; the pacing rule was not checked")
        return
    if not isinstance(breaks, list) or not all(isinstance(b, (int, float)) for b in breaks):
        rep.fail("pattern-breaks-shape", "pattern_breaks must be a list of seconds")
        return
    points = [0.0] + sorted(float(b) for b in breaks)
    if isinstance(dur, (int, float)):
        points.append(float(dur))
    worst = max((b - a for a, b in zip(points, points[1:])), default=0.0)
    if worst > PATTERN_BREAK_MAX_GAP_S:
        rep.warn("pattern-break-gap", f"longest stretch without a change is {worst:g} s; the working heuristic is {PATTERN_BREAK_MAX_GAP_S} s")


def check_package(pkg):
    rep = Report()
    check_title(pkg, rep)
    check_hook(pkg, rep)
    check_chapters(pkg, rep)
    check_description(pkg, rep)
    check_tags(pkg, rep)
    check_disclosure(pkg, rep)
    check_pacing(pkg, rep)
    fails = sum(1 for f in rep.findings if f["severity"] == "FAIL")
    warns = sum(1 for f in rep.findings if f["severity"] == "WARN")
    hook = pkg.get("hook") if isinstance(pkg.get("hook"), str) else ""
    return {
        "command": "video_check",
        "ok": fails == 0,
        "counts": {"fail": fails, "warn": warns},
        "hook_words": len(words(hook)),
        "title_chars": len(pkg.get("title")) if isinstance(pkg.get("title"), str) else None,
        "chapter_count": len(pkg.get("chapters")) if isinstance(pkg.get("chapters"), list) else None,
        "findings": rep.findings,
    }


def emit_error(message):
    print(json.dumps({"command": "video_check", "ok": False, "error": message}, ensure_ascii=False))
    return 2


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        return emit_error("usage: video_check.py <package.json | ->")
    try:
        if argv[0] == "-":
            raw = sys.stdin.read()
        else:
            with open(argv[0], encoding="utf-8-sig") as fh:
                raw = fh.read()
    except OSError as exc:
        return emit_error(f"cannot read {argv[0]}: {exc.strerror or exc}")
    except UnicodeDecodeError:
        return emit_error("file is not UTF-8 text")
    if not raw.strip():
        return emit_error("input is empty")
    try:
        pkg = json.loads(raw)
    except json.JSONDecodeError as exc:
        return emit_error(f"invalid JSON: {exc}")
    except RecursionError:
        return emit_error("nesting_too_deep: the JSON is nested too deeply to read")
    except ValueError as exc:
        return emit_error(f"invalid_number: {str(exc)[:120]}")
    if not isinstance(pkg, dict):
        return emit_error("top level of the JSON must be an object")
    report = check_package(pkg)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main())
