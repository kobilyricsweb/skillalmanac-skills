import sys

from slugtools import slugify


def main():
    print(slugify(" ".join(sys.argv[1:])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
