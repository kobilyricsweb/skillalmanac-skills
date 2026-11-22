#!/usr/bin/env python3
"""audit_lyrics.py - craft audit for an ORIGINAL lyric or poem draft.

Usage:
    python scripts/audit_lyrics.py DRAFT.txt [--form FORM] [--title "hook phrase"]
        [--overrides FILE.json] [--compare FILE.txt] [--min-ngram 5]
        [--keep-parentheses] [--lines]
    python scripts/audit_lyrics.py --list-cliches

FORM is one of: verse-chorus, aaba, ballad, sonnet, haiku, limerick, rap, none.

Reads: the draft file, plus optional --overrides (JSON) and --compare (text).
Writes: one strict-JSON report to stdout (no NaN, no trailing text). Nothing on disk.
Exit codes: 0 report printed (flags do not change the exit code); 2 usage or input error.

Draft format: section labels alone on a line, e.g. [Verse 1], [Chorus], (Bridge),
Verse 2:, # Pre-Chorus. Text before the first label, or a file with no labels, is split
into blocks at blank lines. A second [Chorus] label with no lines under it is a repeat of
the earlier chorus. Text in (parentheses) inside a line is treated as a backing vocal and
left out of syllable and rhyme counts unless --keep-parentheses is given.

Overrides file (JSON, both keys optional):
    {"syllables": {"fire": 2, "wind": 1}, "rhyme_like": {"wind": "find"}}

All of this is HEURISTIC and English-only: syllables come from a vowel-group rule, rhyme
from spelling-based end-sound keys, meter from syllable counts only (stress is not
analysed). It finds candidates for the author to judge; it is not a ground truth.
It cannot tell whether a line copies an existing song or poem: see the originality block.
"""
import argparse
import difflib
import json
import math
import os
import re
import statistics
import sys
import unicodedata
from collections import Counter

SCHEMA_VERSION = 1
SYLLABLE_METHOD = (
    "vowel-group count (a, e, i, o, u, y runs) minus silent final e/ed/es, plus splits "
    "for ia/io/iu/ua/uo and vowel+ing; digits count 1; min 1 per word; overrides win"
)

# ---- thresholds (working values, not measured optima; see SKILL.md) -------------------
STDEV_WARN = 2.5            # syllable stdev above this in a verse/chorus reads as ragged
STDEV_WARN_RAP = 3.5        # rap bars vary more by design
REGULAR_SHARE_REGULAR = 0.85  # share of lines within +-1 syllable of the median
REGULAR_SHARE_LOOSE = 0.60
# section type -> (ideal_lo, ideal_hi, hard_lo, hard_hi) in lines
LENGTHS = {
    "verse": (4, 8, 2, 12),
    "chorus": (4, 8, 2, 10),
    "bridge": (2, 6, 1, 8),
    "pre-chorus": (2, 4, 1, 6),
    "intro": (1, 4, 1, 8),
    "outro": (1, 4, 1, 8),
}
VERSE_UNEVEN_DIFF = 2       # verses differing by this many lines or more are flagged
FIRST_CHORUS_MAX_LINES = 16  # more lyric lines than this before the first chorus delays the hook
HOOK_RANGE = (2, 4)         # title phrase per chorus
DRIFT_LOW = 0.5             # chorus repeats between this and 1.0 similar = likely accidental edits
CLICHE_DENSITY = 1 / 8      # cliche hits per lyric line above which a warn is raised
UNCERTAIN_SHARE = 0.20      # share of lines with uncertain syllable words that triggers a note
MIN_LINES_RELIABLE = 8      # below this the statistics are noisy
MAX_LIST = 10               # cap for long lists in the report
SEARCH_LIST_MAX = 8         # originality search phrases offered
SEARCH_MIN_WORDS = 5        # a phrase shorter than this is too common to search usefully

VOW = "aeiouy"
TOKEN_RE = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)

# ---- syllable heuristic ------------------------------------------------------------
SYLL_EXC = {
    "the": 1, "every": 2, "different": 2, "business": 2, "beyond": 2, "poem": 2, "poems": 2,
    "poet": 2, "poets": 2, "quiet": 2, "giant": 2, "hour": 1, "hours": 1, "our": 1, "ours": 1,
    "area": 3, "idea": 3, "ideas": 3, "evening": 2, "science": 2, "diet": 2, "lion": 2,
    "cruel": 2, "jewel": 2, "fuel": 2, "duel": 2, "ruin": 2, "ruins": 2, "chaos": 2,
    "create": 2, "created": 3, "creation": 3, "creative": 3, "video": 3, "radio": 3,
    "cant": 1, "wont": 1, "shant": 1, "aint": 1, "havent": 2, "heaven": 2, "being": 2,
    "fire": 1, "fires": 1, "desire": 2, "higher": 2, "prayer": 1, "prayers": 1, "world": 1,
    "girl": 1, "girls": 1, "world's": 1, "worlds": 1,
}
INSERT_RE = re.compile(r"(?<![cstg])i[aou](?!ns?$)|(?<![qg])u[ao]")
UNCERTAIN_RE = re.compile(
    r"[aeiou]{3,}|ia|io|iu|ua|uo|eo|ea[^rtdsklmnp]|(?:ire|ires|ired|ower|ours?|ayer|ayers)$"
)


def ascii_fold(s):
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def norm_token(tok):
    return ascii_fold(tok.replace("’", "'")).lower()


def letters_only(tok):
    return re.sub(r"[^a-z]", "", norm_token(tok))


def count_core(w):
    """Syllables in a letters-only lowercase word (documented heuristic)."""
    if not w:
        return 0
    if w in SYLL_EXC:
        return SYLL_EXC[w]
    n = len(re.findall(r"[aeiouy]+", w))
    if (w.endswith("e") and len(w) > 2 and w[-2] not in VOW and n > 1
            and not (w.endswith("le") and w[-3] not in VOW)):
        n -= 1
    elif (w.endswith("ed") and n > 1 and len(w) > 3 and w[-3] not in "td"
          and w[-3] not in VOW):
        n -= 1
    elif (w.endswith("es") and n > 1 and len(w) > 3 and w[-3] not in "sxz"
          and w[-3] not in VOW and not w.endswith(("ches", "shes", "ces", "ges"))
          and not (w.endswith("les") and w[-4] not in VOW)):
        n -= 1
    for suffix in ("ely", "eful", "eless", "eness"):
        if n > 2 and w.endswith(suffix) and w[-len(suffix) - 1] not in VOW:
            n -= 1  # silent e before a suffix: lonely, careful, homeless, likeness
            break
    n += len(INSERT_RE.findall(w))
    if re.search(r"[aeiouy]ing$", w):
        n += 1
    if w.endswith(("ism", "asm", "ythm")):
        n += 1
    return max(n, 1)


def token_syllables(tok, overrides):
    """Return (syllables, uncertain) for one raw token."""
    t = norm_token(tok)
    if not re.search(r"[a-z0-9]", t):
        return 0, False
    if t.isdigit():
        return 1, True
    nt = t.endswith("n't")
    base = t[:-3] if nt else t
    w = re.sub(r"[^a-z]", "", base)
    full = re.sub(r"[^a-z]", "", t)
    if full in overrides:
        return overrides[full], False
    if nt:
        if full in SYLL_EXC:
            return SYLL_EXC[full], False
        if not w:
            return 1, True
        return count_core(w) + (0 if w[-1] in VOW else 1), UNCERTAIN_RE.search(w) is not None
    if not w:
        return 0, False
    return count_core(w), UNCERTAIN_RE.search(w) is not None and w not in SYLL_EXC


# ---- rhyme heuristic -----------------------------------------------------------------
LONG = {"a": "A", "e": "EE", "i": "AI", "o": "O", "u": "OO", "y": "AI"}
LONG_CLUSTERS = {"st", "th", "sh", "ch", "ng", "bl", "pl", "dl", "gl", "kl", "tl", "fl",
                 "cl", "zl", "br", "pr", "tr", "dr", "gr", "cr", "fr"}
