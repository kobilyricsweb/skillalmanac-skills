#!/usr/bin/env python3
"""vault_report.py - turn vault_scan.py JSON into a plain Markdown findings list.

Usage: python vault_report.py scan.json [--sections broken,orphans,duplicates,tags,frontmatter,moves]

Read-only, standard library only, no network. Prints one bullet per finding with the
exact paths and line numbers, so the reply can be pasted or trimmed to the user's format.
"""
import json
import sys

ALL = ["broken", "ambiguous", "orphans", "duplicates", "tags", "frontmatter", "moves"]


def render(d, sections):
    out = []
    c = d.get("counts", {})
    out.append("Counts: " + ", ".join("%s=%s" % (k, v) for k, v in c.items()))
    if "broken" in sections:
        out.append("\n## Broken links (%s)" % c.get("broken_links", 0))
        for b in d.get("broken_links", []):
            s = ("; did you mean " + ", ".join(b["suggestions"])) if b.get("suggestions") else ""
            out.append("- %s:%s links to [[%s]] (no match)%s" % (b["source"], b["line"], b["target"], s))
    if "ambiguous" in sections:
        out.append("\n## Ambiguous links (%s)" % c.get("ambiguous_links", 0))
        for a in d.get("ambiguous_links", []):
            out.append("- %s:%s [[%s]] could be: %s" % (a["source"], a["line"], a["target"], ", ".join(a["candidates"])))
    if "orphans" in sections:
        out.append("\n## Orphans (%s)" % c.get("orphans", 0))
        for o in d.get("orphans", []):
            out.append("- %s (%s words, %s outbound links)" % (o["path"], o["words"], o["outbound_links"]))
    if "duplicates" in sections:
        out.append("\n## Duplicate content (%s groups)" % c.get("duplicate_content_groups", 0))
        for g in d.get("duplicate_content", []):
            out.append("- identical: " + " = ".join(g["paths"]))
        out.append("\n## Duplicate titles (%s groups)" % c.get("duplicate_title_groups", 0))
        for g in d.get("duplicate_titles", []):
            out.append("- title '%s': %s%s" % (g["title"], ", ".join(g["paths"]),
                                               " (same file name)" if g.get("same_filename") else ""))
    if "tags" in sections:
        out.append("\n## Tag variants (%s groups)" % c.get("tag_variant_groups", 0))
        for g in d.get("tag_variants", []):
            vs = ", ".join("%s (%s notes)" % (v["tag"], v["notes"]) for v in g["variants"])
            out.append("- %s -> suggested %s" % (vs, g["suggested"]))
    if "frontmatter" in sections:
        out.append("\n## Missing frontmatter (%s)" % c.get("missing_frontmatter", 0))
        for m in d.get("missing_frontmatter", []):
            out.append("- %s (%s)" % (m["path"], m["reason"]))
    if "moves" in sections:
        mp = d.get("move_plan", {})
        out.append("\n## Proposed moves (%s)" % len(mp.get("moves", [])))
        for m in mp.get("moves", []):
            out.append("- %s: %s -> %s [%s, %s] links affected: %s" % (
                m["id"], m["from"], m["to"], m["rule"], m["confidence"], m["path_links_affected"]))
    if d.get("truncated"):
        out.append("\nTruncated lists: %s" % json.dumps(d["truncated"]))
    return "\n".join(out)


def main(argv):
    if not argv or argv[0].startswith("-"):
        print(__doc__, file=sys.stderr)
        return 2
    sections = ALL
    if "--sections" in argv:
        i = argv.index("--sections")
        sections = argv[i + 1].split(",") if i + 1 < len(argv) else ALL
    try:
        with open(argv[0], encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError) as exc:
        print("vault_report.py: " + str(exc), file=sys.stderr)
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    print(render(d, sections))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
