#!/usr/bin/env python3
"""Clean a raw machine transcript or subtitle file without summarising it.

Usage:
    python clean_transcript.py INPUT --out-dir DIR [--policy clean-verbatim|verbatim]
        [--glossary FILE.json] [--format auto|srt|vtt|plain] [--merge-gap SECONDS]
        [--no-merge] [--max-edits N] [--dry-run]

INPUT is an SRT file, a WebVTT file, or a plain transcript whose lines look like
"[hh:mm:ss] Speaker: text", "hh:mm:ss text", "Speaker: text" or just text.

What it does, in this order:
  1. parses cues or lines and splits the speaker label from the text;
  2. normalises speaker labels (case, titles, "Speaker 1" variants, partial names);
  3. applies the glossary, removes listed fillers and stutters (clean-verbatim only);
  4. drops segments that became empty;
  5. merges fragments that are clearly one sentence;
  6. measures subtitle limits (SRT and VTT only) and reports every problem it finds.
Timestamps are kept. It never adds a word: a token-level self-check lists any word
in the output that is not in the input or the glossary.

Reads INPUT (and the glossary). Writes ONE file, <stem>.cleaned.<ext>, inside
--out-dir, and never the input path. --dry-run writes nothing. The strict JSON
report goes to stdout.

Exit codes: 0 done and nothing left to review; 1 done but the report lists issues
or ambiguous speakers or an integrity warning; 2 usage or input error.
"""
import argparse
import collections
import json
import os
import re
import sys

SCHEMA = 1

# Subtitle limits. Sources and reasoning: references/format-and-limits.md.
MAX_LINE_CHARS = 42      # widely used per-line ceiling for subtitles
MAX_LINES = 2            # at most two lines per cue
MIN_CUE_MS = 1000        # a cue shorter than 1 s is hard to read
MAX_CUE_MS = 7000        # a cue longer than 7 s feels frozen
MAX_CPS = 21.0           # above about 21 characters per second most viewers cannot keep up
MIN_GAP_MS = 80          # about two frames at 25 fps so cues do not flash together
# Merge guards.
MERGE_GAP_MS = 1000      # default largest silence between cues that may still be one sentence
MAX_MERGED_CHARS = MAX_LINE_CHARS * MAX_LINES
MAX_PLAIN_MERGE_MS = 15000   # timestamped plain lines further apart than this are not merged
EVIDENCE_CAP = 50
DEFAULT_MAX_EDITS = 1000

TITLES = {"dr", "mr", "mrs", "ms", "miss", "prof", "professor", "sir", "mx", "mister"}
NAME_PARTICLES = {"van", "von", "de", "der", "den", "la", "le", "di", "da", "bin", "al", "el"}
# Words that look like "Label:" but are not speakers.
NON_SPEAKER = {
    "note", "notes", "warning", "tip", "example", "summary", "update", "edit", "caption",
    "subtitle", "subtitles", "translator", "transcript", "source", "time", "date", "music",
    "sound", "important", "reminder", "todo", "ps", "nb", "re", "fwd", "subject", "agenda",
    "url", "http", "https", "action", "decision", "question", "answer",
}
# Fillers removed under clean-verbatim. "uh-huh", "mm-hmm", "like", "so", "right" are
# never removed: they carry meaning (assent, quotation, discourse structure).
WORD_FILLER = r"(?:um+|uh+m*|er|erm|hm+|mm+)"
PHRASE_FILLER = r"(?:you know|i mean)"
# Words after which a removed filler keeps its comma ("Well, um, I think" -> "Well, I think").
COMMA_KEEPERS = {"yes", "no", "well", "so", "okay", "ok", "right", "sure", "yeah", "now",
                 "anyway", "actually", "basically", "and", "but"}
STUTTER_WORDS = ("i|we|you|he|she|they|it|the|a|an|and|but|to|of|in|is|was|my|"
                 "i'm|it's|that's|we're|they're|you're")

