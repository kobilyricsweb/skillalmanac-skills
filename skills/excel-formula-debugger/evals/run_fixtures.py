#!/usr/bin/env python3
"""Build the test workbooks and run the fixture cases against scripts/audit_workbook.py.

    python evals/run_fixtures.py                  run every case; exit 0 if all pass
    python evals/run_fixtures.py --write-dir DIR  also write the workbooks as .xlsx files into DIR
    python evals/run_fixtures.py --show NAME      print the audit JSON for workbook NAME

The package is text only, so fixtures/workbooks.json describes each workbook and
this script writes a real .xlsx (a zip of XML parts) to a temporary folder (or DIR).
Reads fixtures; writes only to the temporary folder or the DIR you name.
"""
import contextlib
import io
import json
import os
import re
import sys
import tempfile
import zipfile
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import audit_workbook  # noqa: E402

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def split_addr(text):
    m = re.match(r"^([A-Z]+)(\d+)$", text)
    return int(m.group(2)), audit_workbook.col_to_num(m.group(1))


def cell_xml(ref, spec):
    if isinstance(spec, str):
        return f'<c r="{ref}" t="inlineStr"><is><t>{escape(spec)}</t></is></c>'
    if isinstance(spec, (int, float)):
        return f'<c r="{ref}"><v>{spec!r}</v></c>'
    f_xml = ""
    if "f" in spec and spec.get("ref"):
        f_xml = f'<f t="shared" ref="{spec["ref"]}" si="{spec["si"]}">{escape(spec["f"])}</f>'
    elif spec.get("shared"):
        f_xml = f'<f t="shared" si="{spec["si"]}"/>'
    elif "f" in spec:
        f_xml = f"<f>{escape(spec['f'])}</f>"
    if "e" in spec:
        return f'<c r="{ref}" t="e">{f_xml}<v>{escape(spec["e"])}</v></c>'
    if "v" not in spec:
        return f'<c r="{ref}">{f_xml}</c>'
    v = spec["v"]
    if isinstance(v, str):
        return f'<c r="{ref}" t="str">{f_xml}<v>{escape(v)}</v></c>'
    return f'<c r="{ref}">{f_xml}<v>{v!r}</v></c>'


