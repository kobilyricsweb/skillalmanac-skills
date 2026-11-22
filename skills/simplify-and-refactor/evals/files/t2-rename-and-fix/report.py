from lib import avg, pct


def weekly(rows):
    return {"mean": avg([r["n"] for r in rows]), "share": pct(3, len(rows))}
