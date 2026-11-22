#!/usr/bin/env python3
"""Check a drafted customer-support reply against the ticket and the policy text.

Standard library only. Reads three files, prints a report, writes nothing.

    python reply_check.py DRAFT --ticket TICKET --policy POLICY

DRAFT is Markdown with two headings: "## Reply" (what the customer will read)
and "## Internal note" (for the agent who sends it). The script checks the
Reply part for:
  - commitments that nothing backs: any number (amount, percent, days, hours)
    that is in neither the policy nor the ticket;
  - promise words the policy does not use (guarantee, definitely, immediately ...);
  - unfilled placeholders, internal wording, repeated apologies, blaming phrases;
and prints the customer's questions as a checklist to confirm by eye.
It checks the Internal note for the lines "Policy used:" and "Needs a human:".

Exit codes: 0 = no FAIL, 1 = at least one FAIL, 2 = usage or file error.
The script cannot tell whether the reply applies the policy correctly; a
person approves every reply before it is sent.
"""
import re
import sys

# Words that commit the company beyond what a front-line reply can know.
PROMISE_WORDS = ("guarantee", "guaranteed", "promise", "definitely", "certainly will", "without fail", "immediately",
                 "right away", "instantly", "always", "never again", "100%", "no matter what", "rest assured")
BLAME_PHRASES = ("you should have", "you failed", "you neglected", "as stated", "as we said", "as previously mentioned",
                 "you must understand", "obviously", "clearly you", "per our policy", "your mistake", "your fault")
INTERNAL_WORDS = ("internal note", "macro", "tier 2", "tier-2", "sla", "kb article", "ticket queue", "policy section")
MAX_APOLOGIES = 1       # one sincere apology; more reads as a script
MAX_REPLY_WORDS = 220   # longer replies bury the answer
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


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


def numbers(text):
    out = set()
    for m in NUM.findall(text):
        n = m.replace(",", "").rstrip(".")
        if "." in n:
            n = n.rstrip("0").rstrip(".")
        out.add(n)
    return out


def section(text, name):
    m = re.search(rf"^#{{1,4}}\s*{name}\b.*$", text, re.I | re.M)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(r"^#{1,4}\s", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def customer_name(ticket):
    m = re.search(r"^(?:from|name|customer)\s*:\s*([A-Z][\w'-]+)", ticket, re.I | re.M)
    if m:
        return m.group(1)
    tail = [l.strip() for l in ticket.strip().split("\n") if l.strip()][-1]
    m = re.fullmatch(r"[-–— ]*([A-Z][a-z'-]+)(?: [A-Z][\w'.-]+)?", tail)
    return m.group(1) if m else None


def main(argv):
    utf8_output()
    opts = {"--ticket": None, "--policy": None}
    args, i = [], 0
    while i < len(argv):
        if argv[i] in opts and i + 1 < len(argv):
            opts[argv[i]] = argv[i + 1]
            i += 2
        else:
            args.append(argv[i])
            i += 1
    if len(args) != 1 or not opts["--ticket"] or not opts["--policy"]:
        print(__doc__)
        return 2
    draft, ticket, policy = read(args[0]), read(opts["--ticket"]), read(opts["--policy"])
    fails, warns = [], []

    reply = section(draft, "reply")
    note = section(draft, "internal note")
    if reply is None:
        fails.append("no '## Reply' heading; put the customer-facing text under it")
        reply = draft
    if note is None:
        fails.append("no '## Internal note' heading")
    else:
        for label in ("policy used:", "needs a human:"):
            if label not in note.lower():
                fails.append(f"Internal note lacks the line '{label.capitalize()}'")
    low = reply.lower()

    backed = numbers(policy) | numbers(ticket)
    prose = re.sub(r"(?m)^\s*\d{1,2}[.)]\s", "", reply)      # numbered steps are not commitments
    for n in sorted(numbers(prose) - backed, key=lambda s: (len(s), s)):
        ctx = re.search(rf"[^.\n]{{0,40}}(?<![\d.,]){re.escape(n)}(?![\d])[^.\n]{{0,30}}", prose.replace(",", ""))
        fails.append(f"UNBACKED NUMBER '{n}' is in neither the policy nor the ticket" + (f": \"...{ctx.group(0).strip()}...\"" if ctx else ""))
    pol_low = policy.lower()
    for w in PROMISE_WORDS:
        if re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", low) and w not in pol_low:
            fails.append(f"PROMISE WORD '{w}': the policy does not use it; say what will happen and when, as the policy states it")
    for pat, what in ((r"\[[^\]\n]{1,40}\]", "square-bracket placeholder"), (r"\{\{[^}\n]*\}\}", "template placeholder"),
                      (r"<[a-z_ ]{2,30}>", "angle-bracket placeholder"), (r"\b(XXX+|TBD|TODO)\b", "unfinished marker")):
        m = re.search(pat, reply)
        if m:
            fails.append(f"{what} left in the reply: '{m.group(0)}'")
    for w in INTERNAL_WORDS:
        if w in low:
            warns.append(f"internal wording '{w}' in the customer-facing text")
    for p in BLAME_PHRASES:
        if p in low:
            warns.append(f"blaming or lecturing phrase '{p}'")
    apologies = len(re.findall(r"\b(sorry|apologi[sz]e|apologies)\b", low))
    if apologies > MAX_APOLOGIES:
        warns.append(f"{apologies} apologies; one is enough")
    n_words = len(re.findall(r"\w+", reply))
    if n_words > MAX_REPLY_WORDS:
        warns.append(f"reply is {n_words} words; aim for under {MAX_REPLY_WORDS}")
    if n_words < 15:
        fails.append("reply is under 15 words; it cannot answer the ticket")
    name = customer_name(ticket)
    if name and name.lower() not in low:
        warns.append(f"the customer's name '{name}' is not used in the reply")
    if re.search(r"\b[A-Z]{5,}\b", reply):
        warns.append("word in capital letters in the reply")
    if not re.search(r"\b(will|next|by|within|once|after|when|please|you can|reply to)\b", low):
        warns.append("no next step found; say what happens next and who does it")

    questions = [q.strip() for q in re.findall(r"[^.!?\n]*\?", ticket) if len(q.split()) >= 3]
    print("SUPPORT REPLY CHECK")
    for f in fails:
        print("  FAIL  " + f)
    for w in warns:
        print("  WARN  " + w)
    if not fails:
        print("  OK    no unbacked numbers, promise words or placeholders; internal note complete")
    if questions:
        print("\n  Questions in the ticket - confirm by eye that the reply answers each one:")
        for q in questions:
            print("   [ ] " + q)
    print(f"\nRESULT: {'FAIL' if fails else 'PASS'} ({len(fails)} fail, {len(warns)} warn)")
    print("Not checked: whether the policy was applied correctly. A person approves the reply before sending.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