WORD_FILLER_RE = re.compile(
    r"(?P<pre>,\s*)?(?<![\w'\u2019-])(?P<w>" + WORD_FILLER + r")(?![\w'\u2019-])(?P<post>\s*[,.?!\u2026]*)",
    re.I)
PHRASE_FILLER_RE = re.compile(
    r"(?P<pre>,\s*)?(?<![\w'\u2019-])(?P<w>" + PHRASE_FILLER + r")(?![\w'\u2019-])(?P<post>\s*,)",
    re.I)
STUTTER_RE = re.compile(
    r"(?<![\w'\u2019-])(?P<w>" + STUTTER_WORDS + r")(?:,?\s+(?P=w)(?![\w'\u2019-]))+", re.I)
HYPHEN_STUTTER_RE = re.compile(
    r"(?<![\w'\u2019-])(?P<w>i|we|it|the|a|they|he|she|you)(?:-(?P=w))+(?![\w'\u2019-])", re.I)
SENT_END_RE = re.compile(r"[.?!\u2026][\"\u201d\u2019)\]]*\s*$")
FINISHED_RE = re.compile(r"[.?!\u2026][\"\u201d\u2019)\]]*$|(--|\u2014)$")
TOKEN_RE = re.compile(r"[^\W_]+(?:['\u2019][^\W_]+)*")

TIME_RE = re.compile(r"(?:(\d{1,3}):)?(\d{1,2}):(\d{2})[.,](\d{1,3})")
LABEL_RE = re.compile(
    r"^(?:>>\s*)?(?P<label>[A-Za-z][\w.'\u2019-]*(?:[ ]+[\w.'\u2019-]+){0,3})\s*:\s+(?P<rest>\S.*)$")
GENERIC_SPEAKER_RE = re.compile(r"(?:speaker|spk|spkr|s)[ _-]?0*(\d+)", re.I)
PLAIN_TS_RE = re.compile(
    r"^\s*(?P<prefix>[\[(]?(?P<ts>\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?)[\])]?(?:\s*[-\u2013\u2014])?)"
    r"(?:\s+|(?<=[\])])\s*|$)(?P<rest>.*)$")
VOICE_RE = re.compile(r"^<v(?:\.[\w.]+)?\s+(?P<name>[^>]+)>(?P<rest>.*?)(?:</v>)?$")
TAG_RE = re.compile(r"<[^>]+>")


class Seg:
    """One cue or one transcript line."""

    def __init__(self, sid, start=None, end=None, raw="", **kw):
        self.sid = sid
        self.start = start
        self.end = end
        self.raw = raw
        self.settings = ""
        self.speaker = None
        self.label_raw = None
        self.show_label = False
        self.style = "inline"     # inline "Name: text" or vtt voice tag
        self.text = ""
        self.locked = False       # dialogue cue with several speakers: left untouched
        self.prefix = ""          # plain-format timestamp prefix, re-emitted verbatim
        self.para_break = False
        self.explicit_id = False
        self.src = [sid]
        self.dirty = False
        self.__dict__.update(kw)


# ---------------------------------------------------------------- reading

def read_text(path, warnings):
    data = open(path, "rb").read()
    if data.startswith(b"\xef\xbb\xbf"):
        text = data[3:].decode("utf-8", errors="replace")
    elif data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        text = data.decode("utf-16", errors="replace")
    else:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("cp1252", errors="replace")
            warnings.append("input is not UTF-8; read as cp1252 (output is written as UTF-8)")
    return text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")


def detect_format(text):
    if text.lstrip().startswith("WEBVTT"):
        return "vtt"
    if re.search(r"\d{1,2}:\d{2}[.,]\d{1,3}\s*-->\s*\d", text[:6000]):
        return "srt"
    return "plain"


def time_to_ms(match):
    h = int(match.group(1) or 0)
    return ((h * 60 + int(match.group(2))) * 60 + int(match.group(3))) * 1000 + int(match.group(4).ljust(3, "0")[:3])


