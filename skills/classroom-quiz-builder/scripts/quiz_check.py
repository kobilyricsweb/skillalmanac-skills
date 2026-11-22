#!/usr/bin/env python3
"""Check a multiple-choice quiz against the source material it was written from.

Standard library only. Reads the files it is given and prints to the screen; writes nothing.

    python quiz_check.py QUIZ --source SOURCE [--count N]
        Validate the quiz (format below) and trace every answer to the source.

    python quiz_check.py QUIZ --student
        Print the student copy: questions and options only, no answers.

Quiz format (Markdown), one block per question:

    ## Q1 [recall]
    Question text?
    A. option
    B. option
    C. option
    D. option
    Answer: B
    Source: "words copied exactly from the source that prove the answer"
    Why: one line on why the answer is right and the best wrong option is wrong

The tag is one of recall, understand, apply.
Exit codes: 0 = no FAIL, 1 = at least one FAIL, 2 = usage or file error.
The script proves that each quoted source line exists. It cannot prove that the
line really supports the answer; a teacher reads the key before using the quiz.
"""
import re
import sys

LEVELS = ("recall", "understand", "apply")
OPTION_COUNT = 4
MIN_SOURCE_WORDS = 4        # a shorter quote proves nothing
MAX_LETTER_SHARE = 0.4      # one letter holding more than this share of answers is guessable (needs 8+ questions)
MAX_RUN = 3                 # the same answer letter this many times in a row is a visible pattern
LONGEST_SHARE = 0.5         # the correct option being clearly the longest in more than this share gives the answer away
LONGEST_MARGIN = 1.25       # "clearly longest" = at least this many times the length of the next-longest option
MIN_HIGHER_SHARE = 0.3      # at least this share of questions should be understand/apply, not recall
BANNED_OPTIONS = ("all of the above", "none of the above", "both a and b", "a and b", "all of these", "none of these")


