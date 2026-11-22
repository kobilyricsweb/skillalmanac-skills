#!/usr/bin/env python3
"""Scan an .xlsx workbook for hidden-risk signals. Read-only, Python stdlib only.

Reports: sheets with state hidden or veryHidden, defined names (hidden flag,
external reference), external link parts, cells whose cached value is an error
(t="e", e.g. #DIV/0!), formula count, and formulas that contain a numeric
literal above a threshold. Formulas are never recalculated. No network access.

Usage:
    python -I scripts/xlsx_scan.py <input.xlsx> [--threshold N] [--out report.json]

Exit codes: 0 no findings, 1 findings reported, 2 usage or input error.
Errors are one line of JSON on stderr. The only file written is the optional
--out path, which is refused when it resolves to the input file.
"""
import argparse
import io
import json
import os
import posixpath
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

VERSION = "0.1.0"
MAX_INPUT_BYTES = 2 * 1024 * 1024        # input file cap (working value)
MAX_ENTRIES = 1000                       # zip entries cap
MAX_TOTAL_UNCOMPRESSED = 32 * 1024 * 1024
MAX_PART_BYTES = 8 * 1024 * 1024         # per XML part, uncompressed
MAX_NESTING = 64                         # XML element depth cap
MAX_LIST = 100                           # items per output list
DEFAULT_THRESHOLD = 1000.0               # working value, not a standard

STRING_RE = re.compile(r'"(?:[^"]|"")*"')
SHEET_PREFIX_RE = re.compile(r"(?:'(?:[^']|'')*'|[A-Za-z_][\w.]*)!")
CELL_REF_RE = re.compile(r"\$?\b[A-Za-z]{1,3}\$?\d+\b")
NUMBER_RE = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])")
EXT_PART_RE = re.compile(r"xl/externalLinks/externalLink\d+\.xml$")


class InputError(Exception):
    """Raised for input that cannot be scanned safely."""


def local(tag):
    return tag.rsplit("}", 1)[-1]


def read_part(zf, name):
    info = zf.getinfo(name)
    if info.file_size > MAX_PART_BYTES:
        raise InputError("part too large: " + name)
    with zf.open(info) as fh:
        data = fh.read(MAX_PART_BYTES + 1)
    if len(data) > MAX_PART_BYTES:
        raise InputError("part too large: " + name)
    return data


def parse_xml(data, name):
    if b"<!DOCTYPE" in data or b"<!ENTITY" in data:
        raise InputError("DTD or entity declaration in " + name)
    parser = ET.XMLPullParser(events=("start", "end"))
    parser.feed(data)
    parser.close()
    depth = 0
    root = None
    for event, elem in parser.read_events():
        if event == "start":
            if root is None:
                root = elem
            depth += 1
            if depth > MAX_NESTING:
                raise InputError("XML nesting too deep in " + name)
        else:
            depth -= 1
    if root is None:
        raise InputError("empty XML part: " + name)
    return root


def large_constants(formula, threshold):
    text = STRING_RE.sub('""', formula)
    text = SHEET_PREFIX_RE.sub("", text)
    text = CELL_REF_RE.sub(" ", text)
    return [m for m in NUMBER_RE.findall(text) if float(m) > threshold]


def scan_sheet(root, sheet_name, threshold):
    formulas = 0
    errors = []
    large = []
    for cell in root.iter():
        if local(cell.tag) != "c":
            continue
        ref = cell.get("r", "?")
        has_f = False
        ftext = ""
        err_value = None
        for child in cell:
            kind = local(child.tag)
            if kind == "f":
                has_f = True
                ftext = child.text or ""
            elif kind == "v" and cell.get("t") == "e":
                err_value = (child.text or "").strip()
        if cell.get("t") == "e" and err_value is None:
            err_value = ""
        if has_f:
            formulas += 1
        if err_value is not None:
            errors.append({"sheet": sheet_name, "cell": ref,
                           "error": err_value[:20]})
        if ftext:
            consts = large_constants(ftext, threshold)
            if consts:
                large.append({"sheet": sheet_name, "cell": ref,
                              "constants": consts[:10],
                              "formula": ftext[:120]})
    return formulas, errors, large


def read_rels(zf, names, rels_name):
    rels = {}
    if rels_name not in names:
        return rels
    root = parse_xml(read_part(zf, rels_name), rels_name)
    for elem in root.iter():
        if local(elem.tag) == "Relationship":
            rels[elem.get("Id")] = (elem.get("Target", ""),
                                    elem.get("TargetMode", ""))
    return rels


def resolve_part(target):
    if target.startswith("/"):
        return posixpath.normpath(target.lstrip("/"))
    return posixpath.normpath("xl/" + target)


