#!/usr/bin/env python3
"""Check a story outline (outline.json) for structural and continuity defects.

Usage:
    python check_outline.py check outline.json     validate and report defects
    python check_outline.py budget <structure> <word_target>
                                                   print per-beat word budgets
    python check_outline.py structures             list structure templates

Reads only the file named on the command line. Writes JSON to stdout and
nothing to disk. Standard library only, no network.

Exit codes: 0 no error-level defects, 1 one or more error-level defects,
2 usage problem or a file that is not strict JSON (message on stderr).

The outline is strict JSON: duplicate keys, NaN and Infinity are rejected, and
unknown fields are reported as SCHEMA defects. The checks are mechanical. They
find missing fields, drift and broken references; they cannot judge whether a
scene is any good. Full field list: references/outline_schema.md.
"""
import datetime
import json
import os
import sys

# Beat templates: (beat name, span start %, span end %) of the word target.
# A beat's first scene is the turn the beat is named for; the rest of the span
# is its fallout. Spans are working values for planning, not laws of fiction.
TEMPLATES = {
    "three-act": [
        ("hook", 0, 10), ("inciting_incident", 10, 25), ("first_plot_point", 25, 50),
        ("midpoint", 50, 75), ("second_plot_point", 75, 90), ("climax", 90, 98),
        ("resolution", 98, 100),
    ],
    "save-the-cat": [
        ("opening_image", 0, 2), ("setup", 2, 10), ("catalyst", 10, 20),
        ("break_into_two", 20, 25), ("fun_and_games", 25, 50), ("midpoint", 50, 55),
        ("bad_guys_close_in", 55, 75), ("all_is_lost", 75, 80), ("break_into_three", 80, 85),
        ("finale", 85, 98), ("final_image", 98, 100),
    ],
    "heros-journey": [
        ("ordinary_world", 0, 8), ("call_to_adventure", 8, 15), ("refusal", 15, 20),
        ("meeting_mentor", 20, 25), ("crossing_threshold", 25, 30),
        ("tests_allies_enemies", 30, 45), ("approach", 45, 50), ("ordeal", 50, 60),
        ("reward", 60, 70), ("road_back", 70, 80), ("resurrection", 80, 95),
        ("return_with_elixir", 95, 100),
    ],
    "seven-point": [
        ("hook", 0, 25), ("plot_turn_1", 25, 37), ("pinch_1", 37, 50), ("midpoint", 50, 62),
        ("pinch_2", 62, 75), ("plot_turn_2", 75, 88), ("resolution", 88, 100),
    ],
}

BEAT_DRIFT_POINTS = 10      # first scene of a beat may start this far (in % points) from the span start
BUDGET_LOW = 0.5            # planned words under half the budget: beat is thin
BUDGET_HIGH = 1.5           # over one and a half times the budget: beat is bloated
TARGET_TOLERANCE = 0.15     # planned total may differ from the word target by this share
MIDDLE_THIRD = (100 / 3.0, 200 / 3.0)   # scene centre inside this band is "middle third"
SUCCESS_RUN = 3             # this many "yes" outcomes in a row means no real opposition
VANISH_BELOW_PCT = 75.0     # a major character whose last scene centre is before this has dropped out
ARC_MIN_TURNS_PROTAGONIST = 2   # a protagonist arc needs at least a midpoint and a late turn
MAJOR_ROLES = {"protagonist", "antagonist", "ally", "mentor", "love_interest"}
ROLES = MAJOR_ROLES | {"minor"}
TENSES = {"past", "present", "future"}
PERSONS = {"first", "second", "third"}
POV_MODES = {"single", "multiple", "omniscient"}
OUTCOME_TYPES = {"yes", "no", "yes-but", "no-and"}
EMPTY_WORDS = {"", "none", "n/a", "na", "-", "tbd", "todo", "?", "unknown"}

