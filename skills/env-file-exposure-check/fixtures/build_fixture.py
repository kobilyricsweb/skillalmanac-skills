"""Build a throwaway smoke-test folder for scripts/env_exposure.py.

Usage:
    python -I fixtures/build_fixture.py [TARGET_DIR]

Writes three files: a .env holding a fake AWS-shaped key (assembled at run
time, so no secret-shaped literal is stored in the package), a .gitignore
that does not list .env, and a clean text file. With no TARGET_DIR a new
folder is created under the system temp directory. The folder path is
printed on stdout. Exit 0 ok, 2 if TARGET_DIR exists and is not empty.
"""
import os
import sys
import tempfile


def main(argv):
    if len(argv) > 2:
        sys.stderr.write('{"error": "usage: build_fixture.py [TARGET_DIR]"}\n')
        return 2
    if len(argv) == 2:
        target = argv[1]
        if os.path.exists(target) and (not os.path.isdir(target) or os.listdir(target)):
            sys.stderr.write('{"error": "target must be a new or empty directory"}\n')
            return 2
        os.makedirs(target, exist_ok=True)
    else:
        target = tempfile.mkdtemp(prefix="env_exposure_smoke_")
    fake_key = "AKI" + "A" + "Q7RZ3PLM" + "2XKD9VBN"
    files = {
        ".env": "APP_NAME=demo\nAWS_ACCESS_KEY_ID=" + fake_key + "\n",
        ".gitignore": "node_modules/\n*.log\n",
        "clean.txt": "Project notes. Nothing secret here.\n",
    }
    for name, body in files.items():
        with open(os.path.join(target, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