def ts_to_ms(ts):
    parts = ts.replace(",", ".").split(":")
    seconds = float(parts[-1])
    minutes = int(parts[-2])
    hours = int(parts[-3]) if len(parts) == 3 else 0
    return int(round(((hours * 60 + minutes) * 60 + seconds) * 1000))


def split_label(s):
    """Return (label or None, rest). Conservative: a wrong label would corrupt speakers."""
    m = LABEL_RE.match(s)
    if not m:
        return None, s
    label, rest = m.group("label").strip(), m.group("rest")
    if rest.startswith("//"):
        return None, s
    toks = label.split()
    if GENERIC_SPEAKER_RE.fullmatch(label) or re.fullmatch(r"[A-Za-z]+[ _]\d+", label):
        return (None, s) if toks[0].lower() in NON_SPEAKER else (label, rest)
    if label.lower() in NON_SPEAKER or toks[0].lower() in NON_SPEAKER:
        return None, s
    for i, t in enumerate(toks):
        if t.lower() in NAME_PARTICLES and i > 0:
            continue
        if not t[0].isupper():
            return None, s
    return label, rest


def parse_cues(text, fmt, warnings):
    segs, meta = [], {"header": "", "dropped": 0}
    blocks = re.split(r"\n[ \t]*\n", text.strip("\n"))
    n = 0
    for block in blocks:
        lines = block.split("\n")
        if fmt == "vtt" and lines[0].startswith("WEBVTT"):
            meta["header"] = block
            continue
        if fmt == "vtt" and re.match(r"(NOTE|STYLE|REGION)\b", lines[0]):
            meta["dropped"] += 1
            continue
        idx = next((i for i, ln in enumerate(lines) if "-->" in ln), None)
        if idx is None:
            warnings.append("skipped a block with no timing line: " + block[:40].replace("\n", " "))
            continue
        left, right = lines[idx].split("-->", 1)
        lm, rm = TIME_RE.search(left), TIME_RE.search(right)
        if not lm or not rm:
            warnings.append("skipped a cue with an unreadable timing line: " + lines[idx][:60])
            continue
        n += 1
        cue_id = lines[idx - 1].strip() if idx > 0 else ""
        seg = Seg(cue_id or str(n), time_to_ms(lm), time_to_ms(rm), "\n".join(lines[idx + 1:]))
        seg.explicit_id = bool(cue_id)
        seg.settings = right[rm.end():].strip()
        body = [ln.strip() for ln in lines[idx + 1:]]
        if sum(1 for ln in body if ln.startswith("-")) >= 2:
            seg.locked = True
            seg.text = " ".join(body)
        else:
            flat = " ".join(ln for ln in body if ln)
            vm = VOICE_RE.match(flat) if fmt == "vtt" else None
            if vm:
                seg.label_raw, seg.text, seg.style = vm.group("name").strip(), vm.group("rest").strip(), "voice"
            else:
                seg.label_raw, seg.text = split_label(flat)
            seg.show_label = seg.label_raw is not None
            seg.speaker = seg.label_raw
        segs.append(seg)
    return segs, meta


def parse_plain(text, warnings):
    segs, pending, blank = [], "", False
    for no, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            blank = True
            continue
        m = PLAIN_TS_RE.match(line)
        prefix = m.group("prefix").strip() if m else ""
        rest = m.group("rest").strip() if m else line.strip()
        start = ts_to_ms(m.group("ts")) if m else None
        if m and not rest:
            pending, blank = prefix, blank
            continue
        if not m and pending:
            prefix, start = pending, ts_to_ms(re.sub(r"[\[\]()\s\-\u2013\u2014]", "", pending))
        pending = ""
        seg = Seg(str(no), start, None, line.strip())
        seg.prefix = prefix
        seg.para_break = blank and bool(segs)
        blank = False
        seg.label_raw, seg.text = split_label(rest)
        seg.show_label = seg.label_raw is not None
        seg.speaker = seg.label_raw
        segs.append(seg)
    return segs, {"header": "", "dropped": 0}


# ---------------------------------------------------------------- speakers

