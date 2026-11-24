#!/usr/bin/env python3
"""Score the [script] assertions of one eval task by reading the files the agent wrote.

    python evals/score_task.py <task-id> <output-dir>

Prints JSON {task, passed, total, details[]}. Curly quotes and dashes are normalized, so
straight or curly quotes and hyphen or en dash all pass. Exit 0 always unless usage is wrong (2).
"""
import json
import os
import re
import sys


def norm(text):
    text = (text.replace("“", '"').replace("”", '"').replace("’", "'")
            .replace("‘", "'").replace("–", "-").replace("—", "-"))
    return " ".join(text.split())


def read(out, name):
    path = os.path.join(out, name)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def numbered(text):
    """Return list of (number, normalized text) for '[n] ...' lines."""
    rows = []
    for line in (text or "").splitlines():
        m = re.match(r"\s*\[(\d+)\]\s+(.*\S)\s*$", line)
        if m:
            rows.append((int(m.group(1)), norm(m.group(2))))
    return rows


def web_fix(s):
    return s.replace(", Accessed:", ". Accessed:")


def is_numbered(rows, n):
    return [r[0] for r in rows] == list(range(1, n + 1))


def surnames_ok(rows, names):
    return len(rows) == len(names) and all(
        re.search(r"\b" + re.escape(n) + r"\b", r[1].split(",")[0].split(" and ")[0]) or n in r[1][:60]
        for r, n in zip(rows, names))


T1 = [
    'W. Chen and M. Gonzalez, "Frequency regulation with distributed storage," IEEE Trans. Power Syst., vol. 36, no. 4, pp. 3101-3112, Jul. 2021, doi: 10.1109/TPWRS.2021.3051234.',
    'N. Okafor et al., "Battery degradation under grid cycling," J. Power Sources, vol. 440, Dec. 2019, Art. no. 227118, doi: 10.1016/j.jpowsour.2019.227118.',
    'D. Lee, P. Patel, and M. Webb Jr., "Grid inertia from wind farms," Nature, vol. 585, pp. 212-219, Sep. 2020.',
    'H. Marsh and O. Said, Power Grid Fundamentals, 3rd ed. London, U.K.: Wiley, 2018.',
    'H. Zhang and I. Alvarez, "Day-ahead scheduling with storage," in Proc. 12th Int. Conf. Smart Grid Technol., Denver, CO, USA, Oct. 5-8, 2022, pp. 401-406, doi: 10.1109/SGT.2022.4455667.',
]
T1_DRAFT = ("Frequency regulation with storage is well studied [1]. Degradation, wind inertia and system "
            "fundamentals are reviewed in [2], [3], [4]. Scheduling is covered in [5]. Both [1], [5] used day-ahead models.")

T2 = [
    'N. Gupta et al., "Liquid cooling trials," IEEE Access, vol. 8, pp. 100-110, Nov. 2020, doi: 10.1109/ACCESS.2020.3001234.',
    'K. Adams and L. Brown, "Cooling loads in data centers," IEEE Trans. Sustain. Comput., vol. 4, no. 2, pp. 88-97, Sep. 2019.',
    'S. Roy, "Cooling basics," Chill Blog. Accessed: Mar. 3, 2023. [Online]. Available: https://example.org/cooling',
    'R. Singh, Data Center Design, 2nd ed. Austin, TX, USA: Wiley, 2015.',
    'M. Chu, "Heat reuse," Energy Rep., to be published.',
]
T2_MS = ["Liquid cooling is now common [1]. Earlier surveys [2], [1] covered loads, and the basics are online [3]. "
         "Design guidance exists [4], and heat reuse is coming [5].",
         "Liquid cooling is now common [1]. Earlier surveys [1], [2] covered loads, and the basics are online [3]. "
         "Design guidance exists [4], and heat reuse is coming [5]."]

T3 = [
    'H. Brandt, "Thermal limits of GaN devices," presented at the Int. Symp. Power Semicond. Devices, Kyoto, Japan, May 12-16, 2024.',
    'R. Delgado, "Understanding load balancing," TechDocs. Accessed: Mar. 14, 2025. [Online]. Available: https://techdocs.example.com/lb',
    'T. Haddad, "Why we moved to Rust," Engineering Notes, Oct. 9, 2024. [Online]. Available: https://notes.example.com/rust',
    'Y. Tanaka, "Sensor fusion basics," in Handbook of Robotics Methods, C. Mendes and R. Adler, Eds., Boston, MA, USA: Academic, 2017, ch. 6, pp. 141-170.',
    'I. Solberg, Digital Signal Processing in Practice, 4th ed. Upper Saddle River, NJ, USA: Prentice-Hall, 2011.',
    'B. Costa and O. Nilsen, "Sparse recovery bounds," IEEE Trans. Inf. Theory, vol. 70, no. 2, pp. 1100-1115, Jan./Feb. 2024, doi: 10.1109/TIT.2024.3345678.',
]
T3_DRAFT = ("Thermal limits of wide-gap devices are discussed in [1]. Practical load balancing is summarized online "
            "[2], [3]. Fusion methods appear in [4], signal processing in [5], and recovery theory in [6].")