R_MAP = {"a": "AR", "o": "OR", "e": "UR", "i": "UR", "u": "UR", "y": "UR", "oa": "OR",
         "ou": "OR", "oo": "OR", "ai": "AIR", "ei": "AIR", "ee": "EER", "ie": "EER",
         "au": "OR", "ue": "OOR", "ui": "OOR", "ua": "AR", "ea": "EER"}
R_SILENT = {"a": "AIR", "e": "EER", "i": "AIER", "o": "OR", "u": "OOR", "y": "AIER"}
VOWEL_MAP = {"ee": "EE", "ea": "EE", "ie": "EE", "ei": "EE", "oa": "O", "oe": "O",
             "ow": "OW", "ou": "OW", "oo": "OO", "ue": "OO", "ew": "OO", "ui": "OO",
             "eu": "OO", "au": "AW", "aw": "AW", "oi": "OY", "oy": "OY", "ai": "A",
             "ay": "A", "ey": "A", "y": "i", "eau": "O"}
OW_WORDS = {"now", "how", "cow", "wow", "brow", "vow", "plow", "pow", "chow"}
IRREG = {
    "i": ("AI", ""), "you": ("OO", ""), "do": ("OO", ""), "who": ("OO", ""), "to": ("OO", ""),
    "too": ("OO", ""), "two": ("OO", ""), "through": ("OO", ""), "shoe": ("OO", ""),
    "whose": ("OO", "s"), "lose": ("OO", "s"), "though": ("O", ""), "although": ("O", ""),
    "dough": ("O", ""), "tough": ("u", "f"), "enough": ("u", "f"), "rough": ("u", "f"),
    "cough": ("o", "f"), "bough": ("OW", ""), "own": ("O", "n"), "grown": ("O", "n"),
    "known": ("O", "n"), "shown": ("O", "n"), "blown": ("O", "n"), "thrown": ("O", "n"),
    "flown": ("O", "n"), "bowl": ("O", "l"), "soul": ("O", "l"), "roll": ("O", "l"),
    "control": ("O", "l"), "most": ("O", "st"), "post": ("O", "st"), "host": ("O", "st"),
    "ghost": ("O", "st"), "would": ("U", "d"), "could": ("U", "d"), "should": ("U", "d"),
    "good": ("U", "d"), "stood": ("U", "d"), "hood": ("U", "d"), "wood": ("U", "d"),
    "blood": ("u", "d"), "flood": ("u", "d"), "love": ("u", "v"), "above": ("u", "v"),
    "dove": ("u", "v"), "glove": ("u", "v"), "shove": ("u", "v"), "of": ("u", "v"),
    "come": ("u", "m"), "some": ("u", "m"), "become": ("u", "m"), "done": ("u", "n"),
    "none": ("u", "n"), "one": ("u", "n"), "gone": ("o", "n"), "have": ("a", "v"),
    "give": ("i", "v"), "forgive": ("i", "v"), "live": ("i", "v"), "move": ("OO", "v"),
    "prove": ("OO", "v"), "improve": ("OO", "v"), "are": ("AR", ""), "were": ("UR", ""),
    "there": ("AIR", ""), "where": ("AIR", ""), "their": ("AIR", ""), "bear": ("AIR", ""),
    "wear": ("AIR", ""), "swear": ("AIR", ""), "pear": ("AIR", ""), "heart": ("AR", "t"),
    "hearth": ("AR", "th"), "war": ("OR", ""), "warm": ("OR", "m"), "warn": ("OR", "n"),
    "ward": ("OR", "d"), "word": ("UR", "d"), "world": ("UR", "ld"), "work": ("UR", "k"),
    "worth": ("UR", "th"), "worse": ("UR", "s"), "worm": ("UR", "m"), "hour": ("OWR", ""),
    "our": ("OWR", ""), "sour": ("OWR", ""), "flour": ("OWR", ""), "tour": ("OOR", ""),
    "sure": ("OR", ""), "bread": ("e", "d"), "head": ("e", "d"), "dead": ("e", "d"),
    "thread": ("e", "d"), "spread": ("e", "d"), "instead": ("e", "d"), "ahead": ("e", "d"),
    "dread": ("e", "d"), "said": ("e", "d"), "friend": ("e", "nd"), "death": ("e", "th"),
    "breath": ("e", "th"), "health": ("e", "lth"), "wealth": ("e", "lth"),
    "sweat": ("e", "t"), "threat": ("e", "t"), "great": ("A", "t"), "break": ("A", "k"),
    "steak": ("A", "k"), "height": ("AI", "t"), "reply": ("AI", ""), "supply": ("AI", ""),
    "apply": ("AI", ""), "imply": ("AI", ""), "rely": ("AI", ""), "comply": ("AI", ""),
    "july": ("AI", ""), "maybe": ("EE", ""), "the": ("u", ""), "key": ("EE", ""),
    "any": ("EE", ""), "many": ("EE", ""), "beyond": ("o", "nd"), "once": ("u", "ns"),
    "wind": ("i", "nd"), "blood": ("u", "d"), "again": ("e", "n"), "anyone": ("u", "n"),
    "everyone": ("u", "n"), "someone": ("u", "n"), "tear": ("EER", ""),
}
ENDS_IRREG = (("bove", ("u", "v")), ("shove", ("u", "v")), ("prove", ("OO", "v")),
              ("move", ("OO", "v")), ("give", ("i", "v")), ("come", ("u", "m")))
SHORT_OO_ENDS = ("good", "stood", "hood", "wood")
OBEY_ENDS = ("obey", "prey", "grey", "they", "survey", "convey", "hey")


def norm_tail(t):
    t = t.replace("ght", "t").replace("tch", "ch").replace("dg", "j").replace("ck", "k")
    t = t.replace("ph", "f")
    t = re.sub(r"gh$", "", t)
    t = re.sub(r"gn$", "n", t)
    t = re.sub(r"mb$", "m", t)
    t = t.replace("x", "ks").replace("z", "s")
    t = re.sub(r"c(?!h)", "k", t)
    return re.sub(r"(.)\1", r"\1", t)


def split_last_vowel_group(s):
    def is_vowel(i):
        c = s[i]
        if c in "aeiou" or (c == "y" and i > 0):
            return True
        # w after a/e/o and not before a vowel belongs to the vowel (down, crowd, dawn)
        return c == "w" and i > 0 and s[i - 1] in "aeo" and (i + 1 == len(s) or s[i + 1] not in VOW)

    idx = [i for i in range(len(s)) if is_vowel(i)]
    if not idx:
        return None
    end = idx[-1]
    start = end
    while (start - 1) in idx:
        start -= 1
    return s[:start], s[start:end + 1], s[end + 1:]


def finish(v, c):
    """Map a (vowel group, tail) pair to a normalised (vowel token, tail)."""
    if c.startswith("r") and v in R_MAP:
        rk = R_MAP[v]
        rest = c[1:]
        if v == "ea" and rest:
            rk = "UR"
        return rk, norm_tail(rest)
    if c.startswith("gh"):
        if v == "i":
            return "AI", norm_tail(c[2:])
        if v in ("ou", "au"):
            return "AW", norm_tail(c[2:])
        if v in ("ei", "ey"):
            return "A", norm_tail(c[2:])
    if v == "i" and c in ("nd", "ld", "gn"):
        return "AI", norm_tail(c)
    if v == "o" and c in ("ld", "lt"):
        return "O", c
    if v == "a" and c in ("ll", "lk", "lt", "ld"):
        return "AW", norm_tail(c)
    if v == "oo" and c == "k":
        return "U", "k"
    if v in VOWEL_MAP:
        return VOWEL_MAP[v], norm_tail(c)
    return v, norm_tail(c)


def silent_tail(c):
    if c == "ng":
        return "nj"
    if c.endswith("c"):
        return norm_tail(c[:-1]) + "s"
    if c.endswith("g"):
        return norm_tail(c[:-1]) + "j"
    return norm_tail(c)


