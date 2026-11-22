#!/usr/bin/env python3
"""readability.py - plain-language measurements for English text.

Usage:
    python readability.py TEXT [--rewrite REWRITE] [--grade N]
                          [--max-sentence-words N] [--jargon FILE]
                          [--out FILE [--force]]

    TEXT       the text to measure (UTF-8, plain text or Markdown).
    --rewrite  a rewrite of TEXT. Scores and lists then describe the rewrite,
               and "comparison" holds before/after figures plus the checks that
               numbers, links, modal verbs, negations, conditions and names
               survived.
    --grade N  target Flesch-Kincaid grade; exit 1 when the measured text is above.
    --max-sentence-words N   a sentence longer than N words is listed (default 25).
    --jargon FILE   one term per line: "term" (replace it), "term => plain"
               (replace it, with a suggestion) or "!term" (needed technical
               term: keep it, give it a gloss). Lines starting with # are comments.
    --out FILE write the JSON report to FILE as well as printing it. Refuses a
               path that resolves to TEXT, REWRITE or JARGON (even with --force)
               and refuses an existing file unless --force is given.

Reads only the files named on the command line. Writes only --out. No network.

Exit codes: 0 all checks passed; 1 a check failed (numbers or links changed, a
needed term dropped, target grade missed; see "failures"); 2 bad input or usage
(missing or empty file, non-English text, no sentences, refused --out path).

Everything printed is strict JSON. All figures are estimates from surface
counts; none of them measures whether a reader understands the text.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter

VERSION = "0.1.0"

# --- constants, each with its reason -------------------------------------------------

LOW_RELIABILITY_WORDS = 100   # readability formulas are unstable on short samples
LOW_RELIABILITY_SENTENCES = 5  # an average over fewer sentences is dominated by one sentence
DEFAULT_LONG_SENTENCE = 25    # common plain-language ceiling for a single sentence
VERY_LONG_SENTENCE = 40       # a sentence this long almost always holds several ideas
CHOPPY_AVG_WORDS = 8          # below this average, shortening has probably gone too far
SHRINK_WARN = 0.60            # a rewrite under 60% of the original length may have lost content
GROW_WARN = 1.40              # a rewrite over 140% of the original length is rarely "plainer"
ENGLISH_FUNCTION_SHARE = 0.15  # real English prose is about 35-45% function words
NON_LATIN_SHARE = 0.30        # share of letters outside the Latin script that triggers refusal
LANG_CHECK_MIN_WORDS = 20     # the function-word test is meaningless below this
MAX_LIST = 60                 # cap on list sizes in the report (counts are never capped)
GLOSS_WINDOW = 120            # characters after a kept term searched for a definition
GLOSS_WINDOW_BEFORE = 80      # characters before a kept term searched for "called ..."

EASE_BANDS = [  # (lowest ease score, label, usual US school-grade reading)
    (90, "very easy", "about grade 5"),
    (80, "easy", "about grade 6"),
    (70, "fairly easy", "about grade 7"),
    (60, "plain English", "about grade 8-9"),
    (50, "fairly difficult", "about grade 10-12"),
    (30, "difficult", "college"),
    (0, "very difficult", "college graduate"),
]

# Common everyday English words (base forms). Inflections are matched by stripping
# common suffixes. This is a small hand-made list, not a frequency corpus: a word
# missing here is "not on the list", not "hard".
COMMON = set("""
a able about above accept accident account across act action add address afraid after again against age ago agree
air all allow almost alone along already also always among amount and animal another answer any anyone anything
appear apply area arm around arrive art as ask at away baby back bad bag ball bank base be beat beautiful because
become bed before begin behind believe below best better between big bill bit black blood blue board boat body book
born both bottom box boy break bring brother build building bus business busy but buy by call can car card care
carry case catch cause center century certain chair chance change charge check child choice choose church city class
clean clear close cloth clothes cold college color come common community company complete computer cook cool copy
corner cost could count country course court cover create cross cut dark date daughter day dead deal dear death
decide decision deep department different difficult dinner direct do doctor dog dollar door down draw dream dress
drink drive drop dry during each early earth east easy eat effect effort eight either else end enough enter even
evening event ever every everyone everything exactly example except expect eye face fact fail fall family far farm
fast father fear feel few field fight fill final find fine finger finish fire first fish five floor fly follow food
foot for force forget form forward four free friend from front full fun future game garden gas gave general get
girl give glad glass go god gold good got government great green ground group grow guess gun guy had hair half hall
hand happen happy hard has hat have he head hear heart heavy held help her here high him his history hit hold home
hope horse hospital hot hotel hour house how however human hundred hurt i idea if important in include increase
inside instead into is it job join just keep kid kill kind king kitchen knew know land language large last late
laugh law lay lead learn least leave left leg less let letter level lie life light like line list listen little
live local long look lose lost lot love low machine made main make man many map mark market matter may maybe me
mean meet member men mention middle might mile milk mind minute miss moment money month more morning most mother
mouth move movie much music must my name national near need never new news next nice night nine no none nor north
nose not note nothing notice now number of off offer office often oh oil old on once one only open or order other
our out outside over own page paper parent park part party pass past pay people perhaps person phone pick picture
piece place plan plant play please point police poor power present president press pretty price probably problem
program provide public pull put question quick quite race radio rain raise reach read ready real really reason
receive record red remember report rest result return rich ride right ring rise river road rock room round rule run
safe said same save saw say school second see seem sell send sense serve service set seven several shall shape she
ship shop short should show side sign simple since sing sister sit six size sleep slow small smile so social some
someone something sometimes son song soon sorry sort sound south speak special spend sport spring stand star start
state station stay step still stop store story street strong student study such summer sun sure table take talk tax
teacher team tell ten test than thank that the their them then there these they thing think third this those though
thought three through time to today together told tonight too took top toward town trade train travel tree trip
true try turn two type under understand until up upon us use usual very visit voice wait walk wall want war warm
was wash watch water way we wear week weight well went were west what when where whether which while white who whole
why wide wife will win wind window winter wish with within without woman wonder word work world would write wrong
year yes yesterday yet you young your
information inform form forms apply applied apply payment pay paid benefit benefits cost fee fees fine plan plans
pay late soon deadline address phone email mail letter call visit website online contact contacts support
customer customers order orders refund refunds receipt ticket tickets issue issues problem fix fixed update updates
password login account accounts click button page link file files download upload copy delete save send reply message
messages help question questions answer answers staff team office hours open closed monday tuesday wednesday thursday
friday saturday sunday january february march april may june july august september october november december
health care doctor nurse medicine medical pill pills dose daily weekly monthly pain sick ill safe safety danger
water food home house room door rent tenant landlord lease tax taxes income wage wages job jobs work worker workers
child children student students lesson lessons class classes grade grades teacher teachers read reading write writing
rule rules law laws legal court judge right rights claim claims decision appeal result results approved denied
cancel cancelled stop starts begin began begun ends ended allowed allow required receive received keep kept need needs
list lists table tables step steps first next last then also again both either each such same other another
collect collection resident household energy process although plant leaf leaves tree waste bin bins been sent shown written taken given known seen done brought later continue request unless desk failure weekday weekdays
online card cards bank money cash price total amount number numbers date dates time times month months year years
important simple easy hard clear short long large small free fast slow safe full empty new old
""".split())

# Formal word -> plain word. Hand-made, original wording; a suggestion, never an
# automatic replacement (the plain word must still fit the sentence).
PLAIN_SWAPS = {
    "utilize": "use", "utilise": "use", "commence": "start", "terminate": "end", "assist": "help",
    "assistance": "help", "ascertain": "find out", "endeavor": "try", "endeavour": "try",
    "facilitate": "help", "purchase": "buy", "obtain": "get", "demonstrate": "show", "sufficient": "enough",
    "additional": "more", "approximately": "about", "subsequent": "later", "subsequently": "later",
    "remainder": "rest", "residence": "home", "reside": "live", "indicate": "show", "initiate": "begin",
    "modify": "change", "modification": "change", "attempt": "try", "accomplish": "do", "comply": "follow",
    "ensure": "make sure", "regarding": "about", "concerning": "about", "therefore": "so",
    "nevertheless": "still", "furthermore": "also", "additionally": "also", "consequently": "so",
    "notwithstanding": "despite", "pursuant": "under", "aforementioned": "this", "forthwith": "now",
    "expedite": "speed up", "optimal": "best", "minimum": "least", "maximum": "most", "cease": "stop",
    "remit": "send", "remuneration": "pay", "personnel": "staff", "individual": "person",
    "enquire": "ask", "inquire": "ask", "advise": "tell", "deem": "consider", "retain": "keep",
    "relocate": "move", "concur": "agree", "disseminate": "share", "implement": "carry out",
    "methodology": "method", "functionality": "feature", "leverage": "use", "hence": "so",
    "whilst": "while", "whereas": "while", "apparent": "clear", "adequate": "enough", "authorize": "allow",
    "authorise": "allow", "verify": "check", "validate": "check", "finalize": "finish", "finalise": "finish",
    "delineate": "describe", "elucidate": "explain", "ameliorate": "improve", "mitigate": "reduce",
    "exacerbate": "make worse", "necessitate": "need", "applicable": "that applies", "disclose": "tell",
    "notification": "notice", "notify": "tell", "requirement": "what is needed", "eligible": "able to get",
    "prohibited": "not allowed", "permitted": "allowed", "commencement": "start", "termination": "end",
    "duration": "length of time", "inadvertently": "by mistake", "equivalent": "equal", "discontinue": "stop",
    "ascertained": "found out", "supplementary": "extra", "subsequent to": "after", "reimbursement": "repayment",
    "reimburse": "repay", "documentation": "documents", "correspondence": "letters", "endorse": "approve",
}

# (regex, suggestion). Matched case-insensitively with word boundaries.
WORDY_PHRASES = [
    (r"in order to", "to"), (r"due to the fact that", "because"), (r"owing to the fact that", "because"),
    (r"in the event that", "if"), (r"in the event of", "if there is"), (r"prior to", "before"),
    (r"subsequent to", "after"), (r"with regard to", "about"), (r"with respect to", "about"),
    (r"in regard to", "about"), (r"in relation to", "about"), (r"for the purpose of", "to"),
    (r"a number of", "some or several"), (r"the majority of", "most"), (r"a large number of", "many"),
    (r"at this point in time", "now"), (r"at the present time", "now"), (r"in the near future", "soon"),
    (r"in accordance with", "under or following"), (r"in addition to", "besides"),
    (r"in spite of the fact that", "although"), (r"is able to", "can"), (r"has the ability to", "can"),
    (r"it is necessary that", "must"), (r"please be advised that", "(delete)"), (r"is in receipt of", "has received"),
    (r"make a determination", "decide"), (r"give consideration to", "consider"),
    (r"take into consideration", "consider"), (r"with the exception of", "except"),
    (r"on a daily basis", "daily"), (r"on a regular basis", "regularly"), (r"until such time as", "until"),
    (r"as a result of", "because of"), (r"for the reason that", "because"), (r"by means of", "by or with"),
    (r"in conjunction with", "with"), (r"in the absence of", "without"), (r"has a requirement for", "needs"),
]

MODALS = ["must", "shall", "should", "may", "might", "can", "cannot", "can't", "could", "will", "won't"]
NEGATIONS = {"not", "no", "never", "none", "nobody", "nothing", "neither", "nor", "cannot", "without"}
CONDITIONS = ["if", "unless", "except", "only", "until"]

EN_FUNCTION = set("""the of and to a in is that for it as with was on be by this are or you your we will can have
not from at an if they but all our their has had which more when who what there been would should may must""".split())

# Syllable overrides for words the vowel-group count gets wrong (hand-checked).
SYLLABLE_OVERRIDES = {
    "people": 2, "business": 2, "every": 2, "everyone": 3, "everything": 3, "evening": 2, "different": 3,
    "area": 3, "idea": 3, "video": 3, "radio": 3, "create": 2, "created": 3, "creating": 3, "creation": 3,
    "science": 2, "quiet": 2, "being": 2, "doing": 2, "going": 2, "seeing": 2, "ago": 2, "lion": 2, "poem": 2,
    "poet": 2, "really": 3, "player": 2, "media": 3, "area": 3, "experience": 4, "experiences": 4,
    "usual": 3, "usually": 4, "february": 4, "wednesday": 3, "interesting": 4, "comfortable": 4,
    "beautiful": 3, "family": 3, "fire": 1, "hour": 1, "our": 1, "your": 1, "their": 1, "eye": 1, "the": 1,
    "reason": 2, "reasons": 2, "especially": 4, "separate": 3, "several": 3, "average": 3, "chocolate": 3,
    "vegetable": 4, "chargeback": 2, "diet": 2, "client": 2, "science": 2, "technology": 4, "violence": 3, "genuine": 3,
}

ABBR_MERGE = {"mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.", "st.", "vs.", "fig.", "no.", "u.s.", "u.k.",
              "e.g.", "i.e."}

IRREGULAR_PARTICIPLES = set("""made done given taken seen shown known written held built sent paid kept left lost
brought bought caught found told sold chosen driven broken spoken stolen forgotten hidden begun drawn grown thrown
worn torn born won met led fed heard understood lent spent""".split())
NOT_PARTICIPLES = set("""tired interested excited concerned surprised pleased worried married bored scared shocked
relaxed determined supposed hundred need speed indeed proceed succeed exceed breed feed seed bleed weed greed creed
embedded limited entitled""".split())

NUMBER_WORDS = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
                "seven": "7", "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12",
                "thirteen": "13", "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
                "eighteen": "18", "nineteen": "19", "twenty": "20"}

WORD_RE = re.compile(r"[A-Za-z]+(?:['\-][A-Za-z]+)*|\d+(?:[.,:/]\d+)*%?")
SPLIT_RE = re.compile(r"([.!?]+[\"')\]]*)\s+(?=[\"'(\[]*[A-Z0-9])")
URL_RE = re.compile(r"https?://[^\s)>\]]+|www\.[^\s)>\]]+|[\w.+-]+@[\w-]+\.[\w.-]+")
NUM_RE = re.compile(r"(?<![\w.])[$\u00a3\u20ac]?(\d+(?::\d{2})+|\d[\d,]*(?:\.\d+)?)%?")
BE = r"(?:am|is|are|was|were|be|been|being|isn't|aren't|wasn't|weren't)"
ADV = r"(?:\s+(?:not|never|also|still|often|always|already|just|only|then|now|usually|[a-z]+ly))*"
PASSIVE_RE = re.compile(r"\b(" + BE + r")\b" + ADV + r"\s+([a-z]+)\b", re.I)


class InputError(Exception):
    """Bad input; the message tells the user what to fix."""


# --- reading and parsing -------------------------------------------------------------

def read_text(path):
    if not os.path.isfile(path):
        raise InputError("file not found: " + path)
    raw = open(path, "rb").read()
    if not raw.strip():
        raise InputError("file is empty: " + path)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")
    text = (text.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
            .replace("\u00a0", " ").replace("\u2013", "-").replace("\u2014", " - ").replace("\r\n", "\n"))
    return text.replace("\r", "\n")


def clean_inline(s, counters):
    """Strip Markdown inline syntax. Returns text without links, URLs or code."""
    s = re.sub(r"`[^`]*`", lambda m: counters.update(inline_code=1) or " ", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\*\*|__|(?<!\w)\*|\*(?!\w)|(?<!\w)_|_(?!\w)", "", s)
    return s


def parse(text):
    """Split into prose paragraphs and the pieces that are excluded from sentence stats."""
    counters = Counter()
    paragraphs, para = [], []
    all_lines = []   # every non-code line, markers removed: used for numbers, links, names, terms
    list_words = 0
    in_code, last_kind = False, ""

    def flush():
        if para:
            paragraphs.append(" ".join(para))
            para.clear()

    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            flush()
            in_code = not in_code
            counters["code_lines"] += 1
            last_kind = "code"
            continue
        if in_code:
            counters["code_lines"] += 1
            continue
        if not stripped:
            flush()
            last_kind = ""
            continue
        if re.fullmatch(r"([-*_=])\1{2,}", stripped):
            flush()
            continue
        if re.match(r"#{1,6}\s", stripped):
            flush()
            counters["headings"] += 1
            body = re.sub(r"^#{1,6}\s+(?:\d+[.)]\s+)?", "", stripped)
            all_lines.append(body)
            last_kind = "heading"
            continue
        if stripped.startswith("|"):
            flush()
            if not re.fullmatch(r"[|\s:\-]+", stripped):
                counters["table_rows"] += 1
                all_lines.append(stripped.replace("|", " "))
            last_kind = "table"
            continue
        m = re.match(r"\s*(?:[-*+]|\u2022|\d{1,3}[.)])\s+(.*)", line)
        if m:
            flush()
            counters["list_items"] += 1
            all_lines.append(m.group(1))
            list_words += len(WORD_RE.findall(m.group(1)))
            last_kind = "list"
            continue
        if last_kind == "list" and line.startswith((" ", "\t")):
            all_lines.append(stripped)   # continuation of a list item
            list_words += len(WORD_RE.findall(stripped))
            continue
        body = stripped.lstrip(">").strip()
        para.append(body)
        all_lines.append(body)
        last_kind = "prose"
    flush()
    return paragraphs, all_lines, counters, list_words


def split_sentences(par):
    out, start = [], 0
    for m in SPLIT_RE.finditer(par):
        piece = par[start:m.end(1)]
        last = re.search(r"(\S+)$", piece)
        tok = last.group(1).lower() if last else ""
        if tok in ABBR_MERGE or re.fullmatch(r"[a-z]\.", tok):
            continue
        out.append(piece.strip())
        start = m.end()
    tail = par[start:].strip()
    if tail:
        out.append(tail)
    return out


# --- measurements --------------------------------------------------------------------

def count_syllables(word):
    """Vowel-group heuristic with silent-e, -es and -ed rules. Estimates only."""
    w = re.sub(r"[^a-z]", "", word.lower().replace("'s", ""))
    if not w:
        return 0
    if w in SYLLABLE_OVERRIDES:
        return SYLLABLE_OVERRIDES[w]
    if len(w) <= 3:
        return 1
    n = len(re.findall(r"[aeiouy]+", w))
    vowels = "aeiouy"
    if n > 1:
        if w.endswith("e") and w[-2] not in vowels:
            if not (w.endswith("le") and len(w) > 2 and w[-3] not in vowels):
                n -= 1
        elif w.endswith("es") and len(w) > 3 and w[-3] not in vowels and w[-3] not in "sxzcg":
            n -= 1
        elif w.endswith("ed") and len(w) > 3 and w[-3] not in vowels and w[-3] not in "td":
            n -= 1
    return max(n, 1)


def token_syllables(tok):
    if tok[0].isdigit():
        return 1
    return sum(count_syllables(p) for p in tok.split("-"))


def stem_variants(w):
    c = [w]
    if w.endswith("ies") and len(w) > 4:
        c.append(w[:-3] + "y")
    if w.endswith("es"):
        c.append(w[:-2])
    if w.endswith("s"):
        c.append(w[:-1])
    if w.endswith("ed"):
        c += [w[:-2], w[:-1]]
        if len(w) > 4 and w[-3] == w[-4]:
            c.append(w[:-3])
    if w.endswith("ing"):
        c += [w[:-3], w[:-3] + "e"]
        if len(w) > 5 and w[-4] == w[-5]:
            c.append(w[:-4])
    if w.endswith("ly"):
        c.append(w[:-2])
    if w.endswith("er") or w.endswith("est"):
        c.append(w[:-2] if w.endswith("er") else w[:-3])
    if w.endswith("ation"):
        c.append(w[:-5] + "e")
    return c


def is_common(w):
    if len(w) <= 3:
        return True
    if "-" in w:
        return all(is_common(p) for p in w.split("-") if p)
    return any(v in COMMON for v in stem_variants(w))


def plain_suggestion(w):
    for v in stem_variants(w):
        if v in PLAIN_SWAPS:
            return PLAIN_SWAPS[v]
    return None


def analyse(paragraphs, max_long):
    """Sentence-level measurements for the prose paragraphs."""
    sentences, names, acronyms = [], set(), set()
    word_total = syl_total = complex_total = rare_total = alpha_total = 0
    rare, passive = {}, []
    for par in paragraphs:
        for sent in split_sentences(clean_inline(par, Counter())):
            toks = WORD_RE.findall(URL_RE.sub(" ", sent))
            if not toks:
                continue
            idx = len(sentences) + 1
            sentences.append({"index": idx, "words": len(toks), "text": sent})
            first_alpha = True
            for t in toks:
                word_total += 1
                s = token_syllables(t)
                syl_total += s
                if t[0].isdigit():
                    continue
                is_first, first_alpha = first_alpha, False
                if len(t) > 1 and t.isupper() and t.replace("-", "").isalpha():
                    acronyms.add(t)
                    continue
                if t[0].isupper() and not is_first and t != "I":
                    names.add(t)
                    continue
                low = t.lower().replace("'s", "")
                alpha_total += 1
                if s >= 3:
                    complex_total += 1
                if not is_common(low):
                    rare_total += 1
                    entry = rare.setdefault(low, {"word": low, "count": 0, "syllables": s, "plain": plain_suggestion(low)})
                    entry["count"] += 1
            for m in PASSIVE_RE.finditer(sent):
                part = m.group(2).lower()
                if part in NOT_PARTICIPLES:
                    continue
                ok = part in IRREGULAR_PARTICIPLES or (part.endswith("ed") and len(part) > 4)
                if not ok or (part == "used" and sent[m.end():m.end() + 4].strip().lower().startswith("to")):
                    continue
                passive.append({"sentence": idx, "match": m.group(0), "agentless": " by " not in sent[m.end():].lower(),
                                "text": sent})
    return {"sentences": sentences, "words": word_total, "syllables": syl_total, "alpha": alpha_total,
            "complex": complex_total, "rare_total": rare_total, "rare": rare, "passive": passive,
            "names": names, "acronyms": acronyms}


def scores_from(a, max_long):
    w, s, syl = a["words"], len(a["sentences"]), a["syllables"]
    wps, spw = w / s, syl / w
    ease = 206.835 - 1.015 * wps - 84.6 * spw      # Flesch (1948)
    grade = 0.39 * wps + 11.8 * spw - 15.59        # Kincaid et al. (1975)
    band = next(b for b in EASE_BANDS if ease >= b[0] or b[0] == 0)
    long_n = sum(1 for x in a["sentences"] if x["words"] > max_long)
    return {
        "flesch_reading_ease": round(ease, 1), "ease_band": band[1], "ease_band_grade_reading": band[2],
        "fk_grade": round(grade, 1), "avg_sentence_words": round(wps, 1), "avg_syllables_per_word": round(spw, 2),
        "long_sentence_count": long_n, "very_long_sentence_count": sum(1 for x in a["sentences"] if x["words"] >= VERY_LONG_SENTENCE),
        "passive_count": len(a["passive"]),
        "passive_share": round(len({p["sentence"] for p in a["passive"]}) / s, 2),
        "rare_word_share": round(a["rare_total"] / a["alpha"], 3) if a["alpha"] else 0.0,
        "complex_word_share": round(a["complex"] / a["alpha"], 3) if a["alpha"] else 0.0,
    }


# --- facts: numbers, links, modals, names, terms -------------------------------------

def facts_of(all_lines, a):
    text = "\n".join(all_lines)
    urls = {u.rstrip(".,;:").lower() for u in URL_RE.findall(text)}
    stripped = URL_RE.sub(" ", text)
    stripped = re.sub(r"`[^`]*`", " ", stripped)
    nums = set()
    for m in NUM_RE.finditer(stripped):
        nums.add(m.group(1).replace(",", "").rstrip(".") if ":" not in m.group(1) else m.group(1))
    words = re.findall(r"[A-Za-z']+", stripped.lower())
    wc = Counter(words)
    return {
        "numbers": nums, "urls": urls,
        "spelled": {k for k, v in NUMBER_WORDS.items() if wc[k]},
        "symbols": Counter(ch for ch in stripped if ch in "%$\u00a3\u20ac"),
        "modals": {m: wc[m] for m in MODALS if wc[m]},
        "negations": sum(wc[n] for n in NEGATIONS) + sum(1 for x in words if x.endswith("n't")),
        "conditions": {c: wc[c] for c in CONDITIONS if wc[c]},
        "names": set(a["names"]) | set(a["acronyms"]), "text": text,
    }


def parse_jargon(path):
    terms = []
    for line in read_text(path).split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("!"):
            terms.append({"term": line[1:].strip(), "mode": "keep", "plain": None})
        elif "=>" in line:
            t, p = line.split("=>", 1)
            terms.append({"term": t.strip(), "mode": "replace", "plain": p.strip()})
        else:
            terms.append({"term": line, "mode": "replace", "plain": None})
    return [t for t in terms if t["term"]]


def term_re(term):
    return re.compile(r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])", re.I)


def has_gloss(text, term):
    m = term_re(term).search(text)
    if not m:
        return False
    after = text[m.end():m.end() + GLOSS_WINDOW]
    before = text[max(0, m.start() - GLOSS_WINDOW_BEFORE):m.start()]
    return bool(re.search(r"\(|\bmeans\b|\b(?:is|are) (?:a|an|the)\b|\brefers? to\b|:| - ", after)
                or re.search(r"\b(?:called|known as|termed)\s*$", before, re.I))


def jargon_report(terms, orig_text, new_text):
    rows, failures = [], []
    for t in terms:
        rx = term_re(t["term"])
        count_new = len(rx.findall(new_text))
        row = {"term": t["term"], "mode": t["mode"], "plain": t["plain"], "count": count_new}
        if orig_text is not None:
            row["count_original"] = len(rx.findall(orig_text))
        if t["mode"] == "keep":
            if count_new == 0 and row.get("count_original", 0) > 0:
                row["status"] = "dropped"
                failures.append("needed term dropped: " + t["term"])
            elif count_new == 0:
                row["status"] = "absent"
            else:
                row["status"] = "kept_with_gloss" if has_gloss(new_text, t["term"]) else "kept_no_gloss"
        else:
            row["status"] = "remaining" if count_new else "replaced_or_absent"
        rows.append(row)
    return rows, failures


# --- reporting -----------------------------------------------------------------------

def pack(a, sc, max_long):
    longs = [{"sentence": x["index"], "words": x["words"], "text": x["text"][:200]}
             for x in a["sentences"] if x["words"] > max_long]
    rare = sorted(a["rare"].values(), key=lambda e: (-e["syllables"], -e["count"], e["word"]))
    return (longs[:MAX_LIST],
            [{**p, "text": p["text"][:200]} for p in a["passive"][:MAX_LIST]],
            rare[:MAX_LIST])


def wordy(text):
    out = []
    for rx, plain in WORDY_PHRASES:
        n = len(re.findall(r"\b" + rx + r"\b", text, re.I))
        if n:
            out.append({"phrase": rx, "suggest": plain, "count": n})
    return out


def bucket(a):
    b = Counter()
    for s in a["sentences"]:
        n = s["words"]
        b["1-10" if n <= 10 else "11-20" if n <= 20 else "21-25" if n <= 25 else "26+"] += 1
    return {k: b.get(k, 0) for k in ("1-10", "11-20", "21-25", "26+")}


def build(path, max_long):
    text = read_text(path)
    paragraphs, all_lines, counters, list_words = parse(text)
    letters = [ch for ch in text if ch.isalpha()]
    if letters and sum(1 for ch in letters if ord(ch) > 0x24F) / len(letters) > NON_LATIN_SHARE:
        raise InputError("text is mostly non-Latin script; the formulas are English-only, no scores given: " + path)
    a = analyse(paragraphs, max_long)
    if not a["sentences"]:
        raise InputError("no prose sentences found (only headings, lists, tables or code?): " + path)
    toks = [t.lower() for s in a["sentences"] for t in WORD_RE.findall(s["text"]) if not t[0].isdigit()]
    if len(toks) >= LANG_CHECK_MIN_WORDS and sum(1 for t in toks if t in EN_FUNCTION) / len(toks) < ENGLISH_FUNCTION_SHARE:
        raise InputError("text does not look like English; the formulas are English-only, no scores given: " + path)
    sc = scores_from(a, max_long)
    f = facts_of(all_lines, a)
    notes = []
    if a["words"] < LOW_RELIABILITY_WORDS:
        notes.append("under %d words: scores are low-reliability" % LOW_RELIABILITY_WORDS)
    if len(a["sentences"]) < LOW_RELIABILITY_SENTENCES:
        notes.append("fewer than %d sentences: averages rest on very little" % LOW_RELIABILITY_SENTENCES)
    info = {"path": path, "words": a["words"], "sentences": len(a["sentences"]), "syllables": a["syllables"],
            "excluded": {"headings": counters["headings"], "list_items": counters["list_items"],
                         "list_item_words": list_words, "table_rows": counters["table_rows"],
                         "code_lines": counters["code_lines"], "inline_code": counters["inline_code"]},
            "low_reliability": bool(notes), "reliability_notes": notes}
    return a, sc, f, info


def compare(a0, s0, f0, a1, s1, f1, i0, i1):
    keys = [("words", i0["words"], i1["words"], "any"), ("sentences", i0["sentences"], i1["sentences"], "any")]
    for k, direction in (("flesch_reading_ease", "up"), ("fk_grade", "down"), ("avg_sentence_words", "down"),
                         ("long_sentence_count", "down"), ("passive_count", "down"), ("rare_word_share", "down"),
                         ("complex_word_share", "down")):
        keys.append((k, s0[k], s1[k], direction))
    table = {}
    for k, before, after, direction in keys:
        d = round(after - before, 3)
        table[k] = {"before": before, "after": after, "delta": d,
                    "improved": None if direction == "any" else (d > 0 if direction == "up" else d < 0)}
    warnings = []
    ratio = i1["words"] / i0["words"]
    if ratio < SHRINK_WARN:
        warnings.append("rewrite has %d%% of the original words: check that no content was dropped" % round(ratio * 100))
    elif ratio > GROW_WARN:
        warnings.append("rewrite has %d%% of the original words: check it is not padded" % round(ratio * 100))
    if s1["avg_sentence_words"] < CHOPPY_AVG_WORDS:
        warnings.append("average sentence under %d words: the rewrite may be choppy; do not split only to lower the score" % CHOPPY_AVG_WORDS)
    miss_n = sorted(f0["numbers"] - f1["numbers"], key=lambda x: (len(x), x))
    add_n = sorted(f1["numbers"] - f0["numbers"], key=lambda x: (len(x), x))
    spelled = [n for n in miss_n if n in NUMBER_WORDS.values() and any(NUMBER_WORDS[w] == n for w in f1["spelled"])]
    miss_n_real = [n for n in miss_n if n not in spelled]
    miss_u, add_u = sorted(f0["urls"] - f1["urls"]), sorted(f1["urls"] - f0["urls"])
    modal_keys = set(f0["modals"]) | set(f1["modals"])
    modals = {m: {"before": f0["modals"].get(m, 0), "after": f1["modals"].get(m, 0)} for m in sorted(modal_keys)}
    if any(v["before"] != v["after"] for v in modals.values()):
        warnings.append("modal verbs changed (" + ", ".join("%s %d->%d" % (m, v["before"], v["after"]) for m, v in modals.items() if v["before"] != v["after"]) + "): confirm each change keeps the obligation, permission or possibility")
    if f0["negations"] != f1["negations"]:
        warnings.append("negation count changed %d->%d: confirm no 'not' was lost or added" % (f0["negations"], f1["negations"]))
    lost_cond = [c for c, n in f0["conditions"].items() if f1["conditions"].get(c, 0) < n]
    if lost_cond:
        warnings.append("fewer uses of " + ", ".join(lost_cond) + ": confirm no condition, exception or limit was lost")
    sym = {k: [f0["symbols"].get(k, 0), f1["symbols"].get(k, 0)] for k in set(f0["symbols"]) | set(f1["symbols"]) if f0["symbols"].get(k, 0) != f1["symbols"].get(k, 0)}
    if sym:
        warnings.append("percent or currency symbols changed " + json.dumps(sym, sort_keys=True) + ": confirm the units are unchanged")
    nm, na = sorted(f0["names"] - f1["names"]), sorted(f1["names"] - f0["names"])
    if nm or na:
        warnings.append("names or acronyms differ (missing: %s; added: %s): confirm by hand" % (", ".join(nm[:8]) or "none", ", ".join(na[:8]) or "none"))
    cmp_ = {"metrics": table, "numbers": {"missing": miss_n_real, "added": add_n, "spelled_out_in_rewrite": spelled},
            "links": {"missing": miss_u, "added": add_u}, "modals": modals,
            "negations": {"before": f0["negations"], "after": f1["negations"]}, "warnings": warnings}
    return cmp_, not (miss_n_real or add_n), not (miss_u or add_u)


def run(argv):
    ap = argparse.ArgumentParser(prog="readability.py", add_help=True)
    ap.add_argument("text")
    ap.add_argument("--rewrite")
    ap.add_argument("--grade", type=float)
    ap.add_argument("--max-sentence-words", type=int, default=DEFAULT_LONG_SENTENCE)
    ap.add_argument("--jargon")
    ap.add_argument("--out")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    if args.out:
        out_real = os.path.normcase(os.path.realpath(args.out))
        for p in (args.text, args.rewrite, args.jargon):
            if p and os.path.normcase(os.path.realpath(p)) == out_real:
                raise InputError("refusing to write --out over an input file: " + args.out)
        if os.path.exists(args.out) and not args.force:
            raise InputError("--out file exists; pass --force to replace it: " + args.out)
    max_long = args.max_sentence_words
    a0, s0, f0, i0 = build(args.text, max_long)
    jargon_terms = parse_jargon(args.jargon) if args.jargon else []
    report = {"tool": "readability.py", "version": VERSION, "scored": "rewrite" if args.rewrite else "text"}
    failures = []
    if args.rewrite:
        a1, s1, f1, i1 = build(args.rewrite, max_long)
        cmp_, nums_ok, links_ok = compare(a0, s0, f0, a1, s1, f1, i0, i1)
        report["comparison"], report["numbers_preserved"] = cmp_, nums_ok
        if not nums_ok:
            failures.append("numbers changed between original and rewrite")
        if not links_ok:
            failures.append("links or contact details changed between original and rewrite")
        a, sc, f, info = a1, s1, f1, i1
        rows, jf = jargon_report(jargon_terms, f0["text"], f1["text"]) if jargon_terms else ([], [])
    else:
        report["comparison"], report["numbers_preserved"] = None, None
        a, sc, f, info = a0, s0, f0, i0
        rows, jf = jargon_report(jargon_terms, None, f0["text"]) if jargon_terms else ([], [])
    failures += jf
    target = None
    if args.grade is not None:
        target = {"fk_grade_max": args.grade, "measured": sc["fk_grade"], "met": sc["fk_grade"] <= args.grade}
        if not target["met"]:
            failures.append("Flesch-Kincaid grade %.1f is above the target %.1f" % (sc["fk_grade"], args.grade))
    longs, passive, rare = pack(a, sc, max_long)
    report.update({
        "input": info, "scores": sc, "target": target, "sentence_length_buckets": bucket(a),
        "long_sentences": longs, "passive": passive, "rare_words": rare, "wordy_phrases": wordy(f["text"]),
        "acronyms": sorted(a["acronyms"])[:MAX_LIST], "jargon": rows,
        "failures": failures, "ok": not failures,
        "limits": "English-only surface estimates; a score does not show that readers understand the text",
    })
    out = json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False, sort_keys=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(out + "\n")
    print(out)
    return 0 if not failures else 1


def main(argv=None):
    try:
        return run(sys.argv[1:] if argv is None else argv)
    except InputError as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
