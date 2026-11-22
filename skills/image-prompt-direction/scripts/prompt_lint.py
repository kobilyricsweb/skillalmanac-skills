#!/usr/bin/env python3
"""Lint an image-generation prompt file against the eight-field prompt contract.

Usage:
    python prompt_lint.py lint <prompt-file> [--allow TERM ...]
    python prompt_lint.py diff <old-prompt-file> <new-prompt-file>

lint  Reads one prompt (labelled fields such as "Subject: ..." or free prose).
      Prints one JSON object: fields found, completeness score (0-100),
      findings (missing fields, rights hits, contradictions, aspect ratio
      problems, filler tokens) and a verdict: pass, revise or blocked.
      --allow TERM skips a rights hit whose matched text equals TERM
      (use only for a brand or person the user owns or has written rights to).
diff  Compares the labelled fields of two prompt files and reports which
      fields changed. ok is true when at most one field changed (the
      one-variable-per-iteration rule).

Reads only the files named on the command line. Writes nothing except the
JSON report on stdout. No network.
Exit codes: lint 0 = pass, 1 = revise or blocked; diff 0 = at most one field
changed, 1 = more than one; 2 = usage error, missing, empty or unreadable file,
or (diff) a file with no labelled fields.
"""
import json
import re
import sys

# ---------------------------------------------------------------- contract
# Fields and weights. Weights are working values: subject and lighting carry
# the most because a prompt without them leaves the generator to guess the
# two things viewers notice first.
FIELDS = ["subject", "composition", "camera", "lighting", "palette", "style", "negative", "aspect_ratio"]
WEIGHTS = {"subject": 20, "composition": 15, "camera": 10, "lighting": 15,
           "palette": 10, "style": 15, "negative": 5, "aspect_ratio": 10}
REQUIRED = ["subject", "composition", "lighting", "style", "aspect_ratio"]
PASS_SCORE = 70  # a prompt at or above this with no errors is a pass

LABELS = {
    "subject": "subject", "composition": "composition", "framing": "composition", "layout": "composition",
    "camera": "camera", "lens": "camera", "camera/lens": "camera", "lens/camera": "camera",
    "camera and lens": "camera", "lighting": "lighting", "light": "lighting",
    "palette": "palette", "color": "palette", "colour": "palette", "colors": "palette",
    "colours": "palette", "color palette": "palette", "colour palette": "palette",
    "style": "style", "medium": "style", "style/medium": "style", "style and medium": "style",
    "negative": "negative", "negatives": "negative", "negative prompt": "negative",
    "negative constraints": "negative", "avoid": "negative", "exclude": "negative",
    "aspect ratio": "aspect_ratio", "aspect": "aspect_ratio", "ratio": "aspect_ratio", "size": "aspect_ratio",
}

# Keyword vocabularies used when a field has no label. Matching is
# case-insensitive on whole words.
VOCAB = {
    "composition": ["close-up", "closeup", "extreme close-up", "wide shot", "medium shot", "long shot", "full-body",
                    "headshot", "rule of thirds", "centered", "centred", "symmetrical", "low angle", "high angle",
                    "bird's-eye", "birds-eye", "overhead", "top-down", "over-the-shoulder", "eye level", "eye-level",
                    "foreground", "background", "negative space", "leading lines", "diagonal", "panoramic",
                    "establishing shot", "framing", "composition", "three-quarter view", "profile view"],
    "camera": ["mm", "aperture", "depth of field", "bokeh", "wide-angle", "ultra-wide", "telephoto", "macro",
               "fisheye", "tilt-shift", "dslr", "mirrorless", "medium format", "long exposure", "shutter", "iso",
               "35mm film", "anamorphic", "prime lens", "lens", "camera"],
    "lighting": ["golden hour", "blue hour", "overcast", "backlit", "backlight", "rim light", "rim lighting",
                 "softbox", "studio lighting", "window light", "candlelight", "neon", "hard light", "soft light",
                 "diffused", "chiaroscuro", "dappled", "moonlight", "moonlit", "sunlight", "volumetric", "low-key",
                 "high-key", "lighting", "lit", "noon", "sunset", "sunrise", "daylight", "twilight", "firelight"],
    "palette": ["palette", "muted", "pastel", "monochrome", "monochromatic", "teal and orange", "earth tones",
                "warm tones", "cool tones", "desaturated", "saturated", "complementary", "analogous", "colour scheme",
                "color scheme", "tones", "black and white"],
    "style": ["illustration", "photograph", "photography", "photorealistic", "watercolor", "watercolour",
              "oil painting", "3d render", "vector", "flat design", "line art", "cinematic", "editorial",
              "documentary", "risograph", "linocut", "gouache", "ink drawing", "pixel art", "collage", "claymation",
              "art deco", "bauhaus", "ukiyo-e", "woodblock", "screen print", "screenprint", "charcoal", "pencil",
              "isometric", "low-poly", "film still", "style", "medium"],
}

