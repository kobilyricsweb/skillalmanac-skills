"""Converts an HTML fragment or page to Markdown. Offline, Python stdlib only.

Usage: python -I html_to_md.py <input-file> <output-file>

Reads <input-file> as UTF-8 (at most 2 MB) and writes a new Markdown file at
<output-file>. An existing output file is never overwritten, and the output
path is never the input path. Prints one JSON summary line on stdout.

Exit 0: converted, no unsupported tags.
Exit 1: converted, but unsupported tags were kept as plain text (see summary).
Exit 2: usage or input/output error, reported as one JSON line on stderr.
"""

import json
import os
import re
import sys
from html.parser import HTMLParser

MAX_BYTES = 2 * 1024 * 1024
DROP = {"script", "style", "nav", "noscript", "template", "head", "title"}
BLOCK_PASS = {"div", "section", "article", "main", "body", "html", "hr",
              "thead", "tbody", "tfoot"}
PASS = {"span", "meta", "link"}
HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
INLINE_MARK = {"strong": "**", "b": "**", "em": "*", "i": "*"}
SPAN_ATTRS = {"colspan", "rowspan"}
ESCAPE_RE = re.compile(r"([\\`*_\[\]])")


def _clean_href(value):
    href = (value or "").strip()
    if not href:
        return ""
    return href.replace(" ", "%20").replace("(", "%28").replace(")", "%29")


