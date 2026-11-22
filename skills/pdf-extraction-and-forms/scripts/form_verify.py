#!/usr/bin/env python3
"""Check a filled PDF form against its field-mapping file. Standard library only.

    python form_verify.py mapping.json output_inspect.json [--original original_inspect.json]

Both JSON inputs are reports: mapping.json is the field-mapping contract
(see SKILL.md) and output_inspect.json is the output of
`pdf_inspect.py filled.pdf`. The optional original report (pdf_inspect.py on
the blank form) lets the check also detect fields that changed without being
in the mapping.

Reads the files, writes one strict JSON object to stdout, changes nothing.
Exit codes: 0 = every mapped value was read back as written and nothing
unexpected changed, 1 = at least one problem, 2 = usage error or bad input.
A value that cannot be read back (for example fields stored in compressed
object streams) is reported as "unreadable", never as a pass.
"""
import json
import sys

STATUS_OK = "ok"


def norm(v):
    """Compare values loosely: trim, drop a leading slash on names, case-fold On/Yes style names only for buttons later."""
    if v is None:
        return None
    return str(v).strip()


def load(path):
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def main(argv):
    original = None
    args = list(argv)
    if "--original" in args:
        k = args.index("--original")
        try:
            original = args[k + 1]
        except IndexError:
            args = []
        else:
            del args[k:k + 2]
    if len(args) != 2:
        print(json.dumps({"ok": False, "error": "usage: form_verify.py mapping.json output_inspect.json [--original original_inspect.json]"}))
        return 2
    try:
        mapping, out = load(args[0]), load(args[1])
        orig = load(original) if original else None
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": "cannot read input: %s" % exc}))
        return 2
    if not isinstance(mapping.get("fields"), list) or "form" not in out:
        print(json.dumps({"ok": False, "error": "mapping needs a 'fields' list and the inspect report needs a 'form' object"}))
        return 2

    out_fields = {f["name"]: f for f in out["form"].get("fields", [])}
    orig_fields = {f["name"]: f for f in orig["form"].get("fields", [])} if orig else None
    skipped = {s["pdf_field"] for s in mapping.get("unfilled_on_purpose", [])}
    problems, results, mapped = [], [], set()
    unreadable_all = bool(out.get("encryption", {}).get("encrypted")) or (
        out["form"].get("field_count", 0) == 0 and out.get("object_streams", 0) > 0)

    for item in mapping["fields"]:
        name, want = item.get("pdf_field"), item.get("value")
        mapped.add(name)
        f = out_fields.get(name)
        if f is None:
            status = "unreadable" if unreadable_all else "missing_in_output"
        else:
            got = f.get("value")
            want_s, got_s = norm(want), norm(got)
            if f.get("type") in ("checkbox", "radio") and want_s is not None:
                want_s = want_s if want_s.startswith("/") else "/" + want_s
            if f.get("type") in ("checkbox", "radio") and got_s is not None:
                got_s = got_s if got_s.startswith("/") else "/" + got_s
            if got_s is None and want_s not in (None, ""):
                status = "empty_in_output"
            elif got_s == want_s or (want_s in (None, "") and got_s is None):
                status = STATUS_OK
            else:
                status = "value_mismatch"
        results.append({"pdf_field": name, "status": status, "wanted": want, "read_back": f.get("value") if f else None})
        if status != STATUS_OK:
            problems.append(name)

    for name, f in out_fields.items():
        if name in mapped or name in skipped:
            continue
        before = orig_fields.get(name, {}).get("value") if orig_fields is not None else None
        if f.get("value") is not None and (orig_fields is None or f.get("value") != before):
            results.append({"pdf_field": name, "status": "unexpected_value", "wanted": None, "read_back": f.get("value")})
            problems.append(name)
        elif f.get("required") and f.get("value") is None:
            results.append({"pdf_field": name, "status": "required_empty_not_declared", "wanted": None, "read_back": None})
            problems.append(name)

    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    rep = {"ok": not problems, "mapped_fields": len(mapped), "counts": counts, "results": results,
           "limits": "Reads form field values only. It does not check what a viewer displays (appearance streams) or text printed on the page."}
    print(json.dumps(rep, ensure_ascii=True, allow_nan=False, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