def speaker_key(raw):
    g = GENERIC_SPEAKER_RE.fullmatch(raw.strip())
    if g:
        return "speaker " + str(int(g.group(1)))
    toks = [t for t in re.findall(r"[a-z0-9']+", raw.lower()) if t not in TITLES]
    return " ".join(toks) or raw.lower()


def normalise_speakers(counter, glossary):
    """Return (mapping raw->(canonical, reason), ambiguous list)."""
    gloss = {k.lower(): v for k, v in glossary.items()}
    groups = collections.OrderedDict()   # key -> list of raws
    forced = {}                          # key -> canonical from the glossary
    for raw in counter:
        if raw.lower() in gloss:
            key = speaker_key(gloss[raw.lower()])
            forced[key] = gloss[raw.lower()]
        else:
            key = speaker_key(raw)
        groups.setdefault(key, []).append(raw)
    reasons = {}
    for key in forced:
        for raw in groups[key]:
            if raw.lower() in gloss:
                reasons[raw] = "glossary"
    ambiguous = []
    multi = [k for k in groups if " " in k and not k.startswith("speaker ")]
    for key in list(groups):
        if " " in key or key.startswith("speaker "):
            continue
        cands = sorted(k for k in multi if key in (k.split()[0], k.split()[-1]))
        if len(cands) == 1:
            groups[cands[0]].extend(groups.pop(key))
            for raw in groups[cands[0]]:
                if speaker_key(raw) == key:
                    reasons.setdefault(raw, "partial-name")
        elif len(cands) > 1:
            ambiguous.append({"label": groups[key][0], "could_be": [
                max(groups[c], key=lambda r: (len(r.split()), counter[r])) for c in cands]})
    mapping = {}
    for key, raws in groups.items():
        if key in forced:
            canon = forced[key]
        elif key.startswith("speaker "):
            canon = "Speaker " + key.split()[1]
        else:
            canon = max(raws, key=lambda r: (len(r.split()), counter[r],
                                              r != r.upper() and r != r.lower()))
            if (canon.isupper() or canon.islower()) and len(canon) > 2:
                canon = canon.title()
        for raw in raws:
            if raw in [a["label"] for a in ambiguous]:
                continue
            reason = reasons.get(raw)
            if raw != canon:
                if not reason:
                    reason = "generic-number" if key.startswith("speaker ") else (
                        "case" if raw.lower() == canon.lower() else "title")
                mapping[raw] = (canon, reason)
            else:
                mapping[raw] = (canon, None)
    return mapping, ambiguous


# ---------------------------------------------------------------- text cleaning

def cap_first(s):
    for i, c in enumerate(s):
        if c.isalpha():
            return s[:i] + c.upper() + s[i + 1:]
        if c.isdigit():
            return s
    return s


def tidy(s):
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s+([,.;:?!\u2026])", r"\1", s)
    s = re.sub(r",\s*,", ",", s)
    return re.sub(r"^[,;\s]+", "", s)


def drop_fillers(text, pattern, need_set_off):
    """Remove every match of pattern; return (text, list of removed strings)."""
    removed, pos = [], 0
    while True:
        m = pattern.search(text, pos)
        if not m:
            return text, removed
        w = m.group("w")
        before, after = text[:m.start()], text[m.end():]
        pre, post = m.group("pre"), m.group("post") or ""
        sentence_start = (not pre) and (before.strip() == "" or bool(SENT_END_RE.search(before)))
        if (w.isupper() and len(w) <= 3 and not text.isupper()) or (need_set_off and not pre and not sentence_start):
            pos = m.end()
            continue
        terminal = next((c for c in post if c in ".?!\u2026"), "")
        if terminal and not after.strip():
            new = (before.rstrip() + terminal) if before.strip() else ""
        elif sentence_start:
            # A lower-case filler at the very start is a continuation cue: keep the next word as is.
            lower_start = before.strip() == "" and w[0].islower()
            new = before + (after.lstrip() if lower_start else cap_first(after.lstrip()))
        elif terminal:
            new = before.rstrip() + terminal + (" " + cap_first(after.lstrip()) if after.strip() else "")
        else:
            words = re.findall(r"[\w'\u2019]+", before)
            keep = bool(pre or "," in post) and bool(words) and words[-1].lower() in COMMA_KEEPERS
            new = before.rstrip() + ("," if keep else "") + (" " + after.lstrip() if after.strip() else "")
        removed.append(w if not need_set_off else w.lower())
        text = new
        pos = max(len(before.rstrip()) - 1, 0)