def utf8_output():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def read(path):
    try:
        raw = open(path, "rb").read()
    except OSError as err:
        print(f"ERROR: cannot read {path}: {err.strerror}. Check the path.")
        sys.exit(2)
    for enc in ("utf-8-sig", "cp1252"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if not text.strip():
        print(f"ERROR: {path} is empty.")
        sys.exit(2)
    return text.replace("\r\n", "\n")


def norm(text):
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"[*_`#>]", "", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def parse(quiz):
    title = ""
    blocks = re.split(r"^##\s+", quiz, flags=re.M)
    m = re.match(r"^#\s+(.+)$", blocks[0].strip(), re.M)
    if m:
        title = m.group(1).strip()
    questions = []
    for block in blocks[1:]:
        lines = block.split("\n")
        head = lines[0].strip()
        hm = re.match(r"^Q\s*(\d+)\s*(?:\[([^\]]*)\])?", head, re.I)
        if not hm:
            continue
        q = {"n": int(hm.group(1)), "level": (hm.group(2) or "").strip().lower(), "stem": [], "options": {}, "answer": None, "source": None, "why": None}
        for line in lines[1:]:
            s = line.strip()
            om = re.match(r"^([A-F])[.)]\s+(.*)$", s)
            if om:
                q["options"][om.group(1)] = om.group(2).strip()
            elif re.match(r"^answer\s*:", s, re.I):
                q["answer"] = s.split(":", 1)[1].strip().strip("*. ").upper()
            elif re.match(r"^source\s*:", s, re.I):
                q["source"] = s.split(":", 1)[1].strip()
            elif re.match(r"^why\s*:", s, re.I):
                q["why"] = s.split(":", 1)[1].strip()
            elif s and not q["options"]:
                q["stem"].append(s)
        q["stem"] = " ".join(q["stem"])
        questions.append(q)
    return title, questions


def student_copy(title, questions):
    print(f"# {title or 'Quiz'}\n\nName: ____________________   Date: ____________\n")
    for q in questions:
        print(f"**{q['n']}.** {q['stem']}\n")
        for letter in sorted(q["options"]):
            print(f"   {letter}. {q['options'][letter]}")
        print()
    return 0


def main(argv):
    utf8_output()
    opts = {"--source": None, "--count": None}
    student, args, i = False, [], 0
    while i < len(argv):
        if argv[i] in opts and i + 1 < len(argv):
            opts[argv[i]] = argv[i + 1]
            i += 2
        elif argv[i] == "--student":
            student = True
            i += 1
        else:
            args.append(argv[i])
            i += 1
    if len(args) != 1 or (not student and not opts["--source"]):
        print(__doc__)
        return 2
    title, questions = parse(read(args[0]))
    if not questions:
        print("ERROR: no question blocks found. Each question must start with a line like '## Q1 [recall]'.")
        return 2
    if student:
        return student_copy(title, questions)
    source = norm(read(opts["--source"]))
    fails, warns = [], []

    if opts["--count"] and opts["--count"].isdigit() and len(questions) != int(opts["--count"]):
        fails.append(f"{len(questions)} questions found, {opts['--count']} were requested")
    if [q["n"] for q in questions] != list(range(1, len(questions) + 1)):
        warns.append("question numbers are not 1, 2, 3 ... in order")
    stems = {}
    for q in questions:
        tag = f"Q{q['n']}"
        if not q["stem"]:
            fails.append(f"{tag}: no question text")
        if len(q["options"]) != OPTION_COUNT or sorted(q["options"]) != ["A", "B", "C", "D"]:
            fails.append(f"{tag}: needs exactly four options lettered A to D (found {''.join(sorted(q['options'])) or 'none'})")
        if q["answer"] not in q["options"]:
            fails.append(f"{tag}: 'Answer:' must be one letter that matches an option (found '{q['answer']}')")
        texts = [norm(t) for t in q["options"].values()]
        if len(set(texts)) < len(texts):
            fails.append(f"{tag}: two options are the same")
        for t in texts:
            if t.rstrip(".") in BANNED_OPTIONS:
                fails.append(f"{tag}: option '{t}' tests reading the options, not the material; write a real alternative")
        if q["level"] not in LEVELS:
            fails.append(f"{tag}: level tag must be one of {', '.join(LEVELS)} (found '{q['level']}')")
        if not q["source"]:
            fails.append(f"{tag}: no 'Source:' line")
        else:
            quotes = re.findall(r'"([^"]+)"', q["source"].replace("“", '"').replace("”", '"')) or [q["source"]]
            for quote in quotes:
                nq = norm(quote).strip(" .")
                parts = [p.strip(" .") for p in re.split(r"\s*(?:\.\.\.|…)\s*", nq) if p.strip(" .")]
                if len(nq.split()) < MIN_SOURCE_WORDS:
                    fails.append(f"{tag}: source quote is under {MIN_SOURCE_WORDS} words")
                elif not all(p in source for p in parts):
                    fails.append(f"{tag}: source quote is not in the material word for word: \"{quote[:60]}\"")
        if not q["why"]:
            warns.append(f"{tag}: no 'Why:' line for the answer key")
        if re.search(r"\b(not|except|never|least)\b", q["stem"], re.I) and not re.search(r"\b(NOT|EXCEPT|NEVER|LEAST)\b", q["stem"]):
            warns.append(f"{tag}: negative wording in the question; put NOT / EXCEPT in capitals or rephrase positively")
        key = norm(q["stem"])
        if key in stems:
            fails.append(f"{tag}: same question as Q{stems[key]}")
        stems[key] = q["n"]

    keyed = [q for q in questions if q["answer"] in q["options"]]
    letters = [q["answer"] for q in keyed]
    if len(letters) >= 8:
        for letter in "ABCD":
            share = letters.count(letter) / len(letters)
            if share > MAX_LETTER_SHARE:
                fails.append(f"answer {letter} is correct in {letters.count(letter)} of {len(letters)} questions; spread the correct answers across A to D")
        unused = [l for l in "ABCD" if l not in letters]
        if unused:
            warns.append("never the correct answer: " + ", ".join(unused))
    run, longest_run = 1, 1
    for a, b in zip(letters, letters[1:]):
        run = run + 1 if a == b else 1
        longest_run = max(longest_run, run)
    if longest_run >= MAX_RUN:
        warns.append(f"the same answer letter appears {longest_run} times in a row")
    if len(keyed) >= 4:
        longest = 0
        for q in keyed:
            others = [len(t) for letter, t in q["options"].items() if letter != q["answer"]]
            if others and len(q["options"][q["answer"]]) >= LONGEST_MARGIN * max(others):
                longest += 1
        if longest / len(keyed) > LONGEST_SHARE:
            fails.append(f"the correct option is clearly the longest one in {longest} of {len(keyed)} questions; even out option lengths")
    higher = sum(1 for q in questions if q["level"] in ("understand", "apply"))
    if len(questions) >= 5 and higher / len(questions) < MIN_HIGHER_SHARE:
        warns.append(f"only {higher} of {len(questions)} questions go beyond recall")

    print("QUIZ CHECK")
    print(f"  {len(questions)} questions; answer letters: " + " ".join(f"{l}={letters.count(l)}" for l in "ABCD")
          + "; levels: " + " ".join(f"{lv}={sum(1 for q in questions if q['level'] == lv)}" for lv in LEVELS))
    for f in fails:
        print("  FAIL  " + f)
    for w in warns:
        print("  WARN  " + w)
    if not fails:
        print("  OK    format valid; every answer cites a line that exists in the material")
    print(f"\nRESULT: {'FAIL' if fails else 'PASS'} ({len(fails)} fail, {len(warns)} warn)")
    print("Not checked: that each quoted line really proves the answer, and that wrong options are clearly wrong. Read the key once before use.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
