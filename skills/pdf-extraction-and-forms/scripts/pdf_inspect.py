#!/usr/bin/env python3
"""Byte-level PDF triage. Standard library only, read-only, no network.

    python pdf_inspect.py <file.pdf>

Prints one strict JSON object to stdout (no NaN, ASCII only). It reads the
file once and writes nothing.

Exit codes: 0 = inspected, 2 = usage error, unreadable file or not a PDF
(the JSON still carries "ok": false and an "error" text).

What it does: scans the raw bytes for indirect objects ("N G obj"), inflates
FlateDecode content streams with zlib, and reports page count, a text-layer
verdict, AcroForm field names, types and current values, and encryption.

What it is NOT: a PDF parser. It never follows the cross-reference table, so
objects stored inside compressed object streams (/ObjStm, common in PDF 1.5+
files) and everything in an encrypted file are invisible to it. When that
matters the report says so in "warnings" and the verdict becomes "unknown".
"""
import json
import re
import sys
import zlib

MAX_FILE_BYTES = 200 * 1024 * 1024    # refuse bigger files: whole-file read, keep memory bounded
MAX_STREAM_BYTES = 8 * 1024 * 1024    # inflate cap per stream: stops decompression bombs
MAX_TOTAL_INFLATED = 96 * 1024 * 1024  # inflate cap for the whole file
PARENT_DEPTH = 12                      # field hierarchy depth we are willing to follow

OBJ_RE = re.compile(rb"(?<![0-9])(\d{1,10})\s+(\d{1,5})\s+obj\b")
PAGE_RE = re.compile(rb"/Type\s*/Page(?![A-Za-z])")
PAGES_RE = re.compile(rb"/Type\s*/Pages(?![A-Za-z])")
FONT_RE = re.compile(rb"/Type\s*/Font(?![A-Za-z])")
IMAGE_RE = re.compile(rb"/Subtype\s*/Image(?![A-Za-z])")
TEXT_OP_RE = re.compile(rb"(\((?:\\.|[^\\()])+\)|<[0-9A-Fa-f\s]+>)\s*Tj|\[[^\]]*[(<][^\]]*\]\s*TJ", re.S)
INVISIBLE_RE = re.compile(rb"(?<![0-9.])3\s+Tr\b")
SKIP_STREAM_RE = re.compile(rb"/Subtype\s*/Image|/Type\s*/XRef|/Type\s*/ObjStm|/Type\s*/Metadata|/Length1|/Subtype\s*/(Type1C|CIDFontType0C|OpenType)|/FunctionType|/ShadingType|/ICCBased|/N\s+[134]\s")


def _num_after(body, key):
    m = re.search(rb"/" + key + rb"\s+(-?\d+)(?![\d.])", body)
    return int(m.group(1)) if m else None


def _ref_after(body, key):
    m = re.search(rb"/" + key + rb"\s+(\d+)\s+\d+\s+R", body)
    return int(m.group(1)) if m else None


def _pdf_string(raw):
    """Decode the bytes of a literal (...) or hex <...> string to text."""
    if raw[:1] == b"<":
        h = re.sub(rb"[^0-9A-Fa-f]", b"", raw)
        if len(h) % 2:
            h += b"0"
        data = bytes.fromhex(h.decode("ascii"))
    else:
        inner, out, i = raw[1:-1], bytearray(), 0
        esc = {ord("n"): 10, ord("r"): 13, ord("t"): 9, ord("b"): 8, ord("f"): 12}
        while i < len(inner):
            c = inner[i]
            if c == 92 and i + 1 < len(inner):
                n = inner[i + 1]
                if 48 <= n <= 55:
                    j = i + 1
                    while j < len(inner) and j < i + 4 and 48 <= inner[j] <= 55:
                        j += 1
                    out.append(int(inner[i + 1:j], 8) & 255)
                    i = j
                    continue
                if n in (10, 13):
                    i += 2
                    continue
                out.append(esc.get(n, n))
                i += 2
                continue
            out.append(c)
            i += 1
        data = bytes(out)
    if data[:2] == b"\xfe\xff":
        return data[2:].decode("utf-16-be", "replace")
    if data[:3] == b"\xef\xbb\xbf":
        return data[3:].decode("utf-8", "replace")
    return data.decode("latin-1")


