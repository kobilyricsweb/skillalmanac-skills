#!/usr/bin/env python3
"""Run the fixture cases in fixtures/cases.json against scripts/review_session.py,
then a few synthetic cases built in a temporary directory (default thresholds,
citation check, secret redaction, JSON-document layout).

    python evals/run_fixtures.py

Reads fixtures, writes only into a temporary directory it removes afterwards.
Exit 0 if every case matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import review_session  # noqa: E402


def run(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = review_session.main(args)
        except SystemExit as exc:
            code = exc.code
    return code, (json.loads(out.getvalue()) if out.getvalue().strip() else None)


def summarize(rep):
    f = rep["findings"]
    return {
        "events": rep["totals"]["events"],
        "formats": [x["format"] for x in rep["files"]],
        "kinds": [x["kind"] for x in f],
        "evidence_lines": [x["evidence_lines"] for x in f],
        "finding_tokens": [x["estimated_tokens"] for x in f],
        "unparseable_total": rep["checks"]["unparseable_total"],
        "missing_timestamps": rep["checks"]["missing_timestamps"],
        "mixed_sessions": rep["checks"]["mixed_sessions"],
        "top_turn_line": rep["top_turns"][0]["line"],
        "usage_input_tokens": (rep["totals"]["reported_usage"] or {}).get("input_tokens"),
    }


def check(code, rep, want_exit, expect):
    problems = []
    if code != want_exit:
        problems.append("exit %r, wanted %r" % (code, want_exit))
    if rep is not None and expect:
        got = summarize(rep)
        for key, want in expect.items():
            if got[key] != want:
                problems.append("%s: got %r, wanted %r" % (key, got[key], want))
    return problems


def fixture_cases():
    fx = os.path.join(HERE, "fixtures")
    cases = json.load(open(os.path.join(fx, "cases.json"), encoding="utf-8"))["cases"]
    for case in cases:
        args = [os.path.join(fx, a) if a.endswith((".jsonl", ".txt")) else a for a in case["args"]]
        code, rep = run(args)
        yield " ".join(case["args"][:3]), check(code, rep, case["exit"], case["expect"])


def synthetic_cases(tmp):
    def write(name, text):
        path = os.path.join(tmp, name)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        return path

    def rec(role, content, **extra):
        return json.dumps(dict(role=role, content=content, **extra))

    big = ("alpha_module_name beta_function_call gamma_parameter_x " * 400)[:21000]
    ask = rec("user", "Find the config loader")
    call = json.dumps({"role": "assistant", "content": [{"type": "tool_use", "id": "z1", "name": "Bash", "input": {"command": "grep -r loader ."}}]})
    res = json.dumps({"role": "user", "content": [{"type": "tool_result", "tool_use_id": "z1", "content": big}]})

    # a) 21,000-character result nobody cites, default thresholds
    p = write("big_uncited.jsonl", "\n".join([ask, call, res, rec("assistant", "Nothing relevant came back.")]) + "\n")
    code, rep = run([p])
    yield "default thresholds: uncited 21k result", check(
        code, rep, 0, {"kinds": ["oversized_output"], "finding_tokens": [5250], "evidence_lines": [[3]]})

    # b) same result, cited later by three of its identifiers
    cite = rec("assistant", "The loader lives in alpha_module_name, using beta_function_call with gamma_parameter_x.")
    p = write("big_cited.jsonl", "\n".join([ask, call, res, cite]) + "\n")
    code, rep = run([p])
    yield "default thresholds: cited 21k result", check(code, rep, 0, {"kinds": []})

    # c) secrets are redacted in previews; key built from pieces so this file holds no key literal
    key = "AK" + "IA" + "ABCDEFGHIJKLMNOP"
    tok = "sk" + "-" + "abcdefghijklmnopqrstuvwxyz0123"
    secret_res = json.dumps({"role": "user", "content": [{"type": "tool_result", "tool_use_id": "z1", "content": "AWS key " + key + " and token " + tok}]})
    p = write("secret.jsonl", "\n".join([ask, call, secret_res]) + "\n")
    code, rep = run([p])
    blob = json.dumps(rep)
    problems = []
    if code != 0:
        problems.append("exit %r" % code)
    if key in blob or tok in blob or "[REDACTED]" not in blob:
        problems.append("secret not redacted in output")
    yield "secrets redacted in previews", problems

    # d) one JSON document (list of records)
    doc = [json.loads(ask), json.loads(rec("assistant", "Hello there."))]
    p = write("doc.json", json.dumps(doc, indent=1))
    code, rep = run([p])
    yield "json document layout", check(code, rep, 0, {"events": 2, "formats": ["json_document"]})

    # e) message bodies never exceed 80 characters in the output
    long_user = rec("user", "word " * 100)
    p = write("long.jsonl", long_user + "\n")
    code, rep = run([p])
    longest = max(len(t["preview"]) for t in rep["top_turns"]) if rep else 999
    yield "preview capped at 80 characters", ([] if code == 0 and longest <= 80 else ["longest preview %d" % longest])


def main():
    results = list(fixture_cases())
    tmp = tempfile.mkdtemp(prefix="session_cost_review_")
    try:
        results += list(synthetic_cases(tmp))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    failed = 0
    for label, problems in results:
        print(("PASS " if not problems else "FAIL ") + label)
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print("%d/%d cases passed" % (len(results) - failed, len(results)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