# ------------------------------------------------------------ rights lists
# Documented in references/rights-lists.md. These are illustrative, not
# exhaustive: a miss means "not on the list", never "cleared".
LIVING_ARTISTS = [
    "Greg Rutkowski", "Loish", "Artgerm", "Beeple", "Banksy", "Takashi Murakami", "Yayoi Kusama",
    "Hayao Miyazaki", "Makoto Shinkai", "Wes Anderson", "Tim Burton", "Annie Leibovitz", "Alex Ross",
    "Kehinde Wiley", "David Hockney", "Jeff Koons", "Ai Weiwei", "Sam Yang", "Simon Stalenhag",
    "James Jean", "Hiroshi Nagai", "Junji Ito", "Gerhard Richter", "Damien Hirst", "Roger Deakins",
    "Steve McCurry", "Rebecca Louise Law", "Craig Mullins", "Tomer Hanuka",
]
# Note: Kim Jung Gi (died 2022) is not in the list above, which holds living artists
# only. A deceased artist's name is still caught as "possible-artist-name" after
# "in the style of", and estates can hold rights; see references/rights-lists.md.
REAL_PEOPLE = [
    "Taylor Swift", "Elon Musk", "Donald Trump", "Barack Obama", "Joe Biden", "Beyonce", "Beyoncé", "Zendaya",
    "Tom Cruise", "Emma Watson", "Keanu Reeves", "Kim Kardashian", "Lionel Messi", "Cristiano Ronaldo",
    "Scarlett Johansson", "Margot Robbie", "Ryan Gosling", "Rihanna", "Drake", "Kanye West", "Jeff Bezos",
    "Mark Zuckerberg", "Vladimir Putin", "Emmanuel Macron", "Greta Thunberg", "Oprah Winfrey", "Dwayne Johnson",
    "Billie Eilish", "Timothee Chalamet", "Timothée Chalamet", "Tom Hanks", "Brad Pitt", "Angelina Jolie",
]
TRADEMARKS = [
    "Disney", "Pixar", "Marvel", "DC Comics", "Pokemon", "Pokémon", "Nintendo", "Mickey Mouse", "Star Wars",
    "Harry Potter", "Hogwarts", "Nike", "Adidas", "Coca-Cola", "Coca Cola", "Pepsi", "Lego", "Barbie",
    "Hello Kitty", "Batman", "Spider-Man", "Spiderman", "Superman", "Iron Man", "Super Mario", "Pikachu",
    "Studio Ghibli", "Gucci", "Louis Vuitton", "Rolex", "Ferrari", "Lamborghini", "Tesla", "Netflix",
    "McDonald's", "Starbucks", "Apple logo", "iPhone", "Playstation", "PlayStation", "Xbox", "Minecraft",
    "Fortnite", "Hermes", "Hermès", "Chanel", "Prada", "Red Bull", "Lord of the Rings", "Game of Thrones",
    "Simpsons", "SpongeBob", "Shrek", "Frozen", "Hulk", "Darth Vader", "Yoda", "Mandalorian", "Sonic the Hedgehog",
]
# Phrases that name a person's likeness whatever the name is.
LIKENESS_PATTERNS = [
    (r"(?i:\b(?:deepfake|face[- ]?swap(?:ped)?)\b)", "rights-likeness", "asks for a face swap or deepfake"),
    (r"(?i:\b(?:looks?\s+like|resembl(?:es|ing)|likeness\s+of|spitting\s+image\s+of|look-?alike\s+of)\s+(?:the\s+)?)"
     r"(?:(?i:actor|actress|singer|president|prime\s+minister|celebrity|politician|footballer)|[A-Z][a-z]+\s+[A-Z][a-z]+)",
     "rights-likeness", "asks for a real person's likeness"),
    (r"(?i:\b(?:celebrity|famous\s+(?:actor|actress|singer|politician|footballer|athlete))\b)", "rights-likeness",
     "names a celebrity category instead of an invented character"),
]
ROLE_PATTERN = r"\b(?:President|Prime\s+Minister|Chancellor|Pope|Queen|King)\s+[A-Z][a-z]+"
# "in the style of X" style hooks. X is then checked against the lists and
# against SAFE_STYLE_WORDS (movements and places, not people).
STYLE_HOOK = (r"(?i:\b(?:in\s+the\s+style\s+of|style\s+of|inspired\s+by|reminiscent\s+of|painted\s+by|"
              r"photographed\s+by|illustrated\s+by|drawn\s+by|shot\s+by|directed\s+by|art\s+by|artwork\s+by|"
              r"à\s+la))\s+([A-Z][\w'’.-]*(?:\s+(?:de|van|von|da|di|del|le|la)?\s*[A-Z][\w'’.-]*){0,2})")
