---
name: context-window-packer
description: Packs one prompt's context under a fixed token budget by ranking files as must, should or nice, dropping duplicates, lockfiles and secret-looking text, shrinking files to signatures or a stub, and keeping a 15 percent reserve, then returns strict JSON of what was included or left out and why, with a stated estimate error. Use when the user asks what fits in the context window, which files to paste, how to trim context to N tokens, or says the prompt is too long or the context is overflowing. Do not use for chunking documents for retrieval, pricing token spend, shortening replies, or compacting a running chat.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only, and works offline. Without Python, follow the manual procedure in the last section.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Context window packer

Decide what goes into one prompt when the window is limited, and leave a record of every choice. The unit of work is a single package for a single question: a fixed budget, a list of candidates, a result that says kept, compressed or dropped, and why.

## Inputs to collect first

Ask only for what is missing. Do not start packing without a budget and a question.

| Input | Default if the user does not know |
|---|---|
| `budget`: the window in tokens | none; ask. Use the smaller of the model's window and what the user wants to spend |
| `fixed_tokens`: instructions and the question itself | estimate them with `estimate` on a saved copy |
| `reserve`: tokens kept free for reasoning and the answer | 15 percent of the budget (the floor; a lower figure is raised to it) |
| candidates: `id`, `path`, `priority` (must, should, nice), optional `relevance` 0 to 10 (default 5), `note` | none; every candidate needs a priority |

Priority is the user's call, not yours. Must means the answer is wrong or impossible without it. If the user marks everything must, say that the budget cannot be honoured and ask which half is really should.

## Decision tables

Allowed forms per priority (the compression ladder):

| Priority | full | signatures | summary stub | drop |
|---|---|---|---|---|
| must | yes | only if the item lists `"allow": ["signatures"]` | only if its `allow` lists `"summary"` | never; error `must_exceeds_budget` instead |
| should | yes | yes | yes | last resort, reason `no_room` |
| nice | yes | yes | no, because a stub costs tokens and answers nothing | yes |

Order of selection:

1. Must items first, in full. If they exceed the usable space, shrink only those that allow it, largest first. If they still do not fit, report the error and stop packing: do not quietly demote a must item.
2. Then all should items, then all nice items. A tier is never raised above an earlier tier because of relevance.
3. Inside a tier, highest relevance per estimated full token first; ties go to the earlier item in the list.
4. An item is shrunk only when its full text does not fit the space still left, never to make room for a lower-ranked item.

Usable space = `budget` - `fixed_tokens` - reserve. Reserve is at least 15 percent of the budget because reasoning and the answer count against the same window.

Forms: signatures are an outline (definition lines and first docstring lines for Python and similar code, headings for Markdown, keys for JSON and YAML, header plus 3 rows for CSV, first 15 lines otherwise). A form is only offered if it costs at most 70 percent of the full text. The summary stub is the user's `summary` text, or one generated line with path, line count, size and first line.

Never pack, whatever the priority: binary or non-UTF-8 files, minified files (a line over 1,500 characters in a file of 5,000 bytes or more), text matching a secret pattern (`KEY=value` or `KEY: value` lines whose name holds PASSWORD, PASSWD, SECRET, TOKEN or API_KEY with a value of 6+ characters that is not a `$`, `os.` or `process.env` reference; JWTs, meaning three base64url segments starting `eyJ`; RSA, EC, OpenSSH, PGP and plain private-key blocks; `AKIA` access key ids; `sk-`, GitHub and Slack tokens). An excluded file is listed by path and pattern name only; the matched value is never printed. Applies unless the item sets `allow_secret_match` after the user confirmed it is a harmless sample. Generated lockfiles are dropped unless marked must. Exact duplicates (same text after trimming line-end spaces) keep the higher-priority copy.

## Workflow

```
- [ ] 1 Collect budget, reserve, fixed tokens, candidates with priorities
- [ ] 2 Write manifest.json beside the files
- [ ] 3 Run pack, read errors and warnings first
- [ ] 4 Fix the inputs, never the script, and re-run
- [ ] 5 Write the package with --out and give the report
```

1. Collect the inputs. Save the question text to a file and run `python scripts/pack_context.py estimate question.txt` to get `fixed_tokens`.
2. Write `manifest.json` next to the files (paths are relative to it and may not leave its folder):

```json
{"budget": 32000, "reserve": 6000, "fixed_tokens": 900,
 "candidates": [{"id": "app", "path": "src/app.py", "priority": "must", "relevance": 9, "note": "entry point"},
                {"id": "docs", "path": "docs/api.md", "priority": "nice", "relevance": 3}]}
```

