"""pdf_meta.py - read-only PDF metadata privacy check.

Usage:
    python -I scripts/pdf_meta.py INPUT.pdf

The input is read as bytes (2 MB cap). The script does not decompress streams
and does not rebuild the object graph. It pulls the Info dictionary keys
(Author, Creator, Producer, Title, Subject, Keywords, CreationDate, ModDate)
and four XMP fields with bounded scans, flags values that look like personal
names, e-mail addresses or local file paths, and prints one JSON object to
stdout. The input file is never written. The script writes no other file.

Exit codes: 0 = no flagged value, 1 = at least one flagged value,
2 = usage or input error (a one-line JSON error is printed to stdout).
Standard library only. No network, no subprocess, no eval or exec.
"""
import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
MAX_STRING = 512
MAX_NEST = 8
MAX_HITS_PER_KEY = 20
MAX_XMP_HITS = 20
INFO_KEYS = (b"Author", b"Creator", b"Producer", b"Title", b"Subject",
             b"Keywords", b"CreationDate", b"ModDate")
NAME_KEYS = ("Author", "dc:creator")
XMP_RE = re.compile(
    rb"<(dc:creator|xmp:CreatorTool|pdf:Producer|dc:title)(?:\s[^>]{0,200})?>"
    rb"(.{0,1024}?)</\1>", re.S)
TAG_RE = re.compile(rb"<[^>]{0,200}>")
HEX_RE = re.compile(rb"<([0-9A-Fa-f\s]{0,2048})>")
VERSION_RE = re.compile(rb"^%PDF-(\d\.\d)")
OBJSTM_RE = re.compile(rb"/ObjStm")
NAME_RE = re.compile(r"^[A-Z][a-z]{1,30}(?:[ .-][A-Z][A-Za-z.'-]{0,30}){1,2}$")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,255}\.[A-Za-z]{2,24}")
PATH_RE = re.compile(r"[A-Za-z]:\\[^\s]{1,200}|/(?:Users|home)/[^\s]{1,200}")
ESCAPES = {ord("n"): 10, ord("r"): 13, ord("t"): 9, ord("b"): 8, ord("f"): 12,
           ord("("): 40, ord(")"): 41, ord("\\"): 92}
ADVICE = {
    "e-mail address": "Remove the address from the document properties or replace it with a role mailbox.",
    "local file path": "The value exposes a folder layout. Re-export from the source program with metadata removed.",
    "possible personal name": "Clear the Author field or replace it with a team or role name.",
}


def fail(message):
    sys.stdout.write(json.dumps({"error": message}) + "\n")
    sys.exit(2)


def read_literal(data, start):
    """Parse a literal string whose opening parenthesis is data[start].

    Returns (raw_bytes, end_index) or None when nesting or length caps are hit.
    """
    out = bytearray()
    depth = 0
    limit = min(len(data), start + MAX_STRING * 4)
    j = start
    while j < limit:
        c = data[j]
        if c == 0x28:
            depth += 1
            if depth > MAX_NEST:
                return None
            if depth > 1:
                out.append(c)
        elif c == 0x29:
            depth -= 1
            if depth == 0:
                return bytes(out), j + 1
            out.append(c)
        elif c == 0x5C:
            j += 1
            if j >= limit:
                break
            e = data[j]
            if 0x30 <= e <= 0x37:
                k = j
                value = 0
                while k < j + 3 and k < limit and 0x30 <= data[k] <= 0x37:
                    value = value * 8 + data[k] - 0x30
                    k += 1
                out.append(value & 0xFF)
                j = k - 1
            elif e in ESCAPES:
                out.append(ESCAPES[e])
            elif e not in (0x0D, 0x0A):
                out.append(e)
        else:
            out.append(c)
        if len(out) > MAX_STRING:
            return None
        j += 1
    return None


def read_hex(data, start):
    match = HEX_RE.match(data, start)
    if not match:
        return None
    digits = re.sub(rb"\s", b"", match.group(1))
    if len(digits) % 2:
        digits += b"0"
    return bytes.fromhex(digits.decode("ascii"))[:MAX_STRING]


def decode_text(raw):
    if raw.startswith(b"\xfe\xff"):
        text = raw[2:].decode("utf-16-be", errors="replace")
    else:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
    text = "".join(ch if ch.isprintable() else "?" for ch in text)
    return " ".join(text.split())[:MAX_STRING]


def scan_info(data, notes):
    entries = []
    for key in INFO_KEYS:
        name = key.decode("ascii")
        pattern = re.compile(rb"/" + key + rb"(?![A-Za-z])")
        for hits, match in enumerate(pattern.finditer(data), start=1):
            if hits > MAX_HITS_PER_KEY:
                notes.append(name + ": more than 20 occurrences, the rest were skipped")
                break
            j = match.end()
            while j < min(len(data), match.end() + 4) and data[j] in b" \t\r\n":
                j += 1
            raw = None
            if j < len(data) and data[j] == 0x28:
                got = read_literal(data, j)
                if got is None:
                    notes.append(name + ": literal string too deeply nested or too long, skipped")
                else:
                    raw = got[0]
            elif j < len(data) and data[j] == 0x3C and data[j + 1:j + 2] != b"<":
                raw = read_hex(data, j)
            else:
                notes.append(name + ": indirect reference or non-string value, not followed")
                continue
            if raw:
                value = decode_text(raw)
                if value:
                    entries.append({"key": name, "value": value, "source": "info"})
    return entries


def scan_xmp(data):
    entries = []
    for hits, match in enumerate(XMP_RE.finditer(data), start=1):
        if hits > MAX_XMP_HITS:
            break
        text = TAG_RE.sub(b" ", match.group(2))
        value = decode_text(text)
        if value:
            entries.append({"key": match.group(1).decode("ascii"), "value": value, "source": "xmp"})
    return entries


def flag_entries(entries):
    flags = []
    for entry in entries:
        value = entry["value"]
        reasons = []
        if EMAIL_RE.search(value):
            reasons.append("e-mail address")
        if PATH_RE.search(value):
            reasons.append("local file path")
        if entry["key"] in NAME_KEYS and NAME_RE.match(value):
            reasons.append("possible personal name")
        for reason in reasons:
            flags.append({"key": entry["key"], "value": value, "reason": reason})
    return flags


def main(argv):
    if len(argv) != 2:
        fail("usage: pdf_meta.py INPUT.pdf")
    path = argv[1]
    if not os.path.isfile(path):
        fail("input is not a readable regular file")
    try:
        if os.path.getsize(path) > MAX_BYTES:
            fail("input is larger than 2 MB")
        with open(path, "rb") as handle:
            data = handle.read(MAX_BYTES + 1)
    except OSError:
        fail("input could not be read")
    if len(data) > MAX_BYTES:
        fail("input is larger than 2 MB")
    version = VERSION_RE.match(data)
    if not version:
        fail("input does not start with a %PDF- header")

    notes = []
    entries = scan_info(data, notes) + scan_xmp(data)
    flags = flag_entries(entries)
    if OBJSTM_RE.search(data):
        notes.append("compressed object streams present: entries inside them are not read, "
                     "so a missing entry is not proof of a clean file")
    advice = sorted({ADVICE[f["reason"]] for f in flags})
    result = {
        "file": os.path.basename(path),
        "size_bytes": len(data),
        "pdf_version": version.group(1).decode("ascii"),
        "entries": entries,
        "flags": flags,
        "objstm_present": bool(OBJSTM_RE.search(data)),
        "notes": notes,
        "scrub_advice": advice,
    }
    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=True) + "\n")
    return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