TOP_FIELDS = {"title", "structure", "word_target", "pov_mode", "tense", "person",
              "characters", "scenes", "setups"}
SCENE_FIELDS = {"id", "chapter", "beat", "pov", "tense", "person", "goal", "conflict", "outcome",
                "outcome_type", "change", "stakes_change", "date", "location", "characters",
                "words", "requires", "plants", "pays_off", "flashback", "pov_marked",
                "tense_marked"}
CHAR_FIELDS = {"id", "name", "role", "introduced_in", "exit_scene", "dies_on", "arc"}
ARC_FIELDS = {"want", "need", "turning_points", "end_state"}


class Strict(Exception):
    pass


def _no_dupes(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise Strict("duplicate key %r" % k)
        out[k] = v
    return out


def _bad_const(name):
    raise Strict("%s is not valid JSON" % name)


def load_strict(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise Strict("cannot read %s: %s" % (path, exc.strerror or exc))
    if not raw.strip():
        raise Strict("%s is empty" % path)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise Strict("%s is not UTF-8; save it as UTF-8" % path)
    try:
        return json.loads(text, object_pairs_hook=_no_dupes, parse_constant=_bad_const)
    except json.JSONDecodeError as exc:
        raise Strict("%s is not valid JSON (line %d, column %d): %s" % (path, exc.lineno, exc.colno, exc.msg))


def norm(value):
    return value.strip().lower() if isinstance(value, str) else ""


def is_empty(value):
    return not isinstance(value, str) or norm(value) in EMPTY_WORDS


def parse_date(value):
    """ISO date or date-time without a timezone suffix; None when invalid."""
    if not isinstance(value, str):
        return None
    try:
        if len(value) == 10:
            return datetime.datetime.combine(datetime.date.fromisoformat(value), datetime.time())
        return datetime.datetime.fromisoformat(value)
    except ValueError:
        return None


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def is_strlist(value):
    return isinstance(value, list) and all(isinstance(v, str) and v for v in value)


def budgets(structure, word_target):
    rows = []
    for name, start, end in TEMPLATES[structure]:
        rows.append({"beat": name, "span_pct": [start, end],
                     "budget_words": int(round(word_target * (end - start) / 100.0))})
    return rows


class Report:
    def __init__(self):
        self.defects = []

    def add(self, code, severity, scene_id, message, fix, ref=None):
        self.defects.append({"code": code, "severity": severity, "scene_id": scene_id,
                             "ref": ref, "message": message, "fix": fix})


def check_schema(doc, rep):
    """Returns True when the outline is sound enough for the content checks."""
    if not isinstance(doc, dict):
        rep.add("SCHEMA", "error", None, "top level must be a JSON object", "wrap the outline in { }")
        return False
    fatal = False
    for key in sorted(set(doc) - TOP_FIELDS):
        rep.add("SCHEMA", "error", None, "unknown top-level field %r" % key, "remove it or check the spelling", key)
    if doc.get("structure") not in TEMPLATES:
        rep.add("SCHEMA", "error", None, "structure must be one of %s" % ", ".join(sorted(TEMPLATES)),
                "set \"structure\" to one of the listed names", "structure")
        fatal = True
    if not is_int(doc.get("word_target")) or doc.get("word_target", 0) <= 0:
        rep.add("SCHEMA", "error", None, "word_target must be a positive whole number", "set the planned length in words", "word_target")
        fatal = True
    if doc.get("tense") not in TENSES:
        rep.add("SCHEMA", "error", None, "tense must be one of past, present, future", "set the narrative tense", "tense")
        fatal = True
    if "person" in doc and doc["person"] not in PERSONS:
        rep.add("SCHEMA", "error", None, "person must be first, second or third", "fix or remove it", "person")
    if "pov_mode" in doc and doc["pov_mode"] not in POV_MODES:
        rep.add("SCHEMA", "error", None, "pov_mode must be single, multiple or omniscient", "fix or remove it", "pov_mode")
        fatal = True
    if "title" in doc and not isinstance(doc["title"], str):
        rep.add("SCHEMA", "error", None, "title must be a string", "fix it", "title")
    if not isinstance(doc.get("scenes"), list) or not doc.get("scenes"):
        rep.add("SCHEMA", "error", None, "scenes must be a non-empty list", "add scene objects", "scenes")
        fatal = True
    if not isinstance(doc.get("characters"), list):
        rep.add("SCHEMA", "error", None, "characters must be a list", "add character objects (it may be empty only for omniscient pieces)", "characters")
        fatal = True
    if "setups" in doc and not (isinstance(doc["setups"], list) and all(
            isinstance(s, dict) and isinstance(s.get("id"), str) for s in doc["setups"])):
        rep.add("SCHEMA", "error", None, "setups must be a list of objects with a string id", "fix it", "setups")
    if fatal:
        return False

    char_ids = set()
    for ch in doc["characters"]:
        if not isinstance(ch, dict) or not isinstance(ch.get("id"), str) or not ch.get("id"):
            rep.add("SCHEMA", "error", None, "every character needs a string id", "add an id", "characters")
            fatal = True
            continue
        cid = ch["id"]
        if cid in char_ids:
            rep.add("SCHEMA", "error", None, "duplicate character id %r" % cid, "make ids unique", cid)
        char_ids.add(cid)
        for key in sorted(set(ch) - CHAR_FIELDS):
            rep.add("SCHEMA", "error", None, "character %s: unknown field %r" % (cid, key), "remove it", cid)
        if ch.get("role") not in ROLES:
            rep.add("SCHEMA", "error", None, "character %s: role must be one of %s" % (cid, ", ".join(sorted(ROLES))), "set a role", cid)
        if "dies_on" in ch and parse_date(ch["dies_on"]) is None:
            rep.add("SCHEMA", "error", None, "character %s: dies_on must be YYYY-MM-DD or YYYY-MM-DDTHH:MM" % cid, "fix the date", cid)
        arc = ch.get("arc")
        if arc is not None:
            if not isinstance(arc, dict):
                rep.add("SCHEMA", "error", None, "character %s: arc must be an object" % cid, "fix it", cid)
            else:
                for key in sorted(set(arc) - ARC_FIELDS):
                    rep.add("SCHEMA", "error", None, "character %s: unknown arc field %r" % (cid, key), "remove it", cid)
                if "turning_points" in arc and not is_strlist(arc["turning_points"]):
                    rep.add("SCHEMA", "error", None, "character %s: turning_points must be a list of scene ids" % cid, "fix it", cid)

    seen = set()
    for i, sc in enumerate(doc["scenes"]):
        where = "scene #%d" % (i + 1)
        if not isinstance(sc, dict) or not isinstance(sc.get("id"), str) or not sc.get("id"):
            rep.add("SCHEMA", "error", None, "%s needs a string id" % where, "add an id", "scenes")
            fatal = True
            continue
        sid = sc["id"]
        if sid in seen:
            rep.add("DUPLICATE_SCENE_ID", "error", sid, "scene id %r is used more than once" % sid, "make scene ids unique")
            fatal = True
        seen.add(sid)
        for key in sorted(set(sc) - SCENE_FIELDS):
            rep.add("SCHEMA", "error", sid, "unknown scene field %r" % key, "remove it or check the spelling", key)
        if not isinstance(sc.get("beat"), str) or not sc.get("beat"):
            rep.add("SCHEMA", "error", sid, "scene needs a beat (a beat name from the structure)", "assign the scene to a beat", "beat")
        for key in ("pov", "tense", "person", "goal", "conflict", "outcome", "location", "date"):
            if key in sc and not isinstance(sc[key], str):
                rep.add("SCHEMA", "error", sid, "%s must be a string" % key, "fix it", key)
        if "tense" in sc and sc["tense"] not in TENSES:
            rep.add("SCHEMA", "error", sid, "tense must be past, present or future", "fix it", "tense")
        if "person" in sc and sc["person"] not in PERSONS:
            rep.add("SCHEMA", "error", sid, "person must be first, second or third", "fix it", "person")
        if "outcome_type" in sc and sc["outcome_type"] not in OUTCOME_TYPES:
            rep.add("SCHEMA", "error", sid, "outcome_type must be yes, no, yes-but or no-and", "fix it", "outcome_type")
        if "date" in sc and parse_date(sc["date"]) is None:
            rep.add("SCHEMA", "error", sid, "date must be YYYY-MM-DD or YYYY-MM-DDTHH:MM with no timezone", "fix the date", "date")
        if "words" in sc and not (is_int(sc["words"]) and sc["words"] > 0):
            rep.add("SCHEMA", "error", sid, "words must be a positive whole number", "fix it", "words")
        if "chapter" in sc and not (is_int(sc["chapter"]) or isinstance(sc["chapter"], str)):
            rep.add("SCHEMA", "error", sid, "chapter must be a number or a string", "fix it", "chapter")
        for key in ("characters", "requires", "plants", "pays_off"):
            if key in sc and not is_strlist(sc[key]):
                rep.add("SCHEMA", "error", sid, "%s must be a list of strings" % key, "fix it", key)
        for key in ("stakes_change", "flashback", "pov_marked", "tense_marked"):
            if key in sc and not isinstance(sc[key], bool):
                rep.add("SCHEMA", "error", sid, "%s must be true or false" % key, "fix it", key)
        if "change" in sc:
            chg = sc["change"]
            if not (isinstance(chg, dict) and set(chg) <= {"from", "to"} and all(isinstance(v, str) for v in chg.values())):
                rep.add("SCHEMA", "error", sid, "change must be an object {\"from\": text, \"to\": text}", "fix it", "change")
    return not fatal


def check_content(doc, rep):
    scenes = doc["scenes"]
    structure = doc["structure"]
    template = TEMPLATES[structure]
    beat_names = [b[0] for b in template]
    pov_mode = doc.get("pov_mode", "multiple")
    default_tense = doc["tense"]
    default_person = doc.get("person")
    chars = {c["id"]: c for c in doc["characters"]}
    index = {sc["id"]: i for i, sc in enumerate(scenes)}

    # positions in percent of planned words; scenes without words count as 1 unit
    have_words = all(is_int(sc.get("words")) for sc in scenes)
    weights = [sc["words"] if have_words else 1 for sc in scenes]
    total = float(sum(weights))
    starts, ends, cum = [], [], 0.0
    for w in weights:
        starts.append(cum / total * 100.0)
        cum += w
        ends.append(cum / total * 100.0)
    centres = [(a + b) / 2.0 for a, b in zip(starts, ends)]

    # ---- beats and budgets
    first_scene, beat_words, beat_scenes = {}, {}, {}
    for i, sc in enumerate(scenes):
        b = sc["beat"]
        first_scene.setdefault(b, i)
        beat_scenes.setdefault(b, []).append(sc["id"])
        beat_words[b] = beat_words.get(b, 0) + (sc["words"] if have_words else 0)
        if b not in beat_names:
            rep.add("UNKNOWN_BEAT", "warn", sc["id"], "beat %r is not in the %s template" % (b, structure),
                    "use one of: %s" % ", ".join(beat_names), b)
    for name in beat_names:
        if name not in first_scene:
            rep.add("MISSING_BEAT", "error", None, "no scene is assigned to the %s beat of %s" % (name, structure),
                    "add a scene that carries this turn, or assign an existing one", name)
    prev = None
    for name in beat_names:
        if name not in first_scene:
            continue
        if prev is not None and first_scene[name] < first_scene[prev]:
            rep.add("BEAT_ORDER", "warn", scenes[first_scene[name]]["id"],
                    "beat %s starts before beat %s" % (name, prev), "reorder the scenes or reassign the beats", name)
        prev = name
    budget_rows = []
    word_target = doc["word_target"]
    for row in budgets(structure, word_target):
        name = row["beat"]
        start_pct = row["span_pct"][0]
        entry = {"beat": name, "span_pct": row["span_pct"], "budget_words": row["budget_words"],
                 "planned_words": beat_words.get(name) if have_words and name in first_scene else None,
                 "scene_ids": beat_scenes.get(name, []), "status": "missing" if name not in first_scene else "unknown"}
        if name in first_scene:
            fi = first_scene[name]
            drift = starts[fi] - start_pct
            entry["starts_at_pct"] = round(starts[fi], 1)
            if abs(drift) > BEAT_DRIFT_POINTS:
                rep.add("BEAT_DRIFT", "warn", scenes[fi]["id"],
                        "beat %s starts at %.1f%% of the planned words; the template puts it at about %d%%" % (name, starts[fi], start_pct),
                        "move the turn earlier or later, or rebalance the scenes before it", name)
            if have_words:
                ratio = beat_words[name] / float(row["budget_words"])
                entry["status"] = "under" if ratio < BUDGET_LOW else "over" if ratio > BUDGET_HIGH else "ok"
                if entry["status"] != "ok":
                    rep.add("BEAT_BUDGET", "warn", scenes[fi]["id"],
                            "beat %s plans %d words against a budget of %d (%s)" % (name, beat_words[name], row["budget_words"], entry["status"]),
                            "add or trim scenes in this beat, or change word_target", name)
        budget_rows.append(entry)
    planned_total = sum(sc["words"] for sc in scenes) if have_words else None
    if have_words:
        if abs(planned_total - word_target) / float(word_target) > TARGET_TOLERANCE:
            rep.add("TARGET_MISMATCH", "warn", None,
                    "scene words add up to %d against a target of %d" % (planned_total, word_target),
                    "rescale the scene budgets or change word_target", "word_target")
    else:
        rep.add("NO_WORD_COUNTS", "info", None, "not every scene has words, so budgets and positions use equal weights",
                "add a planned word count to every scene")

    # ---- per-scene field checks, change, pacing
    run = 0
    for i, sc in enumerate(scenes):
        sid = sc["id"]
        for key in ("goal", "conflict", "outcome"):
            if is_empty(sc.get(key)):
                rep.add("MISSING_FIELD", "error", sid, "scene has no %s" % key, "state the %s in one concrete sentence" % key, key)
        chg = sc.get("change")
        if not isinstance(chg, dict) or is_empty(chg.get("from")) or is_empty(chg.get("to")):
            rep.add("NO_CHANGE", "error", sid, "scene does not say what changes", "fill change.from and change.to, or cut or merge the scene", "change")
        elif norm(chg["from"]) == norm(chg["to"]):
            rep.add("NO_CHANGE", "error", sid, "change.from and change.to are the same, so nothing changes", "find the value that moves, or cut or merge the scene", "change")
        if MIDDLE_THIRD[0] <= centres[i] <= MIDDLE_THIRD[1] and sc.get("stakes_change") is not True:
            rep.add("MIDDLE_NO_STAKE_CHANGE", "warn", sid, "scene sits in the middle third (%.0f%%) and does not change a stake" % centres[i],
                    "raise, lower or reveal something at stake here, or cut the scene")
        if sc.get("outcome_type") == "yes":
            run += 1
            if run == SUCCESS_RUN:
                rep.add("RUN_OF_SUCCESS", "warn", sid, "%d scenes in a row end in a plain yes" % SUCCESS_RUN,
                        "make at least one of them yes-but or no-and")
        else:
            run = 0

    # ---- POV, tense and person drift
    if pov_mode != "omniscient":
        first_pov = None
        for i, sc in enumerate(scenes):
            sid, pov = sc["id"], sc.get("pov")
            if is_empty(pov):
                rep.add("MISSING_FIELD", "error", sid, "scene has no pov", "name the viewpoint character", "pov")
                continue
            if pov not in chars:
                rep.add("POV_UNKNOWN", "error", sid, "pov %r is not a character id" % pov, "add the character or fix the id", pov)
            if first_pov is None:
                first_pov = pov
                continue
            prev_sc = scenes[i - 1]
            marked = sc.get("pov_marked") is True or sc.get("chapter") != prev_sc.get("chapter")
            if pov_mode == "single" and pov != first_pov and not marked:
                rep.add("POV_DRIFT", "error", sid, "single-POV outline: scene is told from %s, not %s, and the change is unmarked" % (pov, first_pov),
                        "retell from %s or start a new chapter and set pov_marked" % first_pov, pov)
            elif pov_mode == "multiple" and pov != prev_sc.get("pov") and not marked:
                rep.add("POV_DRIFT", "error", sid, "viewpoint moves from %s to %s inside a chapter with no marker" % (prev_sc.get("pov"), pov),
                        "start a new chapter, add a scene break and set pov_marked, or keep one viewpoint", pov)
    for sc in scenes:
        sid = sc["id"]
        if sc.get("flashback") is True:
            continue
        if sc.get("tense", default_tense) != default_tense and sc.get("tense_marked") is not True:
            rep.add("TENSE_DRIFT", "error", sid, "scene is %s tense; the outline is %s" % (sc["tense"], default_tense),
                    "rewrite in %s, or mark it as a flashback or tense_marked" % default_tense, sc["tense"])
        if default_person and sc.get("person", default_person) != default_person and sc.get("tense_marked") is not True:
            rep.add("PERSON_DRIFT", "error", sid, "scene is %s person; the outline is %s" % (sc["person"], default_person),
                    "rewrite in %s person, or set tense_marked for a deliberate switch" % default_person, sc["person"])

    # ---- timeline
    prev_date = None
    for i, sc in enumerate(scenes):
        sid = sc["id"]
        d = parse_date(sc.get("date"))
        flash = sc.get("flashback") is True
        if d is not None and not flash:
            if prev_date is not None and d < prev_date:
                rep.add("TIMELINE_BACKWARDS", "warn", sid, "scene is dated %s, earlier than the scene before it" % sc["date"],
                        "fix the date, reorder, or mark the scene as a flashback")
            prev_date = d
        for req in sc.get("requires", []):
            if req not in index:
                rep.add("REQUIRES_UNKNOWN", "error", sid, "requires %r, which is not a scene id" % req, "fix the id", req)
                continue
            other = scenes[index[req]]
            od = parse_date(other.get("date"))
            if d is not None and od is not None and d < od:
                rep.add("TIMELINE_CONTRADICTION", "error", sid,
                        "scene is dated %s but needs %s (dated %s) to have happened first" % (sc["date"], req, other["date"]),
                        "move one of the dates, or drop the dependency", req)
            if index[req] > i and not flash:
                rep.add("REQUIRES_ORDER", "warn", sid, "scene appears before %s, which it depends on" % req,
                        "reorder, or mark the scene as a flashback", req)
        present = set(sc.get("characters", []))
        if isinstance(sc.get("pov"), str) and sc["pov"] in chars:
            present.add(sc["pov"])
        for cid in sorted(present):
            ch = chars.get(cid)
            if ch is None:
                rep.add("CHAR_UNKNOWN", "error", sid, "character %r is not in the characters list" % cid, "add the character or fix the id", cid)
                continue
            dd = parse_date(ch.get("dies_on"))
            if d is not None and dd is not None and d > dd and not flash:
                rep.add("CHAR_AFTER_DEATH", "error", sid, "%s appears on %s, after dying on %s" % (cid, sc["date"], ch["dies_on"]),
                        "move the death, change the date, or mark the scene as a flashback", cid)

    # ---- setups and payoffs
    planted, paid = {}, {}
    for i, sc in enumerate(scenes):
        for s in sc.get("plants", []):
            planted.setdefault(s, i)
        for s in sc.get("pays_off", []):
            paid.setdefault(s, []).append(i)
    for s, i in planted.items():
        if s not in paid:
            rep.add("SETUP_NO_PAYOFF", "warn", scenes[i]["id"], "setup %r is planted and never paid off" % s,
                    "add a payoff scene or cut the plant", s)
    for s, idxs in paid.items():
        for j in idxs:
            if s not in planted:
                rep.add("PAYOFF_NO_SETUP", "error", scenes[j]["id"], "payoff %r has no earlier setup" % s,
                        "plant it in an earlier scene, or change the payoff", s)
            elif planted[s] >= j:
                rep.add("PAYOFF_BEFORE_SETUP", "error", scenes[j]["id"], "payoff %r comes at or before its setup" % s,
                        "plant it earlier or move the payoff later", s)
    for st in doc.get("setups", []):
        if st["id"] not in planted:
            rep.add("SETUP_NEVER_PLANTED", "warn", None, "declared setup %r is not planted in any scene" % st["id"],
                    "add it to a scene's plants list or delete it", st["id"])

    # ---- characters
    appearances = {cid: [] for cid in chars}
    for i, sc in enumerate(scenes):
        present = set(sc.get("characters", []))
        if isinstance(sc.get("pov"), str):
            present.add(sc["pov"])
        for cid in present:
            if cid in appearances:
                appearances[cid].append(i)
    for cid, ch in chars.items():
        intro = ch.get("introduced_in")
        if intro is not None:
            if intro not in index:
                rep.add("CHAR_INTRO_UNKNOWN", "error", None, "%s: introduced_in %r is not a scene id" % (cid, intro), "fix the id", cid)
            else:
                for i in appearances[cid]:
                    if i < index[intro] and scenes[i].get("flashback") is not True:
                        rep.add("CHAR_BEFORE_INTRO", "error", scenes[i]["id"],
                                "%s appears before being introduced in %s" % (cid, intro),
                                "move the introduction earlier or take the character out of this scene", cid)
        apps = appearances[cid]
        major = ch.get("role") in MAJOR_ROLES
        if major and apps and ch.get("exit_scene") is None and ch.get("dies_on") is None:
            last = apps[-1]
            if centres[last] < VANISH_BELOW_PCT:
                rep.add("CHAR_VANISHES", "warn", scenes[last]["id"],
                        "%s (%s) is last seen at %.0f%% of the story with no exit" % (cid, ch["role"], centres[last]),
                        "bring them back before the final turn, or give them an exit_scene", cid)
        if major and not apps:
            rep.add("CHAR_NEVER_APPEARS", "warn", None, "%s (%s) is in no scene" % (cid, ch["role"]), "add scenes or cut the character", cid)
        if ch.get("exit_scene") is not None and ch["exit_scene"] not in index:
            rep.add("CHAR_EXIT_UNKNOWN", "error", None, "%s: exit_scene %r is not a scene id" % (cid, ch["exit_scene"]), "fix the id", cid)
        arc = ch.get("arc")
        if arc is None:
            if ch.get("role") == "protagonist":
                rep.add("ARC_MISSING", "error", None, "protagonist %s has no arc" % cid, "add arc with want, need and turning_points", cid)
            continue
        if is_empty(arc.get("want")) or is_empty(arc.get("need")):
            rep.add("ARC_INCOMPLETE", "warn", None, "%s: arc needs both a want and a need" % cid, "state what they want and what they actually need", cid)
        tps = arc.get("turning_points", [])
        if not tps:
            rep.add("ARC_NO_TURNING_POINT", "error", None, "%s has an arc with no turning point" % cid, "name the scenes where their belief or choice changes", cid)
            continue
        for t in tps:
            if t not in index:
                rep.add("ARC_TURN_UNKNOWN", "error", None, "%s: turning point %r is not a scene id" % (cid, t), "fix the id", cid)
            else:
                sc = scenes[index[t]]
                if cid not in appearances or index[t] not in appearances[cid]:
                    rep.add("ARC_TURN_ABSENT", "warn", sc["id"], "%s has a turning point here but is not in the scene" % cid, "add them to the scene or pick another", cid)
        if ch.get("role") == "protagonist" and len(set(tps)) < ARC_MIN_TURNS_PROTAGONIST:
            rep.add("ARC_FEW_TURNS", "warn", None, "protagonist %s has %d turning point(s); at least %d expected" % (cid, len(set(tps)), ARC_MIN_TURNS_PROTAGONIST),
                    "add a turning point near the midpoint and one late in the story", cid)

    return {"beat_budgets": budget_rows, "planned_words": planned_total, "have_words": have_words,
            "centres": centres}


def run_check(path):
    doc = load_strict(path)
    rep = Report()
    extra = {"beat_budgets": [], "planned_words": None}
    if check_schema(doc, rep):
        extra = check_content(doc, rep)
    order = {sc["id"]: i for i, sc in enumerate(doc["scenes"])} if isinstance(doc, dict) and isinstance(doc.get("scenes"), list) and all(isinstance(s, dict) and isinstance(s.get("id"), str) for s in doc["scenes"]) else {}
    sev = {"error": 0, "warn": 1, "info": 2}
    rep.defects.sort(key=lambda d: (-1 if d["scene_id"] is None else order.get(d["scene_id"], 10 ** 6), sev[d["severity"]], d["code"], str(d["ref"])))
    counts = {}
    for d in rep.defects:
        counts[d["code"]] = counts.get(d["code"], 0) + 1
    errors = sum(1 for d in rep.defects if d["severity"] == "error")
    warns = sum(1 for d in rep.defects if d["severity"] == "warn")
    out = {
        "command": "check",
        "file": os.path.basename(path),
        "ok": errors == 0,
        "summary": {
            "structure": doc.get("structure") if isinstance(doc, dict) else None,
            "word_target": doc.get("word_target") if isinstance(doc, dict) else None,
            "planned_words": extra.get("planned_words"),
            "scenes": len(doc["scenes"]) if isinstance(doc, dict) and isinstance(doc.get("scenes"), list) else 0,
            "errors": errors,
            "warnings": warns,
        },
        "beat_budgets": extra["beat_budgets"],
        "counts_by_code": dict(sorted(counts.items())),
        "defects": rep.defects,
    }
    return out, (0 if errors == 0 else 1)


def emit(obj):
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    usage = "usage: check_outline.py check <outline.json> | budget <structure> <word_target> | structures"
    if not argv:
        sys.stderr.write(usage + "\n")
        return 2
    cmd = argv[0]
    if cmd == "structures":
        emit({"command": "structures", "structures": {k: [b[0] for b in v] for k, v in TEMPLATES.items()}})
        return 0
    if cmd == "budget":
        if len(argv) != 3 or argv[1] not in TEMPLATES or not argv[2].isdigit() or int(argv[2]) <= 0:
            sys.stderr.write("budget needs a structure (%s) and a positive whole word target\n" % ", ".join(sorted(TEMPLATES)))
            return 2
        emit({"command": "budget", "structure": argv[1], "word_target": int(argv[2]), "beats": budgets(argv[1], int(argv[2]))})
        return 0
    if cmd == "check" and len(argv) == 2:
        try:
            out, code = run_check(argv[1])
        except Strict as exc:
            sys.stderr.write("error: %s\n" % exc)
            return 2
        emit(out)
        return code
    sys.stderr.write(usage + "\n")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
