#!/usr/bin/env python3
"""Redline two plain-text or Markdown versions: paragraphs first, then words.

Usage:
    python -I scripts/redline.py <old-file> <new-file> [--report <report-file>]
        [--ignore-case] [--ignore-whitespace]

Paragraphs are blocks separated by one or more blank lines. Words are split on
whitespace. Changed words print inline as [-deleted-] and [+inserted+]. Whole
removed or added paragraphs print as one bracketed block. A removed paragraph
whose exact text reappears as an added paragraph is reported as moved.

Exit codes: 0 no differences, 1 differences found, 2 usage or input error.
The script only reads its inputs. It writes at most one report file, created
with exclusive mode, so it never overwrites and never writes to an input path.
Standard library only. No network, no subprocess, no eval or exec.
"""
import argparse
import difflib
import json
import os
import sys

MAX_BYTES = 2 * 1024 * 1024
PAIR_THRESHOLD = 0.5  # working value: minimum word similarity to pair two paragraphs


def fail(code, message):
    sys.stderr.write(json.dumps({"error": message, "code": code}) + "\n")
    sys.exit(2)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        fail("usage", message)


def read_input(path):
    if not os.path.isfile(path):
        fail("missing_file", "input file not found or not a regular file")
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError:
        fail("missing_file", "input file could not be opened")
    if len(raw) > MAX_BYTES:
        fail("too_large", "input file is larger than 2 MB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("invalid_utf8", "input file is not valid UTF-8 text")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def split_paragraphs(text):
    paragraphs, current = [], []
    for line in text.split("\n"):
        if line.strip():
            current.append(line.rstrip())
        elif current:
            paragraphs.append("\n".join(current))
            current = []
    if current:
        paragraphs.append("\n".join(current))
    return paragraphs


def inline(old_wd, new_wd):
    old_disp, old_keys = old_wd
    new_disp, new_keys = new_wd
    out, ins, dele = [], 0, 0
    matcher = difflib.SequenceMatcher(None, old_keys, new_keys, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            out.extend(new_disp[j1:j2])
            continue
        if i2 > i1:
            out.append("[-" + " ".join(old_disp[i1:i2]) + "-]")
            dele += i2 - i1
        if j2 > j1:
            out.append("[+" + " ".join(new_disp[j1:j2]) + "+]")
            ins += j2 - j1
    return " ".join(out), ins, dele


def analyse(old_paras, new_paras, ignore_case, ignore_ws):
    def pkey(text):
        base = " ".join(text.split()) if ignore_ws else text
        return base.casefold() if ignore_case else base

    def wtoks(text):
        disp = text.split()
        keys = [t.casefold() for t in disp] if ignore_case else disp
        return disp, keys

    old_keys = [pkey(p) for p in old_paras]
    new_keys = [pkey(p) for p in new_paras]
    old_w = [wtoks(p) for p in old_paras]
    new_w = [wtoks(p) for p in new_paras]

    stats = {"changed": 0, "inserted": 0, "deleted": 0, "moved": 0,
             "whitespace_only": 0, "unchanged": 0,
             "inserted_words": 0, "deleted_words": 0}
    blocks = []  # (anchor new index, rank, heading, body)
    deleted, inserted, pairs = [], [], []

    matcher = difflib.SequenceMatcher(None, old_keys, new_keys, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            stats["unchanged"] += i2 - i1
        elif tag == "delete":
            deleted.extend((i, j1) for i in range(i1, i2))
        elif tag == "insert":
            inserted.extend(range(j1, j2))
        else:
            cursor = j1
            for i in range(i1, i2):
                match = None
                for j in range(cursor, j2):
                    ratio = difflib.SequenceMatcher(
                        None, old_w[i][1], new_w[j][1], autojunk=False).ratio()
                    if ratio >= PAIR_THRESHOLD:
                        match = j
                        break
                if match is None:
                    deleted.append((i, cursor))
                    continue
                inserted.extend(range(cursor, match))
                pairs.append((i, match))
                cursor = match + 1
            inserted.extend(range(cursor, j2))

    for i, j in pairs:
        if old_keys[i] == new_keys[j]:
            stats["unchanged"] += 1
        elif old_w[i][1] == new_w[j][1]:
            stats["whitespace_only"] += 1
            blocks.append((j, 1, "Whitespace-only: old P%d -> new P%d" % (i + 1, j + 1),
                           new_paras[j]))
        else:
            body, ins, dele = inline(old_w[i], new_w[j])
            stats["changed"] += 1
            stats["inserted_words"] += ins
            stats["deleted_words"] += dele
            blocks.append((j, 1, "Changed: old P%d -> new P%d" % (i + 1, j + 1), body))

    ins_by_key = {}
    for j in inserted:
        ins_by_key.setdefault(new_keys[j], []).append(j)
    moved, still_deleted = [], []
    for i, anchor in deleted:
        candidates = ins_by_key.get(old_keys[i])
        if candidates:
            moved.append((i, candidates.pop(0)))
        else:
            still_deleted.append((i, anchor))
    moved_new = {j for _, j in moved}
    inserted = [j for j in inserted if j not in moved_new]

    for i, j in moved:
        stats["moved"] += 1
        blocks.append((j, 1, "Moved: old P%d -> new P%d" % (i + 1, j + 1), new_paras[j]))
    for i, anchor in still_deleted:
        words = old_w[i][0]
        stats["deleted"] += 1
        stats["deleted_words"] += len(words)
        blocks.append((anchor, 0, "Deleted: old P%d" % (i + 1),
                       "[-" + " ".join(words) + "-]"))
    for j in inserted:
        words = new_w[j][0]
        stats["inserted"] += 1
        stats["inserted_words"] += len(words)
        blocks.append((j, 1, "Inserted: new P%d" % (j + 1),
                       "[+" + " ".join(words) + "+]"))

    blocks.sort(key=lambda b: (b[0], b[1]))
    return stats, blocks


def render(old_name, new_name, old_count, new_count, ignore_case, ignore_ws, stats, blocks):
    lines = [
        "# Redline",
        "old: " + old_name,
        "new: " + new_name,
        "flags: case=%s whitespace=%s" % ("ignored" if ignore_case else "sensitive",
                                          "ignored" if ignore_ws else "strict"),
        "paragraphs: old=%d new=%d" % (old_count, new_count),
        "paragraph_counts: changed=%d inserted=%d deleted=%d moved=%d "
        "whitespace_only=%d unchanged=%d" % (
            stats["changed"], stats["inserted"], stats["deleted"], stats["moved"],
            stats["whitespace_only"], stats["unchanged"]),
        "word_counts: inserted=%d deleted=%d" % (stats["inserted_words"],
                                                  stats["deleted_words"]),
    ]
    if not blocks:
        lines += ["", "No differences."]
    for _, _, heading, body in blocks:
        lines += ["", "## " + heading, body]
    return "\n".join(lines) + "\n"


def write_report(path, text):
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except FileExistsError:
        fail("output_exists", "report file already exists; choose a new name")
    except OSError:
        fail("output_write_failed", "report file could not be created")


def main(argv=None):
    parser = Parser(description="Redline two text or Markdown versions by paragraph and word.")
    parser.add_argument("old_file")
    parser.add_argument("new_file")
    parser.add_argument("--report", metavar="REPORT_FILE")
    parser.add_argument("--ignore-case", action="store_true")
    parser.add_argument("--ignore-whitespace", action="store_true")
    args = parser.parse_args(argv)

    if args.report:
        report = os.path.normcase(os.path.abspath(args.report))
        inputs = [os.path.normcase(os.path.abspath(args.old_file)),
                  os.path.normcase(os.path.abspath(args.new_file))]
        if report in inputs:
            fail("output_is_input", "report path matches an input file")
        if os.path.exists(args.report):
            fail("output_exists", "report file already exists; choose a new name")

    old_paras = split_paragraphs(read_input(args.old_file))
    new_paras = split_paragraphs(read_input(args.new_file))
    stats, blocks = analyse(old_paras, new_paras, args.ignore_case, args.ignore_whitespace)
    text = render(os.path.basename(args.old_file), os.path.basename(args.new_file),
                  len(old_paras), len(new_paras), args.ignore_case,
                  args.ignore_whitespace, stats, blocks)

    if args.report:
        write_report(args.report, text)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.write(text)

    differences = sum(stats[k] for k in ("changed", "inserted", "deleted",
                                         "moved", "whitespace_only"))
    return 1 if differences else 0


if __name__ == "__main__":
    sys.exit(main())
