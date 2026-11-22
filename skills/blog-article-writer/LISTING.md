# Listing page content: blog-article-writer

**One line:** Writes a new blog article from a sourced brief and audits it with numeric rules before you publish.

## What it does

The skill makes an agent write a one-page brief first (audience, promise, angle, what is not covered, and a table of claims each tied to a source URL), then choose an article shape, find one element competitors lack, and draft against a table of numeric structure rules: intro at most 120 words, one idea per H2, 80 to 450 words per section, an example in every section, a source for every figure. A script then audits the Markdown and the brief and prints strict JSON. A hand checklist and a fixed report finish the job. Rules forbid invented statistics, anecdotes and sources.

## How it differs from natural-prose-editor

`natural-prose-editor` takes text that already exists and removes machine habits while keeping every fact. This skill is for authoring: it starts from nothing but a topic or outline, decides what the piece says and how it is built, and refuses to add any claim without a source. If you already have a draft and only want it to sound better, use the editor. It is also not product documentation or an academic paper writer.

## Capabilities

- `scripts/article_audit.py audit`: heading structure, intro and section lengths, stock-phrase openers, numbers with no link nearby, sentence-length spread and a reading-grade proxy, internal link count, optional check that every figure appears in the brief
- `scripts/article_audit.py brief`: required fields, promise length, placeholders, claim table with a page URL and check date per row
- Five article shapes with H2 skeletons, an opener swap table, a final-pass checklist and a fixed report

## When to use

You say write a blog post, draft an article, write a post that ranks, or turn this outline into an article.

## When not to use

Editing or humanizing an existing text, translation, social posts, ad copy, product documentation, academic papers, and technical SEO audits.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent applies the tables and checklists by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so no agent-written article is shown. Real script runs on the saved fixtures:

1. `python scripts/article_audit.py audit evals/fixtures/article_bad.md --site-host example.org`: verdict `fix`, 10 errors and 14 warnings, exit 1. Errors include `generic-era-opener` ("In today's fast-paced"), `generic-rhetorical-wonder` ("Have you ever wondered"), `intro-long` (130 words against a 120 limit), `heading-skip` (H1 straight to H3) and `uncited-number` ("73%"). Reading proxy: mean 26.3 words per sentence, 20% of sentences over 30 words, grade proxy 12.6.
2. `python scripts/article_audit.py audit evals/fixtures/article_good.md --site-host example.org --brief evals/fixtures/brief_good.md`: verdict `pass`, 0 errors, 0 warnings, 498 words, intro 46 words, 4 H2 sections of 102 to 126 words, 2 internal links, mean sentence 14.6 words. `article_good.md` is hand-written reference text, not an agent run.
3. `python scripts/article_audit.py brief evals/fixtures/brief_bad.md`: verdict `fix`, 7 errors (placeholder promise, missing "not covered", a claim row with no URL, only 2 claim rows) and 2 warnings.

## Limits

- Surface measurement only: an example "signal" is not proof the example is good.
- Uncited-number detection covers percentages, currency, magnitudes, comma numbers and common units; bare counts and vague claims ("experts agree") are left to the hand checklist.
- Thresholds are working values for 800 to 2,500 word English articles.
- It does not verify that a cited page says what the brief claims, and does not predict ranking.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL / 0 WARN; 11 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Prompt: "Write a blog post on release notes from this brief." The agent runs `brief`; it fails on a placeholder promise and a claim with no URL.
2. The brief is fixed (3 sourced rows); the agent drafts and runs `audit`: `fix`, stock opener plus an uncited 62%.
3. The agent replaces the opener with a specific claim, adds the link, re-runs: `pass`.
4. The fixed report appears, including claims cut for lacking a source and what was not checked.

## FAQ seeds

- Will it invent statistics to make the post look credible? The rules forbid it, and the audit flags any figure without a nearby link; whether the cited page says what is claimed is not checked by the script.
- Does it need network access? The script does not. The agent may use its own search tools to gather sources; without them it writes no figures.
- How is it different from natural-prose-editor? That skill edits existing text; this one plans and authors a new article from a brief.
- Will the article rank? No promise is made; the skill enforces structure and originality rules only.
- Does it work in other languages? The audit patterns are English.
- Can I change the thresholds? They are named constants at the top of the script; the skill tells the agent not to edit the script to pass a check.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
