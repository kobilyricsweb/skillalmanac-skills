# Listing page content: react-native-practices

**One line:** Mobile-specific rules and a scanner that help an agent avoid common React Native and Expo mistakes.

## What it does

The skill makes the agent read the project's React Native, Expo and navigation versions first, then pick the rule set for the task (lists, navigation and data, platform code, permissions, accessibility, release) and read only the matching reference. A regex scanner, `scripts/rn_scan.py`, walks .tsx and .jsx files and reports eight documented anti-patterns with line numbers, severity and confidence as strict JSON. The agent fixes, re-runs, and closes with a fixed report that lists unconfirmed claims and what was not checked.

## Capabilities

- `scripts/rn_scan.py`: flags ScrollView with `.map`, inline `renderItem`, list tags without `keyExtractor`, index keys, leftover `console.log`/`debug`/`info`, invalid `Platform.OS` strings, per-platform magic numbers and files with many platform checks
- Decision table for ScrollView, FlatList, SectionList and FlashList; FlatList tuning table with defaults and costs
- Three-outcome permission procedure with the "cannot ask again" path
- Release checklist for Expo (EAS) and bare projects, with store requirements marked unconfirmed
- Claims that depend on a React Native, Expo or library major are tagged "verify (unconfirmed)"

## When to use

You work on a React Native or Expo app and ask about list lag, `Platform.OS`, permission prompts, navigation structure, tokens, EAS builds, or want a mobile code review.

## When not to use

React web apps and Next.js, Flutter, native Swift or Kotlin, store marketing copy. It does not measure runtime performance.

## How it differs from react-best-practices (batch_01)

That skill covers React for the web. This one covers only mobile concerns that web React rules do not: virtualised lists, native permissions, platform splits, store and OTA release, and a scanner built for RN-specific patterns. (The two were not compared line by line; the folder bodies in other batches were deliberately not read.)

## Requirements

Python 3.9 or newer for the scanner (standard library only). No network. Without Python the agent follows the manual checks in SKILL.md step 4.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real scanner runs on saved fixtures (no with-skill agent run exists yet):

1. `python scripts/rn_scan.py evals/files/t1-slow-feed`: exit 1; `console-log` (warn, line 13), `scrollview-map` (warn, medium, line 16), `index-as-key` (info, line 17).
2. `python scripts/rn_scan.py evals/fixtures/bad/Layout.tsx`: exit 1; `platform-branch-density` (info, line 4), `platform-literal-invalid` for `'iOS'` (warn, line 4), `platform-magic-number` (info, line 5).
3. `python scripts/rn_scan.py evals/fixtures/good`: exit 0, no findings.

## Limits

- Regex scan, not a parser; props from a spread are invisible.
- Array length is unknown; ScrollView severity is a naming guess.
- Thresholds are working values, not measured.
- Library and store details change; unconfirmed items are tagged.
- Nothing measures runtime performance.

## Evidence

See `VERIFICATION.md`. Passed: static lint, 8 script fixture cases. Not tested: efficacy against a baseline, trigger behaviour, native discovery, cross-tool use, human review, and all version-dependent facts.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Show a laggy notes screen; the agent reads `package.json` and states the versions.
2. Run the scanner: warn for ScrollView map and console.log, info for index key.
3. The agent switches to FlatList with a memoised row and stable keys; re-run shows zero warn.
4. The agent reports what was not measured on a device.

## FAQ seeds

- Does it need network? No.
- Does it work in Expo Go? It is advice and a file scanner; it does not run your app.
- Will it tell me the exact current store rules? No; it marks them unconfirmed and points to the sources list.
- Does it cover React Native Web? Only the platform-boundary rules; web React concerns are out of scope.
- Why does the scanner flag a short ScrollView map as info only? It cannot know the length; names that look like static lists get low severity.
- How is it different from a general React skill? See above.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures only.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet; accountable editor: Global Media Holdings.