def drop_stutters(text):
    found = []

    def repl(m):
        found.append(m.group(0))
        return m.group("w")
    text = HYPHEN_STUTTER_RE.sub(repl, text)
    text = STUTTER_RE.sub(repl, text)
    return text, found


def apply_terms(text, terms):
    done = []
    for wrong, right in terms:
        pat = re.compile(r"(?<![\w])" + re.escape(wrong) + r"(?![\w])", re.I)

        def repl(m, right=right):
            if m.group(0) != right:
                done.append(right)
            return right
        text = pat.sub(repl, text)
    return text, done


# ---------------------------------------------------------------- wrapping, emit

def wrap_lines(full, vis_len=0):
    if len(full) <= MAX_LINE_CHARS:
        return [full]
    words = full.split(" ")
    if len(full) <= MAX_LINE_CHARS * MAX_LINES:
        best = None
        for i in range(1, len(words)):
            a, b = " ".join(words[:i]), " ".join(words[i:])
            if len(a) <= vis_len - 1:
                continue   # never break inside the speaker label
            if len(a) <= MAX_LINE_CHARS and len(b) <= MAX_LINE_CHARS:
                key = (0 if a[-1] in ",;:.?!\u2026" else 1, max(len(a), len(b)))
                if best is None or key < best[0]:
                    best = (key, [a, b])
        if best:
            return best[1]
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > MAX_LINE_CHARS:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w) if cur else w
    return lines + [cur]


def seg_lines(seg, cue_format):
    """Final text lines for a cue-format segment."""
    if not seg.dirty or seg.locked:
        return seg.raw.split("\n")
    vis = (seg.speaker + ": ") if (seg.show_label and seg.speaker and seg.style != "voice") else ""
    lines = wrap_lines(vis + seg.text, len(vis))
    if seg.show_label and seg.speaker and seg.style == "voice":
        lines[0] = "<v " + seg.speaker + ">" + lines[0]
    return lines


def fmt_time(ms, sep):
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, milli = divmod(rem, 1000)
    return "%02d:%02d:%02d%s%03d" % (h, m, s, sep, milli)


def render(segs, fmt, meta, had_blank):
    if fmt == "plain":
        out = []
        for i, seg in enumerate(segs):
            if not seg.dirty and not seg.locked:
                line = seg.raw
            else:
                line = (seg.prefix + " " if seg.prefix else "") + \
                    ((seg.speaker + ": ") if (seg.show_label and seg.speaker) else "") + seg.text
            out.append(("\n" if (i and seg.para_break) else "") + line)
        return "\n".join(out) + "\n"
    sep = "," if fmt == "srt" else "."
    blocks = []
    if fmt == "vtt":
        blocks.append(meta["header"] or "WEBVTT")
    for i, seg in enumerate(segs, 1):
        head = []
        if fmt == "srt":
            head.append(str(i))
        elif seg.explicit_id:
            head.append(seg.sid)
        timing = fmt_time(seg.start, sep) + " --> " + fmt_time(seg.end, sep)
        if seg.settings:
            timing += " " + seg.settings
        blocks.append("\n".join(head + [timing] + seg_lines(seg, fmt)))
    return "\n\n".join(blocks) + "\n"


# ---------------------------------------------------------------- checks

CATEGORIES = ("overlap", "bad_timing", "empty", "reading_speed", "line_length",
              "too_many_lines", "too_short", "too_long", "short_gap")