def stem_key(s):
    """(vowel token, tail) for a letters-only stem."""
    s = s.replace("qu", "kw")
    if s in IRREG:
        return IRREG[s]
    for end, key in ENDS_IRREG:
        if s.endswith(end):
            return key
    mono = count_core(s) == 1
    if s.endswith("e") and len(s) >= 2 and s[-2] not in VOW:
        core = s[:-1]
        parts = split_last_vowel_group(core)
        if parts is None:
            return "EE", ""
        _, v, c = parts
        if c == "r" and len(v) == 1:
            return R_SILENT[v], ""
        if len(v) == 1 and v in LONG:
            if (len(c) == 1 or c in LONG_CLUSTERS
                    or (len(c) == 2 and c[0] != c[1] and c[1] in "lr" and c[0] in "bcdfgkptz")):
                return LONG[v], silent_tail(c)
        return finish(v, c)
    if re.search(r"(igh|eye|uy)$", s) or (s.endswith("ye") and len(s) > 2):
        return "AI", ""
    if s.endswith(("eigh", "ay")):
        return "A", ""
    if s.endswith("ey"):
        return ("A", "") if (mono or s.endswith(OBEY_ENDS)) else ("EE", "")
    if s.endswith("ie"):
        return ("AI", "") if mono else ("EE", "")
    if s.endswith("y"):
        return ("AI", "") if mono else ("EE", "")
    if s.endswith(("ee", "ea")):
        return "EE", ""
    if s.endswith("oe"):
        return "O", ""
    if s.endswith("ow"):
        if s in OW_WORDS or s.endswith(("allow", "somehow", "anyhow", "avow")):
            return "OW", ""
        return "O", ""
    if s.endswith(("oo", "ew", "ue", "ui", "ou", "eu")):
        return "OO", ""
    if s.endswith(("aw", "au")):
        return "AW", ""
    if s.endswith(("oy", "oi")):
        return "OY", ""
    if s.endswith("o"):
        return "O", ""
    if s.endswith("a"):
        return "ah", ""
    if s.endswith("u"):
        return "OO", ""
    if s.endswith("i"):
        return ("AI", "") if mono else ("EE", "")
    parts = split_last_vowel_group(s)
    if parts is None:
        return "", norm_tail(s)
    _, v, c = parts
    if v == "oo" and s.endswith(SHORT_OO_ENDS):
        return "U", norm_tail(c)
    return finish(v, c)


def rhyme_key(word, like):
    """(vowel token, tail, flag) end-sound key for a word, or None."""
    w = letters_only(word)
    if not w:
        return None
    w = like.get(w, w)
    if w in IRREG:
        return IRREG[w] + ("",)
    base, flag = w, ""
    if len(base) > 3 and base.endswith("s") and not base.endswith(("ss", "us", "is", "ous")):
        base = base[:-2] if base.endswith(("shes", "ches", "xes", "zes", "sses")) else base[:-1]
        flag = "s"
        if base in IRREG:
            return IRREG[base] + (flag,)
    n = count_core(base)
    if n >= 2 and len(base) > 4 and base.endswith("ing"):
        stem = base[:-3]
        if len(stem) >= 3 and stem[-1] == stem[-2] and stem[-1] not in VOW:
            stem = stem[:-1]
        return stem_key(stem) + (flag + "ing",)
    groups = len(re.findall(r"[aeiouy]+", base))
    if len(base) > 3 and base.endswith("ed") and (groups >= 2 or base.endswith("yed")):
        if base[-3] in "td":
            return stem_key(base[:-2]) + (flag + "ed",)
        if base[-3] == "y":
            return stem_key(base[:-2]) + (flag + "d",)
        if base[-3] in VOW or base[-4] in VOW:
            return stem_key(base[:-1]) + (flag + "d",)
        return stem_key(base[:-2]) + (flag + "d",)
    if n >= 2 and len(base) > 4 and base.endswith("er"):
        if base.endswith("ower") and base not in ("lower", "mower", "blower", "grower", "thrower", "slower", "knower"):
            return ("OWR", "", flag)
        key = stem_key(base[:-2])
        if key == ("AI", ""):
            return ("AIER", "", flag)
        if key == ("OW", ""):
            return ("OWR", "", flag)
        return key + (flag + "er",)
    if n >= 2 and len(base) > 4 and base.endswith("ly"):
        return stem_key(base[:-2]) + (flag + "ly",)
    return stem_key(base) + (flag,)


def classify_pair(wa, wb, ka, kb):
    """identical | perfect | slant | none for two end words with keys."""
    if ka is None or kb is None:
        return "none"
    if letters_only(wa) == letters_only(wb):
        return "identical"
    if ka == kb:
        return "perfect"
    if ka[0] and ka[0] == kb[0]:
        return "slant"
    if ka[1] and ka[1] == kb[1] and ka[0] != kb[0]:
        return "slant"
    return "none"


# ---- bundled lists -------------------------------------------------------------------
CLICHES = (
    "heart of gold", "heart on my sleeve", "heart skips a beat", "heart skipped a beat",
    "tears like rain", "tears fall like rain", "tears in my eyes", "cry me a river",
    "broken heart", "shattered heart", "heart of stone", "cold as ice", "cold as stone",
    "dark as night", "black as night", "light at the end of the tunnel", "sands of time",
    "time heals all wounds", "time stands still", "time stood still", "test of time",
    "love is blind", "love at first sight", "head over heels", "madly in love",
    "burning desire", "burning love", "burning passion", "flame of love", "soul on fire",
    "set me free", "break the chains", "break free", "spread my wings", "spread your wings",
    "fly away", "touch the sky", "reach for the stars", "shoot for the moon",
    "sky is the limit", "stars align", "written in the stars", "dance in the rain",
    "dance the night away", "end of the road", "crossroads of life", "journey of life",
    "rise from the ashes", "fall from grace", "fall apart", "falling apart",
    "pieces of my heart", "pick up the pieces", "lost and found", "lost in your eyes",
    "deep in your eyes", "ocean of tears", "sea of tears", "river of tears",
    "calm before the storm", "weather the storm", "after the rain", "sun will shine",
    "sun will rise again", "brand new day", "dawn of a new day", "turn the page",
    "one more night", "all night long", "forever and a day", "forever and ever",
    "till the end of time", "end of time", "until the day i die", "to the moon and back",
    "from the bottom of my heart", "my one and only", "you are my everything",
    "youre my everything", "meant to be", "feel the beat", "feel the rhythm", "feel alive",
    "young and free", "wild and free", "young and wild", "live for today",
    "no tomorrow", "dreams come true", "chase my dreams", "chasing dreams",
    "follow my dreams", "follow your heart", "darkest hour", "darkest night",
    "hand in hand", "side by side", "arm in arm", "face to face", "heart to heart",
    "day by day", "night and day", "day and night", "words cant say",
    "words cannot describe", "cant live without you", "take my breath away",
    "walking on air", "cloud nine", "over the moon", "fire in my soul", "fire in my veins",
    "ice in my veins", "blood runs cold", "chill down my spine", "butterflies in my stomach",
    "whisper in the wind", "whispers in the wind", "wind in my hair", "stars in the sky",
    "stars above", "castles in the sky", "castles in the air", "diamond in the rough",
    "weight of the world", "world on my shoulders", "world on fire", "end of the world",
    "whole wide world", "open your eyes", "open my eyes", "close my eyes", "closed my eyes",
    "dead of night", "midnight hour", "break of dawn", "crack of dawn", "morning light",
    "tears of joy", "tears of pain", "pain and sorrow", "love and pain", "love and loss",
    "ups and downs", "highs and lows", "all alone", "nowhere to run", "nowhere to hide",
    "take me away", "take me home", "take me higher", "lift me up", "hold me tight",
    "hold me close", "never let me go", "never let you go", "never let go", "dont let go",
    "hold on tight", "stay with me", "by my side", "by your side", "young at heart",
    "heart and soul", "body and soul", "mind body and soul", "roses are red",
    "violets are blue", "sweet as honey", "sweet as sugar", "soft as silk",
    "soft as a feather", "light as a feather", "white as snow", "pure as snow",
    "pure as gold", "bright as the sun", "silver moon", "silvery moon", "velvet sky",
    "velvet night", "blanket of snow", "blanket of stars", "carpet of leaves",
    "tapestry of life", "dance of life", "circle of life", "cycle of life", "river of life",
    "path of life", "game of love", "game of life", "flames of passion", "ocean of love",
    "bleeding heart", "aching heart", "heavy heart", "heart is breaking", "heart is broken",
    "burning bright", "golden sunset", "sunset sky",
)
PREDICTABLE_PAIRS = {
    frozenset(p) for p in (
        ("love", "above"), ("fire", "desire"), ("heart", "apart"), ("heart", "start"),
        ("heart", "part"), ("eyes", "skies"), ("night", "light"), ("night", "tonight"),
        ("tears", "years"), ("tears", "fears"), ("pain", "rain"), ("soul", "whole"),
        ("you", "true"), ("you", "blue"), ("fly", "sky"), ("high", "sky"), ("cry", "die"),
        ("dream", "seem"), ("mine", "shine"), ("me", "free"), ("me", "be"),
        ("alone", "stone"), ("day", "away"), ("stay", "away"), ("tonight", "right"),
        ("fire", "higher"), ("moon", "june"), ("kiss", "miss"), ("burn", "turn"),
        ("gone", "on"), ("feel", "real"), ("fall", "all"), ("fate", "wait"),
        ("hand", "understand"), ("end", "friend"), ("alive", "survive"),
    )
}
STOP = frozenset(
    "the and but for you are was had has have with that this they them then than not out "
    "off our who how why now too his her him she can did get got let may say see use way "
    "yes yet".split()
)

