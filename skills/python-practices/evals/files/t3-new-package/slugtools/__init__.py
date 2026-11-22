import re

from unidecode import unidecode


def slugify(text, max_len=60):
    text = unidecode(text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:max_len].rstrip("-")