def check_items(items):
    """items: dicts with id, start, end, lines. Returns category -> evidence list."""
    res = {c: [] for c in CATEGORIES}
    prev_end = None
    for it in items:
        lines = [TAG_RE.sub("", ln) for ln in it["lines"]]
        visible = sum(len(ln) for ln in lines)
        dur = it["end"] - it["start"]
        if not "".join(lines).strip():
            res["empty"].append({"cue_id": it["id"]})
        if dur <= 0:
            res["bad_timing"].append({"cue_id": it["id"], "ms": dur})
        else:
            if dur < MIN_CUE_MS:
                res["too_short"].append({"cue_id": it["id"], "ms": dur})
            if dur > MAX_CUE_MS:
                res["too_long"].append({"cue_id": it["id"], "ms": dur})
            cps = visible / (dur / 1000.0)
            if cps > MAX_CPS:
                res["reading_speed"].append({"cue_id": it["id"], "cps": round(cps, 1)})
        longest = max((len(ln) for ln in lines), default=0)
        if longest > MAX_LINE_CHARS:
            res["line_length"].append({"cue_id": it["id"], "longest": longest})
        if len(lines) > MAX_LINES:
            res["too_many_lines"].append({"cue_id": it["id"], "lines": len(lines)})
        if prev_end is not None:
            gap = it["start"] - prev_end
            if gap < 0:
                res["overlap"].append({"cue_id": it["id"], "overlap_ms": -gap})
            elif gap < MIN_GAP_MS:
                res["short_gap"].append({"cue_id": it["id"], "gap_ms": gap})
        prev_end = it["end"] if prev_end is None else max(prev_end, it["end"])
    return res


# ---------------------------------------------------------------- main pipeline

def tokens(texts):
    c = collections.Counter()
    for t in texts:
        c.update(TOKEN_RE.findall(t.lower()))
    return c


def first_alpha(s):
    return next((c for c in s if c.isalpha()), "")