KEYWORDS = (
    (r"pre[- ]?chorus", "pre-chorus"),
    (r"chorus|hook|refrain", "chorus"),
    (r"verse", "verse"),
    (r"bridge|middle[- ]?(?:8|eight)", "bridge"),
    (r"intro(?:duction)?", "intro"),
    (r"outro|coda|ending", "outro"),
    (r"interlude|instrumental|solo|break|drop", "other"),
    (r"stanza|octave|sestet|quatrain|couplet|tercet|bars?", "stanza"),
)
FORMS = ("verse-chorus", "aaba", "ballad", "sonnet", "haiku", "limerick", "rap", "none")


# ---- parsing -------------------------------------------------------------------------
def kw_type(core, strict):
    c = core.strip().lower()
    for pat, typ in KEYWORDS:
        m = re.match(pat, c)
        if m:
            rest = c[m.end():]
            if strict and not re.fullmatch(r"\s*\d*\s*[a-z]?\s*(?:x\d+|\d+x)?\s*", rest):
                return None
            return typ
    return None


def label_info(line):
    s = line.strip()
    if not s:
        return None
    m = re.fullmatch(r"\[([^\]]{1,60})\]\s*:?", s)
    if m:
        core = m.group(1).strip()
        return core, kw_type(core, False) or "other"
    core = None
    for pat in (r"\(([^)]{1,60})\)\s*:?", r"#{1,4}\s*(.{1,60})", r"(.{1,40}?)\s*:"):
        m = re.fullmatch(pat, s)
        if m:
            core = m.group(1)
            break
    if core is None and len(s) <= 30:
        core = s
    if core:
        t = kw_type(core, True)
        if t:
            return core.strip(), t
    return None


def parse_draft(text):
    raw = text.splitlines()
    has_labels = any(label_info(ln) for ln in raw)
    sections = []
    cur = None
    for n, ln in enumerate(raw, 1):
        info = label_info(ln)
        if info:
            cur = {"label": info[0], "type": info[1], "start_line": n, "lines": []}
            sections.append(cur)
            continue
        if not ln.strip():
            if not has_labels:
                cur = None
            continue
        if cur is None:
            label = "(unlabelled)" if has_labels else "Block %d" % (len(sections) + 1)
            cur = {"label": label, "type": "stanza" if not has_labels else "other",
                   "start_line": n, "lines": []}
            sections.append(cur)
        cur["lines"].append({"n": n, "text": ln.strip()})
    last_chorus = None
    for i, s in enumerate(sections, 1):
        s["index"] = i
        s["repeat_of"] = None
        if s["type"] == "chorus" and not s["lines"] and last_chorus is not None:
            s["repeat_of"] = last_chorus
        if s["type"] == "chorus" and s["lines"]:
            last_chorus = i
    return sections


# ---- per-line analysis -----------------------------------------------------------------
def analyse_line(text, keep_paren, overrides, like):
    main = text if keep_paren else re.sub(r"\([^)]*\)", " ", text)
    if not re.search(r"[^\W_]", main):
        main = text
    toks = TOKEN_RE.findall(main)
    syl = 0
    unc = []
    unsupported = 0
    words = []
    for t in toks:
        n, u = token_syllables(t, overrides)
        if n == 0:
            unsupported += 1
            continue
        syl += n
        words.append(t)
        if u:
            unc.append(norm_token(t))
    end_word = words[-1] if words else None
    key = rhyme_key(end_word, like) if end_word and not end_word.isdigit() else None
    return {
        "syllables": syl, "words": words, "end_word": end_word, "key": key,
        "uncertain": unc, "unsupported": unsupported,
        "norm": " ".join(letters_only(w) for w in words if letters_only(w)),
    }


def word_norm(text):
    return [letters_only(t) for t in TOKEN_RE.findall(text) if letters_only(t)]


def group_scheme(items):
    """items: list of (end_word, key). Returns perfect_groups, slant_groups, relation list."""
    n = len(items)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        parent[find(i)] = find(j)

    rel = {}
    for i in range(n):
        for j in range(i + 1, n):
            if items[i][1] is None or items[j][1] is None:
                continue
            r = classify_pair(items[i][0], items[j][0], items[i][1], items[j][1])
            rel[(i, j)] = r
            if r in ("perfect", "identical"):
                union(i, j)
    perfect_root = [find(i) for i in range(n)]
    sizes = Counter(perfect_root)
    slant_parent = {r: r for r in set(perfect_root)}

    def sfind(r):
        while slant_parent[r] != r:
            slant_parent[r] = slant_parent[slant_parent[r]]
            r = slant_parent[r]
        return r

    for (i, j), r in rel.items():
        if r == "slant" and (sizes[perfect_root[i]] == 1 or sizes[perfect_root[j]] == 1):
            a, b = sfind(perfect_root[i]), sfind(perfect_root[j])
            if a != b:
                slant_parent[a] = b
    slant_root = [sfind(r) for r in perfect_root]
    return perfect_root, slant_root, rel


def letters(roots, keys):
    """Scheme string: letters by first appearance, X for a line that rhymes with nothing."""
    sizes = Counter(r for r, k in zip(roots, keys) if k is not None)
    out = []
    names = {}
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    for r, k in zip(roots, keys):
        if k is None:
            out.append("-")
        elif sizes[r] == 1:
            out.append("X")
        else:
            if r not in names:
                names[r] = alphabet[len(names)] if len(names) < len(alphabet) else "?"
            out.append(names[r])
    return "".join(out)


def stats(values):
    if not values:
        return {"mean": 0.0, "stdev": 0.0, "variance": 0.0, "min": 0, "max": 0, "median": 0.0}
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / len(values)
    return {"mean": round(mean, 2), "stdev": round(math.sqrt(var), 2), "variance": round(var, 2),
            "min": min(values), "max": max(values), "median": float(statistics.median(values))}