class Converter(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.buf = []
        self.drop_stack = []
        self.dropped = {}
        self.unsupported = {}
        self.counts = {"headings": 0, "links": 0, "lists": 0,
                       "tables": 0, "code_blocks": 0}
        self.list_stack = []
        self.item = None
        self.quote = 0
        self.pre = 0
        self.hrefs = []
        self.table = None
        self.row = None
        self.cell_saved = None

    # helpers -------------------------------------------------------------
    def _in_cell(self):
        return self.cell_saved is not None

    def _take(self):
        text = "".join(self.buf)
        self.buf = []
        return text

    @staticmethod
    def _lines(text):
        cleaned = (re.sub(r"[ \t]+", " ", part).strip() for part in text.split("\n"))
        return [line for line in cleaned if line]

    def flush(self):
        if self._in_cell():
            return
        lines = self._lines(self._take())
        if not lines:
            return
        if self.item:
            first, rest = self.item
        else:
            first = rest = "> " * self.quote
        text = "\n".join([first + lines[0]] + [rest + ln for ln in lines[1:]])
        self.blocks.append((text, bool(self.item)))

    def _heading_end(self, level):
        if self._in_cell():
            return
        text = " ".join(self._lines(self._take()))
        if text:
            self.blocks.append(("#" * level + " " + text, False))
            self.counts["headings"] += 1

    def _pre_end(self):
        self.pre = max(0, self.pre - 1)
        if self.pre:
            return
        text = self._take().strip("\n")
        if not text:
            return
        if self._in_cell():
            self.buf.append(text)
            return
        self.blocks.append(("```\n" + text + "\n```", False))
        self.counts["code_blocks"] += 1

    def _close_cell(self):
        if not self._in_cell():
            return
        text = " ".join(self._lines(self._take()))
        self.row.append(text.replace("|", "\\|"))
        self.buf = self.cell_saved
        self.cell_saved = None

    def _close_row(self):
        self._close_cell()
        if self.row:
            self.table.append(self.row)
        self.row = None

    def _end_table(self):
        self._close_row()
        rows, self.table = self.table, None
        if not rows:
            return
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        lines = ["| " + " | ".join(rows[0]) + " |",
                 "| " + " | ".join(["---"] * width) + " |"]
        lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
        self.blocks.append(("\n".join(lines), False))

    # parser callbacks ----------------------------------------------------
    def handle_starttag(self, tag, attrs):
        if tag == "body" and self.drop_stack:
            self.drop_stack = [t for t in self.drop_stack if t not in ("head", "title")]
        if self.drop_stack:
            if tag in DROP:
                self.drop_stack.append(tag)
            return
        a = dict(attrs)
        if tag in DROP:
            self.drop_stack.append(tag)
            self.dropped[tag] = self.dropped.get(tag, 0) + 1
        elif tag in HEADINGS or tag == "p" or tag in BLOCK_PASS:
            self.flush()
        elif tag == "br":
            self.buf.append("\n")
        elif tag == "pre":
            self.flush()
            self.pre += 1
        elif tag == "code":
            if not self.pre:
                self.buf.append("`")
        elif tag in INLINE_MARK:
            if not self.pre:
                self.buf.append(INLINE_MARK[tag])
        elif tag == "a":
            href = _clean_href(a.get("href"))
            self.hrefs.append(href)
            if href:
                self.buf.append("[")
        elif tag in ("ul", "ol"):
            self.flush()
            self.list_stack.append([tag, 0])
            self.counts["lists"] += 1
        elif tag == "li":
            self.flush()
            indent = "  " * max(0, len(self.list_stack) - 1)
            marker = "- "
            if self.list_stack:
                top = self.list_stack[-1]
                top[1] += 1
                if top[0] == "ol":
                    marker = str(top[1]) + ". "
            base = "> " * self.quote
            self.item = (base + indent + marker, base + indent + " " * len(marker))
        elif tag == "blockquote":
            self.flush()
            self.quote += 1
        elif tag == "table":
            self.flush()
            self.table = []
            self.counts["tables"] += 1
        elif tag == "tr" and self.table is not None:
            self._close_row()
            self.row = []
        elif tag in ("td", "th") and self.table is not None:
            self._close_cell()
            if self.row is None:
                self.row = []
            if SPAN_ATTRS.intersection(a):
                key = "td[colspan/rowspan]"
                self.unsupported[key] = self.unsupported.get(key, 0) + 1
            self.cell_saved = self.buf
            self.buf = []
        elif tag in PASS:
            pass
        else:
            self.unsupported[tag] = self.unsupported.get(tag, 0) + 1

    def handle_endtag(self, tag):
        if self.drop_stack:
            if tag in self.drop_stack:
                while self.drop_stack.pop() != tag:
                    pass
            return
        if tag in HEADINGS:
            self._heading_end(HEADINGS[tag])
        elif tag == "p" or tag in BLOCK_PASS:
            self.flush()
        elif tag in INLINE_MARK:
            if not self.pre:
                self.buf.append(INLINE_MARK[tag])
        elif tag == "code":
            if not self.pre:
                self.buf.append("`")
        elif tag == "pre":
            self._pre_end()
        elif tag == "a":
            href = self.hrefs.pop() if self.hrefs else ""
            if href:
                self.buf.append("](" + href + ")")
                self.counts["links"] += 1
        elif tag in ("ul", "ol"):
            self.flush()
            if self.list_stack:
                self.list_stack.pop()
            self.item = None
        elif tag == "li":
            self.flush()
            self.item = None
        elif tag == "blockquote":
            self.flush()
            self.quote = max(0, self.quote - 1)
        elif tag == "table":
            if self.table is not None:
                self._end_table()
        elif tag == "tr" and self.table is not None:
            self._close_row()
        elif tag in ("td", "th") and self.table is not None:
            self._close_cell()

    def handle_data(self, data):
        if self.drop_stack:
            return
        if self.pre:
            self.buf.append(data)
        else:
            self.buf.append(ESCAPE_RE.sub(r"\\\1", re.sub(r"\s+", " ", data)))


def _join(blocks):
    """Joins blocks with a blank line, except consecutive list items (one newline)."""
    out = []
    prev_item = False
    for text, is_item in blocks:
        if out:
            out.append("\n" if (is_item and prev_item) else "\n\n")
        out.append(text)
        prev_item = is_item
    return "".join(out)


def convert(text):
    parser = Converter()
    parser.feed(text)
    parser.close()
    if parser.table is not None:
        parser._end_table()
    parser.flush()
    markdown = _join(parser.blocks) + "\n" if parser.blocks else ""
    return markdown, parser


def fail(code):
    sys.stderr.write(json.dumps({"error": code}) + "\n")
    sys.exit(2)


def main(argv):
    if len(argv) != 3:
        fail("usage")
    src, dst = argv[1], argv[2]
    if not os.path.isfile(src):
        fail("input_missing")
    if os.path.getsize(src) > MAX_BYTES:
        fail("input_too_large")
    try:
        with open(src, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError:
        fail("input_unreadable")
    if len(raw) > MAX_BYTES:
        fail("input_too_large")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("input_not_utf8")
    if os.path.abspath(src) == os.path.abspath(dst):
        fail("output_is_input")
    if not os.path.isdir(os.path.dirname(os.path.abspath(dst))):
        fail("output_dir_missing")
    if os.path.exists(dst):
        fail("output_exists")
    try:
        markdown, parser = convert(text)
    except Exception:
        fail("parse_failed")
    try:
        with open(dst, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(markdown)
    except FileExistsError:
        fail("output_exists")
    except OSError:
        fail("output_unwritable")
    findings = parser.unsupported
    summary = {"status": "findings" if findings else "ok"}
    summary.update(parser.counts)
    summary["dropped"] = parser.dropped
    summary["unsupported"] = findings
    summary["bytes_written"] = len(markdown.encode("utf-8"))
    print(json.dumps(summary, sort_keys=True))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
