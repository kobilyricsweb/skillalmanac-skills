# Listing page content: slide-deck-builder

**One line:** Plans, writes and checks presentation decks, with speaker notes and a validator for outlines and .pptx files.

## What it does

The skill gives an agent a deck contract with numbers (one message per slide, a takeaway headline of at most 15 words, 6 lines and 50 words per main slide, one sourced chart per slide, 25 to 220 words of speaker notes, an appendix for detail) and an eight-step procedure: brief, one-sentence message, headline spine, evidence and body, notes, validate, generate, inspect and report. A standard-library script checks a Markdown or JSON outline, or an existing .pptx read as zip and XML, and prints strict JSON. The skill names python-pptx, Marp and reveal.js as generator options with when to pick each, and never installs anything on its own.

## Capabilities

- `scripts/deck_check.py <file>`: JSON report with slide count, per-slide lines, words, notes words, charts and images, and findings for crowded slides, topic headlines (no verb), missing or thin notes, duplicate headlines, charts without a source, more than one chart, images without descriptions, and (for .pptx) text under 12 pt or 18 pt
- Deck structures by purpose, a slide-count rule from the time slot, the evidence slide pattern, a speaker notes template and visual rules (sizes, contrast, colour)
- A fixed closing report that lists placeholders and what was not checked

## When to use

You ask for a presentation, slide deck, pitch deck or board update, or you have slides that feel wordy, topic-titled or note-less and want them tightened or reviewed.

## When not to use

Brand templates and theme design, Word or PDF reports, posters, or one chart with no deck. Neighbours: `word-document-builder` covers Word documents and `pdf-extraction-and-forms` covers PDFs; this skill covers the argument and structure of a presentation and checks it.

## Requirements

Python 3.9 or newer for the checker (standard library only). No network. A generator (python-pptx, Marp or reveal.js) only if the user wants a file and approves its installation. Without Python the agent checks the rule table by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both outputs below come from `evals/run_fixtures.py` fixtures; no with-skill agent run exists yet.

1. Prompt: "Check this deck outline before I present it." Command: `python scripts/deck_check.py evals/fixtures/bad_deck.json`. Output (abridged): 3 slides, no appendix, `counts` 4 errors and 3 warnings, `ok` false; findings: slide 1 `missing-notes`; slide 2 `headline-topic`, `notes-thin`, `chart-no-source`, `image-no-alt`; slide 3 `duplicate-headline`, `headline-topic`. Exit code 1.
2. Prompt: "Is this good deck ready?" Command: `python scripts/deck_check.py evals/fixtures/good_deck.md`. Output: 5 slides, appendix starts at slide 5, 0 errors, 0 warnings, `ok` true. Exit code 0.

## Limits

- The topic-headline check is a verb word list, not grammar: it misses some topic headlines and flags some real takeaways.
- Only explicit font sizes in a .pptx are seen; template-inherited sizes are not. Image descriptions and chart sources are checked for presence, not quality.
- No fact, contrast, overflow or visual check; the agent must render and look.
- Thresholds are working values for a live 16:9 talk, not measured optima.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and the 10 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a messy five-slide outline with topic titles; run the checker: 7 errors, 4 warnings.
2. The agent writes the headline spine and reads it aloud as a story, then moves the introduction to an appendix.
3. It adds notes and a Source line, reruns the checker: `ok` true.
4. The closing report names placeholders and what was not checked.

## FAQ seeds

- Does it need network access? No.
- Will it install python-pptx or Marp? No; it names the command and waits for your approval.
- Does it work on an existing .pptx? It reports slide count, text per slide, notes, images without descriptions and explicit small fonts; it does not edit the file.
- Why a 6-line limit? It is a default for live talks; the skill says how to relax it for decks that are read instead of presented.
- Can it match my company template? The contract is independent of design; python-pptx can use your template.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
