# Listing page content: image-prompt-direction

**One line:** Writes image prompts like an art director and lints them for gaps, contradictions and rights problems.

## What it does

The skill gives an agent an eight-field prompt contract (subject, composition, camera/lens, lighting, palette, style, negative, aspect ratio) with weights, a six-step brief-to-prompt procedure, a table for turning named references into plain descriptions, and iteration rules that change one field per version. A lint script reads the prompt file and reports missing fields, a completeness score, rights hits (living artists, real people, trademarks, likeness phrases), 12 kinds of contradictory terms, aspect ratio problems and filler words, as strict JSON. A second command compares two versions and says whether more than one field changed.

## Capabilities

- `scripts/prompt_lint.py lint`: JSON with fields found, score out of 100, findings and a verdict of pass, revise or blocked
- `scripts/prompt_lint.py diff`: JSON listing which fields changed between two versions; `ok` when at most one
- A vocabulary guide for lens, lighting, composition, palette and style terms
- Documented rights lists (29 living artists, 33 public figures, 59 brands and franchises) with finding codes
- A fixed report: score, assumed slots, translated references, warnings kept, what was not checked

## When to use

You say write an image prompt, prompt for a hero image, product photo prompt, why do my AI images look generic, or fix this prompt; or you have a brief and need a prompt a generator can follow.

## When not to use

Editing or retouching an existing image, video prompts, logo design, layout and typography, alt text, or any request to copy a living artist or put a real person's face in an image. The skill declines those and offers a description-based alternative.

## How it differs from nearby skills

`prompt-writing` covers prompts for language models. This skill covers only image prompts and adds the contract, the lint script and the rights rules. `canvas-poster-design` builds the layout of a poster; this skill writes the prompt for a generated picture.

## Requirements

Python 3.9 or newer, standard library only, no network. Without Python the agent follows the contract and checklist by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real fixture runs of the script (`python evals/run_fixtures.py` saved in `evals/fixtures/RESULTS.txt`):

1. `python scripts/prompt_lint.py lint evals/fixtures/bad_contradiction.txt`: exit 1, verdict `revise`, score 100, four `contradiction` errors: golden hour against overcast, photorealistic against flat vector, 16 mm wide-angle against 200 mm telephoto, shallow depth against everything in focus. The clause "no night sky" is correctly ignored.
2. `python scripts/prompt_lint.py lint evals/fixtures/bad_rights.txt`: exit 1, verdict `blocked`, score 90; errors for a living artist, a public figure and two trademarks, plus a warning for an unknown name after "inspired by".
3. `python scripts/prompt_lint.py diff evals/fixtures/iter_v1.txt evals/fixtures/iter_v2_two_changes.txt`: exit 1, `ok` false, changed fields composition and lighting.

No with-skill agent run exists yet, so there is no saved agent-written prompt to show.

## Limits

- English only; unlabelled fields are detected by keywords and are approximate.
- Twelve contradiction pairs; a deliberate pair is flagged and should be rewritten.
- The rights lists are short and illustrative; a clean lint is not legal clearance.
- The script cannot see the generated image.
- One prompt per file; vendor-specific negative syntax is left to the user.

## Evidence

See `VERIFICATION.md`: static lint 0 FAIL and 0 WARN, 12 of 12 script fixture cases pass. Not tested: efficacy against a baseline, trigger behaviour, native discovery, cross-tool installs, human review.

## FAQ seeds

- Does it need network or an API key? No.
- Does it work with my generator? The contract is vendor-neutral; the script does not call any generator.
- Why does it refuse artist names? Naming a living artist asks the model to imitate them; the skill describes the look instead.
- Can I use my own brand? Yes, with `--allow "<brand>"` when you own it; the report records it.
- How is it different from a general prompt skill? It is image-specific and ships a linter.
- How do I uninstall? Delete the folder.

## Changelog

0.1.0, 2026-11-21: first draft. Static lint and script fixtures only.

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
