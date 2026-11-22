## תקציר

- תוכן עמוד ה-skill: מימוש נאמן של עיצוב מיוצא (JSON של צמתי עיצוב) לקוד front-end, עם script שמתרגם את המאפיינים ל-CSS וממפה ל-tokens קיימים.
- אין שימוש ברשת ואין חיבור לכלי עיצוב; הקובץ המיוצא צריך להיות כבר בסביבת העבודה.
- הראיות הן מריצה אחת לכל תא, מודל אחד (haiku), כלי אחד, על קבצי JSON שנכתבו ביד בצורת ה-REST. טיוטה: לא לפרסום לפני סקירה אנושית.

---

# Listing page content: design-to-code-handoff

**One line:** Implement a design export as front-end code that matches the spec value by value and reuses the project's tokens and components.

## What it does

The skill has the agent locate the node JSON, the token source and the existing components, then run `node_to_css.py`, which prints for every layer the CSS its properties mean (auto layout to flexbox, sizing modes, fills, strokes, radii, shadows, text styles), swaps exact matches for the project's custom properties, and flags what needs a decision: off-token values, hidden layers, artboard widths, vector layers, component instances, centre-aligned strokes. A `--diff` mode prints only what changes between two frames, which becomes the breakpoint rules. The workflow then covers reuse before writing, structure by meaning rather than by layer tree, states and breakpoints that were not drawn, a value-by-value fidelity table and a deviations report.

## Capabilities

- `node_to_css.py`: translation of REST-shape node JSON to CSS declarations, per layer, with text content and element hints.
- Token mapping from a CSS custom-properties file: exact matches become `var(--name)`, near misses are flagged with the nearest tokens.
- `--diff` between two frames (for example desktop and mobile) and `--node` for one subtree.
- A property mapping reference for hand translation (layout, sizing, constraints, paints, effects, text, units that go wrong).
- A fixed report: deviations, states and breakpoints not in the design, open questions.

## When to use

Implementing a design, mockup, frame or component exactly; design handoff; redlines; "the build does not match the design".

## When not to use

Designing a new interface without a spec; editing the design file; creating a token system; exporting images.

## Requirements

Python 3.9+ for the script (standard library only). No network access. Without Python the written workflow still applies and the script step is reported as not run.

## Install

To be generated at publication: one pinned command per tool, writing to `.agents/skills/design-to-code-handoff/` and `.claude/skills/design-to-code-handoff/`.

## Examples (from saved eval runs)

1. Prompt: "Build the text field component from design/text-field.json (a component set with variants State=Default, Focus, Error, Disabled)..." Saved output: `evals/runs/h3-text-field/with_skill/` (blind grader: 34 of 35 checks against 28 of 35; the baseline fixed the width at 320px, shifted layout on focus and keyed states on classes).
2. Prompt: "Implement the hero section from design/hero.json ... two frames, Desktop (1440) and Mobile (375)..." Saved output: `evals/runs/h2-hero-responsive/with_skill/` (28 of 32 against 25 of 32; the with-skill run still left the media as an empty placeholder with no image or alt text).

## Limits

- Works from an exported file; it does not connect to any design tool.
- Grid auto layout, masks, blend modes, image crops and component property logic are flagged, not translated.
- Token matching is exact for colours and lengths; composite tokens match only when written the same way.
- Nothing is rendered: fidelity is checked value by value, not visually.
- Verified only on hand-written JSON in the REST shape, not on real exports.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one small model, Claude Code only; a blind grader preferred the with-skill output in 3 of 3. Not tested: any other tool, native triggering, human review.

## Demo script (60 to 90 seconds)

1. Show plan-card.json (raw floats, layoutMode fields) and the project's tokens.css.
2. Run the script: per-layer CSS with `var(--space-6)`, `var(--color-surface)`, and flags for the 6px gap, the off-token grey and the hidden "Old price" layer.
3. The agent reuses the existing `.btn` classes, skips the hidden layer and writes the deviations table.
4. Side by side with the baseline: same tokens, but the skill run reports both off-token values.

## FAQ seeds

- Does it connect to my design tool or need a token? No. It reads a JSON export that is already in the workspace.
- Which export format? The REST node shape used by Figma and tools that copy it.
- Does it produce React or Tailwind? It prints CSS declarations; the agent writes them in the project's conventions.
- What about hover and focus states? Only drawn variants are in the export; the skill requires the rest to be reused or listed.
- Is the result pixel-perfect? It is value-faithful. Nothing is rendered or compared visually.
- Which tools is it verified on? Claude Code only so far.
- What data leaves my machine? None.

## Changelog

- 0.1.0 (2026-11-20): first version; all evals ran on this version.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
