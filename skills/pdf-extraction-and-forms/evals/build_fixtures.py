#!/usr/bin/env python3
"""Regenerate the tiny PDF fixtures in evals/fixtures/ (standard library only).

    python evals/build_fixtures.py

Writes only into evals/fixtures/. The PDFs are hand-built, minimal and valid
enough for byte-level scanning; they are not meant to render in a viewer. The
saved fixture files are the source of truth for the recorded expectations;
this script exists so a reviewer can see how each one was made.
"""
import os
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "fixtures")
FONT = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"


def stream(dict_extra, data, flate=False):
    if flate:
        data = zlib.compress(data)
        dict_extra += b" /Filter /FlateDecode"
    return b"<< " + dict_extra + b" /Length " + str(len(data)).encode() + b" >>\nstream\n" + data + b"\nendstream"


def build(objs, root=1, trailer_extra=b""):
    """objs: dict num -> body bytes. Returns PDF bytes with a correct xref table."""
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offs = {}
    for n in sorted(objs):
        offs[n] = len(out)
        out += str(n).encode() + b" 0 obj\n" + objs[n] + b"\nendobj\n"
    xref = len(out)
    size = max(objs) + 1
    out += b"xref\n0 " + str(size).encode() + b"\n0000000000 65535 f \n"
    for n in range(1, size):
        out += (b"%010d 00000 n \n" % offs[n]) if n in offs else b"0000000000 65535 f \n"
    out += b"trailer\n<< /Size " + str(size).encode() + b" /Root " + str(root).encode() + b" 0 R " + trailer_extra + b">>\nstartxref\n" + str(xref).encode() + b"\n%%EOF\n"
    return bytes(out)


def pages_doc(page_contents, extra_objs=None, flate=True, with_image=None):
    """page_contents: list of content-stream bytes. with_image: set of page indexes that reference an image."""
    objs = {1: b"<< /Type /Catalog /Pages 2 0 R >>", 3: FONT}
    n_pages = len(page_contents)
    kids, nxt = [], 10
    with_image = with_image or set()
    for i, content in enumerate(page_contents):
        pg, cs = nxt, nxt + 1
        nxt += 2
        res = b"/Font << /F1 3 0 R >>"
        if i in with_image:
            res += b" /XObject << /Im0 4 0 R >>"
        objs[pg] = b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << " + res + b" >> /Contents " + str(cs).encode() + b" 0 R >>"
        objs[cs] = stream(b"", content, flate)
        kids.append(str(pg).encode() + b" 0 R")
    objs[2] = b"<< /Type /Pages /Kids [" + b" ".join(kids) + b"] /Count " + str(n_pages).encode() + b" >>"
    if with_image:
        objs[4] = stream(b"/Type /XObject /Subtype /Image /Width 8 /Height 8 /ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /DCTDecode", b"\xff\xd8not-a-real-jpeg\xff\xd9")
    objs.update(extra_objs or {})
    return objs


TEXT = b"BT /F1 12 Tf 72 700 Td (Invoice total 1234.50) Tj ET"
IMG = b"q 612 0 0 792 0 0 cm /Im0 Do Q"
OCR = IMG + b"\nBT 3 Tr /F1 12 Tf 72 700 Td (Invoice total 1234.50) Tj ET"


def form(values, xfa=False):
    name_v = b" /V (" + values.get("Name", b"") + b")" if values.get("Name") else b""
    chk_v = b" /V /" + values["agree"] if values.get("agree") else b" /V /Off"
    objs = pages_doc([TEXT], flate=False)
    objs[1] = b"<< /Type /Catalog /Pages 2 0 R /AcroForm << /Fields [20 0 R 24 0 R 25 0 R] /NeedAppearances true" + (b" /XFA [(template) 30 0 R]" if xfa else b"") + b" >> >>"
    objs[20] = b"<< /T (form1) /Kids [21 0 R] >>"
    objs[21] = b"<< /Type /Annot /Subtype /Widget /FT /Tx /T (Name) /Parent 20 0 R /Rect [72 600 300 620]" + name_v + b" >>"
    objs[24] = b"<< /Type /Annot /Subtype /Widget /FT /Btn /T (agree) /Rect [72 560 90 578] /AP << /N << /Yes 26 0 R /Off 27 0 R >> >>" + chk_v + b" >>"
    objs[25] = b"<< /Type /Annot /Subtype /Widget /FT /Tx /Ff 2 /T (SSN) /Rect [72 520 300 540]" + (b" /V (" + values["SSN"] + b")" if values.get("SSN") else b"") + b" >>"
    objs[26] = stream(b"/Type /XObject /Subtype /Form /BBox [0 0 18 18]", b"0 0 m")
    objs[27] = stream(b"/Type /XObject /Subtype /Form /BBox [0 0 18 18]", b"")
    objs[10] = objs[10].replace(b">>\n", b">>") if False else objs[10]
    return objs


def main():
    os.makedirs(OUT, exist_ok=True)
    files = {}
    files["text_flate.pdf"] = build(pages_doc([TEXT]))
    files["text_plain_2pages.pdf"] = build(pages_doc([TEXT, b"BT /F1 12 Tf 72 700 Td [(Page) -250 (two)] TJ ET"], flate=False))
    files["scanned.pdf"] = build(pages_doc([IMG, IMG], with_image={0, 1}))
    files["scanned_ocr.pdf"] = build(pages_doc([OCR], with_image={0}))
    files["mixed.pdf"] = build(pages_doc([TEXT, IMG], with_image={1}))
    files["form_blank.pdf"] = build(form({}))
    files["form_filled.pdf"] = build(form({"Name": b"Jane Doe", "agree": b"Yes", "SSN": b"000-00-0000"}))
    files["form_filled_bad.pdf"] = build(form({"Name": b"Jane Roe", "agree": b"Yes"}))
    files["form_xfa.pdf"] = build(form({}, xfa=True))
    enc = pages_doc([b"\x8f\x13garbage-ciphertext\x00\x01"], flate=False)
    enc[9] = b"<< /Filter /Standard /V 2 /R 3 /Length 128 /P -3904 /O (x) /U (y) >>"
    files["encrypted.pdf"] = build(enc, trailer_extra=b"/Encrypt 9 0 R ")
    objstm = {1: b"<< /Type /Catalog /Pages 2 0 R >>", 5: stream(b"/Type /ObjStm /N 2 /First 10", b"2 0 3 40 << /Type /Pages /Kids [3 0 R] /Count 1 >> << /Type /Page /Parent 2 0 R >>", True)}
    files["objstm.pdf"] = build(objstm)
    for name, data in files.items():
        with open(os.path.join(OUT, name), "wb") as fh:
            fh.write(data)
    with open(os.path.join(OUT, "not_a_pdf.pdf"), "wb") as fh:
        fh.write(b"This is plain text, not a PDF.\n")
    print("wrote %d PDF fixtures to %s" % (len(files) + 1, OUT))


if __name__ == "__main__":
    main()