SAFE_STYLE_WORDS = {w.lower() for w in [
    "Art", "Bauhaus", "Impressionism", "Impressionist", "Baroque", "Renaissance", "Brutalist", "Memphis", "Ukiyo-e",
    "Pop", "Cubism", "Cubist", "Surrealism", "Surrealist", "Romanticism", "Gothic", "Victorian", "Edwardian",
    "Japanese", "French", "Scandinavian", "Mid-Century", "Midcentury", "Soviet", "Chinese", "Italian", "Dutch",
    "German", "American", "British", "Indian", "Persian", "Byzantine", "Rococo", "Modernist", "Minimalist",
    "Expressionism", "Expressionist", "Constructivism", "Futurism", "Dadaism", "Fauvism", "Nordic", "African",
    "Mexican", "Polish", "Swiss", "Neoclassical", "Arts", "Vintage", "Retro", "Classic", "Golden", "Silver",
    "The", "A", "An", "Old", "Early", "Late", "Medieval", "Tudor", "Georgian", "Edo", "Meiji", "Showa", "Hollywood",
    "National",
]}
BRAND_MARK_PATTERN = r"\b(?:logo|logos|trademark|brand\s+name|branded)\b"

# ----------------------------------------------------------- contradictions
# Each rule: (label, list of terms or regexes for side A, same for side B).
# A rule fires only when both sides match in the positive text (text outside
# the negative field and outside "no ...", "without ..." clauses).
CONTRADICTIONS = [
    ("sun position vs flat light", [r"golden\s+hour", r"sunset", r"sunrise", r"magic\s+hour"],
     [r"overcast", r"mid-?day", r"high\s+noon", r"\bnoon\b", r"blue\s+hour", r"grey\s+sky", r"gray\s+sky"]),
    ("day vs night", [r"golden\s+hour", r"daylight", r"sunny", r"mid-?day", r"bright\s+sun", r"blue\s+sky"],
     [r"\bnight(?:time)?\b", r"midnight", r"moonlit", r"starry\s+sky"]),
    ("photographic vs drawn or painted", [r"photorealistic", r"hyper-?realistic", r"photograph\b", r"photo\s+of", r"\bdslr\b",
                                          r"documentary\s+photo"],
     [r"watercolou?r", r"cartoon", r"flat\s+vector", r"vector\s+illustration", r"pixel\s+art", r"oil\s+painting",
      r"line\s+art", r"\banime\b", r"claymation", r"low-?poly", r"gouache", r"linocut"]),
    ("macro vs wide framing", [r"\bmacro\b", r"extreme\s+close-?up"],
     [r"aerial", r"drone\s+view", r"establishing\s+shot", r"wide\s+shot", r"panoramic", r"bird'?s-?eye"]),
    ("wide lens vs long lens", [r"wide-?angle", r"ultra-?wide", r"fisheye", r"\b(?:[89]|1[0-9]|2[0-8])\s?mm\b(?!\s?film)"],
     [r"telephoto", r"\b(?:1[3-9][0-9]|[2-7][0-9]{2}|800)\s?mm\b(?!\s?film)"]),
    ("shallow vs deep focus", [r"shallow\s+depth", r"bokeh", r"\bf/(?:1(?:\.\d)?|2(?:\.[08])?)\b"],
     [r"deep\s+focus", r"everything\s+in\s+focus", r"pan-?focus", r"\bf/(?:11|16|22|32)\b"]),
    ("long exposure vs frozen motion", [r"long\s+exposure", r"motion\s+blur", r"light\s+trails"],
     [r"frozen", r"freeze-?frame", r"high-?speed", r"1/(?:500|1000|2000|4000)"]),
    ("black and white vs colour", [r"black\s+and\s+white", r"b&w", r"grayscale", r"greyscale", r"monochrome\b"],
     [r"colou?rful", r"vibrant", r"saturated", r"rainbow", r"teal\s+and\s+orange", r"\bneon\b"]),
    ("minimal vs crowded", [r"minimali(?:st|stic)", r"\bsparse\b", r"empty\s+space"],
     [r"cluttered", r"maximali(?:st|stic)", r"\bcrowded\b", r"\bbusy\b", r"densely\s+packed"]),
    ("high-key vs low-key", [r"high-?key"], [r"low-?key", r"chiaroscuro", r"dark\s+and\s+moody"]),
    ("soft vs hard light", [r"soft\s+(?:diffused\s+)?light", r"diffused\s+light", r"softbox"],
     [r"hard\s+light", r"harsh\s+light", r"hard\s+shadows", r"harsh\s+shadows"]),
    ("clear vs stormy weather", [r"clear\s+sky", r"\bsunny\b", r"cloudless"],
     [r"heavy\s+rain", r"\bstorm(?:y)?\b", r"blizzard", r"thick\s+fog"]),
]