T4_KEEP = {
    1: 'A. Reyes, "Sparse coding," Neural Comput., vol. 12, no. 3, pp. 55-68, Mar. 2010.',
    2: 'B. Ono and C. Park, "Edge devices," J. Embedded Syst., vol. 7, no. 7-8, pp. 1-9, Jul./Aug. 2018, doi: 10.1000/j.2018.77.',
    3: 'D. Voss, "Quantum notes," Phys. Rev. Appl., vol. 9, May 2017, Art. no. 044011.',
    6: 'H. Zane, "Ledger basics," Chain Notes. Accessed: Apr. 2, 2023. [Online]. Available: https://example.org/ledger',
}


def score(task, out):
    d = []

    def check(label, ok):
        d.append({"assertion": label, "passed": bool(ok)})

    if task == "t1-journal-set":
        rows = numbered(read(out, "references.txt"))
        check("five lines [1]-[5], first authors in citation order",
              is_numbered(rows, 5) and all(r[1].startswith(n) for r, n in zip(rows, ["W. Chen", "N. Okafor", "D. Lee", "H. Marsh", "H. Zhang"])))
        check("reference 2 exact", len(rows) > 1 and rows[1][1] == T1[1])
        check("reference 3 exact", len(rows) > 2 and rows[2][1] == T1[2])
        check("references 1, 4, 5 exact", len(rows) == 5 and rows[0][1] == T1[0] and rows[3][1] == T1[3] and rows[4][1] == T1[4])
        draft = norm(read(out, "draft_cited.txt") or "")
        check("draft_cited exact", draft == T1_DRAFT)
    elif task == "t2-fix-and-renumber":
        rows = numbered(read(out, "references_fixed.txt"))
        check("five lines in order Gupta, Adams, Roy, Singh, Chu",
              is_numbered(rows, 5) and all(r[1].startswith(n) for r, n in zip(rows, ["N. Gupta", "K. Adams", "S. Roy", "R. Singh", "M. Chu"])))
        check("Gupta entry exact", len(rows) > 0 and rows[0][1] == T2[0])
        check("Adams and Singh entries exact", len(rows) > 3 and rows[1][1] == T2[1] and rows[3][1] == T2[3])
        check("web and Chu entries exact", len(rows) == 5 and rows[2][1] == T2[2] and rows[4][1] == T2[4])
        check("manuscript_fixed renumbered", norm(read(out, "manuscript_fixed.txt") or "") in T2_MS)
    elif task == "t3-mixed-sources":
        rows = numbered(read(out, "references.txt"))
        check("six lines, first authors in citation order",
              is_numbered(rows, 6) and all(r[1].startswith(n) for r, n in zip(rows, ["H. Brandt", "R. Delgado", "T. Haddad", "Y. Tanaka", "I. Solberg", "B. Costa"])))
        check("web page entry exact (URL last, no final period)", len(rows) > 1 and web_fix(rows[1][1]) == T3[1])
        check("chapter entry exact", len(rows) > 3 and rows[3][1] == T3[3])
        check("talk entry exact", len(rows) > 0 and rows[0][1] == T3[0])
        check("book and journal entries exact", len(rows) == 6 and rows[4][1] == T3[4] and rows[5][1] == T3[5])
        check("draft_cited exact", norm(read(out, "draft_cited.txt") or "") == T3_DRAFT)
    elif task == "t4-keep-the-correct":
        rows = numbered(read(out, "references_checked.txt"))
        by = dict(rows)
        check("six lines; 1, 2, 3, 6 unchanged", is_numbered(rows, 6) and all(by.get(k) == v for k, v in T4_KEEP.items()))
        check("entries 4 and 5 fixed",
              by.get(4) == 'E. Wolfe, "Open data," IEEE Data Eng. Bull., Sep. 2021.'
              and by.get(5) == 'F. Xu and G. Yee, "Tooling," Softw. Pract., vol. 2, pp. 4-9, Oct. 2019.')
        check("Jul./Aug. and Art. no. kept", "Jul./Aug." in by.get(2, "") and "Art. no. 044011" in by.get(3, "") and "pp." not in by.get(3, ""))
        check("manuscript_checked written out", norm(read(out, "manuscript_checked.txt") or "") == "Prior work [1], [2], [3], [4] is broad; see also [5] and [6].")
    else:
        return None
    return {"task": task, "passed": sum(x["passed"] for x in d), "total": len(d), "details": d}


def main(argv):
    if len(argv) != 3:
        print("usage: score_task.py <task-id> <output-dir>", file=sys.stderr)
        return 2
    res = score(argv[1], argv[2])
    if res is None:
        print("unknown task id", file=sys.stderr)
        return 2
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
