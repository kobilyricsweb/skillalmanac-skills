#!/usr/bin/env python3
"""Fixture tests for skill_manifest.py. Builds small skill folders in a temporary
directory and checks what the script reports.

    python evals/run_fixtures.py

Exit 0 when every case matches, 1 otherwise. Standard library only.
"""
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "skill_manifest.py")
AUTH = "skills.example.com"


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data if isinstance(data, bytes) else data.encode("utf-8"))


def skill(root, name, folder=None, extra=None, description="Formats invoices. Use when asked."):
    d = os.path.join(root, folder or name)
    write(os.path.join(d, "SKILL.md"), f"---\nname: {name}\ndescription: {description}\nlicense: MIT\n---\n\n# {name}\n")
    write(os.path.join(d, "scripts", "run.py"), "print('ok')\n")
    for rel, data in (extra or {}).items():
        write(os.path.join(d, rel), data)
    return d


def run(*args):
    p = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True, encoding="utf-8")
    try:
        return p.returncode, json.loads(p.stdout)
    except ValueError:
        return p.returncode, {"errors": [p.stderr], "warnings": []}


def has(report, text):
    return any(text in e for e in report.get("errors", []))


def main():
    results = []

    def case(name, ok, detail=""):
        results.append(ok)
        print(f"{'PASS' if ok else 'FAIL'} {name} {detail}")

    with tempfile.TemporaryDirectory() as tmp:
        # 1. A clean build, checked against the folder.
        root = os.path.join(tmp, "clean")
        skill(root, "invoice-format", extra={"references/notes.md": "café €\n"})
        skill(root, "csv-clean")
        man = os.path.join(tmp, "clean.json")
        code, rep = run("build", root, f"--authority={AUTH}", f"--out={man}")
        doc = json.load(open(man, encoding="utf-8")) if code == 0 else {"skills": []}
        entry = next((e for e in doc["skills"] if e["frontmatter"]["name"] == "invoice-format"), None)
        case("build-clean", code == 0 and rep["skills"] == 2 and entry is not None
             and entry["uri"] == f"skill://{AUTH}/invoice-format/SKILL.md"
             and any(r["uri"] == entry["uri"] for r in entry["resources"])
             and entry["frontmatter"].get("license") == "MIT")
        notes = next((r for r in (entry or {}).get("resources", []) if r["uri"].endswith("/references/notes.md")), {})
        raw = "café €\n".encode("utf-8")
        case("size-is-bytes-and-digest-is-raw-sha256",
             notes.get("size") == len(raw) == 10 and notes.get("digest") == "sha256:" + hashlib.sha256(raw).hexdigest())
        code, rep = run("check", man, f"--root={root}", f"--authority={AUTH}")
        case("check-clean", code == 0 and rep["ok"])

        # 2. The folder changes after the build.
        write(os.path.join(root, "invoice-format", "scripts", "run.py"), "print('changed')\n")
        code, rep = run("check", man, f"--root={root}", f"--authority={AUTH}")
        case("edited-file-caught", code == 1 and (has(rep, "size is") or has(rep, "digest does not match")))
        write(os.path.join(root, "invoice-format", "scripts", "run.py"), "print('ko')\n")
        code, rep = run("check", man, f"--root={root}", f"--authority={AUTH}")
        case("same-size-different-bytes-caught", code == 1 and has(rep, "digest does not match"))
        write(os.path.join(root, "invoice-format", "scripts", "run.py"), "print('ok')\r\n")
        code, rep = run("check", man, f"--root={root}", f"--authority={AUTH}")
        case("crlf-changes-the-bytes", code == 1 and has(rep, "size is"))
        write(os.path.join(root, "invoice-format", "scripts", "run.py"), "print('ok')\n")
        write(os.path.join(root, "invoice-format", "extra.txt"), "new\n")
        code, rep = run("check", man, f"--root={root}", f"--authority={AUTH}")
        case("unlisted-file-caught", code == 1 and has(rep, "not listed"))
        os.remove(os.path.join(root, "invoice-format", "extra.txt"))
        os.remove(os.path.join(root, "invoice-format", "references", "notes.md"))
        code, rep = run("check", man, f"--root={root}", f"--authority={AUTH}")
        case("missing-file-caught", code == 1 and has(rep, "does not exist"))
        write(os.path.join(root, "invoice-format", "references", "notes.md"), raw)
        md = os.path.join(root, "invoice-format", "SKILL.md")
        text = open(md, encoding="utf-8").read().replace("license: MIT", "license: Apache-2.0")
        write(md, text)
        code, rep = run("check", man, f"--root={root}", f"--authority={AUTH}")
        case("frontmatter-change-caught", code == 1 and has(rep, "frontmatter differs") and has(rep, "license"))

        # 3. Folders the build must refuse.
        bad = os.path.join(tmp, "badname")
        skill(bad, "Bad_Name", folder="bad-name")
        code, rep = run("build", bad, f"--authority={AUTH}")
        case("bad-name-refused", code == 1 and has(rep, "naming rules"))
        dup = os.path.join(tmp, "dup")
        skill(dup, "same-name", folder="a")
        skill(dup, "same-name", folder="b")
        code, rep = run("build", dup, f"--authority={AUTH}")
        case("duplicate-name-refused", code == 1 and has(rep, "collide"))
        many = os.path.join(tmp, "many")
        skill(many, "many-files", extra={f"data/f{i:03d}.txt": "x" for i in range(511)})
        code, rep = run("build", many, f"--authority={AUTH}")
        case("more-than-512-files-refused", code == 1 and has(rep, "limit is 512"))
        big = os.path.join(tmp, "big")
        skill(big, "big-skill", extra={"data/blob.bin": b"\0" * (16 * 1024 * 1024)})
        code, rep = run("build", big, f"--authority={AUTH}")
        case("more-than-16-mib-refused", code == 1 and has(rep, "16 MiB"))
        nofm = os.path.join(tmp, "nofm")
        write(os.path.join(nofm, "plain", "SKILL.md"), "# no frontmatter\n")
        code, rep = run("build", nofm, f"--authority={AUTH}")
        case("no-frontmatter-refused", code == 1 and has(rep, "frontmatter"))

        # 4. Excludes and nested skills.
        ex = os.path.join(tmp, "ex")
        skill(ex, "with-cache", extra={"__pycache__/run.cpython-311.pyc": b"\x00\x01", "evals/fixture/SKILL.md": "---\nname: inner\ndescription: Inner. Use never.\n---\n"})
        code, rep = run("build", ex, f"--authority={AUTH}")
        case("junk-file-warned", code == 0 and any("build or system file" in w for w in rep["warnings"]) and rep["skills"] == 1)
        code, rep = run("build", ex, f"--authority={AUTH}", "--exclude=__pycache__")
        case("exclude-removes-it", code == 0 and not rep["warnings"] and rep["resources"] == 3)
        code, rep = run("build", ex, f"--authority={AUTH}", "--exclude=__pycache__", "--nested")
        case("nested-is-opt-in", code == 0 and rep["skills"] == 2)

        # 5. Structural checks on a manifest from elsewhere.
        base = json.load(open(man, encoding="utf-8"))

        def variant(change):
            d = copy.deepcopy(base)
            change(d)
            path = os.path.join(tmp, "variant.json")
            json.dump(d, open(path, "w", encoding="utf-8"))
            return run("check", path)

        def drop_skill_md(d):
            e = d["skills"][0]
            e["resources"] = [r for r in e["resources"] if r["uri"] != e["uri"]]

        code, rep = variant(drop_skill_md)
        case("skill-md-must-be-listed", code == 1 and has(rep, "SKILL.md itself"))
        code, rep = variant(lambda d: d["skills"][0]["resources"][0].update(digest=d["skills"][0]["resources"][0]["digest"].upper()))
        case("uppercase-digest-refused", code == 1 and has(rep, "64 lowercase hex"))
        code, rep = variant(lambda d: d["skills"][0]["resources"][0].update(digest="md5:abc"))
        case("wrong-digest-algorithm-refused", code == 1 and has(rep, "64 lowercase hex"))
        code, rep = variant(lambda d: d["skills"][0].pop("resources"))
        case("missing-resources-refused", code == 1 and has(rep, "invalid"))
        code, rep = variant(lambda d: d["skills"][0].update(resources="dynamic"))
        case("dynamic-allowed-with-warning", code == 0 and any("dynamic" in w for w in rep["warnings"]))
        code, rep = variant(lambda d: d["skills"][0]["resources"].append({"uri": f"skill://{AUTH}/other/x.md", "digest": "sha256:" + "0" * 64, "size": 1}))
        case("file-outside-skill-refused", code == 1 and has(rep, "outside the skill"))
        code, rep = variant(lambda d: d["skills"][0]["frontmatter"].update(name="renamed"))
        case("name-must-match-uri", code == 1 and has(rep, "must equal frontmatter.name"))
        code, rep = variant(lambda d: d.update(cacheScope="shared"))
        case("cache-scope-enum", code == 1 and has(rep, "cacheScope"))
        code, rep = variant(lambda d: d["skills"][0]["resources"].append(dict(d["skills"][0]["resources"][0])))
        case("duplicate-resource-refused", code == 1 and has(rep, "listed twice"))

        # 6. Cases from the independent review.
        def raw_run(*args, hide_yaml=False):
            code = "import sys, runpy\n"
            if hide_yaml:
                code += "sys.modules['yaml'] = None\n"
            code += f"sys.argv = [{SCRIPT!r}] + {list(args)!r}\nrunpy.run_path({SCRIPT!r}, run_name='__main__')\n"
            pr = subprocess.run([sys.executable, "-c", code], capture_output=True)
            out = pr.stdout.decode("utf-8", "replace")
            err = pr.stderr.decode("utf-8", "replace")
            try:
                return pr.returncode, json.loads(out), err
            except ValueError:
                return pr.returncode, {"errors": [err], "warnings": []}, err

        def one(folder, name, front, extra=None):
            d = os.path.join(tmp, folder, name)
            write(os.path.join(d, "SKILL.md"), front)
            for rel, data in (extra or {}).items():
                write(os.path.join(d, rel), data)
            return os.path.join(tmp, folder)

        r6 = one("uni", "uni-skill", "---\nname: uni-skill\ndescription: \u65e5\u672c\u8a9e caf\u00e9. Use when asked.\n---\n")
        code, rep, err = raw_run("build", r6, f"--authority={AUTH}")
        case("non-ascii-output-no-crash", code == 0 and "Traceback" not in err
             and rep["manifest"]["skills"][0]["frontmatter"]["description"].startswith("\u65e5"))

        r6 = one("blk", "blk-skill", "---\nname: blk-skill\ndescription: |\n  first\n  ---\n  second\nlicense: MIT\n---\nbody\n")
        code, rep, err = raw_run("build", r6, f"--authority={AUTH}")
        fm = rep["manifest"]["skills"][0]["frontmatter"] if code == 0 else {}
        case("indented-dashes-do-not-close-frontmatter", fm.get("license") == "MIT" and "second" in fm.get("description", ""))

        for label, bad in (("dot-dot", "/../other/x.md"), ("encoded-dot-dot", "/%2e%2e/x.md"), ("encoded-slash", "/a%2F..%2Fb"),
                           ("empty-segment", "//x.md"), ("query", "/a.txt?x=1")):
            def add(d, bad=bad):
                e = d["skills"][0]
                e["resources"].append({"uri": e["uri"][: -len("/SKILL.md")] + bad, "digest": "sha256:" + "0" * 64, "size": 1})
            code, rep = variant(add)
            case(f"escaping-uri-refused-{label}", code == 1 and len(rep["errors"]) >= 1)

        code, rep = variant(lambda d: d["skills"].append("junk"))
        case("non-object-entry-refused", code == 1 and has(rep, "not an object"))

        def rename_bad(d):
            e = d["skills"][0]
            old = e["uri"][: -len("/SKILL.md")]
            new_root = old.rsplit("/", 1)[0] + "/Bad_Name"
            e["frontmatter"]["name"] = "Bad_Name"
            e["uri"] = new_root + "/SKILL.md"
            for r in e["resources"]:
                r["uri"] = new_root + r["uri"][len(old):]
        code, rep = variant(rename_bad)
        case("bad-name-refused-in-check", code == 1 and has(rep, "naming rules"))

        def no_scheme(d):
            e = d["skills"][0]
            e["uri"] = e["uri"].replace("skill://", "")
            for r in e["resources"]:
                r["uri"] = r["uri"].replace("skill://", "")
        code, rep = variant(no_scheme)
        case("uri-without-scheme-refused", code == 1 and has(rep, "scheme"))

        r6 = one("nan", "nan-skill", "---\nname: nan-skill\ndescription: d. Use when asked.\nscore: .nan\n---\n")
        code, rep, err = raw_run("build", r6, f"--authority={AUTH}")
        case("nan-refused", code == 1 and "Traceback" not in err and has(rep, "NaN"))
        r6 = one("intkey", "key-skill", "---\nname: key-skill\ndescription: d. Use when asked.\n1: one\n---\n")
        code, rep, err = raw_run("build", r6, f"--authority={AUTH}")
        case("non-string-key-refused", code == 1 and "Traceback" not in err and has(rep, "not a string"))
        r6 = os.path.join(tmp, "utf16")
        write(os.path.join(r6, "wide", "SKILL.md"), "---\nname: wide\ndescription: d\n---\n".encode("utf-16"))
        code, rep, err = raw_run("build", r6, f"--authority={AUTH}")
        case("utf16-skill-md-clean-error", code == 1 and "Traceback" not in err)

        code, rep, err = raw_run("build", root, f"--authority={AUTH}", f"--out={os.path.join(root, 'skills-list.json')}")
        case("out-inside-root-refused", code == 2 and "outside" in err)
        code, rep, err = raw_run("build", root, f"--authority={AUTH}", "--nested=false")
        case("nested-takes-no-value", code == 2)
        code, rep, err = raw_run("check", man, "--root=" + os.path.join(tmp, "missing"), f"--authority={AUTH}")
        case("missing-root-clean-error", code == 2 and "Traceback" not in err)

        code, rep, err = raw_run("build", ex, f"--authority={AUTH}", "--nested", "--exclude=evals", "--exclude=__pycache__")
        case("exclude-applies-to-nested-discovery", code == 0 and rep["skills"] == 1)

        single = os.path.join(tmp, "single", "solo-skill")
        skill(os.path.join(tmp, "single"), "solo-skill")
        code, rep, err = raw_run("build", single, f"--authority={AUTH}")
        case("root-is-a-skill", code == 0 and rep["skills"] == 1 and not rep["warnings"])

        # Dynamic content lacks digests, but frontmatter comparison is still required.
        dynroot = os.path.join(tmp, "dynamic-fm")
        skill(dynroot, "dynamic-fm")
        _, dynrep = run("build", dynroot, f"--authority={AUTH}")
        dyn = dynrep["manifest"]
        dyn["skills"][0]["resources"] = "dynamic"
        dyn["skills"][0]["frontmatter"]["description"] = "Wrong description"
        dynfile = os.path.join(tmp, "dynamic-fm.json")
        write(dynfile, json.dumps(dyn))
        dc, dr = run("check", dynfile, f"--root={dynroot}", f"--authority={AUTH}")
        case("dynamic-frontmatter-mismatch-refused", dc == 1 and has(dr, "frontmatter differs"))

        for nested_key in (False, True):
            extra = "metadata:\n  author: first\n  author: second\n" if nested_key else "description: second\n"
            dup = one("dup-yaml", "dup-yaml", "---\nname: dup-yaml\ndescription: first\n" + extra + "---\n")
            dc, dr, de = raw_run("build", dup, f"--authority={AUTH}")
            case("duplicate-yaml-key-refused-" + str(nested_key), dc == 1 and has(dr, "appears twice") and "Traceback" not in de)

        for label, value in (("empty", ""), ("whitespace", "   "), ("too-long", "x" * 1025)):
            bad_desc = one("bad-desc", "bad-desc", "---\nname: bad-desc\ndescription: " + json.dumps(value) + "\n---\n")
            dc, dr = run("build", bad_desc, f"--authority={AUTH}")
            case("description-refused-" + label, dc == 1 and has(dr, "description must be non-empty"))

        # Fallback parser, with PyYAML hidden: plain frontmatter reads the same, anything else stops.
        r6 = one("fb1", "fb-skill", "---\nname: fb-skill\ndescription: Formats invoices (PDF). Use when asked.\nlicense: Apache-2.0\nmetadata:\n  version: \"0.1.0\"\n  author: Someone\n---\n")
        c1, rep1, _ = raw_run("build", r6, f"--authority={AUTH}", hide_yaml=True)
        c2, rep2, _ = raw_run("build", r6, f"--authority={AUTH}")
        case("fallback-matches-pyyaml-on-plain-frontmatter", c1 == 0 and c2 == 0
             and rep1["manifest"]["skills"][0]["frontmatter"] == rep2["manifest"]["skills"][0]["frontmatter"])
        stops = ["version: 1.0", "enabled: yes", "tags:\n  - a", "description2: |\n  text", "note: a # b", "count: 010", "x: 'it''s'", "y: \"a\\x41\""]
        ok_all = True
        for extra_line in stops:
            r6 = one("fb2", "fb-stop", f"---\nname: fb-stop\ndescription: d. Use when asked.\n{extra_line}\n---\n")
            c, rp, er = raw_run("build", r6, f"--authority={AUTH}", hide_yaml=True)
            ok_all = ok_all and c == 1 and "Traceback" not in er and has(rp, "PyYAML")
        case("fallback-stops-instead-of-guessing", ok_all)

        strict = os.path.join(tmp, "strict")
        one("strict", "num-skill", "---\nname: num-skill\ndescription: d. Use when asked.\nlevel: 1.0\nflag: true\n---\n")
        sman = os.path.join(tmp, "strict.json")
        raw_run("build", strict, f"--authority={AUTH}", f"--out={sman}")
        sd = json.load(open(sman, encoding="utf-8"))
        sd["skills"][0]["frontmatter"]["level"] = 1
        sd["skills"][0]["frontmatter"]["flag"] = 1
        json.dump(sd, open(sman, "w", encoding="utf-8"))
        code, rep, err = raw_run("check", sman, f"--root={strict}", f"--authority={AUTH}")
        case("frontmatter-types-compared-strictly", code == 1 and has(rep, "frontmatter differs"))

    print(f"{sum(results)}/{len(results)} passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