3. Run `python scripts/pack_context.py pack manifest.json`. Exit 0: no errors. Exit 1: at least one error (a must item does not fit, is missing, is binary or looks like a secret). Exit 2: bad input, with a message saying what to fix.
4. Read `errors`, then `warnings`, then `dropped`. Typical fixes: raise the budget, downgrade a must to should with the user's agreement, allow a must item to shrink, split the question. If `margin_worst_case` is negative, drop one nice item or supply a measured ratio (see references).
5. Write the package: `python scripts/pack_context.py pack manifest.json --out package.md`. The script refuses an output path that is the manifest or any candidate, even with `--force`, and will not replace an existing file without `--force`. Items are written must first, then should, then nice. Put the question after the package, not inside it.

Run the script; do not edit it to make a check pass.

## Output contract

`pack` prints one JSON object. Keys, always present:

| Key | Meaning |
|---|---|
| `schema_version` | `"1"` |
| `status` | `ok` or `error` |
| `budget`, `fixed_tokens`, `reserve` | `reserve` has `requested`, `effective`, `min_pct` (15) |
| `usable`, `used` | tokens available and estimated tokens in the package, headers included |
| `kept[]` | items in full: `id`, `path`, `priority`, `level` ("full"), `tokens`, `relevance`, `reason`, optional `note` |
| `compressed[]` | same plus `tokens_full`; `level` is `signatures` or `summary` |
| `dropped[]` | `id`, `path`, `priority`, `tokens_full`, `reason_code`, `reason` |
| `margin` | `usable` - `used`; negative means the must items alone overflow |
| `margin_worst_case` | `usable` minus `used` raised by `estimate_error_pct`; the safe figure to trust |
| `estimate_error_pct` | token-weighted plus or minus percentage of the estimate |
| `estimator` | the ratios applied and the label "approximate; no tokenizer was run" |
| `warnings[]`, `errors[]` | `code`, `id`, `message` |

Drop reason codes: `duplicate`, `binary`, `minified`, `possible_secret`, `lockfile`, `empty`, `missing_file`, `path_outside_root`, `too_large`, `unreadable`, `no_room`. Warning codes: `reserve_raised`, `user_ratio_used`, `lockfile_flagged`, `worst_case_overflow`. Error codes: `must_exceeds_budget`, `must_unusable`.

## Report to the user

Show a table, then the lines below:

```
Included: <n> in full, <n> compressed (<tokens> of <usable> usable, margin <margin>, worst case <margin_worst_case>)
Left out: <id and reason code for each dropped item>
Estimate: approximate, plus or minus <estimate_error_pct> percent; no tokenizer was run
Decisions for you: <any must item that is blocked, any nice item removed to protect margin>
Not checked: whether the model needs something that was left out; relevance scores are the user's, not measured
```

## Estimating tokens

The script counts ASCII characters divided by a ratio by file type (prose 4.0, code 3.3, data formats 3.0, other 3.5) plus one token per non-ASCII character, plus a few tokens per item header. These ratios are rules of thumb, not measurements: the error is stated as 20 percent for prose, 25 for code, 30 for data and unknown types, 40 when over a fifth of the text is non-ASCII, and 10 when the user supplies a ratio. A user ratio comes from counting a real sample with the target model's own counter: tokens divided into characters. Read [references/estimator-and-ladder.md](references/estimator-and-ladder.md) when the user wants the reasoning, wants to calibrate the ratio, or asks why the order is must, should, nice.

## Manual fallback

Without Python: list each candidate with its character count, divide by 4 for prose or 3.3 for code, add 10 percent for headers and uncertainty, and fill the usable space in the same order: must, then should, then nice, highest relevance per token first. Offer headings or signatures before dropping a should item. Report the same five lines and say the arithmetic was done by hand.

## Limits

- Token counts are estimates. The real count can differ by the stated error or more, and different models count differently. Treat `margin_worst_case` as the number to trust.
- Duplicate detection is exact after whitespace trimming; near-duplicates and files that quote each other are not found.
- Signatures are syntactic outlines. Decorated or multi-line definitions in languages other than Python are shown by their first line only.
- Relevance and priority are supplied by the user. The script ranks; it cannot judge whether the omitted text mattered.
- The secret check matches the named shapes only (credential-named assignments, JWT, private-key blocks, AKIA, sk-, GitHub, Slack). A clean result is not a guarantee that a file holds no secret.
- One package for one question. It does not manage a growing conversation, chunk documents for retrieval, or price the spend.
- Tool definitions, images and attachments are not read; include their cost in `fixed_tokens`.
