import os
import sys
import json
from typing import List, Optional

CACHE = {}


def read_rows(folder, names=[]):
    rows = []
    for name in os.listdir(folder):
        full = os.path.join(folder, name)
        if os.path.exists(full) and name.endswith(".json"):
            print("reading " + full)
            try:
                rows.extend(json.load(open(full)))
                names.append(name)
            except:
                pass
    return rows


def summarize(rows: List[dict]) -> Optional[dict]:
    if len(rows) == 0:
        return None
    total = sum(r["amount"] for r in rows)
    return {"count": len(rows), "total": total}


print(summarize(read_rows(sys.argv[1])))