def run(args, text, fmt, warnings):
    glossary = {"speakers": {}, "terms": {}}
    if args.glossary:
        try:
            data = json.load(open(args.glossary, encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise SystemExit("cannot read glossary %s: %s" % (args.glossary, exc))
        if not isinstance(data, dict):
            raise SystemExit("glossary must be a JSON object with optional 'speakers' and 'terms'")
        glossary["speakers"] = {str(k): str(v) for k, v in (data.get("speakers") or {}).items()}
        glossary["terms"] = {str(k): str(v) for k, v in (data.get("terms") or {}).items()}
    terms = sorted(glossary["terms"].items(), key=lambda kv: -len(kv[0]))

    segs, meta = parse_cues(text, fmt, warnings) if fmt in ("srt", "vtt") else parse_plain(text, warnings)
    if not segs:
        raise SystemExit("no cues or lines found in the input")
    had_blank = any(s.para_break for s in segs)
    n_in = len(segs)
    if meta["dropped"]:
        warnings.append("dropped %d NOTE/STYLE/REGION block(s) from the VTT file" % meta["dropped"])
    locked = [s for s in segs if s.locked]
    if locked:
        warnings.append("%d dialogue cue(s) with several speakers were left untouched" % len(locked))

    edits, counts = [], collections.Counter()

    def log(cue_id, rule, before, after, **extra):
        counts["edits"] += 1
        if len(edits) < args.max_edits:
            edits.append(dict(cue_id=cue_id, rule=rule, before=before, after=after, **extra))

    before_items = [{"id": s.sid, "start": s.start, "end": s.end, "lines": s.raw.split("\n")}
                    for s in segs] if fmt != "plain" else []
    words_in = tokens([s.text for s in segs])

    # speakers
    label_counter = collections.Counter(s.label_raw for s in segs if s.label_raw and not s.locked)
    mapping, ambiguous = normalise_speakers(label_counter, glossary["speakers"]) if label_counter else ({}, [])
    for s in segs:
        if s.label_raw and not s.locked and s.label_raw in mapping:
            canon = mapping[s.label_raw][0]
            if canon != s.label_raw:
                log(s.sid, "speaker-label", s.label_raw, canon)
                counts["labels"] += 1
                s.dirty = True
            s.speaker = canon

    # text cleaning
    allowed = collections.Counter()
    kept = []
    for s in segs:
        if s.locked:
            kept.append(s)
            continue
        t0 = s.text
        t1, done = apply_terms(t0, terms)
        if done:
            counts["terms"] += len(done)
            allowed.update(tokens(done))
            log(s.sid, "glossary-term", t0, t1, replaced=done)
        t2, removed = (t1, [])
        if args.policy == "clean-verbatim":
            t2, w1 = drop_fillers(t1, WORD_FILLER_RE, False)
            t2, w2 = drop_fillers(t2, PHRASE_FILLER_RE, True)
            removed = w1 + w2
            if removed:
                counts["fillers"] += len(removed)
                t2 = tidy(t2)
                log(s.sid, "filler", t1, t2, removed=removed)
            t3, stut = drop_stutters(t2)
            if stut:
                counts["stutters"] += len(stut)
                log(s.sid, "stutter", t2, t3, removed=stut)
                t2 = t3
        if t2 != t0:
            s.dirty = True
        s.text = t2
        if not re.sub(r"[\W_]+", "", s.text):
            counts["empty"] += 1
            log(s.sid, "remove-empty", t0, "")
            continue
        kept.append(s)
    segs = kept

    # merge fragments
    if not args.no_merge:
        merged = []
        for s in segs:
            p = merged[-1] if merged else None
            if p and can_merge(p, s, fmt, args.merge_gap_ms):
                log(p.src[0], "merge", p.text + " | " + s.text, p.text + " " + s.text, source_cue_ids=p.src + s.src)
                counts["merged"] += 1
                p.text += " " + s.text
                p.end = s.end if s.end is not None else p.end
                p.src += s.src
                p.dirty = True
            else:
                merged.append(s)
        segs = merged

    words_out = tokens([s.text for s in segs])
    added = sorted((words_out - words_in - allowed).elements())
    rendered = render(segs, fmt, meta, had_blank)

    checks = {"applies": fmt != "plain"}
    if fmt != "plain":
        out_items = [{"id": str(i), "start": s.start, "end": s.end, "lines": seg_lines(s, fmt)}
                     for i, s in enumerate(segs, 1)]
        before = check_items(before_items)
        after = check_items(out_items)
        checks["limits"] = {"max_line_chars": MAX_LINE_CHARS, "max_lines": MAX_LINES,
                            "min_cue_ms": MIN_CUE_MS, "max_cue_ms": MAX_CUE_MS,
                            "max_chars_per_second": MAX_CPS, "min_gap_ms": MIN_GAP_MS}
        checks["before_counts"] = {c: len(before[c]) for c in CATEGORIES}
        checks["after"] = {c: {"count": len(after[c]), "evidence": after[c][:EVIDENCE_CAP]}
                           for c in CATEGORIES}
        issues_left = sum(len(v) for v in after.values())
    else:
        issues_left = 0

    seg_counts = collections.Counter(s.label_raw and mapping.get(s.label_raw, (s.label_raw,))[0]
                                     for s in kept if s.label_raw)
    report = {
        "tool": "clean_transcript", "schema": SCHEMA,
        "input": os.path.basename(args.input), "format": fmt, "policy": args.policy,
        "dry_run": bool(args.dry_run), "output": None,
        "status": "clean",
        "counts": {
            "segments_in": n_in, "segments_out": len(segs),
            "segments_changed": sum(1 for s in segs if s.dirty),
            "fillers_removed": counts["fillers"], "stutters_removed": counts["stutters"],
            "glossary_replacements": counts["terms"], "segments_merged": counts["merged"],
            "segments_removed_empty": counts["empty"], "speaker_labels_changed": counts["labels"],
            "dialogue_cues_untouched": len(locked),
        },
        "words": {"in": sum(words_in.values()), "out": sum(words_out.values()), "added": added},
        "speakers": {
            "labels": [{"label": k, "segments": v} for k, v in sorted(seg_counts.items())],
            "mapping": [{"from": k, "to": v[0], "reason": v[1]} for k, v in sorted(mapping.items()) if v[1]],
            "ambiguous": ambiguous,
        },
        "checks": checks,
        "edits": edits, "edits_truncated": counts["edits"] > len(edits),
        "warnings": warnings,
    }
    if added:
        warnings.append("integrity: output holds words not in the input or glossary: " + ", ".join(added[:20]))
    if issues_left or ambiguous or added:
        report["status"] = "needs_review"
    return report, rendered


def can_merge(prev, cur, fmt, merge_gap):
    if prev.locked or cur.locked or cur.para_break:
        return False
    if cur.speaker is not None and cur.speaker != prev.speaker:
        return False
    if not prev.text or not cur.text or FINISHED_RE.search(prev.text):
        return False
    first = first_alpha(cur.text)
    if not (prev.text[-1] in ",;:" or (first and first.islower())):
        return False
    if fmt in ("srt", "vtt"):
        if prev.end is None or cur.start is None or cur.end is None:
            return False
        gap = cur.start - prev.end
        if gap < 0 or gap > merge_gap:
            return False
        if cur.end - prev.start > MAX_CUE_MS:
            return False
        vis = len(prev.speaker) + 2 if (prev.show_label and prev.speaker and prev.style != "voice") else 0
        if vis + len(prev.text) + 1 + len(cur.text) > MAX_MERGED_CHARS:
            return False
    elif prev.start is not None and cur.start is not None and cur.start - prev.start > MAX_PLAIN_MERGE_MS:
        return False
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="Clean a raw transcript or subtitle file; never summarises.")
    ap.add_argument("input")
    ap.add_argument("--out-dir", help="directory for the cleaned file (required unless --dry-run)")
    ap.add_argument("--policy", choices=("clean-verbatim", "verbatim"), default="clean-verbatim")
    ap.add_argument("--glossary", help="JSON file: {\"speakers\": {alias: name}, \"terms\": {wrong: right}}")
    ap.add_argument("--format", choices=("auto", "srt", "vtt", "plain"), default="auto")
    ap.add_argument("--merge-gap", type=float, default=MERGE_GAP_MS / 1000.0, help="seconds; default 1.0")
    ap.add_argument("--no-merge", action="store_true")
    ap.add_argument("--max-edits", type=int, default=DEFAULT_MAX_EDITS)
    ap.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    args = ap.parse_args(argv)
    args.merge_gap_ms = int(round(args.merge_gap * 1000))

    if not os.path.isfile(args.input):
        print("error: input file not found: %s" % args.input, file=sys.stderr)
        return 2
    if not args.dry_run and not args.out_dir:
        print("error: give --out-dir DIR (or --dry-run)", file=sys.stderr)
        return 2
    warnings = []
    text = read_text(args.input, warnings)
    if not text.strip():
        print("error: input file is empty", file=sys.stderr)
        return 2
    fmt = detect_format(text) if args.format == "auto" else args.format
    try:
        report, rendered = run(args, text, fmt, warnings)
    except SystemExit as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    if not args.dry_run:
        ext = {"srt": ".srt", "vtt": ".vtt"}.get(fmt) or (os.path.splitext(args.input)[1] or ".txt")
        stem = os.path.splitext(os.path.basename(args.input))[0]
        out_path = os.path.join(args.out_dir, stem + ".cleaned" + ext)
        if os.path.abspath(out_path) == os.path.abspath(args.input):
            print("error: refusing to overwrite the input file", file=sys.stderr)
            return 2
        os.makedirs(args.out_dir, exist_ok=True)
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(rendered)
        report["output"] = os.path.basename(out_path)
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=True) + "\n")
    return 0 if report["status"] == "clean" else 1


if __name__ == "__main__":
    sys.exit(main())
