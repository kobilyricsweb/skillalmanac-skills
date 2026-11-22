"""Fixture: a script. print and a main guard are expected here."""
import sys


def main(argv):
    print("args:", len(argv))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
