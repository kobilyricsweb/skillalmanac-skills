#!/usr/bin/env python3
"""Create the empty placeholder asset files the programmatic-video tasks refer to.

    python evals/make_assets.py PROJECT_DIR TASK

TASK is t1, t2 or t3. Files are written under PROJECT_DIR/assets/. They are empty
on purpose: timeline_check.py only tests that each path exists; the metadata
(fps, size, duration, license) lives in the timeline itself. t2 deliberately omits
scene-b.mp4 (the prompt says it is still being exported). Standard library only.
"""
import os
import sys

TASKS = {
    "t1": ["title-card.png", "chart-anim.mp4", "outro-card.png", "bed-loop.mp3"],
    "t2": ["scene-a.mp4", "Summer Vibes.mp3"],
    "t3": ["demo.mp4", "chart-hit.mp3"],
}


def main(argv):
    if len(argv) != 2 or argv[1] not in TASKS:
        sys.stderr.write("usage: make_assets.py PROJECT_DIR {t1|t2|t3}\n")
        return 2
    folder = os.path.join(argv[0], "assets")
    os.makedirs(folder, exist_ok=True)
    for name in TASKS[argv[1]]:
        open(os.path.join(folder, name), "wb").close()
    print("wrote %d placeholder files to %s" % (len(TASKS[argv[1]]), folder))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