def meter_info(values):
    if len(values) < 3:
        return "n/a", None, None
    med = statistics.median(values)
    share = sum(1 for v in values if abs(v - med) <= 1) / len(values)
    if share >= REGULAR_SHARE_REGULAR:
        label = "regular"
    elif share >= REGULAR_SHARE_LOOSE:
        label = "loose"
    else:
        label = "irregular"
    hint = "median %s syllables, about %s feet if duple (syllable count only; stress not analysed)" % (
        ("%g" % med), ("%g" % round(med / 2, 1)))
    return label, round(share, 2), hint


def flag(flags, severity, code, message, section=None, line=None):
    flags.append({"severity": severity, "code": code, "section": section, "line": line,
                  "message": message})


# ---- form checks -----------------------------------------------------------------------
def scheme_fit(roots, pattern):
    """Share of multi-line pattern groups whose lines all fall in one detected group, and
    pattern groups that map to different detected groups."""
    groups = {}
    for i, ch in enumerate(pattern):
        groups.setdefault(ch, []).append(i)
    multi = {ch: idx for ch, idx in groups.items() if len(idx) > 1}
    if len(roots) != len(pattern) or not multi:
        return 0.0
    ok = 0
    used = []
    for ch, idx in multi.items():
        rs = {roots[i] for i in idx}
        if len(rs) == 1:
            ok += 1
            used.append(next(iter(rs)))
    distinct = len(set(used)) == len(used)
    return round(ok / len(multi), 2) if distinct else round((ok - 1) / len(multi), 2)


def check(name, expected, actual, ok):
    return {"name": name, "expected": expected, "actual": actual, "ok": bool(ok)}


def run_form(form, secs, all_lines, title, balance):
    """secs: analysed sections with lines; all_lines: analysed lines in order."""
    checks = []
    status = "pass"
    if form == "none":
        return {"form": form, "status": "not_requested", "checks": []}
    lyr = [s for s in secs if s["_lines"]]
    if form == "haiku":
        counts = [ln["syllables"] for ln in all_lines]
        checks.append(check("line_count", 3, len(counts), len(counts) == 3))
        exact = counts[:3] == [5, 7, 5]
        near = len(counts) == 3 and all(abs(c - t) <= 1 for c, t in zip(counts, (5, 7, 5)))
        checks.append(check("syllables_5_7_5", [5, 7, 5], counts, exact))
        if len(counts) != 3 or not (exact or near):
            status = "fail"
        elif not exact:
            status = "check"
    elif form == "limerick":
        counts = [ln["syllables"] for ln in all_lines]
        checks.append(check("line_count", 5, len(counts), len(counts) == 5))
        ok_scheme = False
        if len(all_lines) == 5:
            items = [(ln["end_word"], ln["key"]) for ln in all_lines]
            _, sroots, _ = group_scheme(items)
            fit = scheme_fit(sroots, "AABBA")
            ok_scheme = fit == 1.0
            checks.append(check("rhyme_AABBA", "AABBA", letters(sroots, [i[1] for i in items]), ok_scheme))
            rng = [(7, 10), (7, 10), (5, 7), (5, 7), (7, 10)]
            ok_len = all(lo <= c <= hi for c, (lo, hi) in zip(counts, rng))
            checks.append(check("syllables_7-10,7-10,5-7,5-7,7-10", [list(r) for r in rng], counts, ok_len))
            status = "pass" if (ok_scheme and ok_len) else ("check" if ok_scheme else "fail")
        else:
            status = "fail"
    elif form == "sonnet":
        counts = [ln["syllables"] for ln in all_lines]
        checks.append(check("line_count", 14, len(counts), len(counts) == 14))
        if len(all_lines) == 14:
            items = [(ln["end_word"], ln["key"]) for ln in all_lines]
            _, sroots, _ = group_scheme(items)
            fits = {
                "shakespearean ABABCDCDEFEFGG": scheme_fit(sroots, "ABABCDCDEFEFGG"),
                "petrarchan ABBAABBACDECDE": scheme_fit(sroots, "ABBAABBACDECDE"),
                "petrarchan ABBAABBACDCDCD": scheme_fit(sroots, "ABBAABBACDCDCD"),
            }
            best = max(fits, key=lambda k: fits[k])
            checks.append(check("rhyme_pattern_fit", "1.0 for one pattern", fits, fits[best] == 1.0))
            off = [i + 1 for i, c in enumerate(counts) if not 9 <= c <= 11]
            checks.append(check("lines_9-11_syllables", 0, off, not off))
            status = "pass" if (fits[best] == 1.0 and len(off) <= 2) else (
                "check" if fits[best] >= 0.7 else "fail")
        else:
            status = "fail"
    elif form == "ballad":
        if not lyr:
            status = "fail"
        worst = "pass"
        for s in lyr:
            lines = s["_lines"]
            cnt = [ln["syllables"] for ln in lines]
            four = len(lines) == 4
            checks.append(check("%s: four lines" % s["label"], 4, len(lines), four))
            if not four:
                worst = "fail"
                continue
            exact = cnt == [8, 6, 8, 6]
            near = all(abs(c - t) <= 1 for c, t in zip(cnt, (8, 6, 8, 6)))
            checks.append(check("%s: syllables 8-6-8-6" % s["label"], [8, 6, 8, 6], cnt, exact))
            r24 = classify_pair(lines[1]["end_word"], lines[3]["end_word"], lines[1]["key"], lines[3]["key"])
            ok24 = r24 in ("perfect", "identical", "slant")
            checks.append(check("%s: lines 2 and 4 rhyme" % s["label"], True, r24, ok24))
            if not ok24 or not near:
                worst = "fail"
            elif not exact and worst == "pass":
                worst = "check"
        status = worst
    elif form == "aaba":
        body = [s for s in lyr if s["type"] not in ("intro", "outro", "other")]
        checks.append(check("section_count", 4, len(body), len(body) == 4))
        if len(body) == 4:
            a_lines = [len(body[i]["_lines"]) for i in (0, 1, 3)]
            checks.append(check("A sections equal length", "equal", a_lines, len(set(a_lines)) == 1))
            sch = [body[i]["scheme_slant"] for i in range(4)]
            same = sch[0] == sch[1] == sch[3]
            checks.append(check("A sections share a rhyme scheme", "equal", [sch[0], sch[1], sch[3]], same))
            b_ok = body[2]["type"] == "bridge" or sch[2] != sch[0]
            checks.append(check("B section is a bridge or differs", True, body[2]["label"], b_ok))
            if title:
                tn = word_norm(title)
                refr = [find_phrase(body[i]["_lines"][-1]["norm"].split(), tn) > 0 for i in (0, 1, 3)]
                checks.append(check("title in last line of each A", [True, True, True], refr, all(refr)))
            bad = [c for c in checks if not c["ok"]]
            status = "pass" if not bad else ("check" if len(bad) == 1 else "fail")
        else:
            status = "fail"
    elif form == "rap":
        verses = [s for s in lyr if s["type"] in ("verse", "stanza")]
        checks.append(check("has_verses", ">=1", len(verses), len(verses) >= 1))
        sev = "pass" if verses else "fail"
        for s in verses:
            n = len(s["_lines"])
            checks.append(check("%s: bars 8-16" % s["label"], [8, 16], n, 8 <= n <= 16))
            if not 8 <= n <= 16 and sev == "pass":
                sev = "check"
            cov = s["rhyme_coverage"]
            checks.append(check("%s: end-rhyme coverage >= 0.6" % s["label"], 0.6, cov, cov >= 0.6))
            if cov < 0.6 and sev == "pass":
                sev = "check"
            mean = s["syllable_stats"]["mean"]
            checks.append(check("%s: mean syllables per bar 8-16" % s["label"], [8, 16], mean, 8 <= mean <= 16))
            if not 8 <= mean <= 16 and sev == "pass":
                sev = "check"
        status = sev
    else:  # verse-chorus
        types = [s["type"] for s in lyr]
        checks.append(check("has_verse", True, "verse" in types, "verse" in types))
        checks.append(check("has_chorus", True, "chorus" in types, "chorus" in types))
        reps = balance["chorus_occurrences"]
        checks.append(check("chorus_occurs_at_least_twice", 2, reps, reps >= 2))
        lb = balance["lines_before_first_chorus"]
        checks.append(check("first_chorus_within_%d_lines" % FIRST_CHORUS_MAX_LINES,
                            FIRST_CHORUS_MAX_LINES, lb, lb is not None and lb <= FIRST_CHORUS_MAX_LINES))
        hard = []
        for s in lyr:
            rng = LENGTHS.get(s["type"])
            if rng and not (rng[0] <= len(s["_lines"]) <= rng[1]):
                hard.append("%s=%d" % (s["label"], len(s["_lines"])))
        checks.append(check("section_lengths_in_ideal_range", "none outside", hard, not hard))
        bad = [c for c in checks if not c["ok"]]
        status = "pass" if not bad else ("fail" if len(bad) >= 3 else "check")
    return {"form": form, "status": status, "checks": checks}


