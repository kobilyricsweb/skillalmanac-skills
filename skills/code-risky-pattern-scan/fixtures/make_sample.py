"""make_sample: writes the smoke-test code folder from the text sources in fixtures/.

Copies every fixtures/sample-source/**/*.txt file into a new folder with the
trailing ".txt" removed. The planted patterns therefore live on disk as text and
become code files only when this helper runs. The target folder must not exist;
files are created with exclusive-create mode and nothing is overwritten.

Usage:
    python -I fixtures/make_sample.py <new-folder>

Exit codes:
    0  folder written (JSON list of written paths on stdout)
    2  usage or input error (one-line JSON error on stderr)
"""

import json
import os
import sys


PLACEHOLDER = "@@FAKE_AWS_KEY@@"
# Assembled at run time so the stored fixture never contains a key-shaped string.
FAKE_AWS_KEY = "AKIA" + "FAKE" * 4


def fail(message):
    sys.stderr.write(json.dumps({"error": message}) + "\n")
    sys.exit(2)


def main(argv):
    if len(argv) != 2:
        fail("usage: python -I fixtures/make_sample.py <new-folder>")
    target = argv[1]
    if os.path.exists(target):
        fail("target already exists")
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "sample-source")
    if not os.path.isdir(source):
        fail("fixture source folder is missing")

    written = []
    for dirpath, _dirnames, filenames in os.walk(source):
        for name in sorted(filenames):
            if not name.endswith(".txt"):
                continue
            src = os.path.join(dirpath, name)
            rel = os.path.relpath(src, source)[:-4]
            dst = os.path.join(target, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(src, "rb") as reader:
                text = reader.read().decode("utf-8")
            text = text.replace(PLACEHOLDER, FAKE_AWS_KEY)
            with open(dst, "xb") as writer:
                writer.write(text.encode("utf-8"))
            written.append(rel.replace(os.sep, "/"))

    sys.stdout.write(json.dumps({"written": sorted(written)}) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
