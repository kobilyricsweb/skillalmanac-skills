import re

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_ROWS = 5000


class Result:
    def __init__(self):
        self.error = None
        self.created = 0
        self.updated = 0
        self.skipped_rows = []


CONTACTS = {}


def import_csv(text):
    result = Result()
    lines = text.strip().splitlines()
    header = lines[0].split(",")
    if "email" not in header:
        result.error = "missing email column"
        return result
    rows = lines[1:]
    if len(rows) > MAX_ROWS:
        result.error = "too many rows"
        return result
    idx = header.index("email")
    for n, line in enumerate(rows, 1):
        cells = line.split(",")
        email = cells[idx].strip() if idx < len(cells) else ""
        if not EMAIL.match(email):
            result.skipped_rows.append(n)
            continue
        key = email.lower()
        if key in CONTACTS:
            result.updated += 1
        else:
            result.created += 1
        CONTACTS[key] = {"email": email}
    return result