def find_phrase(words, phrase):
    """Count occurrences of the word list 'phrase' inside the word list 'words'."""
    if not phrase or len(phrase) > len(words):
        return 0
    return sum(1 for i in range(len(words) - len(phrase) + 1) if words[i:i + len(phrase)] == phrase)


# ---- main analysis -----------------------------------------------------------------------
def load_overrides(path):
    if not path:
        return {}, {}
    try:
        with open(path, encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        raise SystemExit("error: cannot read overrides file %s: %s" % (path, exc))
    syl = {}
    for k, v in (data.get("syllables") or {}).items():
        if isinstance(v, int) and v >= 0:
            syl[letters_only(k)] = v
    like = {letters_only(k): letters_only(v) for k, v in (data.get("rhyme_like") or {}).items()}
    return syl, like


def read_text(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise SystemExit("error: cannot read %s: %s" % (path, exc))
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    if not text.strip():
        raise SystemExit("error: %s is empty" % path)
    return text


def compare_overlap(draft_lines, other_text, min_ngram, name):
    dwords = []
    dline = []
    for ln in draft_lines:
        for w in word_norm(ln["text"]):
            dwords.append(w)
            dline.append(ln["n"])
    owords = word_norm(other_text)
    index = {}
    for j in range(len(owords) - min_ngram + 1):
        index.setdefault(tuple(owords[j:j + min_ngram]), []).append(j)
    runs = []
    i = 0
    longest = 0
    while i <= len(dwords) - min_ngram:
        best = 0
        for j in index.get(tuple(dwords[i:i + min_ngram]), []):
            k = 0
            while i + k < len(dwords) and j + k < len(owords) and dwords[i + k] == owords[j + k]:
                k += 1
            best = max(best, k)
        if best:
            longest = max(longest, best)
            if len(runs) < MAX_LIST:
                runs.append({"words": best, "text": " ".join(dwords[i:i + min(best, 20)]),
                             "draft_line": dline[i]})
            i += best
        else:
            i += 1
    return {"file": os.path.basename(name), "min_ngram": min_ngram, "longest_shared_run": longest,
            "shared_runs": runs, "status": "shared_runs_found" if runs else "none_found"}


def dominant_scheme(lyr):
    """Most common with-slant scheme among verse/stanza sections of 4+ lines (any type if none)."""
    pool = [s for s in lyr if s["type"] in ("verse", "stanza") and len(s["_lines"]) >= 4]
    pool = pool or [s for s in lyr if len(s["_lines"]) >= 4]
    top = Counter(s["scheme_slant"] for s in pool).most_common(1)
    return top[0][0] if top else None


def audit(text, form, title, overrides, like, keep_paren, with_lines, compare):
    sections = parse_draft(text)
    flags = []
    all_lines = []
    syl_over, _ = overrides, None
    uncertain_all = Counter()
    unsupported = 0
    # analyse every line
    for s in sections:
        s["_lines"] = []
        for ln in s["lines"]:
            a = analyse_line(ln["text"], keep_paren, syl_over, like)
            a["n"] = ln["n"]
            a["text"] = ln["text"]
            a["section"] = s["label"]
            s["_lines"].append(a)
            all_lines.append(a)
            uncertain_all.update(a["uncertain"])
            unsupported += a["unsupported"]
    # repeats expand to the source chorus lines for consistency checks
    by_index = {s["index"]: s for s in sections}
    total_lines = len(all_lines)
    if total_lines < MIN_LINES_RELIABLE:
        flag(flags, "info", "short_text", "only %d lyric lines; statistics are noisy" % total_lines)
    if unsupported:
        flag(flags, "info", "non_latin_text",
             "%d token(s) have no Latin letters or digits and were skipped (English/Latin only)" % unsupported)

    out_sections = []
    for s in sections:
        lines = s["_lines"]
        counts = [a["syllables"] for a in lines]
        st = stats(counts)
        s["syllable_stats"] = st
        label, share, hint = meter_info(counts)
        items = [(a["end_word"], a["key"]) for a in lines]
        proots, sroots, rel = group_scheme(items)
        keys = [a["key"] for a in lines]
        scheme = letters(proots, keys)
        scheme_slant = letters(sroots, keys)
        s["scheme"], s["scheme_slant"] = scheme, scheme_slant
        s["sroots"], s["proots"] = sroots, proots
        rhymed = sum(1 for c in scheme_slant if c not in "X-")
        s["rhyme_coverage"] = round(rhymed / len(lines), 2) if lines else 0.0
        n_perfect = sum(1 for r in rel.values() if r == "perfect")
        n_ident = sum(1 for r in rel.values() if r == "identical")
        n_slant = sum(1 for r in rel.values() if r == "slant")
        # internal rhyme
        internal = []
        for a in lines:
            ws = [w for w in a["words"] if len(letters_only(w)) >= 3 and letters_only(w) not in STOP]
            for x in range(len(ws)):
                for y in range(x + 1, len(ws)):
                    wx, wy = letters_only(ws[x]), letters_only(ws[y])
                    if wx == wy:
                        continue
                    kx, ky = rhyme_key(wx, like), rhyme_key(wy, like)
                    if kx is not None and kx == ky:
                        internal.append({"line": a["n"], "words": [wx, wy]})
        internal_capped = internal[:MAX_LIST]
        # predictable rhyme pairs
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                wi, wj = letters_only(lines[i]["end_word"] or ""), letters_only(lines[j]["end_word"] or "")
                hit = bool(wi and wj) and (
                    frozenset((wi, wj)) in PREDICTABLE_PAIRS
                    or frozenset((wi.rstrip("s"), wj.rstrip("s"))) in PREDICTABLE_PAIRS)
                if hit:
                    flag(flags, "info", "predictable_rhyme",
                         "%s/%s is a very common rhyme pair; keep it only with a fresh image or twist"
                         % (wi, wj), s["label"], lines[j]["n"])
        sec_out = {
            "index": s["index"], "label": s["label"], "type": s["type"],
            "start_line": s["start_line"], "repeat_of": s["repeat_of"], "lines": len(lines),
            "line_numbers": [a["n"] for a in lines], "syllables_per_line": counts,
            "syllable_mean": st["mean"], "syllable_stdev": st["stdev"],
            "syllable_variance": st["variance"], "syllable_min": st["min"], "syllable_max": st["max"],
            "meter_regularity": label, "regular_share": share, "meter_hint": hint,
            "end_words": [letters_only(a["end_word"]) if a["end_word"] else None for a in lines],
            "rhyme_scheme": scheme, "rhyme_scheme_with_slant": scheme_slant,
            "rhyme_coverage": s["rhyme_coverage"],
            "rhyme_types": {"perfect": n_perfect, "identical": n_ident, "slant": n_slant,
                            "internal": len(internal)},
            "internal_rhymes": internal_capped,
        }
        if with_lines:
            sec_out["line_details"] = [
                {"n": a["n"], "text": a["text"], "syllables": a["syllables"],
                 "end_word": a["end_word"],
                 "rhyme_key": list(a["key"]) if a["key"] else None,
                 "uncertain_words": a["uncertain"]} for a in lines]
        out_sections.append(sec_out)
        if not lines and not s["repeat_of"] and s["type"] != "other":
            flag(flags, "info", "empty_section", "section has a label but no lines", s["label"], s["start_line"])
        # per-section flags
        typ = s["type"]
        if lines and typ in ("verse", "chorus", "stanza", "pre-chorus", "bridge") and len(lines) >= 3:
            limit = STDEV_WARN_RAP if form == "rap" else STDEV_WARN
            if form not in ("none", "haiku", "limerick") and st["stdev"] > limit:
                flag(flags, "warn", "line_length_uneven",
                     "syllable stdev %.2f exceeds %.1f (range %d-%d)" % (st["stdev"], limit, st["min"], st["max"]),
                     s["label"], s["start_line"])
        rng = LENGTHS.get(typ)
        if rng and lines:
            n = len(lines)
            if not rng[2] <= n <= rng[3]:
                flag(flags, "warn", "section_length", "%d lines is outside %d-%d for a %s" % (n, rng[2], rng[3], typ),
                     s["label"], s["start_line"])
            elif not rng[0] <= n <= rng[1]:
                flag(flags, "info", "section_length_unusual",
                     "%d lines; usual range for a %s is %d-%d" % (n, typ, rng[0], rng[1]), s["label"], s["start_line"])
        if len(lines) >= 4 and typ in ("verse", "chorus", "stanza") and form not in ("none", "haiku") \
                and scheme_slant.count("X") + scheme_slant.count("-") == len(scheme_slant):
            flag(flags, "warn" if form in ("rap", "verse-chorus", "ballad", "limerick", "sonnet") else "info",
                 "no_end_rhyme", "no end rhyme found (heuristic); fine for free verse, check otherwise",
                 s["label"], s["start_line"])
        if n_ident:
            flag(flags, "info", "identical_rhyme", "%d line pair(s) rhyme by repeating the same word" % n_ident,
                 s["label"], s["start_line"])
        # same line repeated 3+ times inside one section
        cnt = Counter(a["norm"] for a in lines if a["norm"])
        for norm, c in cnt.items():
            if c >= 3 and typ != "chorus":
                flag(flags, "info", "line_repeated_in_section",
                     "one line appears %d times (intended refrain?)" % c, s["label"], s["start_line"])

    lyr = [s for s in sections if s["_lines"]]
    # ---- repeated lines and hook ----
    line_where = {}
    for s in sections:
        for a in s["_lines"]:
            if a["norm"]:
                line_where.setdefault(a["norm"], []).append((s["label"], a["n"]))
    repeated = []
    for norm, w in sorted(line_where.items(), key=lambda kv: -len(kv[1])):
        if len(w) >= 2:
            repeated.append({"text": norm, "count": len(w), "sections": sorted({x[0] for x in w}),
                             "lines": [x[1] for x in w][:MAX_LIST]})
    ngram = Counter()
    for a in all_lines:
        ws = a["norm"].split()
        for k in (3, 4):
            for i in range(len(ws) - k + 1):
                g = ws[i:i + k]
                if any(w not in STOP for w in g):
                    ngram[" ".join(g)] += 1
    phr = [{"text": g, "count": c} for g, c in ngram.most_common(40) if c >= 3
           and not any(g in r["text"] for r in repeated)][:5]

    choruses = [s for s in sections if s["type"] == "chorus"]
    chorus_src = [(s, by_index[s["repeat_of"]] if s["repeat_of"] else s) for s in choruses]
    hook = {"source": "none", "phrase": None, "per_chorus_counts": [], "target_range": list(HOOK_RANGE),
            "status": "no_chorus" if not choruses else "no_hook"}
    phrase_words = None
    if title:
        phrase_words = word_norm(title)
        hook["source"] = "title"
        hook["phrase"] = " ".join(phrase_words)
    else:
        pool = Counter()
        for s, src in chorus_src:
            for a in src["_lines"]:
                if a["norm"]:
                    pool[a["norm"]] += 1
        cand = [x for x in pool.most_common() if x[1] >= 2]
        if cand:
            phrase_words = cand[0][0].split()
            hook["source"] = "most_repeated_chorus_line"
            hook["phrase"] = cand[0][0]
        elif repeated:
            phrase_words = repeated[0]["text"].split()
            hook["source"] = "most_repeated_line"
            hook["phrase"] = repeated[0]["text"]
    if phrase_words and chorus_src:
        counts = []
        for s, src in chorus_src:
            words = []
            for a in src["_lines"]:
                words.extend(a["norm"].split())
            counts.append(find_phrase(words, phrase_words))
        hook["per_chorus_counts"] = counts
        if any(c == 0 for c in counts):
            hook["status"] = "missing_in_a_chorus"
            flag(flags, "warn", "hook_missing_in_chorus",
                 "hook phrase '%s' is absent from at least one chorus" % hook["phrase"])
        elif any(c < HOOK_RANGE[0] for c in counts):
            hook["status"] = "light"
            flag(flags, "warn" if hook["source"] == "title" else "info", "hook_repetition_low",
                 "hook phrase '%s' appears %s time(s) per chorus; target %d-%d"
                 % (hook["phrase"], sorted(set(counts)), HOOK_RANGE[0], HOOK_RANGE[1]))
        elif any(c > HOOK_RANGE[1] for c in counts):
            hook["status"] = "heavy"
            flag(flags, "info", "hook_repetition_high",
                 "hook phrase '%s' appears up to %d times in a chorus; target %d-%d"
                 % (hook["phrase"], max(counts), HOOK_RANGE[0], HOOK_RANGE[1]))
        else:
            hook["status"] = "in_range"
    elif phrase_words and not chorus_src:
        hook["status"] = "no_chorus"

    # ---- chorus consistency ----
    cons = {"occurrences": len(choruses), "status": "none", "similarity_to_first": [], "differing_lines": []}
    if choruses:
        first_src = chorus_src[0][1]
        base = [a["norm"] for a in first_src["_lines"]]
        cons["occurrences"] = len(choruses)
        cons["status"] = "single"
        sims = []
        for s, src in chorus_src[1:]:
            other = [a["norm"] for a in src["_lines"]]
            ratio = difflib.SequenceMatcher(None, base, other).ratio()
            sims.append(round(ratio, 2))
            if ratio < 1.0:
                diff = [x for x in other if x not in base][:MAX_LIST]
                cons["differing_lines"].append({"section": s["label"], "new_lines": diff})
                if ratio >= DRIFT_LOW:
                    flag(flags, "warn", "chorus_drift",
                         "chorus differs from the first (similarity %.2f); accidental edits?" % ratio,
                         s["label"], s["start_line"])
                else:
                    flag(flags, "info", "chorus_dissimilar",
                         "labelled chorus shares little with the first (similarity %.2f); a new section?" % ratio,
                         s["label"], s["start_line"])
        cons["similarity_to_first"] = sims
        if sims:
            cons["status"] = "identical" if all(x == 1.0 for x in sims) else "differs"
        elif len(choruses) == 1 and form == "verse-chorus":
            flag(flags, "info", "chorus_once", "the chorus appears only once")
    elif form == "verse-chorus" and lyr:
        flag(flags, "warn", "no_chorus", "no section is labelled chorus/hook/refrain")

    # ---- balance ----
    verse_lens = [len(s["_lines"]) for s in lyr if s["type"] == "verse"]
    if len(verse_lens) >= 2 and max(verse_lens) - min(verse_lens) >= VERSE_UNEVEN_DIFF:
        flag(flags, "warn", "verse_length_mismatch", "verse lengths %s differ by %d or more lines"
             % (verse_lens, VERSE_UNEVEN_DIFF))
    vs = [s["scheme_slant"] for s in lyr if s["type"] == "verse" and len(s["_lines"]) >= 4]
    if len(set(vs)) > 1:
        flag(flags, "info", "verse_schemes_differ", "verses use different rhyme schemes: %s" % sorted(set(vs)))
    lines_before = None
    running = 0
    for s in sections:
        if s["type"] == "chorus" and (s["_lines"] or s["repeat_of"]):
            lines_before = running
            break
        running += len(s["_lines"])
    if lines_before is not None and lines_before > FIRST_CHORUS_MAX_LINES:
        flag(flags, "warn", "first_chorus_late", "%d lyric lines before the first chorus (limit %d)"
             % (lines_before, FIRST_CHORUS_MAX_LINES))
    first_bridge = next((s for s in sections if s["type"] == "bridge"), None)
    if first_bridge and choruses and first_bridge["index"] < choruses[0]["index"]:
        flag(flags, "info", "bridge_before_chorus", "the bridge comes before any chorus", first_bridge["label"],
             first_bridge["start_line"])
    balance = {
        "lines_by_type": dict(Counter(a for s in lyr for a in [s["type"]] * len(s["_lines"]))),
        "verse_line_counts": verse_lens,
        "chorus_occurrences": len(choruses),
        "lines_before_first_chorus": lines_before,
    }

    # ---- clichés ----
    cl_hits = []
    cl_norm = [(c, " " + " ".join(word_norm(c)) + " ") for c in CLICHES]
    for s in sections:
        ls = s["_lines"]
        for i, a in enumerate(ls):
            text = " " + a["norm"] + " "
            joined = text + (ls[i + 1]["norm"] + " " if i + 1 < len(ls) else "")
            for c, cn in cl_norm:
                if cn in text or (cn in joined and cn not in " " + (ls[i + 1]["norm"] if i + 1 < len(ls) else "") + " "):
                    cl_hits.append({"phrase": c, "line": a["n"], "section": s["label"]})
    seen = set()
    uniq = []
    for h in cl_hits:
        k = (h["phrase"], h["line"])
        if k not in seen:
            seen.add(k)
            uniq.append(h)
    if total_lines and len(uniq) / total_lines > CLICHE_DENSITY:
        flag(flags, "warn", "cliche_density", "%d stock phrases in %d lines (more than 1 per 8)" % (len(uniq), total_lines))
    for h in uniq[:MAX_LIST]:
        flag(flags, "info", "cliche", "stock phrase '%s'" % h["phrase"], h["section"], h["line"])

    # ---- uncertain syllables ----
    unc_lines = sum(1 for a in all_lines if a["uncertain"])
    if total_lines and unc_lines / total_lines >= UNCERTAIN_SHARE:
        flag(flags, "info", "syllable_uncertainty",
             "%d of %d lines contain words whose syllable count is uncertain; add --overrides" % (unc_lines, total_lines))

    form_check = run_form(form, lyr, all_lines, title, balance)
    if form_check["status"] in ("check", "fail"):
        flag(flags, "warn", "form_" + form_check["status"], "%s check status: %s" % (form, form_check["status"]))

    # ---- originality block ----
    cand = []
    seen_n = set()
    def add_c(text, ln, why):
        n = " ".join(word_norm(text))
        if n and n not in seen_n and len(n.split()) >= SEARCH_MIN_WORDS:
            seen_n.add(n)
            cand.append({"phrase": text.strip(), "line": ln, "why": why})
    if hook["phrase"] and hook["source"] != "title":
        for a in all_lines:
            if a["norm"] == hook["phrase"]:
                add_c(a["text"], a["n"], "hook line")
                break
    for s, src in chorus_src:
        if src["_lines"]:
            add_c(src["_lines"][0]["text"], src["_lines"][0]["n"], "first chorus line")
            break
    cl_lines = {h["line"] for h in uniq}
    for a in sorted(all_lines, key=lambda a: -len(a["words"])):
        if a["n"] not in cl_lines:
            add_c(a["text"], a["n"], "longest distinctive line")
        if len(cand) >= SEARCH_LIST_MAX:
            break
    if title:
        cand.insert(0, {"phrase": title.strip(), "line": None, "why": "title or hook (search it even when short)"})
    originality = {
        "scope": "this script cannot know whether a line copies a published song or poem",
        "search_list": cand[:SEARCH_LIST_MAX],
        "how_to_use": "search each phrase in quotation marks with a web search or a lyrics-site search; "
                      "a hit of 5 or more consecutive words in someone else's work means rewrite the line",
        "compare": compare,
    }

    uncertain_list = [{"word": w, "count": c} for w, c in uncertain_all.most_common(MAX_LIST * 2)]
    report = {
        "schema_version": SCHEMA_VERSION,
        "tool": "audit_lyrics",
        "form": form,
        "title": title,
        "syllable_method": SYLLABLE_METHOD,
        "totals": {"lines": total_lines, "words": sum(len(a["words"]) for a in all_lines),
                   "syllables": sum(a["syllables"] for a in all_lines), "sections": len(sections)},
        "sections": out_sections,
        "rhyme_scheme": {
            "by_section": [{"section": s["label"], "scheme": s["scheme"], "with_slant": s["scheme_slant"]}
                           for s in sections if s["_lines"]],
            "dominant": dominant_scheme(lyr),
            "legend": "same letter = lines rhyme; X = rhymes with nothing found; with_slant also links near rhymes",
        },
        "repeats": {"repeated_lines": repeated[:MAX_LIST], "repeated_phrases": phr, "hook": hook},
        "chorus_consistency": cons,
        "section_balance": balance,
        "cliches": uniq[:MAX_LIST * 3],
        "form_check": form_check,
        "originality": originality,
        "uncertain_words": uncertain_list,
        "flags": flags,
        "limits": [
            "English only; syllables, rhyme and meter are spelling-based heuristics",
            "meter regularity uses syllable counts; stress is not analysed",
            "rhyme keys over-match words with unstressed endings (baby/lady) and miss irregular spellings",
            "cliche and predictable-rhyme lists are fixed and partial",
            "originality search list is for a human or search tool; the script checks nothing against published work",
        ],
    }
    return report


def build_parser():
    p = argparse.ArgumentParser(description="Audit an original lyric or poem draft; prints strict JSON.")
    p.add_argument("file", nargs="?", help="text file with the draft")
    p.add_argument("--form", default="none", choices=FORMS)
    p.add_argument("--title", default=None, help="title or hook phrase to count in each chorus")
    p.add_argument("--overrides", default=None, help="JSON file with syllables and rhyme_like maps")
    p.add_argument("--compare", default=None, help="a text file you supply to check for shared word runs")
    p.add_argument("--min-ngram", type=int, default=5, help="shortest shared run reported (default 5)")
    p.add_argument("--keep-parentheses", action="store_true", help="count text in parentheses")
    p.add_argument("--lines", action="store_true", help="include per-line details in the report")
    p.add_argument("--list-cliches", action="store_true", help="print the bundled stock phrase list and exit")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    if args.list_cliches:
        print(json.dumps({"cliches": list(CLICHES), "predictable_rhyme_pairs":
                          sorted(sorted(p) for p in PREDICTABLE_PAIRS)}, indent=2, ensure_ascii=False,
                         allow_nan=False))
        return 0
    if not args.file:
        raise SystemExit("error: give a draft file, e.g. python scripts/audit_lyrics.py draft.txt --form verse-chorus")
    if args.min_ngram < 3:
        raise SystemExit("error: --min-ngram must be 3 or more")
    text = read_text(args.file)
    syl_over, like = load_overrides(args.overrides)
    compare = None
    if args.compare:
        other = read_text(args.compare)
        parsed = parse_draft(text)
        flat = [ln for s in parsed for ln in s["lines"]]
        compare = compare_overlap(flat, other, args.min_ngram, args.compare)
    report = audit(text, args.form, args.title, syl_over, like, args.keep_parentheses, args.lines, compare)
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as exc:
        if isinstance(exc.code, str):
            sys.stderr.write(exc.code + "\n")
            sys.exit(2)
        raise