# Filler tokens that add no information a generator can act on.
FILLER = ["masterpiece", "best quality", "8k", "trending on artstation", "award-winning", "award winning",
          "stunning", "breathtaking", "ultra detailed", "highly detailed", "beautiful", "amazing", "epic"]

# ------------------------------------------------------------ aspect ratios
# Common ratios in current generators. Others in range are allowed with a
# warning because every vendor accepts a different set.
COMMON_RATIOS = {(1, 1), (4, 3), (3, 4), (3, 2), (2, 3), (16, 9), (9, 16), (21, 9), (9, 21), (4, 5), (5, 4),
                 (16, 10), (10, 16), (2, 1), (1, 2), (3, 1), (1, 3)}
MAX_RATIO = 4.0  # beyond 4:1 or 1:4 no mainstream generator accepts the shape
MAX_SIDE = 32    # ratio terms above 32 are almost always a time like 07:40 or a typo
RATIO_CONTEXT = re.compile(r"(?:--ar|--aspect|aspect\s*ratio|\bratio)\s*[:=]?\s*(\d+):(\d+)", re.I)
RATIO_BARE = re.compile(r"(?<![\d:.])(\d{1,2}):(\d{1,2})(?![\d:])(?!\s?(?:am|pm)\b)", re.I)
DIMENSIONS = re.compile(r"(?<![\d.])(\d{3,5})\s?[x×]\s?(\d{3,5})(?![\d.])")

