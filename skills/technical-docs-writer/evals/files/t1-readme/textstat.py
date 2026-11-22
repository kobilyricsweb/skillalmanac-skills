"""textstat: count words, lines and characters in a text file.

Usage: python textstat.py FILE [--json]
Exit 0 on success, 2 if FILE cannot be read.
"""
import json
import sys


def main(argv):
    if not argv or argv[0].startswith("-"):
        print("usage: textstat.py FILE [--json]", file=sys.stderr)
        return 2
    try:
        text = open(argv[0], encoding="utf-8").read()
    except OSError as exc:
        print("cannot read %s: %s" % (argv[0], exc.strerror), file=sys.stderr)
        return 2
    stats = {"words": len(text.split()), "lines": len(text.splitlines()), "chars": len(text)}
    if "--json" in argv[1:]:
        print(json.dumps(stats))
    else:
        print("words: %(words)d  lines: %(lines)d  chars: %(chars)d" % stats)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
