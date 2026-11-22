"""Build a plain HTML email signature and a matching plain-text signature.

Usage:
    python -I signature.py <input-json> <output-html> <output-txt>

Reads one JSON object of contact fields (read-only), validates each field,
checks that the text color meets the WCAG 2.x AA contrast ratio of 4.5:1
against white, and then writes two new files: the HTML signature and the
plain-text signature. Existing output files are never overwritten.

Exit codes:
    0  signature written
    1  findings: text color fails the contrast check; nothing is written
    2  usage or input error; a one-line JSON error is written to stderr

No network, no subprocess, no eval or exec. Standard library only.
"""

import html
import json
import os
import re
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
MIN_CONTRAST = 4.5
DEFAULT_TEXT_COLOR = "#333333"

KNOWN_FIELDS = ("name", "title", "company", "phone", "email", "website", "text_color")
REQUIRED_FIELDS = ("name",)
MAX_LENGTH = {"name": 80, "title": 80, "company": 100}

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\+?[0-9 ().-]{7,20}$")
WEBSITE_RE = re.compile(r"^(https?://)?[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(/[^\s<>\"]*)?$")
COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


class InputError(Exception):
    def __init__(self, code, message, field=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field


def fail_json(code, message, field=None):
    payload = {"status": "error", "code": code, "message": message}
    if field is not None:
        payload["field"] = field
    sys.stderr.write(json.dumps(payload, ensure_ascii=True) + "\n")
    return 2


def load_input(path):
    if not os.path.isfile(path):
        raise InputError("FILE_MISSING", "input file not found")
    if os.path.getsize(path) > MAX_INPUT_BYTES:
        raise InputError("FILE_TOO_LARGE", "input file is larger than 2 MB")
    with open(path, "rb") as handle:
        raw = handle.read(MAX_INPUT_BYTES + 1)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise InputError("BAD_UTF8", "input file is not valid UTF-8")
    try:
        data = json.loads(text)
    except ValueError:
        raise InputError("BAD_JSON", "input file is not valid JSON")
    if not isinstance(data, dict):
        raise InputError("NOT_OBJECT", "input JSON must be an object")
    return data


def validate(data):
    for key in data:
        if key not in KNOWN_FIELDS:
            raise InputError("UNKNOWN_FIELD", "field is not supported", key)
    for key in REQUIRED_FIELDS:
        if key not in data or not str(data[key]).strip():
            raise InputError("MISSING_FIELD", "required field is missing or empty", key)

    clean = {}
    for key in KNOWN_FIELDS:
        value = data.get(key, "")
        if not isinstance(value, str):
            raise InputError("BAD_FIELD", "field must be a string", key)
        value = value.strip()
        if CONTROL_RE.search(value):
            raise InputError("BAD_FIELD", "field contains control characters", key)
        if key in MAX_LENGTH and len(value) > MAX_LENGTH[key]:
            raise InputError("BAD_FIELD", "field is longer than %d characters" % MAX_LENGTH[key], key)
        clean[key] = value

    if clean["phone"]:
        digits = sum(ch.isdigit() for ch in clean["phone"])
        if not PHONE_RE.match(clean["phone"]) or not 7 <= digits <= 15:
            raise InputError("BAD_FIELD", "phone needs 7 to 15 digits and only digits, spaces, ( ) . - and a leading +", "phone")
    if clean["email"]:
        if len(clean["email"]) > 254 or not EMAIL_RE.match(clean["email"]):
            raise InputError("BAD_FIELD", "email is not a valid address", "email")
    if clean["website"]:
        if len(clean["website"]) > 200 or not WEBSITE_RE.match(clean["website"]):
            raise InputError("BAD_FIELD", "website must be a host with a dot, optionally with http:// or https:// and a path", "website")
    if not clean["text_color"]:
        clean["text_color"] = DEFAULT_TEXT_COLOR
    if not COLOR_RE.match(clean["text_color"]):
        raise InputError("BAD_FIELD", "text_color must be #RRGGBB", "text_color")
    return clean


def relative_luminance(hex_color):
    channels = []
    for i in (1, 3, 5):
        c = int(hex_color[i:i + 2], 16) / 255.0
        if c <= 0.03928:
            channels.append(c / 12.92)
        else:
            channels.append(((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_vs_white(hex_color):
    return round(1.05 / (relative_luminance(hex_color) + 0.05), 2)


def render_html(f):
    color = html.escape(f["text_color"], quote=True)
    rows = []
    rows.append('<tr><td style="font-family:Arial,Helvetica,sans-serif;font-size:16px;line-height:22px;font-weight:bold;color:%s;padding:0 0 2px 0;">%s</td></tr>' % (color, html.escape(f["name"])))
    if f["title"]:
        rows.append('<tr><td style="font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:20px;color:%s;padding:0;">%s</td></tr>' % (color, html.escape(f["title"])))
    if f["company"]:
        rows.append('<tr><td style="font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:20px;color:%s;padding:0 0 8px 0;">%s</td></tr>' % (color, html.escape(f["company"])))
    if f["phone"]:
        rows.append('<tr><td style="font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:20px;color:%s;padding:0;">T: %s</td></tr>' % (color, html.escape(f["phone"])))
    if f["email"]:
        address = html.escape(f["email"], quote=True)
        rows.append('<tr><td style="font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:20px;color:%s;padding:0;">E: <a href="mailto:%s" style="color:%s;text-decoration:underline;">%s</a></td></tr>' % (color, address, color, html.escape(f["email"])))
    if f["website"]:
        target = f["website"] if f["website"].startswith(("http://", "https://")) else "https://" + f["website"]
        href = html.escape(target, quote=True)
        label = html.escape(re.sub(r"^https?://", "", f["website"]).rstrip("/"))
        rows.append('<tr><td style="font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:20px;color:%s;padding:0;">W: <a href="%s" style="color:%s;text-decoration:underline;">%s</a></td></tr>' % (color, href, color, label))
    table = (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        'style="max-width:600px;width:100%%;border-collapse:collapse;">\n%s\n</table>'
        % "\n".join(rows)
    )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        "<title>Email signature</title>\n</head>\n<body style=\"margin:0;padding:0;background:#ffffff;\">\n"
        + table + "\n</body>\n</html>\n"
    )


def render_text(f):
    lines = [f["name"]]
    if f["title"]:
        lines.append(f["title"])
    if f["company"]:
        lines.append(f["company"])
    lines.append("")
    if f["phone"]:
        lines.append("T: " + f["phone"])
    if f["email"]:
        lines.append("E: " + f["email"])
    if f["website"]:
        lines.append("W: " + f["website"])
    return "\n".join(lines) + "\n"


def check_output_paths(input_path, out_html, out_txt):
    if not out_html.lower().endswith(".html") or not out_txt.lower().endswith(".txt"):
        raise InputError("OUTPUT_PATH_INVALID", "output must be <name>.html and <name>.txt")
    in_abs = os.path.normcase(os.path.abspath(input_path))
    html_abs = os.path.normcase(os.path.abspath(out_html))
    txt_abs = os.path.normcase(os.path.abspath(out_txt))
    if len({in_abs, html_abs, txt_abs}) != 3:
        raise InputError("OUTPUT_PATH_INVALID", "output paths must differ from each other and from the input")
    for path in (out_html, out_txt):
        if os.path.exists(path):
            raise InputError("OUTPUT_EXISTS", "output file already exists; choose a new name")


def write_new(html_path, txt_path, html_text, txt_text):
    html_handle = None
    try:
        html_handle = open(html_path, "x", encoding="utf-8", newline="\n")
        txt_handle = open(txt_path, "x", encoding="utf-8", newline="\n")
    except FileExistsError:
        if html_handle is not None:
            html_handle.close()
            os.remove(html_path)
        raise InputError("OUTPUT_EXISTS", "output file was created by another process; choose a new name")
    except OSError:
        if html_handle is not None:
            html_handle.close()
            os.remove(html_path)
        raise InputError("WRITE_FAILED", "could not create output files")
    with html_handle, txt_handle:
        html_handle.write(html_text)
        txt_handle.write(txt_text)


def main(argv):
    if len(argv) != 4:
        return fail_json("BAD_ARGS", "usage: signature.py <input-json> <output-html> <output-txt>")
    input_path, out_html, out_txt = argv[1], argv[2], argv[3]
    try:
        data = load_input(input_path)
        fields = validate(data)
        check_output_paths(input_path, out_html, out_txt)
        ratio = contrast_vs_white(fields["text_color"])
        if ratio < MIN_CONTRAST:
            result = {
                "status": "findings",
                "findings": [{
                    "code": "LOW_CONTRAST",
                    "field": "text_color",
                    "ratio": ratio,
                    "minimum": MIN_CONTRAST,
                }],
                "written": [],
            }
            sys.stdout.write(json.dumps(result, ensure_ascii=True) + "\n")
            return 1
        write_new(out_html, out_txt, render_html(fields), render_text(fields))
    except InputError as exc:
        return fail_json(exc.code, exc.message, exc.field)
    except OSError:
        return fail_json("WRITE_FAILED", "could not read or write a file")
    result = {
        "status": "ok",
        "contrast_ratio": ratio,
        "written": [out_html, out_txt],
    }
    sys.stdout.write(json.dumps(result, ensure_ascii=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