def _string_after(body, key):
    """Value of /Key (...) or /Key <...> as text, or None."""
    m = re.search(rb"/" + key + rb"(?![A-Za-z])\s*", body)
    if not m:
        return None
    i = m.end()
    if body[i:i + 1] == b"(":
        depth, j = 0, i
        while j < len(body):
            c = body[j:j + 1]
            if c == b"\\":
                j += 2
                continue
            if c == b"(":
                depth += 1
            elif c == b")":
                depth -= 1
                if depth == 0:
                    return _pdf_string(body[i:j + 1])
            j += 1
        return None
    if body[i:i + 1] == b"<" and body[i + 1:i + 2] != b"<":
        j = body.find(b">", i)
        return _pdf_string(body[i:j + 1]) if j > 0 else None
    return None


def _name_after(body, key):
    m = re.search(rb"/" + key + rb"(?![A-Za-z])\s*/([^\s/<>\[\]()]+)", body)
    return m.group(1).decode("latin-1") if m else None


def split_objects(data):
    """Return {objnum: (dict_bytes, stream_bytes_or_None)}; the last definition of a number wins."""
    marks = list(OBJ_RE.finditer(data))
    objs = {}
    for idx, m in enumerate(marks):
        end = marks[idx + 1].start() if idx + 1 < len(marks) else len(data)
        body = data[m.end():end]
        s = body.find(b"stream")
        stream = None
        head = body
        if s >= 0:
            head = body[:s]
            start = s + 6
            if body[start:start + 2] == b"\r\n":
                start += 2
            elif body[start:start + 1] in (b"\n", b"\r"):
                start += 1
            e = body.rfind(b"endstream")
            stream = body[start:e if e >= start else len(body)]
        objs[int(m.group(1))] = (head, stream)
    return objs


def inflate(stream, budget):
    """Inflate a Flate stream with a size cap. Returns (bytes_or_None, used)."""
    try:
        d = zlib.decompressobj()
        out = d.decompress(stream.lstrip(b"\r\n"), MAX_STREAM_BYTES)
        return out, len(out)
    except zlib.error:
        return None, 0


def content_info(head, stream, state):
    """Decode one content stream. Returns dict(text, invisible) or None if undecodable."""
    if stream is None or SKIP_STREAM_RE.search(head):
        return None
    if b"FlateDecode" in head or b"/Fl" in head:
        if state["inflated"] >= MAX_TOTAL_INFLATED:
            state["capped"] = True
            return None
        raw, used = inflate(stream, state)
        state["inflated"] += used
        if raw is None:
            state["undecodable"] += 1
            return None
    elif re.search(rb"/Filter", head):
        state["undecodable"] += 1
        return None
    else:
        raw = stream
    if b"BT" not in raw:
        return {"text": False, "invisible": False}
    has = bool(TEXT_OP_RE.search(raw))
    return {"text": has, "invisible": has and bool(INVISIBLE_RE.search(raw))}


