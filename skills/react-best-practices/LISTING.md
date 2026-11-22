## תקציר

- תוכן עמוד ה-skill: סקירה, תיקון וכתיבה של רכיבי React לפי סדר בדיקה קבוע, עם סורק דפוסים מצורף.
- אין שימוש ברשת; ה-script קורא קבצי מקור מקומיים בלבד והוא היוריסטי (לא parser).
- שם ה-skill מכיל שם של ספרייה (React) - לבדיקת הבעלים מול כלל "בלי סימני מסחר בשם".
- הראיות הן מריצה אחת לכל תא, מודל אחד (haiku), כלי אחד. טיוטה: לא לפרסום לפני סקירה אנושית.

---

# Listing page content: react-best-practices

**One line:** Review, fix and write React components and hooks for correctness first, with a pattern scanner and a fixed review order.

## What it does

The skill makes an agent read the project context (React version, framework, compiler, data layer), run `react_scan.py`, confirm or dismiss each finding, then review in a fixed order: purity and hook order, state that should not exist, effects, updates, identity (keys, nested components), data fetching, rendering cost, accessibility, types. It gives rules for fixes and new code, requires the project's own checks to be run when present, and ends with a report that orders findings as Bug, Risk, Cost, Style with the triggering sequence for each bug. Two references hold the effect decision table, stale-closure and state-structure rules, a symptom table, memoisation rules and version notes.

## Capabilities

- `react_scan.py`: about 30 heuristic patterns (hooks after an early return or inside conditions, async effect callbacks, effects without cleanup, fetch without cancellation, effects that only copy state, effect loops, stale closures with empty dependencies, state mutation, set-state during render, nested component definitions, unstable or missing keys, `count &&` rendering 0, eager state initialisers, browser globals read during render, inline context values, missing memo dependencies).
- A nine-step review order that puts correctness before performance.
- An effect decision table: what to use instead of an effect, case by case.
- A symptom table: from "input loses focus" or "old results flash" to the usual cause.
- Version notes so advice matches the installed major version.

## When to use

React code review; fixing or refactoring a component or custom hook; stale state, infinite re-renders, double fetches, lost input state; building a new JSX or TSX component.

## When not to use

Visual design, other UI frameworks, native mobile layout, backend code, end-to-end tests.

## Requirements

Python 3.9+ for the script (standard library only). No network access. Without Python the written workflow still applies and the script step is reported as not run.

## Install

To be generated at publication: one pinned command per tool, writing to `.agents/skills/react-best-practices/` and `.claude/skills/react-best-practices/`.

## Examples (from saved eval runs)

1. Prompt: "ProductSearch.jsx has bugs: users report old results flashing over new ones, a stray 0 on the page..." Saved output: `evals/runs/r2-fix-productsearch/with_skill/ProductSearch.fixed.jsx` (blind grader: 13 of 13 key items against 11 of 13 for the baseline, which had no error state and no keyboard-operable results).
2. Prompt: "Write InviteMembers.tsx for a React 18 + TypeScript app..." Saved output: `evals/runs/r3-build-invite/with_skill/InviteMembers.tsx` (13 of 13 against 11 of 13; the baseline reset state with an effect and could not submit with Enter).

## Limits

- The scanner is heuristic: it misses defects that span files or depend on types and can flag correct code. It does not replace the official hooks lint plugin.
- Nothing is executed: races, re-render counts and hydration errors are reasoned from source.
- Framework conventions are covered only where they change how components and hooks are written.
- On a pure review task a capable model without the skill found the same defects (eval r1 was a tie).

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one small model, Claude Code only; a blind grader preferred the with-skill output in 2 of 3 (r1 tie). Not tested: any other tool, native triggering, human review.

## Demo script (60 to 90 seconds)

1. Show ProductSearch.jsx and the bug report (old results flash, a stray 0).
2. The agent runs the scanner: 1 FAIL, 3 WARN on the saved run, each confirmed in the code.
3. It removes the mirrored state and the syncing effect, adds cancellation, an error state and real buttons.
4. Scanner re-run: 0 FAIL, 0 WARN. Close on the "Not verified" list.

## FAQ seeds

- Does it need internet access? No.
- Does it replace ESLint and the hooks plugin? No. Run them too; the scanner is a first pass that needs no install.
- Does it work with Next.js? The component and hook rules apply; server and client component rules are covered briefly.
- Will it add useMemo everywhere? No. It checks for the compiler first and prefers structural fixes.
- Which React versions? The notes distinguish 18 and earlier from 19 and later.
- Which tools is it verified on? Claude Code only so far.
- What data leaves my machine? None.

## Changelog

- 0.1.0 (2026-11-20): first version; all evals ran on this version.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
