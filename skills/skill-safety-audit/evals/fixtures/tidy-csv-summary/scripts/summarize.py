#!/usr/bin/env python3
"""Print row count and empty counts for a CSV. Reads the given file; writes nothing."""
import argparse
import csv
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    with open(args.path, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    empty = {}
    for row in rows:
        for key, value in row.items():
            if not value:
                empty[key] = empty.get(key, 0) + 1
    print(json.dumps({"rows": len(rows), "empty": empty}))


if __name__ == "__main__":
    main()