def field_info(objs):
    """Collect AcroForm leaf fields from plain (uncompressed) objects."""
    heads = {n: h for n, (h, _) in objs.items()}
    kids_of = {}
    for n, h in heads.items():
        p = _ref_after(h, b"Parent")
        if p is not None:
            kids_of.setdefault(p, []).append(n)

    def inherited(n, getter):
        seen, cur = 0, n
        while cur is not None and cur in heads and seen < PARENT_DEPTH:
            v = getter(heads[cur])
            if v is not None:
                return v
            cur = _ref_after(heads[cur], b"Parent")
            seen += 1
        return None

    def full_name(n):
        parts, cur, seen = [], n, 0
        while cur is not None and cur in heads and seen < PARENT_DEPTH:
            t = _string_after(heads[cur], b"T")
            if t is not None:
                parts.append(t)
            cur = _ref_after(heads[cur], b"Parent")
            seen += 1
        return ".".join(reversed(parts))

    fields = []
    for n, h in sorted(heads.items()):
        if _string_after(h, b"T") is None or PAGE_RE.search(h):
            continue
        ft = inherited(n, lambda b: _name_after(b, b"FT"))
        if ft is None or re.search(rb"/Kids\s*\[", h):
            continue  # intermediate node or not a field
        flags = inherited(n, lambda b: _num_after(b, b"Ff")) or 0
        if ft == "Tx":
            ftype = "text"
        elif ft == "Btn":
            ftype = "pushbutton" if flags & (1 << 16) else "radio" if flags & (1 << 15) else "checkbox"
        elif ft == "Ch":
            ftype = "combo" if flags & (1 << 17) else "list"
        elif ft == "Sig":
            ftype = "signature"
        else:
            ftype = "unknown"
        value = inherited(n, lambda b: _string_after(b, b"V"))
        if value is None:
            value = inherited(n, lambda b: ("/" + _name_after(b, b"V")) if _name_after(b, b"V") else None)
        on_states = []
        if ftype in ("checkbox", "radio"):
            for src in [n] + kids_of.get(n, []):
                m = re.search(rb"/AP\s*<<\s*/N\s*<<(.*?)>>", heads[src], re.S)
                if m:
                    for nm in re.findall(rb"/([^\s/<>\[\]()]+)", m.group(1)):
                        s = nm.decode("latin-1")
                        if s != "Off" and s not in on_states:
                            on_states.append(s)
        entry = {"name": full_name(n), "type": ftype, "value": value if value not in (None, "") else None,
                 "required": bool(flags & 2), "read_only": bool(flags & 1), "object": n}
        if on_states:
            entry["on_states"] = on_states
        fields.append(entry)
    return fields


