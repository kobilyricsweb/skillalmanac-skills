#!/usr/bin/env python3
"""Build the synthetic sample images used by the fixtures and the task evals.

    python evals/make_samples.py OUT_DIR GROUP

GROUP is one of: hero, print, banner, thumb. OUT_DIR must not exist or must be
empty. The files are written only inside OUT_DIR. The images carry real headers
(and a decodable body for PNG) but are not meant to be looked at; the checker
reads headers only. Keeping them generated keeps the package text-only.
"""
import os
import struct
import sys
import zlib

GROUPS = ("hero", "print", "banner", "thumb")


def _chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def make_png(w, h, total=None, dpi=None):
    ihdr = _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    phys = b""
    if dpi:
        ppm = int(round(dpi / 0.0254))
        phys = _chunk(b"pHYs", struct.pack(">IIB", ppm, ppm, 1))
    comp = zlib.compressobj(1)
    row = b"\x00" + b"\x00" * (3 * w)
    body = b"".join(comp.compress(row) for _ in range(h)) + comp.flush()
    idat = _chunk(b"IDAT", body)
    iend = _chunk(b"IEND", b"")
    base = b"\x89PNG\r\n\x1a\n" + ihdr + phys
    pad = b""
    if total:
        extra = total - (len(base) + len(idat) + len(iend))
        if extra >= 16:
            pad = _chunk(b"tEXt", b"pad\x00" + b"x" * (extra - 16))
    return base + pad + idat + iend


def _app_segment(marker, data):
    return b"\xff" + bytes([marker]) + struct.pack(">H", len(data) + 2) + data


def make_jpeg(w, h, total=None, jfif=None, exif_dpi=None, truncate=False):
    out = b"\xff\xd8"
    if jfif is not None:
        units, xd, yd = jfif
        out += _app_segment(0xE0, b"JFIF\x00\x01\x01" + bytes([units]) + struct.pack(">HH", xd, yd) + b"\x00\x00")
    if exif_dpi:
        tiff = b"II*\x00" + struct.pack("<I", 8)
        tiff += struct.pack("<H", 3)
        tiff += struct.pack("<HHII", 0x011A, 5, 1, 50)
        tiff += struct.pack("<HHII", 0x011B, 5, 1, 58)
        tiff += struct.pack("<HHI", 0x0128, 3, 1) + struct.pack("<H", 2) + b"\x00\x00"
        tiff += struct.pack("<I", 0)
        tiff += struct.pack("<II", exif_dpi, 1) + struct.pack("<II", exif_dpi, 1)
        out += _app_segment(0xE1, b"Exif\x00\x00" + tiff)
    sof = b"\xff\xc0" + struct.pack(">H", 11) + b"\x08" + struct.pack(">HH", h, w) + b"\x01\x01\x11\x00"
    sos = b"\xff\xda" + struct.pack(">H", 8) + b"\x01\x01\x00\x00\x3f\x00" + b"\x55" * 16
    tail = b"\xff\xd9"
    if total:
        room = total - (len(out) + len(sof) + len(sos) + len(tail))
        while room >= 4:
            n = min(room - 2, 65535)
            out += b"\xff\xfe" + struct.pack(">H", n) + b"c" * (n - 2)
            room -= n + 2
    data = out + sof + sos + tail
    return data[:-3] if truncate else data


def make_gif(w, h):
    return b"GIF89a" + struct.pack("<HH", w, h) + b"\x00\x00\x00" + b"\x3b"


def make_webp_lossless(w, h):
    payload = b"\x2f" + struct.pack("<I", (w - 1) | ((h - 1) << 14)) + b"\x00\x00\x00"
    chunk = b"VP8L" + struct.pack("<I", len(payload)) + payload
    return b"RIFF" + struct.pack("<I", 4 + len(chunk)) + b"WEBP" + chunk


def make_svg(vw, vh):
    return ('<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d">'
            '<rect width="%d" height="%d"/></svg>\n' % (vw, vh, vw, vh)).encode("utf-8")


def files_for(group):
    if group == "hero":
        return {
            "hero_ok.jpg": make_jpeg(1600, 900, total=120000),
            "hero_1px.jpg": make_jpeg(1599, 900, total=100000),
            "hero_wide.jpg": make_jpeg(2400, 900, total=150000),
            "hero_big.jpg": make_jpeg(1600, 900, total=400000),
            "hero_wrongext.jpg": make_png(1600, 900),
            "hero_trunc.jpg": make_jpeg(1600, 900, total=90000, truncate=True),
            "hero_small.webp": make_webp_lossless(800, 450),
        }
    if group == "print":
        return {
            "a5_300.png": make_png(1748, 2480, dpi=300),
            "a5_nodpi.png": make_png(1748, 2480),
            "a5_72.png": make_png(1748, 2480, dpi=72),
            "a5_jfif.jpg": make_jpeg(1748, 2480, jfif=(1, 300, 300)),
            "a5_exif.jpg": make_jpeg(1748, 2480, exif_dpi=300),
            "a5_dpcm.jpg": make_jpeg(1748, 2480, jfif=(2, 118, 118)),
            "a5_jfif_aspect.jpg": make_jpeg(1748, 2480, jfif=(0, 1, 1)),
            "empty.png": b"",
        }
    if group == "banner":
        return {
            "banner_1200x628.png": make_png(1200, 628),
            "banner_1200x630.png": make_png(1200, 630),
            "banner_1000x600.png": make_png(1000, 600),
            "banner_1200x640.png": make_png(1200, 640),
            "banner_a.gif": make_gif(1200, 628),
            "banner.svg": make_svg(1910, 1000),
        }
    if group == "thumb":
        return {
            "thumb_ok.png": make_png(640, 360),
            "thumb_big.png": make_png(1280, 720),
            "thumb_flat.png": make_png(640, 360, total=80000),
            "thumb_photo.png": make_png(640, 360, total=300000),
            "broken.png": b"this is not an image\n",
        }
    raise ValueError("unknown group %r; use one of %s" % (group, ", ".join(GROUPS)))


def write_group(out_dir, group):
    os.makedirs(out_dir, exist_ok=True)
    if os.listdir(out_dir):
        raise SystemExit("error: %s is not empty; give a new or empty folder" % out_dir)
    for name, data in sorted(files_for(group).items()):
        with open(os.path.join(out_dir, name), "wb") as handle:
            handle.write(data)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[1] not in GROUPS:
        sys.stderr.write("usage: make_samples.py OUT_DIR {%s}\n" % "|".join(GROUPS))
        return 2
    write_group(argv[0], argv[1])
    print("wrote %d files to %s" % (len(files_for(argv[1])), argv[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
