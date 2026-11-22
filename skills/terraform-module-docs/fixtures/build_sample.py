#!/usr/bin/env python3
"""Build the smoke-test Terraform module from the text fixtures in this folder.

Usage:
    python -I fixtures/build_sample.py <new-dir>

Creates <new-dir>, which must not exist, and writes variables.tf, main.tf and
outputs.tf into it. The contents are copied from the matching .txt files in
fixtures/sample_module/. The fixtures stay .txt on disk so the package holds
text files only.

Exit codes: 0 = module written; 2 = usage or input error (one-line JSON on stdout).
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "sample_module")
NAMES = ("variables", "main", "outputs")


def fail(message):
    sys.stdout.write(json.dumps({"status": "error", "error": message}) + "\n")
    sys.exit(2)


def main(argv):
    if len(argv) != 2:
        fail("usage: build_sample.py <new-dir>")
    target = argv[1]
    if os.path.lexists(target):
        fail("target already exists")
    if not os.path.isdir(os.path.dirname(os.path.abspath(target))):
        fail("parent directory not found")
    contents = {}
    for base in NAMES:
        try:
            with open(os.path.join(SOURCE, base + ".txt"), "rb") as fh:
                contents[base] = fh.read()
        except OSError:
            fail("fixture missing: " + base + ".txt")
    try:
        os.mkdir(target)
        for base in NAMES:
            with open(os.path.join(target, base + ".tf"), "xb") as fh:
                fh.write(contents[base])
    except OSError:
        fail("cannot write target directory")
    sys.stdout.write(json.dumps({"status": "ok", "files": len(NAMES)}) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
