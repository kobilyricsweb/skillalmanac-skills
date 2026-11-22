# Listing page content: context-window-packer

**One line:** Chooses which files fit one prompt's token budget and records what was kept, shrunk or dropped, and why.

## What it does

You give a budget, a reserve for the answer and a list of candidate files marked must, should or nice. The skill fills the usable space in that order, highest relevance per token first inside each tier. When full text does not fit, a should or nice file can be cut to an outline of its signatures, and a should file can become a one-line stub. Duplicates, binary and minified files, lockfiles and text that looks like a secret never go in. The result is strict JSON listing every item as kept, compressed or dropped with a reason code, plus the remaining margin and a stated error range for the token estimate. A script does the estimate and the selection offline; no tokenizer is downloaded and no model is called.

## Capabilities

- `scripts/pack_context.py pack`: JSON manifest of kept, compressed and dropped items, margin, worst-case margin, estimate error
- Optional `--out package.md` writes the packed context (must first, then should, then nice); it never overwrites the manifest or a candidate file
- `scripts/pack_context.py estimate`: token estimate with error range for any file
- Decision tables for the compression ladder, tier order and the 15 percent reserve
- A reference on calibrating your own characters-per-token ratio

## When to use

You say what fits in the context window, which files to paste, trim this to N tokens, or the prompt is too long, and you can name your must-have files.

## When not to use

Splitting documents for retrieval (see `rag-chunking-planner`), pricing token spend (`llm-cost-estimator`), finding where agent sessions burned tokens (`agent-session-cost-review`), shortening the model's replies (`terse-output-mode`), or compacting a conversation. This skill builds one package for one question from files you already have.

## Requirements

Python 3.9 or newer, standard library only. No network. Tested only on Windows 11 with Python 3.11.

## Install

Copy the `context-window-packer` folder (without `LISTING.md`, `VERIFICATION.md` and `evals/`) into `.claude/skills/` or `.agents/skills/`. Not yet pinned to a release.

## Examples

Prompt: "Build the context for the delivery-date bug from these files. Budget 1000 tokens, 50 used by my question. README.md and app.py are must-have, util.py is important, notes.md is nice, package-lock.json is not important."

Real output of `python scripts/pack_context.py pack evals/fixtures/proj/manifest_tight.json` (abridged):

```
status: ok   budget 1000, fixed 50, reserve 150 (raised from 0), usable 800
used 741, margin 59, margin_worst_case -108, estimate_error_pct 22.5
kept:       readme full 172 | app full 205 | notes full 199
compressed: util signatures 165 (full did not fit: 501 > 423 left)
dropped:    lock, lockfile
warnings:   reserve_raised, worst_case_overflow
```

Second example, same files, budget 400 and no reserve: exit 1, `must_exceeds_budget` (the two must files need 377 tokens, 340 are usable), `util` dropped as `no_room`. Passing `"allow": ["signatures"]` on `app` turns it into exit 0: `app` is kept as signatures (58 tokens) and `util` as a summary stub (46).

## Limits

- Token counts are estimates (plus or minus 20 to 40 percent by file type, 10 percent with a user-measured ratio); `margin_worst_case` is the number to trust.
- Duplicates are found only when text is identical after trimming trailing spaces.
- Signatures are outlines; non-Python code is outlined by first lines of definitions.
- Priority and relevance come from you; the script cannot judge what the model needs.
- The secret check matches five common shapes and is not a guarantee.
- It builds one package; it does not manage a long conversation.

## Evidence

Script fixtures: 21 of 21 cases pass (`python evals/run_fixtures.py`, 2026-11-21, Windows 11, Python 3.11). Static lint: 0 FAIL, 0 WARN. Not tested: efficacy against a baseline, trigger rates, any other tool, any other operating system, human review. See `VERIFICATION.md`.

## Demo script (60 to 90 seconds)

1. Prompt: "Fit these five files into 1,000 tokens for my date bug; README and app are must-have."
2. The agent writes `manifest.json` and runs `pack`.
3. Beat: the report shows the reserve raised to 150, `util.py` shrunk to signatures because full text needed 501 of 423 tokens left, the lockfile dropped.
4. Beat: the agent points out the worst case is 108 tokens over and suggests dropping `notes.md`.
5. After: a `package.md` with three full files and one outline, plus the reasoned manifest.

## FAQ seeds

- Does it need the network or a tokenizer? No; estimates come from a documented ratio table with a stated error.
- How accurate are the counts? Within 20 to 40 percent by file type; calibrate a ratio with your model's counter to get 10 percent.
- How is it different from `rag-chunking-planner`? That splits documents for retrieval; this chooses among whole files for one prompt.
- Will it drop my must-have file? Never; it reports an error and asks you to decide.
- Does it send my files anywhere? No; it reads the paths in your manifest, offline, and refuses paths outside the manifest folder.
- Can it overwrite my files? No; `--out` refuses the manifest and every candidate path, even with `--force`.
- How do I uninstall? Delete the folder.

## Changelog

0.1.0, 2026-11-21: first draft; script fixtures only, not re-verified elsewhere.

## License and authorship

Apache-2.0, Copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5 under the Skill Almanac Editorial byline; accountable publisher Global Media Holdings. No human review has taken place yet.
