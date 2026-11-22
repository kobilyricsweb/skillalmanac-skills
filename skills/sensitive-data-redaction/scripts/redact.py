#!/usr/bin/env python3
"""Redact sensitive values in a text, log or JSON file, and restore them later.

    python redact.py redact <file> [--out-dir DIR] [--names FILE] [--terms FILE]
                     [--mapping PATH] [--keep-last4] [--keep-private-ips]
                     [--skip CAT,CAT] [--force] [--dry-run]
    python redact.py restore <file> --mapping PATH [--out PATH] [--force]

redact reads <file> (UTF-8; a .json file is parsed and every string, number and
key is scanned, other files are scanned as text) and writes, next to the input
or in --out-dir:
    <stem>.redacted<ext>            the text with placeholders such as [EMAIL_1]
    <stem>.redaction_report.json    counts, locations and review samples, never values
It also writes the private mapping (placeholder -> original) to --mapping when
given. The report is printed to stdout. Detected values are never printed.

restore replaces placeholders in <file> (for example an AI answer) with the
originals from the mapping and writes <stem>.restored<ext>, or --out.

Detected classes (in priority order): PRIVATE_KEY, API_KEY, URL_TOKEN, CREDENTIAL,
EMAIL, IBAN, CARD, SSN, IPV6, IPV4, PHONE, plus NAME and TERM only from the lists
you supply. Detection is by content, never by file name.

Exit codes: 0 done (zero matches is still 0), 2 usage or file error.
Standard library only; no network; reads and writes only the paths given.
"""
import argparse
import bisect
import ipaddress
import json
import os
import re
import sys

VERSION = "1"
# Refuse very large inputs: the whole file is held in memory twice.
MAX_BYTES = 20 * 1024 * 1024
# Characters of redacted context shown each side of a review sample.
SAMPLE_CONTEXT = 40
# Review samples kept per category; enough to spot a false-positive pattern.
MAX_SAMPLES = 3
# Locations kept per category in the report; the count stays exact.
MAX_LOCATIONS = 100
# Card numbers are 13 to 19 digits (ISO/IEC 7812); first digit 2-6 covers the major networks.
CARD_MIN, CARD_MAX, CARD_FIRST = 13, 19, "23456"
# IBANs are 15 to 34 characters.
IBAN_MIN, IBAN_MAX = 15, 34
# A card number is never split into more groups than this.
CARD_MAX_GROUPS = 8
# Shortest alias accepted from a names or terms list; shorter ones match too much.
ALIAS_MIN = 3

CATEGORIES = ["PRIVATE_KEY", "API_KEY", "URL_TOKEN", "CREDENTIAL", "EMAIL", "IBAN",
              "CARD", "SSN", "IPV6", "IPV4", "PHONE", "NAME", "TERM"]
