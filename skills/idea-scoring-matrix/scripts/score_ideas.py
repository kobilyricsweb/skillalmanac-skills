"""Rank ideas with a weighted scoring matrix and test whether the winner is stable.

Input: one UTF-8 JSON file, at most 2 MB, nesting depth at most 8, shaped as
  {"criteria": [{"name": str, "weight": number}, ...],
   "ideas":    [{"name": str, "scores": {criterion name: number}}, ...]}

Rules: 2 to 20 criteria, 2 to 200 ideas, weights above 0 and at most 1000,
scores from 1 to 5, scores keys must equal the criterion names exactly.

Weighted total = sum(weight * score) / sum(weight), so totals stay in 1..5.
Ranking: total descending, then idea name ascending (fixed tie-break).
Sensitivity: each criterion weight is multiplied by 0.75, then by 1.25, one at
a time, and the winner is recomputed. The winner is robust when no such
change moves the winner to a different idea.

Output: one JSON object on stdout. A short human table goes to stderr.
The script reads the input file only and writes no files.

Exit codes: 0 winner robust and not tied at the top;
            1 findings (winner changes under a weight shift, or tie at top);
            2 usage or input error (a one-line JSON error on stdout).

Usage: python -I score_ideas.py <input.json>
"""
import json
import math
import sys

MAX_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 8
MIN_CRITERIA = 2
MAX_CRITERIA = 20
MIN_IDEAS = 2
MAX_IDEAS = 200
NAME_MAX = 80
WEIGHT_MAX = 1000.0
FACTORS = (("minus25", 0.75), ("plus25", 1.25))


def fail(message):
    sys.stdout.write(json.dumps({"status": "error", "message": message}) + "\n")
    sys.exit(2)


def load_input(path):
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError:
        fail("cannot read input file")
    if len(raw) > MAX_BYTES:
        fail("input exceeds 2 MB")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        fail("input is not valid UTF-8")
    try:
        return json.loads(text)
    except (ValueError, RecursionError, MemoryError):
        fail("input is not valid JSON")


def max_depth(value):
    deepest = 0
    stack = [(value, 1)]
    while stack:
        node, depth = stack.pop()
        if depth > deepest:
            deepest = depth
        if isinstance(node, dict):
            stack.extend((child, depth + 1) for child in node.values())
        elif isinstance(node, list):
            stack.extend((child, depth + 1) for child in node)
    return deepest


def is_number(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def valid_name(value):
    return isinstance(value, str) and 1 <= len(value.strip()) and len(value) <= NAME_MAX


def validate(data):
    if not isinstance(data, dict):
        fail("top level must be an object")
    if set(data.keys()) != {"criteria", "ideas"}:
        fail("top level keys must be exactly criteria and ideas")
    criteria = data["criteria"]
    ideas = data["ideas"]
    if not isinstance(criteria, list) or not MIN_CRITERIA <= len(criteria) <= MAX_CRITERIA:
        fail("criteria must be a list of 2 to 20 items")
    if not isinstance(ideas, list) or not MIN_IDEAS <= len(ideas) <= MAX_IDEAS:
        fail("ideas must be a list of 2 to 200 items")

    weights = {}
    for item in criteria:
        if not isinstance(item, dict) or set(item.keys()) != {"name", "weight"}:
            fail("each criterion needs exactly name and weight")
        if not valid_name(item["name"]):
            fail("criterion name must be a non-empty string of at most 80 characters")
        if item["name"] in weights:
            fail("duplicate criterion name")
        weight = item["weight"]
        if not is_number(weight) or not 0 < weight <= WEIGHT_MAX:
            fail("weight must be a number above 0 and at most 1000")
        weights[item["name"]] = float(weight)

    scored = []
    seen = set()
    for item in ideas:
        if not isinstance(item, dict) or set(item.keys()) != {"name", "scores"}:
            fail("each idea needs exactly name and scores")
        name = item["name"]
        if not valid_name(name) or name in seen:
            fail("idea name must be a unique non-empty string of at most 80 characters")
        seen.add(name)
        scores = item["scores"]
        if not isinstance(scores, dict) or set(scores.keys()) != set(weights.keys()):
            fail("scores keys must match criterion names exactly")
        clean = {}
        for criterion, score in scores.items():
            if not is_number(score) or not 1 <= score <= 5:
                fail("each score must be a number from 1 to 5")
            clean[criterion] = float(score)
        scored.append((name, clean))
    return weights, scored


def rank(weights, scored, multipliers):
    rows = []
    for name, scores in scored:
        numerator = 0.0
        denominator = 0.0
        for criterion, weight in weights.items():
            effective = weight * multipliers.get(criterion, 1.0)
            numerator += effective * scores[criterion]
            denominator += effective
        rows.append((round(numerator / denominator, 9), name))
    rows.sort(key=lambda row: (-row[0], row[1]))
    return rows


def printable(text):
    return str(text).encode("ascii", "backslashreplace").decode("ascii")


def write_table(ranking, winner, robust, tie, flips, total_checks):
    lines = ["Rank  Idea                             Total"]
    for index, (total, name) in enumerate(ranking, start=1):
        lines.append("%-5d %-32s %.3f" % (index, printable(name)[:32], total))
    lines.append("Winner: %s | robust: %s | tie at top: %s"
                 % (printable(winner), "yes" if robust else "no", "yes" if tie else "no"))
    lines.append("Sensitivity flips: %d of %d" % (flips, total_checks))
    sys.stderr.write("\n".join(lines) + "\n")


def main(argv):
    if len(argv) != 2:
        fail("usage: score_ideas.py <input.json>")
    data = load_input(argv[1])
    if max_depth(data) > MAX_DEPTH:
        fail("input nesting is too deep")
    weights, scored = validate(data)

    base = rank(weights, scored, {})
    winner = base[0][1]
    tie = len(base) > 1 and base[0][0] == base[1][0]
    margin = round(base[0][0] - base[1][0], 9)

    sensitivity = []
    for criterion in weights:
        for label, factor in FACTORS:
            perturbed = rank(weights, scored, {criterion: factor})
            sensitivity.append({
                "criterion": criterion,
                "change": label,
                "winner": perturbed[0][1],
                "winner_changed": perturbed[0][1] != winner,
            })
    flips = sum(1 for row in sensitivity if row["winner_changed"])
    robust = flips == 0

    result = {
        "status": "ok",
        "winner": winner,
        "margin_to_runner_up": round(margin, 3),
        "tie_at_top": tie,
        "winner_robust": robust,
        "ranking": [
            {"rank": index, "idea": name, "total": round(total, 3)}
            for index, (total, name) in enumerate(base, start=1)
        ],
        "sensitivity": sensitivity,
    }
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    write_table(base, winner, robust, tie, flips, len(sensitivity))
    return 0 if robust and not tie else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
