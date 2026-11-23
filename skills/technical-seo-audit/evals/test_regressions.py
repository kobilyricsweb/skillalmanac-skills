#!/usr/bin/env python3
"""Offline regressions for documented technical-seo-audit accuracy defects."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("seo_page_check", ROOT / "scripts" / "seo_page_check.py")
SEO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SEO)


def run_folder(folder):
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        code = SEO.main([str(folder), "--json"])
    return code, json.loads(stream.getvalue())


def write_case(folder, url="https://example.test/page", robots="User-agent: *\nAllow: /\n",
               canonical=None, body="Enough static words for this saved page to avoid the raw HTML heuristic entirely. " * 6,
               extra_head="", sitemap_url=None):
    canonical = canonical or url
    (folder / "page.html").write_text(
        '<!doctype html><html lang="en"><head><title>A descriptive and distinct page title</title>'
        '<meta name="description" content="A sufficiently descriptive summary for this synthetic regression page, written to avoid unrelated length findings during this narrow offline test case.">'
        '<meta name="viewport" content="width=device-width"><link rel="canonical" href="%s">%s</head><body><h1>Page</h1><p>%s</p></body></html>'
        % (canonical, extra_head, body), encoding="utf-8")
    (folder / "urls.csv").write_text("file,url\npage.html,%s\n" % url, encoding="utf-8")
    (folder / "robots.txt").write_text(robots, encoding="utf-8")
    if sitemap_url is not None:
        (folder / "sitemap.xml").write_text(
            '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>%s</loc></url></urlset>' % sitemap_url,
            encoding="utf-8")


class AccuracyRegressions(unittest.TestCase):
    def test_documented_accuracy_boundaries_remain_visible(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        checklist = (ROOT / "references" / "checklist.md").read_text(encoding="utf-8")
        evals = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
        self.assertIn("Google renders JavaScript", skill)
        self.assertIn("75th percentile", checklist)
        self.assertIn("200 ms or less", checklist)
        self.assertIn("0.1 or less", checklist)
        self.assertIn("not every indexable URL must be listed", checklist)
        self.assertIn("no universal 5% requirement", checklist)
        self.assertIn("re-read on 2026-11-23", checklist)
        t2 = next(case for case in evals["evals"] if case["id"] == "t2-not-indexed")
        self.assertFalse(any("main cause" in assertion.lower() for assertion in t2["assertions"]))

    def test_authored_fixtures_remain_stable(self):
        good_code, good = run_folder(ROOT / "evals" / "fixtures" / "good_site")
        bad_code, bad = run_folder(ROOT / "evals" / "fixtures" / "bad_site")
        self.assertEqual((good_code, good["counts"]), (0, {"FAIL": 0, "WARN": 0, "NOTE": 0}))
        self.assertEqual(bad_code, 1)
        self.assertTrue({"C2", "J1", "S1", "S2", "S3", "T3"}.issubset({x["rule"] for x in bad["findings"]}))

    def test_robots_matching_includes_query(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_case(folder, url="https://example.test/products?sort=price", robots="User-agent: *\nDisallow: /*?sort=\n")
            _, result = run_folder(folder)
        self.assertTrue(any(x["rule"] == "R4" for x in result["findings"]), result["findings"])

    def test_allow_carveout_prevents_whole_site_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_case(folder, url="https://example.test/public/page", robots="User-agent: *\nDisallow: /\nAllow: /public/\n")
            _, result = run_folder(folder)
        self.assertFalse(any(x["rule"] == "R0" for x in result["findings"]), result["findings"])

    def test_root_only_disallow_is_not_whole_site(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_case(folder, robots="User-agent: *\nDisallow: /$\n")
            _, result = run_folder(folder)
        self.assertFalse(any(x["rule"] == "R0" for x in result["findings"]), result["findings"])

    def test_trailing_wildcard_does_not_gain_false_precedence(self):
        groups = SEO.parse_robots("User-agent: *\nAllow: /fish\nDisallow: /fish*\n")
        self.assertTrue(SEO.robots_allows(groups, "googlebot", "/fishheads"))

    def test_raw_html_word_heuristic_is_not_documented_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_case(folder, body="Short shell.", extra_head='<script src="/app.js"></script>')
            _, result = run_folder(folder)
        finding = next(x for x in result["findings"] if x["rule"] == "B1")
        self.assertEqual(finding["basis"], "convention")
        self.assertIn("rendered", finding["message"].lower())

    def test_http_urls_are_not_rejected_as_invalid_canonical_or_sitemap(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            url = "http://example.test/page"
            write_case(folder, url=url, canonical=url, sitemap_url=url)
            _, result = run_folder(folder)
        self.assertFalse(any(x["rule"] in {"C3", "S5"} for x in result["findings"]), result["findings"])

    def test_missing_canonical_is_not_labeled_documented_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_case(folder)
            page = folder / "page.html"
            page.write_text(page.read_text(encoding="utf-8").replace('<link rel="canonical" href="https://example.test/page">', ''), encoding="utf-8")
            _, result = run_folder(folder)
        finding = next(x for x in result["findings"] if x["rule"] == "C1")
        self.assertEqual((finding["level"], finding["basis"]), ("NOTE", "convention"))

    def test_nonfinite_jsonld_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_case(folder, extra_head='<script type="application/ld+json">{"value": NaN}</script>')
            _, result = run_folder(folder)
        self.assertTrue(any(x["rule"] == "J1" for x in result["findings"]), result["findings"])

    def test_canonical_messages_do_not_claim_indexing_outcome(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_case(folder, canonical="https://staging.example.test/page")
            _, result = run_folder(folder)
        messages = " ".join(x["message"].lower() for x in result["findings"] if x["rule"] in {"C4", "C7"})
        self.assertNotIn("will not be indexed", messages)
        self.assertNotIn("asking not to be the indexed version", messages)


if __name__ == "__main__":
    unittest.main(verbosity=2)