def build_report(path, threshold):
    if os.path.getsize(path) > MAX_INPUT_BYTES:
        raise InputError("input larger than 2 MB")
    with zipfile.ZipFile(path) as zf:
        infos = zf.infolist()
        if len(infos) > MAX_ENTRIES:
            raise InputError("too many zip entries")
        if sum(i.file_size for i in infos) > MAX_TOTAL_UNCOMPRESSED:
            raise InputError("uncompressed size too large")
        names = set(zf.namelist())
        if "xl/workbook.xml" not in names:
            raise InputError("not an xlsx workbook: xl/workbook.xml missing")

        wb = parse_xml(read_part(zf, "xl/workbook.xml"), "xl/workbook.xml")
        rels = read_rels(zf, names, "xl/_rels/workbook.xml.rels")

        sheets = []
        formula_total = 0
        error_cells = []
        large_all = []
        sheet_elems = [e for e in wb.iter() if local(e.tag) == "sheet"]
        for index, elem in enumerate(sheet_elems):
            name = elem.get("name", "")[:200]
            state = elem.get("state", "visible")
            rid = next((v for k, v in elem.attrib.items()
                        if k.endswith("}id")), None)
            target = rels.get(rid, ("", ""))[0] if rid else ""
            part = resolve_part(target) if target else None
            entry = {"name": name, "index": index, "state": state,
                     "part": part, "formula_count": 0, "error_count": 0,
                     "scanned": False}
            if part and part in names:
                sroot = parse_xml(read_part(zf, part), part)
                fcount, errs, large = scan_sheet(sroot, name, threshold)
                entry["scanned"] = True
                entry["formula_count"] = fcount
                entry["error_count"] = len(errs)
                formula_total += fcount
                error_cells.extend(errs)
                large_all.extend(large)
            sheets.append(entry)

        defined = []
        for elem in wb.iter():
            if local(elem.tag) != "definedName":
                continue
            text = elem.text or ""
            scope = elem.get("localSheetId")
            defined.append({
                "name": elem.get("name", "")[:200],
                "scope_index": int(scope) if scope and scope.isdigit() else None,
                "hidden": elem.get("hidden") in ("1", "true"),
                "external_reference": "[" in text,
                "refers_to": text[:200],
            })

        ext_parts = sorted(n for n in names if EXT_PART_RE.match(n))
        external = []
        for part in ext_parts:
            base = posixpath.basename(part)
            rels_ext = read_rels(zf, names, "xl/externalLinks/_rels/"
                                 + base + ".rels")
            target = None
            for tgt, mode in rels_ext.values():
                if mode == "External":
                    target = tgt[:300]
                    break
            external.append({"part": part, "target": target})

    hidden_sheets = [s for s in sheets if s["state"] in ("hidden", "veryHidden")]
    hidden_names = [d for d in defined if d["hidden"]]
    truncated = []
    lists = {"sheets": sheets, "defined_names": defined,
             "external_links": external, "error_cells": error_cells,
             "large_constants": large_all}
    out_lists = {}
    for key, items in lists.items():
        if len(items) > MAX_LIST:
            truncated.append(key)
        out_lists[key] = items[:MAX_LIST]

    findings = (len(hidden_sheets) + len(external) + len(error_cells)
                + len(large_all) + len(hidden_names))
    return {
        "tool": "xlsx_scan",
        "version": VERSION,
        "input": os.path.basename(path),
        "threshold": threshold,
        "summary": {
            "sheet_count": len(sheets),
            "hidden_sheet_count": len(hidden_sheets),
            "defined_name_count": len(defined),
            "hidden_defined_name_count": len(hidden_names),
            "external_link_count": len(external),
            "formula_count": formula_total,
            "error_cell_count": len(error_cells),
            "large_constant_count": len(large_all),
            "findings": findings,
        },
        "sheets": out_lists["sheets"],
        "defined_names": out_lists["defined_names"],
        "external_links": out_lists["external_links"],
        "error_cells": out_lists["error_cells"],
        "large_constants": out_lists["large_constants"],
        "truncated_lists": truncated,
    }


def fail(message):
    sys.stderr.write(json.dumps({"error": message}, ensure_ascii=True) + "\n")
    return 2


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="xlsx_scan.py",
        description="Read-only hidden-risk scan of an .xlsx workbook.")
    parser.add_argument("input", help="path to the .xlsx file")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                        help="flag numeric literals above this value "
                             "(default 1000, working value)")
    parser.add_argument("--out", default=None,
                        help="write the JSON report here instead of stdout")
    args = parser.parse_args(argv)

    if not (args.threshold >= 0):
        return fail("threshold must be a number >= 0")
    if not os.path.isfile(args.input):
        return fail("input file not found")
    if args.out:
        if os.path.abspath(args.out) == os.path.abspath(args.input):
            return fail("output path must not be the input file")
        if os.path.exists(args.out) and os.path.samefile(args.out, args.input):
            return fail("output path must not be the input file")

    try:
        report = build_report(args.input, args.threshold)
    except InputError as exc:
        return fail(str(exc))
    except Exception as exc:  # any malformed container or XML
        return fail("unreadable workbook (" + type(exc).__name__ + ")")

    text = json.dumps(report, indent=2, ensure_ascii=True)
    if args.out:
        with io.open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    else:
        sys.stdout.write(text + "\n")
    return 1 if report["summary"]["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
