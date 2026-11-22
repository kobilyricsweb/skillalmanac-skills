"""Convert vCard (.vcf) contacts to a CSV file with one row per card.

Reads vCard 2.1, 3.0 and 4.0 text. Folded lines (continuation lines that start
with a space or tab) are unfolded, QUOTED-PRINTABLE values are decoded, and
escaped characters are restored. Several EMAIL, TEL, ADR or NOTE values on one
card are joined with "; ". ORG components are joined with " / ".

Usage:
    python -I vcf_to_csv.py <input-file> <output-file>

Exit codes:
    0  converted, no findings
    1  converted, findings reported (cards without a name, duplicate emails)
    2  usage, input or output error; one-line JSON error on stderr

The script reads the input only, creates the output with mode "x" (it never
overwrites), and uses no network, subprocess, eval or exec.
"""
import csv
import json
import os
import quopri
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
COLUMNS = ["name", "organization", "emails", "phones", "address", "note"]


class InputError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def unescape(text):
    """Undo vCard escapes and collapse whitespace runs to one space."""
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            nxt = text[i + 1]
            if nxt in "nN":
                out.append(" ")
            elif nxt in ",;\\":
                out.append(nxt)
            else:
                out.append(text[i:i + 2])
            i += 2
            continue
        out.append(ch)
        i += 1
    return " ".join("".join(out).split())


def split_structured(value):
    """Split a structured value (N, ORG, ADR) on unescaped semicolons."""
    parts = []
    current = []
    i = 0
    while i < len(value):
        ch = value[i]
        if ch == "\\" and i + 1 < len(value):
            current.append(value[i:i + 2])
            i += 2
            continue
        if ch == ";":
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
        i += 1
    parts.append("".join(current))
    return [unescape(part) for part in parts]


def is_quoted_printable(line):
    head = line.split(":", 1)[0] if ":" in line else line
    return "QUOTED-PRINTABLE" in head.upper()


def logical_lines(text):
    """Return unfolded logical lines, joining QUOTED-PRINTABLE soft breaks."""
    physical = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = []
    qp_flags = []
    for raw in physical:
        if raw == "":
            continue
        if raw[0] in " \t" and lines:
            lines[-1] += raw[1:]
            continue
        if lines and qp_flags[-1] and lines[-1].endswith("="):
            lines[-1] = lines[-1][:-1] + raw
            continue
        lines.append(raw)
        qp_flags.append(is_quoted_printable(raw))
    return lines


def split_property(line):
    """Return (PROPERTY, value) or None when the line has no colon."""
    if ":" not in line:
        return None
    head, value = line.split(":", 1)
    name = head.split(";")[0].split(".")[-1].strip().upper()
    if "QUOTED-PRINTABLE" in head.upper():
        raw = value.encode("utf-8")
        value = quopri.decodestring(raw).decode("utf-8", errors="replace")
    return name, value


def read_input(path):
    if not os.path.isfile(path):
        raise InputError("input_missing")
    try:
        with open(path, "rb") as fh:
            data = fh.read(MAX_INPUT_BYTES + 1)
    except OSError:
        raise InputError("io_error")
    if len(data) > MAX_INPUT_BYTES:
        raise InputError("input_too_large")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("invalid_utf8")


def parse_cards(text):
    """Return (list of cards, skipped line count). A card is a list of (PROP, value)."""
    cards = []
    current = None
    skipped = 0
    for line in logical_lines(text):
        upper = line.strip().upper()
        if upper == "BEGIN:VCARD":
            if current is not None:
                raise InputError("unterminated_card")
            current = []
            continue
        if upper == "END:VCARD":
            if current is not None:
                cards.append(current)
                current = None
            continue
        if current is None:
            continue
        prop = split_property(line)
        if prop is None:
            skipped += 1
            continue
        current.append(prop)
    if current is not None:
        raise InputError("unterminated_card")
    if not cards:
        raise InputError("no_cards")
    return cards, skipped


def build_row(props):
    """Return (CSV row, list of email strings) for one card."""
    fn_value = ""
    n_parts = []
    org_value = ""
    emails = []
    phones = []
    addresses = []
    notes = []
    for name, value in props:
        if name == "FN" and not fn_value:
            fn_value = unescape(value)
        elif name == "N" and not n_parts:
            n_parts = split_structured(value)
        elif name == "ORG" and not org_value:
            org_value = " / ".join(p for p in split_structured(value) if p)
        elif name == "EMAIL":
            email = unescape(value)
            if email and email not in emails:
                emails.append(email)
        elif name == "TEL":
            phone = unescape(value)
            if phone and phone not in phones:
                phones.append(phone)
        elif name == "ADR":
            address = ", ".join(p for p in split_structured(value) if p)
            if address and address not in addresses:
                addresses.append(address)
        elif name == "NOTE":
            note = unescape(value)
            if note and note not in notes:
                notes.append(note)
    if not fn_value and n_parts:
        n_parts = (n_parts + [""] * 5)[:5]
        family, given, additional, prefix, suffix = n_parts
        fn_value = " ".join(p for p in [prefix, given, additional, family, suffix] if p)
    row = [
        fn_value,
        org_value,
        "; ".join(emails),
        "; ".join(phones),
        "; ".join(addresses),
        "; ".join(notes),
    ]
    return row, emails


def analyze(cards):
    rows = []
    no_name = []
    email_cards = {}
    for index, props in enumerate(cards, start=1):
        row, emails = build_row(props)
        rows.append(row)
        if not row[0]:
            no_name.append(index)
        for email in emails:
            seen = email_cards.setdefault(email.lower(), [])
            if index not in seen:
                seen.append(index)
    dup_groups = [group for group in email_cards.values() if len(group) > 1]
    dup_groups.sort(key=lambda group: group[0])
    return rows, no_name, dup_groups


def check_output(input_path, output_path):
    if not output_path.lower().endswith(".csv"):
        raise InputError("output_not_csv")
    if os.path.normcase(os.path.abspath(output_path)) == os.path.normcase(os.path.abspath(input_path)):
        raise InputError("output_is_input")
    if not os.path.isdir(os.path.dirname(os.path.abspath(output_path))):
        raise InputError("output_dir_missing")
    if os.path.exists(output_path):
        raise InputError("output_exists")


def write_csv(path, rows):
    try:
        with open(path, "x", encoding="utf-8-sig", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(COLUMNS)
            writer.writerows(rows)
    except FileExistsError:
        raise InputError("output_exists")
    except OSError:
        raise InputError("io_error")


def main(argv):
    if len(argv) != 3:
        sys.stderr.write(json.dumps({"error": "usage"}) + "\n")
        return 2
    input_path, output_path = argv[1], argv[2]
    try:
        check_output(input_path, output_path)
        text = read_input(input_path)
        cards, skipped = parse_cards(text)
        rows, no_name, dup_groups = analyze(cards)
        write_csv(output_path, rows)
    except InputError as exc:
        sys.stderr.write(json.dumps({"error": exc.code}) + "\n")
        return 2
    findings = bool(no_name or dup_groups)
    summary = {
        "status": "findings" if findings else "ok",
        "cards": len(cards),
        "rows_written": len(rows),
        "cards_without_name": no_name,
        "duplicate_email_groups": len(dup_groups),
        "duplicate_card_groups": dup_groups,
        "skipped_lines": skipped,
    }
    sys.stdout.write(json.dumps(summary) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