MIN_WORDS = 12   # below this a prompt cannot hold the contract
MAX_WORDS = 200  # past this most generators drop or blur later terms (working value)

LABEL_LINE = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?([A-Za-z][A-Za-z /]{1,30}?)(?:\*\*)?\s*:\s*(.*)$")
AR_FLAG = re.compile(r"--(?:ar|aspect)\s+\S+")
NO_FLAG = re.compile(r"--no\s+(.*)$")
NEGATION_START = re.compile(r"^\s*(?:no|not|without|avoid|never|don't|do not)\b", re.I)


def read_text(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        fail("cannot read %s: %s" % (path, exc.strerror or exc))
    text = raw.decode("utf-8", errors="replace").lstrip(chr(0xFEFF))
    if not text.strip():
        fail("%s is empty; write the prompt into it first" % path)
    return text


def fail(message):
    sys.stderr.write("prompt_lint: " + message + "\n")
    sys.exit(2)


def parse(text):
    """Return (fields_by_label, positive_lines, negative_text, labelled).

    fields_by_label maps a contract field to its labelled text.
    positive_lines is a list of (line_number, text) outside the negative field.
    """
    fields = {}
    positive = []
    negative_parts = []
    current = None
    labelled = False
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped in ("---", "```"):
            continue
        m = LABEL_LINE.match(line)
        if m and m.group(1).strip().lower() in LABELS:
            labelled = True
            current = LABELS[m.group(1).strip().lower()]
            value = m.group(2).strip()
            fields[current] = (fields.get(current, "") + " " + value).strip()
            body = value
        else:
            body = stripped
            if m:
                # A line with an unrecognised label ("Prompt note: ...") belongs to no
                # field: it must not be swallowed by a preceding Negative field, where
                # rights terms are legitimate and would escape the rights scan.
                current = None
            elif current == "negative" and not re.match(r"^\s*[-*]\s", line) and not NEGATION_START.match(stripped):
                # A bare prose line after the Negative field is not a negative list
                # item (bullets and "no ..." lines are); scan it as positive text.
                current = None
            if current:
                fields[current] = (fields.get(current, "") + " " + body).strip()
        nm = NO_FLAG.search(body)
        if nm:
            negative_parts.append(nm.group(1))
            body = body[:nm.start()]
        body = AR_FLAG.sub("", body).strip()
        if current == "negative":
            negative_parts.append(body)
        elif body:
            positive.append((number, body))
    return fields, positive, " ".join(p for p in negative_parts if p).strip(), labelled


def positive_clauses(positive_lines):
    """Split positive lines into clauses, dropping clauses that negate."""
    clauses = []
    for number, text in positive_lines:
        for part in re.split(r"[,;]\s*|\.(?:\s+|$)|\s+-\s+|\s+\|\s+", text):
            if part.strip() and not NEGATION_START.match(part):
                clauses.append((number, part.strip()))
    return clauses


def has_term(terms, text):
    for term in terms:
        pattern = r"(?<![\w-])" + re.escape(term) + (r"(?![\w-])" if term[-1].isalnum() else "")
        if re.search(pattern, text, re.I):
            return True
    return False


def detect_fields(fields, positive_lines, labelled, full_text):
    found = {}
    clause_text = " ".join(c for _, c in positive_clauses(positive_lines))
    for name in FIELDS:
        if name in ("negative", "aspect_ratio"):
            continue
        label_value = fields.get(name, "").strip()
        if name == "subject":
            if label_value:
                found[name] = "label"
            elif not labelled and len(clause_text.split()) >= 4:
                found[name] = "free-text"
            else:
                found[name] = None
        elif label_value:
            found[name] = "label"
        elif has_term(VOCAB[name], clause_text):
            found[name] = "keyword"
        else:
            found[name] = None
    return found


def check_rights(positive_lines, allow):
    findings = []
    allow_l = {a.lower() for a in allow}
    for number, line in positive_lines:
        for group, code, label in ((LIVING_ARTISTS, "rights-living-artist", "living artist"),
                                   (REAL_PEOPLE, "rights-real-person", "real person"),
                                   (TRADEMARKS, "rights-trademark", "trademark or franchise")):
            for name in group:
                if name.lower() in allow_l:
                    continue
                if re.search(r"(?<![\w])" + re.escape(name) + r"(?![\w])", line, re.I):
                    findings.append(finding("error", code, "%s named: %s. Describe the look or the character in your own words instead." % (label, name), number, name))
        for pattern, code, why in LIKENESS_PATTERNS:
            for m in re.finditer(pattern, line):
                if m.group(0).lower() in allow_l:
                    continue
                findings.append(finding("error", code, "%s: replace with an invented character described by age, build, clothing and expression." % why, number, m.group(0)))
        for m in re.finditer(ROLE_PATTERN, line):
            if m.group(0).lower() not in allow_l:
                findings.append(finding("warning", "rights-role-name", "a title plus a name usually points at a real person; use an invented role holder.", number, m.group(0)))
        for m in re.finditer(STYLE_HOOK, line):
            name = m.group(1).strip()
            first = re.split(r"[\s]", name)[0].lower().rstrip("'’")
            if first in SAFE_STYLE_WORDS or name.lower() in allow_l:
                continue
            already = any(f["code"] in ("rights-living-artist", "rights-real-person", "rights-trademark") and f["line"] == number
                          and f["match"].lower() in name.lower() for f in findings)
            if not already:
                findings.append(finding("warning", "possible-artist-name", "named style source '%s': describe the look (line quality, palette, era, materials) instead of naming a maker." % name, number, name))
        for m in re.finditer(BRAND_MARK_PATTERN, line, re.I):
            findings.append(finding("warning", "possible-brand-mark", "a logo or brand mark in the image is a trademark question; remove it or confirm you hold the rights.", number, m.group(0)))
    return findings


def check_contradictions(clauses):
    findings = []
    for label, side_a, side_b in CONTRADICTIONS:
        hit_a = hit_b = None
        for number, clause in clauses:
            if hit_a is None:
                for p in side_a:
                    m = re.search(p, clause, re.I)
                    if m:
                        hit_a = (number, m.group(0))
                        break
            if hit_b is None:
                for p in side_b:
                    m = re.search(p, clause, re.I)
                    if m:
                        hit_b = (number, m.group(0))
                        break
        if hit_a and hit_b:
            f = finding("error", "contradiction", "%s: '%s' (line %d) conflicts with '%s' (line %d). Keep one." % (label, hit_a[1], hit_a[0], hit_b[1], hit_b[0]), hit_a[0], hit_a[1] + " / " + hit_b[1])
            f["terms"] = [hit_a[1], hit_b[1]]
            findings.append(f)
    return findings


def check_negative_overlap(clauses, negative):
    findings = []
    positive_text = " ".join(c for _, c in clauses).lower()
    for term in re.split(r"[,;]", negative):
        term = term.strip().lower()
        term = re.sub(r"^(?:no|not|without|avoid)\s+", "", term)
        if len(term) >= 4 and re.search(r"(?<![\w-])" + re.escape(term) + r"(?![\w-])", positive_text):
            findings.append(finding("warning", "negative-overlap", "'%s' appears in both the positive text and the negative list." % term, 0, term))
    return findings


def check_aspect(fields, full_text):
    """Return (aspect_ok_present, findings)."""
    findings = []
    candidates = []  # (w, h, source)
    value = fields.get("aspect_ratio", "")
    for m in RATIO_CONTEXT.finditer(full_text):
        candidates.append((int(m.group(1)), int(m.group(2)), "context"))
    if value:
        for m in re.finditer(r"(\d+):(\d+)", value):
            candidates.append((int(m.group(1)), int(m.group(2)), "label"))
    if not candidates:
        for m in RATIO_BARE.finditer(full_text):
            pair = (int(m.group(1)), int(m.group(2)))
            if pair in COMMON_RATIOS:
                candidates.append((pair[0], pair[1], "bare"))
    dims = [(int(m.group(1)), int(m.group(2))) for m in DIMENSIONS.finditer(value or full_text)]
    seen = set()
    unique = []
    for w, h, src in candidates:
        if (w, h) not in seen:
            seen.add((w, h))
            unique.append((w, h, src))
    present = False
    ratios = []
    for w, h, src in unique:
        if w <= 0 or h <= 0:
            findings.append(finding("error", "aspect-invalid", "aspect ratio %d:%d has a zero side." % (w, h), 0, "%d:%d" % (w, h)))
            continue
        if w > MAX_SIDE or h > MAX_SIDE:
            findings.append(finding("error", "aspect-invalid", "aspect ratio %d:%d has a side over %d; it is probably not a ratio." % (w, h, MAX_SIDE), 0, "%d:%d" % (w, h)))
            continue
        r = w / float(h)
        if r > MAX_RATIO or r < 1 / MAX_RATIO:
            findings.append(finding("error", "aspect-invalid", "aspect ratio %d:%d is outside 1:4 to 4:1, which no mainstream generator accepts." % (w, h), 0, "%d:%d" % (w, h)))
            continue
        g = _gcd(w, h)
        reduced = (w // g, h // g)
        if reduced not in COMMON_RATIOS:
            findings.append(finding("warning", "aspect-uncommon", "aspect ratio %d:%d is valid in range but not in the common set; check that the target generator accepts it." % (w, h), 0, "%d:%d" % (w, h)))
        ratios.append(reduced)
        present = True
    for w, h in dims:
        r = w / float(h)
        if r > MAX_RATIO or r < 1 / MAX_RATIO:
            findings.append(finding("error", "aspect-invalid", "size %dx%d is outside 1:4 to 4:1." % (w, h), 0, "%dx%d" % (w, h)))
            continue
        if w % 8 or h % 8:
            findings.append(finding("warning", "aspect-dimensions", "size %dx%d is not a multiple of 8 on both sides; many generators round it." % (w, h), 0, "%dx%d" % (w, h)))
        g = _gcd(w, h)
        ratios.append((w // g, h // g))
        present = True
    if len(set(ratios)) > 1:
        findings.append(finding("error", "aspect-conflict", "more than one aspect ratio is stated; keep one.", 0, ", ".join("%d:%d" % r for r in sorted(set(ratios)))))
    if value and not present and not any(f["code"].startswith("aspect") for f in findings):
        findings.append(finding("error", "aspect-unparseable", "the aspect ratio field must be numeric, for example 16:9 or 4:5; words like 'square' or 'wide' are not enough.", 0, value[:40]))
    return present, findings


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def finding(severity, code, message, line, match):
    return {"severity": severity, "code": code, "line": line, "match": match, "message": message}


def lint(path, allow):
    text = read_text(path)
    fields, positive_lines, negative, labelled = parse(text)
    clauses = positive_clauses(positive_lines)
    found = detect_fields(fields, positive_lines, labelled, text)
    aspect_present, aspect_findings = check_aspect(fields, text)
    found["aspect_ratio"] = ("label" if fields.get("aspect_ratio") else "keyword") if aspect_present else None
    neg_present = bool(negative.strip())
    found["negative"] = ("label" if fields.get("negative") else "flag") if neg_present else None

    findings = []
    for name in FIELDS:
        if found[name] is None:
            required = name in REQUIRED
            findings.append(finding("error" if required else "warning", "missing-field",
                                    "%s field %s: %s" % ("required" if required else "recommended", name, HINTS[name]), 0, name))
    findings.extend(aspect_findings)
    findings.extend(check_rights(positive_lines, allow))
    findings.extend(check_contradictions(clauses))
    findings.extend(check_negative_overlap(clauses, negative))

    words = len(re.findall(r"\b[\w'’-]+\b", " ".join(t for _, t in positive_lines)))
    if words < MIN_WORDS:
        findings.append(finding("warning", "too-short", "positive text is %d words; under %d cannot carry the contract." % (words, MIN_WORDS), 0, str(words)))
    if words > MAX_WORDS:
        findings.append(finding("warning", "too-long", "positive text is %d words; past %d later terms are often dropped. Cut to the terms that change the image." % (words, MAX_WORDS), 0, str(words)))
    lowered = " ".join(t for _, t in positive_lines).lower()
    for token in FILLER:
        if re.search(r"(?<![\w-])" + re.escape(token) + r"(?![\w-])", lowered):
            findings.append(finding("warning", "filler-token", "'%s' gives the generator nothing to act on; say what you see instead." % token, 0, token))

    score = sum(WEIGHTS[n] for n in FIELDS if found[n] is not None)
    errors = [f for f in findings if f["severity"] == "error"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    rights = [f for f in errors if f["code"].startswith("rights-")]
    if rights:
        verdict = "blocked"
    elif errors or score < PASS_SCORE:
        verdict = "revise"
    else:
        verdict = "pass"
    return {
        "command": "lint", "file": path, "labelled": labelled, "word_count": words,
        "fields": {n: {"present": found[n] is not None, "source": found[n]} for n in FIELDS},
        "score": score, "score_max": 100, "pass_score": PASS_SCORE,
        "counts": {"error": len(errors), "warning": len(warnings)},
        "verdict": verdict, "findings": findings,
    }


HINTS = {
    "subject": "name who or what is in the image, with count, age or material, and what it is doing.",
    "composition": "say the shot size, angle and where the subject sits in the frame.",
    "camera": "name a lens or focal length and depth of field, or say none applies for non-photographic styles.",
    "lighting": "say the light source, direction, quality and time of day.",
    "palette": "name three to five colours or a colour relationship.",
    "style": "name the medium and the visual era or finish, described, not by a maker's name.",
    "negative": "list what must not appear, for example text, extra fingers, watermark.",
    "aspect_ratio": "give a numeric ratio such as 16:9, 4:5 or 1:1.",
}


def diff(old_path, new_path):
    old_fields = parse(read_text(old_path))
    new_fields = parse(read_text(new_path))
    if not old_fields[3] or not new_fields[3]:
        fail("diff needs labelled fields (Subject:, Composition:, ...) in both files")
    changed = []
    for name in FIELDS:
        a = _norm(old_fields[0].get(name, ""))
        b = _norm(new_fields[0].get(name, ""))
        if name == "negative":
            a = _norm(old_fields[0].get(name, "") + " " + old_fields[2])
            b = _norm(new_fields[0].get(name, "") + " " + new_fields[2])
        if a != b:
            kind = "added" if not a else "removed" if not b else "edited"
            changed.append({"field": name, "change": kind, "old": a, "new": b})
    return {"command": "diff", "old": old_path, "new": new_path, "changed_count": len(changed),
            "changed_fields": changed, "ok": len(changed) <= 1}


def _norm(value):
    return re.sub(r"\s+", " ", value).strip().lower()


def emit(report):
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    if len(argv) >= 2 and argv[0] == "lint":
        allow = []
        rest = argv[1:]
        paths = []
        i = 0
        while i < len(rest):
            if rest[i] == "--allow":
                if i + 1 >= len(rest):
                    fail("--allow needs a term")
                allow.append(rest[i + 1])
                i += 2
            else:
                paths.append(rest[i])
                i += 1
        if len(paths) != 1:
            fail("usage: prompt_lint.py lint <prompt-file> [--allow TERM ...]")
        report = lint(paths[0], allow)
        emit(report)
        return 0 if report["verdict"] == "pass" else 1
    if len(argv) == 3 and argv[0] == "diff":
        report = diff(argv[1], argv[2])
        emit(report)
        return 0 if report["ok"] else 1
    fail("usage: prompt_lint.py lint <prompt-file> [--allow TERM ...] | diff <old> <new>")


if __name__ == "__main__":
    sys.exit(main())
