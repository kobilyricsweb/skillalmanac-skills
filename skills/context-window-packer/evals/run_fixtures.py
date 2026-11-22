#!/usr/bin/env python3
"""Run the fixture cases against scripts/pack_context.py.

    python evals/run_fixtures.py

Static cases come from fixtures/cases.json and the fixtures/proj folder.
Generated cases (binary, minified, secret-looking content, output-path
protection, bad input, non-ASCII estimate) build their inputs in a temporary
folder at run time, so no key-like string is stored in the package.
Reads fixtures; writes only inside a temporary folder. Exit 0 if every case
matches, 1 otherwise.
"""
import contextlib
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import pack_context  # noqa: E402

PROJ = os.path.join(HERE, "fixtures", "proj")


def run(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = pack_context.main(args)
        except SystemExit as exc:
            code = exc.code
    report = None
    if code in (0, 1) and out.getvalue().strip():
        report = json.loads(out.getvalue())
    return code, report, err.getvalue()


def view(rep):
    return {
        "status": rep.get("status"), "usable": rep.get("usable"), "used": rep.get("used"),
        "margin": rep.get("margin"), "margin_worst_case": rep.get("margin_worst_case"),
        "estimate_error_pct": rep.get("estimate_error_pct"),
        "kept": [r["id"] for r in rep.get("kept", [])],
        "compressed": {r["id"]: r["level"] for r in rep.get("compressed", [])},
        "dropped": {r["id"]: r["reason_code"] for r in rep.get("dropped", [])},
        "warnings": sorted(w["code"] for w in rep.get("warnings", [])),
        "errors": sorted(w["code"] for w in rep.get("errors", [])),
    }


def compare(code, rep, want_exit, expect):
    problems = []
    if code != want_exit:
        problems.append(f"exit {code}, wanted {want_exit}")
    if expect and rep is not None:
        got = view(rep)
        for key, want in expect.items():
            if got.get(key) != want:
                problems.append(f"{key}: got {got.get(key)!r}, wanted {want!r}")
    return problems


def write(path, data):
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(path, mode, **({} if mode == "wb" else {"encoding": "utf-8", "newline": "\n"})) as fh:
        fh.write(data)


def manifest(folder, budget, candidates, **extra):
    path = os.path.join(folder, "manifest.json")
    write(path, json.dumps(dict(budget=budget, reserve=0, candidates=candidates, **extra)))
    return path


def generated_cases():
    """Yield (name, problems) for cases whose inputs are built in a temp folder."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_key = "AK" + "IA" + "IOSFODNN7EXAMPLE"  # shaped like an access key id, built at run time
        write(os.path.join(tmp, "blob.dat"), b"\x00\x01\x02binary\x00")
        write(os.path.join(tmp, "app.min.js"), "var a=1;" * 800)
        write(os.path.join(tmp, "settings.txt"), f"region=eu\naccess_key={fake_key}\n")
        write(os.path.join(tmp, "plain.md"), "# Plain\n\nJust a short note.\n")
        write(os.path.join(tmp, "empty.txt"), "   \n")
        write(os.path.join(tmp, "wide.txt"), "é" * 20 + "a" * 40)

        # 1. skip rules: binary, minified, secret-looking, empty, missing, outside root
        m = manifest(tmp, 4000, [
            {"id": "bin", "path": "blob.dat", "priority": "should"},
            {"id": "min", "path": "app.min.js", "priority": "nice"},
            {"id": "sec", "path": "settings.txt", "priority": "should"},
            {"id": "empty", "path": "empty.txt", "priority": "nice"},
            {"id": "gone", "path": "nothing_here.md", "priority": "nice"},
            {"id": "out", "path": "../escape.md", "priority": "nice"},
            {"id": "ok", "path": "plain.md", "priority": "should"}])
        code, rep, _ = run(["pack", m])
        yield "skip rules: binary, minified, secret, empty, missing, outside root", compare(code, rep, 0, {
            "kept": ["ok"], "errors": [],
            "dropped": {"bin": "binary", "min": "minified", "sec": "possible_secret", "empty": "empty",
                        "gone": "missing_file", "out": "path_outside_root"}})

        # 2. a must item that cannot be used is an error
        m = manifest(tmp, 4000, [{"id": "bin", "path": "blob.dat", "priority": "must"},
                                 {"id": "ok", "path": "plain.md", "priority": "should"}])
        code, rep, _ = run(["pack", m])
        yield "must item that is binary gives an error", compare(code, rep, 1, {
            "status": "error", "errors": ["must_unusable"], "kept": ["ok"]})

        # 3. the override flag lets a reviewed secret-looking file through
        m = manifest(tmp, 4000, [{"id": "sec", "path": "settings.txt", "priority": "should",
                                  "allow_secret_match": True}])
        code, rep, _ = run(["pack", m])
        yield "allow_secret_match keeps a flagged file", compare(code, rep, 0, {"kept": ["sec"], "dropped": {}})

        # 3b. fake secrets of every shape are excluded and no value is printed
        fakes = {
            "envfile.txt": "APP=demo\nDB_PASSWORD=hunter2hunter2\n",
            "env2.txt": "export API_KEY=notarealvalue123\n",
            "tok.txt": "API_TOKEN: fake-token-value-0001\n",
            "jwt.txt": "auth " + "eyJ" + "hbGciOiJub25l" + ".eyJ" + "zdWIiOiJmYWtlIn0" + ".c2lnbmF0dXJl\n",
            "pem.txt": "-----BEGIN " + "RSA PRIVATE KEY-----\nZmFrZQ==\n-----END " + "RSA PRIVATE KEY-----\n",
            "akia.txt": "id " + fake_key + "\n",
            "sk.txt": "key sk" + "-" + "fakefakefakefakefake0000\n",
            "gh.txt": "t gh" + "p_" + "a" * 36 + "\n",
        }
        for fname, body in fakes.items():
            write(os.path.join(tmp, fname), body)
        write(os.path.join(tmp, "refs.txt"), "DB_PASSWORD=$DB_PASSWORD\nTOKEN_TTL=60\n")
        cands = [{"id": f.split(".")[0], "path": f, "priority": "must"} for f in fakes]
        cands.append({"id": "refs", "path": "refs.txt", "priority": "should"})
        m = manifest(tmp, 8000, cands)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = pack_context.main(["pack", m])
        text = out.getvalue() + err.getvalue()
        rep = json.loads(out.getvalue())
        probs = compare(code, rep, 1, {"kept": ["refs"], "dropped": {
            c["id"]: "possible_secret" for c in cands if c["id"] != "refs"}})
        for needle in ("hunter2", "notarealvalue", "fake-token-value", "hbGciOi", "ZmFrZQ", fake_key,
                       "fakefakefake", "a" * 36):
            if needle in text:
                probs.append("secret value appeared in output: " + needle[:6])
        yield "fake secrets of every shape excluded, values never printed, references kept", probs

        # 4. output protection: never overwrite an input, even with --force
        m = manifest(tmp, 4000, [{"id": "ok", "path": "plain.md", "priority": "should"}])
        before = open(os.path.join(tmp, "plain.md"), encoding="utf-8").read()
        code, _, err = run(["pack", m, "--out", os.path.join(tmp, "plain.md"), "--force"])
        after = open(os.path.join(tmp, "plain.md"), encoding="utf-8").read()
        probs = compare(code, None, 2, {})
        if before != after:
            probs.append("candidate file was modified by --out --force")
        if "refusing" not in err:
            probs.append("no refusal message for --out equal to a candidate")
        yield "--out equal to a candidate is refused even with --force", probs

        mtext = open(m, encoding="utf-8").read()
        code, _, err = run(["pack", m, "--out", m, "--force"])
        probs = compare(code, None, 2, {})
        if open(m, encoding="utf-8").read() != mtext:
            probs.append("manifest was modified by --out --force")
        yield "--out equal to the manifest is refused even with --force", probs

        # 5. a new output file is written; an existing one needs --force
        pkg = os.path.join(tmp, "package.md")
        code, rep, _ = run(["pack", m, "--out", pkg])
        probs = compare(code, rep, 0, {"kept": ["ok"]})
        text = open(pkg, encoding="utf-8").read() if os.path.isfile(pkg) else ""
        if not text.startswith("=== ok: plain.md [full] ===\n") or "Just a short note." not in text:
            probs.append("package file missing header or content")
        yield "--out writes the package", probs
        code, _, _ = run(["pack", m, "--out", pkg])
        yield "existing --out is not replaced without --force", compare(code, None, 2, {})
        code, _, _ = run(["pack", m, "--out", pkg, "--force"])
        yield "existing --out is replaced with --force", compare(code, None, 0, {})

        # 6. bad input
        bad = os.path.join(tmp, "bad.json")
        write(bad, json.dumps({"budget": 0, "candidates": [{"id": "a", "path": "plain.md", "priority": "must"}]}))
        yield "budget 0 is bad input", compare(run(["pack", bad])[0], None, 2, {})
        write(bad, json.dumps({"budget": 100, "reserve": 100,"candidates": [{"id": "a", "path": "plain.md", "priority": "must"}]}))
        yield "reserve that leaves no usable space is bad input", compare(run(["pack", bad])[0], None, 2, {})
        write(bad, json.dumps({"budget": 500, "candidates": [{"id": "a", "path": "plain.md", "priority": "must"},
                                                             {"id": "a", "path": "plain.md", "priority": "nice"}]}))
        yield "duplicate ids are bad input", compare(run(["pack", bad])[0], None, 2, {})
        write(bad, json.dumps({"budget": 500, "candidates": [{"id": "a", "path": "plain.md", "priority": "urgent"}]}))
        yield "unknown priority is bad input", compare(run(["pack", bad])[0], None, 2, {})
        write(bad, "{not json")
        yield "invalid JSON is bad input", compare(run(["pack", bad])[0], None, 2, {})

        # 7. estimate command, non-ASCII text widens the error range
        code, rep, _ = run(["estimate", os.path.join(tmp, "wide.txt")])
        probs = compare(code, None, 0, {})
        row = (rep or {}).get("files", [{}])[0]
        if (row.get("tokens"), row.get("error_pct"), row.get("range")) != (30, 40, [18, 42]):
            probs.append(f"estimate row {row!r}, wanted tokens 30, error 40, range [18, 42]")
        yield "estimate: 40 ASCII + 20 non-ASCII characters", probs


def main():
    cases = json.load(open(os.path.join(HERE, "fixtures", "cases.json"), encoding="utf-8"))["cases"]
    results = []
    for case in cases:
        args = [os.path.join(PROJ, a) if a.endswith(".json") else a for a in case["args"]]
        code, rep, _ = run(args)
        results.append((case["name"], compare(code, rep, case["exit"], case["expect"])))
    results.extend(generated_cases())
    failed = 0
    for name, problems in results:
        print(("PASS " if not problems else "FAIL ") + name)
        for p in problems:
            print("    " + p)
        failed += bool(problems)
    print(f"{len(results) - failed}/{len(results)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