PLACEHOLDER_PREFIX = {"NAME": "PERSON"}
LAST4_CATEGORIES = {"CARD", "IBAN", "PHONE", "SSN"}
HEURISTIC_NOTES = {
    "PHONE": "Heuristic: digit groups with separators or a leading +. Bare digit runs and short local numbers are not detected.",
    "IPV4": "Any dotted quad of valid octets, so version strings such as 1.2.3.4 are redacted too.",
    "CARD": "Luhn check passes for about 1 in 10 random digit runs of this length; order or tracking numbers can match.",
    "IBAN": "Mod-97 check; a random string passes with probability about 1 in 97.",
    "SSN": "US pattern only (NNN-NN-NNNN with invalid ranges excluded); other countries' ID numbers are not detected.",
    "CREDENTIAL": "Matches password, secret or token assignments and Bearer values by name; a secret with no such label is not detected.",
    "NAME": "Only the names you listed; misspellings, nicknames and unlisted people stay in the text.",
    "TERM": "Only the terms you listed.",
}

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}")
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----(?:[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----)?")
API_KEY_RES = [
    re.compile(r"(?<![A-Za-z0-9])(?:AKIA|ASIA)[0-9A-Z]{16}(?![A-Za-z0-9])"),
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(r"(?<![A-Za-z0-9])xox[abprs]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"(?<![A-Za-z0-9_\-])eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"),
]
URL_RE = re.compile(r"https?://[^\s\"'<>\[\]{}|\\^`]+", re.I)
USERINFO_RE = re.compile(r"^https?://[^/\s:@]+:([^@/\s]+)@", re.I)
PARAM_RE = re.compile(r"([?&;])([A-Za-z0-9_.\-]+)=([^&#;\s]*)")
SECRET_PARAMS = {"token", "access_token", "refresh_token", "id_token", "api_key", "apikey", "key",
                 "secret", "client_secret", "password", "passwd", "pwd", "pass", "sig", "signature",
                 "auth", "authorization", "session", "sessionid", "sid", "jwt", "code",
                 "x-amz-signature", "x-amz-credential", "x-amz-security-token"}
SECRET_PARAM_SUFFIXES = ("_token", "_secret", "_password", "_apikey", "_api_key")
CRED_ASSIGN_RE = re.compile(
    r"\b(?:password|passwd|pwd|secret|client_secret|api[_\-]?key|access[_\-]?token|auth[_\-]?token|token)\b[\"']?\s*[:=]\s*[\"']?([^\s\"',;&]{4,})",
    re.I)
BEARER_RE = re.compile(r"\bbearer\s+([A-Za-z0-9._~+/=\-]{16,})", re.I)
CRED_SKIP_VALUES = {"null", "none", "true", "false", "undefined", "****", "***"}
CRED_JSON_KEYS = {"password", "passwd", "pwd", "secret", "client_secret", "api_key", "apikey",
                  "access_token", "refresh_token", "auth_token", "token", "authorization", "private_key"}
IBAN_START_RE = re.compile(r"(?<![A-Za-z0-9])[A-Z]{2}\d{2}(?=[ ]?[A-Z0-9])")
IBAN_UNIT_RE = re.compile(r"[ ]?[A-Z0-9]{1,4}")
CARD_RUN_RE = re.compile(r"(?<!\d)\d+(?:[ \-]\d+)*(?!\d)")
SSN_RE = re.compile(r"(?<![\d\-])(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}(?![\d\-])")
IPV4_RE = re.compile(r"(?<![\w.])\d{1,3}(?:\.\d{1,3}){3}(?!\w|\.\d)")
IPV6_RE = re.compile(r"(?<![\w:])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?!\w)")
PHONE_RE = re.compile(r"(?<![\w+.\-(])[+(]?\d[\d ().\-]{6,19}\d(?![\w\-:])")
PRIVATE_V4 = [ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")]
TOKEN_RE = re.compile(r"\[([A-Z][A-Z0-9]*(?:_[A-Z][A-Z0-9]*)*_\d+)(?: \*{4}[A-Za-z0-9]{0,6})?\]")


# ---------------------------------------------------------------- validators
def luhn_ok(digits):
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


def iban_ok(compact):
    if not (IBAN_MIN <= len(compact) <= IBAN_MAX):
        return False
    moved = compact[4:] + compact[:4]
    try:
        number = "".join(str(int(c, 36)) for c in moved)
    except ValueError:
        return False
    return int(number) % 97 == 1


def phone_ok(raw):
    digits = re.sub(r"\D", "", raw)
    n = len(digits)
    if n < 9 or n > 15:
        return False
    groups = re.findall(r"\d+", raw)
    if len(groups) < 2 or len(groups) > 6:
        return False
    if re.fullmatch(r"\d{4}[-./]\d{1,2}[-./]\d{1,2}|\d{1,2}[-./]\d{1,2}[-./]\d{2,4}", raw):
        return False
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", raw):
        return False
    if all(len(g) == 4 for g in groups) and groups[0][:2] in ("19", "20"):
        return False
    if raw.startswith("+"):
        return True
    if n < 10:
        return False
    if "(" in raw:
        return True
    has_space, has_hyphen, has_dot = " " in raw, "-" in raw, "." in raw
    if has_dot and not has_space and not has_hyphen:
        return re.fullmatch(r"\d{2,4}\.\d{3,4}\.\d{3,4}", raw) is not None
    if has_hyphen and not has_space and not has_dot:
        return len(groups) <= 5 and n <= 13
    if has_space and not has_hyphen and not has_dot:
        return all(len(g) >= 3 for g in groups)
    return True


# ------------------------------------------------------------------- finders
def find_private_key(text, ctx):
    return [(m.start(), m.end(), m.group(0)) for m in PRIVATE_KEY_RE.finditer(text)]


def find_api_key(text, ctx):
    out = []
    for rx in API_KEY_RES:
        out.extend((m.start(), m.end(), m.group(0)) for m in rx.finditer(text))
    return sorted(out)


def find_url_token(text, ctx):
    out = []
    for m in URL_RE.finditer(text):
        url = m.group(0).rstrip(".,;:!?)")
        base = m.start()
        ui = USERINFO_RE.match(url)
        if ui:
            out.append((base + ui.start(1), base + ui.end(1), ui.group(1)))
        for pm in PARAM_RE.finditer(url):
            name = pm.group(2).lower()
            if (name in SECRET_PARAMS or name.endswith(SECRET_PARAM_SUFFIXES)) and pm.group(3):
                out.append((base + pm.start(3), base + pm.end(3), pm.group(3)))
    return sorted(out)


def find_credential(text, ctx):
    out = []
    for rx in (CRED_ASSIGN_RE, BEARER_RE):
        for m in rx.finditer(text):
            if m.group(1).lower() not in CRED_SKIP_VALUES:
                out.append((m.start(1), m.end(1), m.group(1)))
    return sorted(out)


def find_email(text, ctx):
    return [(m.start(), m.end(), m.group(0)) for m in EMAIL_RE.finditer(text)]


def find_iban(text, ctx):
    out = []
    for m in IBAN_START_RE.finditer(text):
        compact, pos, best = m.group(0), m.end(), None
        while True:
            um = IBAN_UNIT_RE.match(text, pos)
            if not um:
                break
            piece = um.group(0).replace(" ", "")
            if len(compact) + len(piece) > IBAN_MAX:
                break
            compact += piece
            pos = um.end()
            if len(compact) >= IBAN_MIN and not (pos < len(text) and text[pos].isalnum()) and iban_ok(compact):
                best = pos
        if best:
            out.append((m.start(), best, text[m.start():best]))
    return out


def find_card(text, ctx):
    out = []
    for run in CARD_RUN_RE.finditer(text):
        groups = [(g.group(0), run.start() + g.start(), run.start() + g.end())
                  for g in re.finditer(r"\d+", run.group(0))]
        i = 0
        while i < len(groups):
            found = None
            for j in range(min(len(groups), i + CARD_MAX_GROUPS) - 1, i - 1, -1):
                digits = "".join(g[0] for g in groups[i:j + 1])
                if (CARD_MIN <= len(digits) <= CARD_MAX and digits[0] in CARD_FIRST
                        and len(set(digits)) > 1 and luhn_ok(digits)):
                    found = j
                    break
            if found is None:
                i += 1
            else:
                s, e = groups[i][1], groups[found][2]
                out.append((s, e, text[s:e]))
                i = found + 1
    return out


def find_ssn(text, ctx):
    return [(m.start(), m.end(), m.group(0)) for m in SSN_RE.finditer(text)]


def find_ipv6(text, ctx):
    out = []
    for m in IPV6_RE.finditer(text):
        raw = m.group(0)
        candidates = [raw]
        if raw.endswith(":") and not raw.endswith("::"):
            candidates.append(raw[:-1])
        for cand in candidates:
            try:
                ip = ipaddress.IPv6Address(cand)
            except ValueError:
                continue
            if not (ip.is_loopback or ip.is_unspecified):
                out.append((m.start(), m.start() + len(cand), cand))
            break
    return out


def find_ipv4(text, ctx):
    out = []
    for m in IPV4_RE.finditer(text):
        try:
            ip = ipaddress.IPv4Address(m.group(0))
        except ValueError:
            continue
        if ip.is_loopback or ip.is_unspecified or ip == ipaddress.IPv4Address("255.255.255.255"):
            continue
        if ctx["keep_private_ips"] and any(ip in net for net in PRIVATE_V4):
            continue
        out.append((m.start(), m.end(), m.group(0)))
    return out


def find_phone(text, ctx):
    return [(m.start(), m.end(), m.group(0)) for m in PHONE_RE.finditer(text) if phone_ok(m.group(0))]


def listed_finder(regex, alias_group):
    def finder(text, ctx):
        return [(m.start(), m.end(), m.group(0)) for m in regex.finditer(text)]
    return finder


FINDERS = {"PRIVATE_KEY": find_private_key, "API_KEY": find_api_key, "URL_TOKEN": find_url_token,
           "CREDENTIAL": find_credential, "EMAIL": find_email, "IBAN": find_iban, "CARD": find_card,
           "SSN": find_ssn, "IPV6": find_ipv6, "IPV4": find_ipv4, "PHONE": find_phone}


def normalise(cat, raw, groups):
    if cat == "EMAIL":
        return raw.lower()
    if cat in ("CARD", "SSN", "PHONE"):
        return ("+" if raw.startswith("+") else "") + re.sub(r"\D", "", raw)
    if cat == "IBAN":
        return raw.replace(" ", "").upper()
    if cat in ("IPV4", "IPV6"):
        return str(ipaddress.ip_address(raw))
    if cat in ("NAME", "TERM"):
        return groups.get(re.sub(r"\s+", " ", raw.lower()), raw.lower())
    return raw


def last4(cat, raw):
    chars = re.sub(r"[^A-Za-z0-9]", "", raw)
    return chars[-4:]


# ------------------------------------------------------------------ redactor
class Redactor:
    def __init__(self, skip, keep_last4, keep_private_ips, names, terms):
        self.skip = skip
        self.keep_last4 = keep_last4
        self.ctx = {"keep_private_ips": keep_private_ips}
        self.groups = {}
        self.extra = {}
        self.warnings = []
        for cat, aliases_by_group in (("NAME", names), ("TERM", terms)):
            regex = self._build_list_regex(cat, aliases_by_group)
            if regex is not None and cat not in skip:
                self.extra[cat] = listed_finder(regex, None)
        self.index, self.next, self.originals = {}, {}, {}
        self.counts, self.unique, self.locs, self.loc_total = {}, {}, {}, {}
        self.samples, self.sample_n = [], {}

    def _build_list_regex(self, cat, lines):
        aliases = []
        for group in lines:
            key = re.sub(r"\s+", " ", group[0].lower())
            for alias in group:
                if len(alias) < ALIAS_MIN:
                    self.warnings.append(f"{cat} alias shorter than {ALIAS_MIN} characters ignored (matches too much)")
                    continue
                norm = re.sub(r"\s+", " ", alias.lower())
                self.groups[norm] = key
                aliases.append(alias)
        if not aliases:
            return None
        aliases.sort(key=len, reverse=True)
        body = "|".join(r"\s+".join(re.escape(w) for w in a.split()) for a in aliases)
        return re.compile(r"(?<!\w)(?:" + body + r")(?!\w)", re.I)

    def find(self, text, forced=None):
        mask = bytearray(len(text))
        accepted = []

        def take(cat, s, e, raw):
            if e > s and not any(mask[s:e]):
                mask[s:e] = b"\x01" * (e - s)
                accepted.append((s, e, cat, raw))

        if forced:
            take(forced, 0, len(text), text)
        for cat in CATEGORIES:
            if cat in self.skip:
                continue
            finder = FINDERS.get(cat) or self.extra.get(cat)
            if finder:
                for s, e, raw in finder(text, self.ctx):
                    take(cat, s, e, raw)
        return sorted(accepted)

    def token_for(self, cat, raw):
        key = (cat, normalise(cat, raw, self.groups))
        if key not in self.index:
            self.next[cat] = self.next.get(cat, 0) + 1
            self.index[key] = f"[{PLACEHOLDER_PREFIX.get(cat, cat)}_{self.next[cat]}]"
            self.originals[self.index[key]] = raw
            self.unique[cat] = self.unique.get(cat, 0) + 1
        return self.index[key]

    def process(self, text, locator, forced=None):
        matches = self.find(text, forced)
        if not matches:
            return text
        pieces, last, outlen, marks = [], 0, 0, []
        for s, e, cat, raw in matches:
            pieces.append(text[last:s])
            outlen += s - last
            token = self.token_for(cat, raw)
            rep = token
            if self.keep_last4 and cat in LAST4_CATEGORIES and len(raw) >= 8:
                rep = f"{token[:-1]} ****{last4(cat, raw)}]"
            marks.append((cat, outlen, len(rep), locator(s)))
            pieces.append(rep)
            outlen += len(rep)
            last = e
        pieces.append(text[last:])
        out = "".join(pieces)
        for cat, pos, length, loc in marks:
            self.counts[cat] = self.counts.get(cat, 0) + 1
            self.loc_total[cat] = self.loc_total.get(cat, 0) + 1
            bucket = self.locs.setdefault(cat, [])
            if len(bucket) < MAX_LOCATIONS and (not bucket or bucket[-1] != loc):
                bucket.append(loc)
            if self.sample_n.get(cat, 0) < MAX_SAMPLES:
                self.sample_n[cat] = self.sample_n.get(cat, 0) + 1
                ctx = out[max(0, pos - SAMPLE_CONTEXT):pos + length + SAMPLE_CONTEXT]
                self.samples.append({"category": cat, "location": loc,
                                     "context": re.sub(r"\s+", " ", ctx)})
        return out


# ------------------------------------------------------------------ file I/O
def read_text(path, warnings):
    try:
        size = os.path.getsize(path)
    except OSError as exc:
        raise SystemExit(f"cannot read {path}: {exc.strerror}")
    if size == 0:
        raise SystemExit(f"{path} is empty; nothing to do")
    if size > MAX_BYTES:
        raise SystemExit(f"{path} is {size} bytes; the limit is {MAX_BYTES}. Split the file first")
    raw = open(path, "rb").read()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        warnings.append("input is not valid UTF-8; decoded as cp1252 and written back as UTF-8")
        return raw.decode("cp1252", errors="replace")


def load_list(path, kind):
    if not os.path.isfile(path):
        raise SystemExit(f"{kind} file not found: {path}")
    groups = []
    for line in open(path, encoding="utf-8-sig").read().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            groups.append([a.strip() for a in line.split("|") if a.strip()])
    return groups


def same_file(a, b):
    if os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b)):
        return True
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


def refuse_input_overwrite(inputs, outputs):
    """Never write over an input file, with or without --force."""
    for label, out in outputs:
        if not out:
            continue
        for src in inputs:
            if src and same_file(out, src):
                raise SystemExit(f"refusing to write {label} over an input file ({os.path.basename(src)}); choose a different path")


def write_new(path, text, force):
    if os.path.exists(path) and not force:
        raise SystemExit(f"{path} already exists; use --force to overwrite")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def walk_json(node, path, red):
    if isinstance(node, str):
        return red.process(node, lambda p: path)
    if isinstance(node, bool) or node is None or isinstance(node, float):
        return node
    if isinstance(node, int):
        as_text = str(node)
        out = red.process(as_text, lambda p: path)
        return out if out != as_text else node
    if isinstance(node, list):
        return [walk_json(v, f"{path}[{i}]", red) for i, v in enumerate(node)]
    if isinstance(node, dict):
        result = {}
        for key, value in node.items():
            new_key = red.process(key, lambda p: path + ".<key>")
            base = new_key
            n = 1
            while new_key in result:
                n += 1
                new_key = f"{base}#{n}"
            child = f"{path}.{new_key}"
            if isinstance(value, str) and value and key.lower() in CRED_JSON_KEYS and "CREDENTIAL" not in red.skip:
                result[new_key] = red.process(value, lambda p: child, forced="CREDENTIAL")
            else:
                result[new_key] = walk_json(value, child, red)
        return result
    return node


def cmd_redact(args):
    warnings = []
    names = load_list(args.names, "names") if args.names else []
    terms = load_list(args.terms, "terms") if args.terms else []
    skip = set()
    if args.skip:
        skip = {c.strip().upper() for c in args.skip.split(",") if c.strip()}
        unknown = sorted(skip - set(CATEGORIES))
        if unknown:
            raise SystemExit(f"unknown category in --skip: {', '.join(unknown)}. Valid: {', '.join(CATEGORIES)}")
    text = read_text(args.input, warnings)
    red = Redactor(skip, args.keep_last4, args.keep_private_ips, names, terms)
    warnings.extend(red.warnings)
    existing = TOKEN_RE.findall(text)
    if existing:
        warnings.append(f"input already contains {len(existing)} placeholder-like tokens such as [EMAIL_1]; restore may mix them up")

    ext = os.path.splitext(args.input)[1]
    mode = "text"
    out_text = None
    if ext.lower() == ".json":
        try:
            data = json.loads(text)
            mode = "json"
        except ValueError:
            warnings.append("file has a .json name but is not valid JSON; scanned as plain text")
    if mode == "json":
        out_text = json.dumps(walk_json(data, "$", red), indent=2, ensure_ascii=False) + "\n"
    else:
        starts = [0] + [i + 1 for i, c in enumerate(text) if c == "\n"]
        out_text = red.process(text, lambda p: "L" + str(bisect.bisect_right(starts, p)))

    out_dir = args.out_dir or os.path.dirname(os.path.abspath(args.input))
    stem = os.path.splitext(os.path.basename(args.input))[0]
    out_path = os.path.join(out_dir, f"{stem}.redacted{ext}")
    report_path = os.path.join(out_dir, f"{stem}.redaction_report.json")
    mapping_path = args.mapping
    refuse_input_overwrite([args.input, args.names, args.terms],
                           [("the redacted copy", out_path), ("the report", report_path), ("the mapping", mapping_path)])
    if mapping_path and os.path.dirname(os.path.abspath(mapping_path)) == os.path.abspath(out_dir):
        warnings.append("the private mapping is in the same folder as the redacted output; move it before sharing that folder")
    if not red.counts:
        warnings.append("no sensitive values were detected; this does not prove none are present")
    total = sum(red.counts.values())
    report = {
        "tool": "redact.py", "version": VERSION, "mode": mode,
        "input": os.path.basename(args.input), "redacted_file": os.path.basename(out_path),
        "mapping_written": bool(mapping_path) and not args.dry_run, "dry_run": bool(args.dry_run),
        "keep_last4": bool(args.keep_last4), "total_replacements": total,
        "counts": {c: {"matches": red.counts[c], "unique": red.unique.get(c, 0)} for c in CATEGORIES if c in red.counts},
        "locations": {c: red.locs[c] for c in CATEGORIES if c in red.locs},
        "locations_truncated": sorted(c for c in red.locs if red.loc_total[c] > len(red.locs[c])),
        "samples": red.samples, "warnings": warnings,
        "notes": {c: HEURISTIC_NOTES[c] for c in CATEGORIES if c in red.counts and c in HEURISTIC_NOTES},
        "limits": "Redaction is not anonymization. Free-text names, addresses and context that identifies a person are not detected unless listed.",
    }
    if not args.dry_run:
        if not os.path.isdir(out_dir):
            raise SystemExit(f"output folder does not exist: {out_dir}")
        write_new(out_path, out_text, args.force)
        write_new(report_path, json.dumps(report, indent=2) + "\n", args.force)
        if mapping_path:
            mapping = {"version": VERSION, "warning": "Contains the original sensitive values. Never share or upload this file.",
                       "tokens": red.originals}
            write_new(mapping_path, json.dumps(mapping, indent=2, ensure_ascii=False) + "\n", args.force)
            try:
                os.chmod(mapping_path, 0o600)
            except OSError:
                pass
    print(json.dumps(report, indent=2))
    return 0


def cmd_restore(args):
    warnings = []
    text = read_text(args.input, warnings)
    try:
        mapping = json.load(open(args.mapping, encoding="utf-8"))["tokens"]
    except (OSError, ValueError, KeyError, TypeError):
        raise SystemExit(f"cannot read a mapping from {args.mapping}; it must be the file written by redact --mapping")
    is_json = os.path.splitext(args.input)[1].lower() == ".json"
    restored, unknown = {}, set()

    def sub(m):
        token = f"[{m.group(1)}]"
        if token not in mapping:
            unknown.add(token)
            return m.group(0)
        cat = m.group(1).rsplit("_", 1)[0]
        restored[cat] = restored.get(cat, 0) + 1
        value = mapping[token]
        return json.dumps(value, ensure_ascii=False)[1:-1] if is_json else value

    out = TOKEN_RE.sub(sub, text)
    ext = os.path.splitext(args.input)[1]
    stem = os.path.splitext(os.path.basename(args.input))[0]
    out_path = args.out or os.path.join(os.path.dirname(os.path.abspath(args.input)), f"{stem}.restored{ext}")
    refuse_input_overwrite([args.input, args.mapping], [("the restored file", out_path)])
    write_new(out_path, out, args.force)
    print(json.dumps({"tool": "redact.py", "command": "restore", "output": os.path.basename(out_path),
                      "restored": restored, "unknown_tokens": sorted(unknown),
                      "warnings": ["the restored file contains the original sensitive values; do not share it"]}, indent=2))
    return 0


def build_parser():
    p = argparse.ArgumentParser(description="Redact or restore sensitive values in a text, log or JSON file.")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("redact", help="write a redacted copy and a report")
    r.add_argument("input")
    r.add_argument("--out-dir", help="folder for the redacted file and report (default: the input's folder)")
    r.add_argument("--names", help="file of names, one per line; 'Dana Reyes | Dana | Ms. Reyes' lists aliases of one person")
    r.add_argument("--terms", help="file of other terms to redact, one per line (client, project, host names)")
    r.add_argument("--mapping", help="write the private placeholder-to-original mapping here (needed for restore)")
    r.add_argument("--keep-last4", action="store_true", help="show the last 4 characters of cards, IBANs, phones and SSNs")
    r.add_argument("--keep-private-ips", action="store_true", help="leave 10.x, 172.16-31.x and 192.168.x addresses alone")
    r.add_argument("--skip", help="comma-separated categories not to redact, e.g. PHONE,IPV4")
    r.add_argument("--force", action="store_true", help="overwrite existing output files")
    r.add_argument("--dry-run", action="store_true", help="print the report, write nothing")
    t = sub.add_parser("restore", help="put the originals back using the mapping")
    t.add_argument("input")
    t.add_argument("--mapping", required=True)
    t.add_argument("--out")
    t.add_argument("--force", action="store_true")
    return p


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    try:
        return cmd_redact(args) if args.command == "redact" else cmd_restore(args)
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print("error: " + exc.code, file=sys.stderr)
            return 2
        raise


if __name__ == "__main__":
    sys.exit(main())
