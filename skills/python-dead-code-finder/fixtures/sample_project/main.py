"""Entry point: prints a greeting."""
from models import Greeter
from utils import format_name


def main():
    print(Greeter().message(format_name("world")))


if __name__ == "__main__":
    main()