def sheet_xml(cells):
    rows = {}
    for ref, spec in cells.items():
        r, c = split_addr(ref)
        rows.setdefault(r, []).append((c, ref, spec))
    parts = [f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="{NS}"><sheetData>']
    for r in sorted(rows):
        parts.append(f'<row r="{r}">')
        for c, ref, spec in sorted(rows[r]):
            parts.append(cell_xml(ref, spec))
        parts.append("</row>")
    parts.append("</sheetData></worksheet>")
    return "".join(parts)


def build_xlsx(path, wb):
    sheets = wb["sheets"]
    sheet_tags = "".join(
        f'<sheet name="{escape(s["name"])}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i, s in enumerate(sheets))
    names = "".join(f'<definedName name="{escape(k)}">{escape(v)}</definedName>'
                    for k, v in wb.get("defined_names", {}).items())
    names = f"<definedNames>{names}</definedNames>" if names else ""
    calc = '<calcPr calcId="191029" iterate="1"/>' if wb.get("iterate") else '<calcPr calcId="191029"/>'
    workbook = (f'<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="{NS}" xmlns:r="{REL_NS}">'
                f"<sheets>{sheet_tags}</sheets>{names}{calc}</workbook>")
    rels = "".join(
        f'<Relationship Id="rId{i + 1}" Type="{REL_NS}/worksheet" Target="worksheets/sheet{i + 1}.xml"/>'
        for i in range(len(sheets)))
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships '
            f'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rels}</Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", rels)
        for i, s in enumerate(sheets):
            zf.writestr(f"xl/worksheets/sheet{i + 1}.xml", sheet_xml(s["cells"]))


def build_all(directory, specs):
    paths = {}
    for name, wb in specs.items():
        if name.startswith("_"):
            continue
        paths[name] = os.path.join(directory, name + ".xlsx")
        build_xlsx(paths[name], wb)
    # three files that are not workbooks, for the error cases
    paths["notzip"] = os.path.join(directory, "notzip.xlsx")
    with open(paths["notzip"], "w", encoding="utf-8") as fh:
        fh.write("this is plain text, not a zip archive\n")
    paths["emptyzip"] = os.path.join(directory, "emptyzip.xlsx")
    with zipfile.ZipFile(paths["emptyzip"], "w") as zf:
        zf.writestr("readme.txt", "no workbook here")
    paths["missing"] = os.path.join(directory, "does_not_exist.xlsx")
    return paths


def run_script(path):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = audit_workbook.main([path])
    return code, out.getvalue(), err.getvalue()


def run_case(case, paths):
    code, out, err = run_script(paths[case["workbook"]])
    problems = []
    if code != case["exit"]:
        problems.append(f"exit {code}, wanted {case['exit']}")
    exp = case.get("expect") or {}
    if code in (0, 1):
        rep = json.loads(out)
        got = {
            "ok": rep["ok"],
            "formula_cells": rep["workbook"]["formula_cells"],
            "cached_values_present": rep["workbook"]["cached_values_present"],
            "iterative_calculation": rep["workbook"]["iterative_calculation"],
            "volatile_cells": rep["workbook"]["volatile_cells"],
            "volatile_downstream_cells": rep["workbook"]["volatile_downstream_cells"],
            "counts_by_category": rep["counts_by_category"],
            "counts_by_severity": rep["counts_by_severity"],
            "findings": sorted(f"{f['severity']}:{f['category']}:{f['sheet']}!{f['cell']}" for f in rep["findings"]),
            "cross_sheet_targets": {s["name"]: s["cross_sheet_targets"] for s in rep["sheets"]},
            "used_ranges": {s["name"]: s["used_range"] for s in rep["sheets"]},
            "circular_paths": sorted(" > ".join(f["path"]) for f in rep["findings"] if f["category"] == "circular_reference"),
            "root_causes": sorted(f"{f['sheet']}!{f['cell']}" for f in rep["findings"]
                                  if f["category"] == "error_value" and f.get("root_cause")),
            "no_saved_results_note": any(s.startswith("No formula in this file") for s in rep["not_checked"]),
        }
        for key, want in exp.items():
            if got.get(key) != want:
                problems.append(f"{key}: got {got.get(key)!r}, wanted {want!r}")
        # strict JSON: re-parse with NaN and Infinity rejected
        def reject(token):
            raise ValueError(f"non-standard JSON constant {token}")
        json.loads(out, parse_constant=reject)
        if not out.isascii():
            problems.append("output is not plain ASCII")
    elif exp.get("stderr_contains") and exp["stderr_contains"] not in err:
        problems.append(f"stderr {err.strip()!r} lacks {exp['stderr_contains']!r}")
    if code == 2 and out:
        problems.append("exit 2 must print nothing on stdout")
    return problems


def main(argv):
    with open(os.path.join(HERE, "fixtures", "workbooks.json"), encoding="utf-8") as fh:
        specs = json.load(fh)
    if "--write-dir" in argv:
        target = argv[argv.index("--write-dir") + 1]
        os.makedirs(target, exist_ok=True)
        build_all(target, specs)
        print("wrote workbooks to " + target)
    with tempfile.TemporaryDirectory() as tmp:
        paths = build_all(tmp, specs)
        if "--show" in argv:
            code, out, err = run_script(paths[argv[argv.index("--show") + 1]])
            sys.stdout.write(out + err)
            return code
        with open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8") as fh:
            cases = json.load(fh)["cases"]
        failed = 0
        for case in cases:
            problems = run_case(case, paths)
            print(("PASS " if not problems else "FAIL ") + case["workbook"])
            for p in problems:
                print("    " + p)
            failed += bool(problems)
    print(f"{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