def inspect(data):
    rep = {"ok": True, "size_bytes": len(data)}
    m = re.match(rb"[\s\S]{0,1024}?%PDF-(\d\.\d)", data[:1030])
    if not m:
        return {"ok": False, "error": "not a PDF: no %PDF- header in the first 1024 bytes", "size_bytes": len(data)}
    rep["pdf_version"] = m.group(1).decode()
    warnings = []
    objs = split_objects(data)
    rep["object_count"] = len(objs)
    rep["incremental_updates"] = max(data.count(b"%%EOF") - 1, 0)

    objstm = sum(1 for h, _ in objs.values() if re.search(rb"/Type\s*/ObjStm", h))
    rep["object_streams"] = objstm
    encrypted = bool(re.search(rb"/Encrypt\s*(\d+\s+\d+\s+R|<<)", data))
    enc = {"encrypted": encrypted}
    if encrypted:
        ref = re.search(rb"/Encrypt\s+(\d+)\s+\d+\s+R", data)
        body = objs.get(int(ref.group(1)), (b"",))[0] if ref else data[data.find(b"/Encrypt"):data.find(b"/Encrypt") + 400]
        enc["filter"] = _name_after(body, b"Filter")
        enc["v"] = _num_after(body, b"V")
        enc["r"] = _num_after(body, b"R")
        warnings.append("encrypted: content streams and strings cannot be read without the password; "
                        "an empty user password may still open it in a real reader")
    rep["encryption"] = enc

    pages = {n for n, (h, _) in objs.items() if PAGE_RE.search(h) and not PAGES_RE.search(h)}
    declared = None
    for n, (h, _) in objs.items():
        if PAGES_RE.search(h) and b"/Parent" not in h:
            c = _num_after(h, b"Count")
            if c is not None:
                declared = max(declared or 0, c)
    rep["pages_by_page_objects"] = len(pages)
    rep["pages_declared"] = declared
    if pages and declared is not None and len(pages) != declared:
        warnings.append("page objects (%d) differ from declared /Count (%d): incremental edits or hidden objects; "
                        "confirm the page count in a real reader" % (len(pages), declared))
    rep["page_count"] = len(pages) if pages else declared
    rep["page_count_confident"] = bool(pages) and (declared is None or len(pages) == declared) and not objstm
    if objstm and not pages:
        warnings.append("page objects live inside compressed object streams; page_count is null unless a declared /Count is visible")

    fonts = [h for h, _ in objs.values() if FONT_RE.search(h)]
    rep["font_objects"] = len(fonts)
    rep["type0_fonts_without_tounicode"] = sum(1 for h in fonts if re.search(rb"/Subtype\s*/Type0", h) and b"/ToUnicode" not in h)
    images = [n for n, (h, _) in objs.items() if IMAGE_RE.search(h)]
    rep["image_objects"] = len(images)

    state = {"inflated": 0, "undecodable": 0, "capped": False}
    info = {}
    if not encrypted:
        for n, (h, s) in objs.items():
            ci = content_info(h, s, state)
            if ci is not None:
                info[n] = ci
    text_streams = sum(1 for v in info.values() if v["text"])
    rep["content_streams_decoded"] = len(info)
    rep["content_streams_with_text"] = text_streams
    rep["streams_undecodable"] = state["undecodable"]
    if state["undecodable"]:
        warnings.append("%d stream(s) use a filter this script cannot decode or failed to inflate" % state["undecodable"])
    if state["capped"]:
        warnings.append("inflate budget reached; later streams were not examined")

    page_text, page_invisible, resolved = 0, 0, 0
    for n in pages:
        h = objs[n][0]
        refs = []
        mm = re.search(rb"/Contents\s*\[([^\]]*)\]", h)
        if mm:
            refs = [int(x) for x in re.findall(rb"(\d+)\s+\d+\s+R", mm.group(1))]
        else:
            r = _ref_after(h, b"Contents")
            if r is not None:
                refs = [r]
        got = [info[r] for r in refs if r in info]
        if got:
            resolved += 1
            if any(g["text"] for g in got):
                page_text += 1
                if any(g["invisible"] for g in got):
                    page_invisible += 1
    rep["pages_with_text_operators"] = page_text if resolved else None
    rep["pages_with_invisible_text"] = page_invisible if resolved else None

    if encrypted:
        verdict = "unknown"
    elif objstm and not info:
        verdict = "unknown"
    elif resolved and resolved == len(pages) and len(pages) > 0:
        if page_text == len(pages):
            verdict = "ocr_layer_likely" if page_invisible and images else "text_layer_likely"
        elif page_text == 0:
            verdict = "image_only_likely" if images else "unknown"
        else:
            verdict = "mixed"
    elif text_streams:
        verdict = "text_layer_likely" if not images else "mixed"
    else:
        verdict = "image_only_likely" if images else "unknown"
    if verdict == "unknown" and not encrypted:
        warnings.append("could not decide: content is in compressed object streams or in an unsupported encoding")
    if verdict in ("text_layer_likely", "ocr_layer_likely", "mixed") and rep["type0_fonts_without_tounicode"]:
        warnings.append("Type0 fonts without /ToUnicode: text may extract as garbled characters despite a text layer")
    rep["text_layer"] = verdict

    form = {"acroform": bool(re.search(rb"/AcroForm(?![A-Za-z])", data)),
            "xfa": bool(re.search(rb"/XFA(?![A-Za-z])", data)),
            "need_appearances": bool(re.search(rb"/NeedAppearances\s+true", data)),
            "fields": []}
    if form["acroform"] and not encrypted:
        form["fields"] = field_info(objs)
        if not form["fields"] and objstm:
            warnings.append("AcroForm present but no fields visible: fields are probably inside compressed object streams")
    if form["xfa"]:
        warnings.append("XFA form data present: dynamic XFA forms are not fillable through AcroForm fields; use a viewer that supports XFA or ask for a static version")
    rep["form"] = form
    rep["form"]["field_count"] = len(form["fields"])
    rep["warnings"] = warnings
    rep["limits"] = ("Byte-level scan, not a full PDF parse: no cross-reference table, no object streams, "
                     "no encrypted content, no per-glyph or layout check.")
    return rep


def main(argv):
    if len(argv) != 1 or argv[0] in ("-h", "--help"):
        print(json.dumps({"ok": False, "error": "usage: pdf_inspect.py <file.pdf>"}))
        return 2
    try:
        with open(argv[0], "rb") as fh:
            data = fh.read(MAX_FILE_BYTES + 1)
    except OSError as exc:
        print(json.dumps({"ok": False, "error": "cannot read file: %s" % exc.strerror}))
        return 2
    if len(data) > MAX_FILE_BYTES:
        print(json.dumps({"ok": False, "error": "file larger than %d MB; split it first" % (MAX_FILE_BYTES // 1048576)}))
        return 2
    rep = inspect(data)
    print(json.dumps(rep, ensure_ascii=True, allow_nan=False, indent=2, sort_keys=True))
    return 0 if rep.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
