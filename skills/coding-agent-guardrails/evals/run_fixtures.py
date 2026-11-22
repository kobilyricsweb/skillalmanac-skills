#!/usr/bin/env python3
"""Run guardrail_audit on each fixture and compare with evals/expected/<name>.json.

    python evals/run_fixtures.py

Prints one PASS/FAIL line per fixture and a final line. Exit 0 only when every
fixture matches exactly and the exit-code rule holds (bad fails, good and
minimal do not). Reads fixtures and expected files; writes nothing.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import guardrail_audit  # noqa: E402

# fixture -> whether the audit should report at least one fail
EXPECT_FAIL = {"bad": True, "good": False, "minimal": True, "leaky": True}


def main():
    bad = 0
    for name, should_fail in EXPECT_FAIL.items():
        got = guardrail_audit.audit(os.path.join(HERE, "fixtures", name))
        with open(os.path.join(HERE, "expected", name + ".json"), encoding="utf-8") as fh:
            want = json.load(fh)
        has_fail = got["summary"]["fail"] > 0
        ok = got == want and has_fail == should_fail
        print(("PASS " if ok else "FAIL ") + name + " (fail count %d)" % got["summary"]["fail"])
        bad += 0 if ok else 1
    print("fixtures ok" if not bad else "%d fixture(s) failed" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
