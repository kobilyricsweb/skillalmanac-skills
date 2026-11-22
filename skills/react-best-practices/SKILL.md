---
name: react-best-practices
description: Reviews, fixes and writes React components and hooks for correctness first (state, effects, keys, rules of hooks, data-fetching races), then rendering cost and accessibility, using a bundled pattern scanner and a fixed review order. Use when the user asks for a React code review or best practices, to fix or refactor a component or custom hook, to debug stale state, infinite re-renders, double fetches or lost input state, or to build a new React component in JSX or TSX. Do not use for visual design, other UI frameworks, native mobile layout or backend code.
license: Apache-2.0
compatibility: The scanner needs Python 3.9 or newer (standard library only). No network access is used. Without Python, apply the review order by hand and say the scanner was not run.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# React best practices

Most React defects come from a short list: state that should not exist, effects that should not exist, effects without cleanup, mutated state, unstable identity (keys, nested components, inline context values) and broken hook order. Work through that list in a fixed order, with `scripts/react_scan.py` as a first pass, before touching style or micro-performance.

## Workflow

Copy this checklist into the reply and tick items as they are done:

```
- [ ] 1. Context read (React version, framework, compiler, data layer)
- [ ] 2. Scanner run; each finding confirmed or dismissed with a reason
- [ ] 3. Manual review in the fixed order
- [ ] 4. Fixes applied (or code written) to the rules below
- [ ] 5. Scanner re-run; project type-check, lint and tests run if present
- [ ] 6. Report: findings by severity, changes, what was not verified
```

### 1. Read the context

Check `package.json` and the config before judging anything: React major version; framework (and whether components are server or client by default); whether the React Compiler is enabled; the data-fetching layer in use (framework loaders, a query library, or hand-written effects); TypeScript strictness; the existing lint setup. Match the project's patterns. Advice that ignores the installed version is a defect (see the version notes in [references/rendering-and-data.md](references/rendering-and-data.md)).

### 2. Scan

```bash
python scripts/react_scan.py src/components/Cart.tsx
python scripts/react_scan.py src/ --json
```

The scanner matches patterns; it does not parse. Open every finding in the code: confirm it, or dismiss it with a one-line reason. `FAIL` is a bug in nearly every case; `WARN` depends on context (an index key is fine for a list that never reorders, filters or grows at the front). Do not edit the script to silence a finding.

### 3. Manual review, in this order

Stop at each heading; do not skip ahead to performance.

1. **Purity and hook order.** Nothing in the render body writes to anything outside it or reads something that changes between renders (time, random, browser storage). Hooks run unconditionally, at the top level, before any return.
2. **State that should not exist.** For each `useState`: can it be computed from props or other state during render? Is it a copy of a prop? Do two states always change together (merge them) or contradict each other (make one a status enum)? Is it in the right component (as low as possible, lifted only as far as its readers)?
3. **Effects.** For each effect ask what external system it synchronises with. If the answer is "none", it should not be an effect. Then: complete dependencies, a cleanup for everything it starts, no race between overlapping async runs. Decision table and replacements: [references/effects-and-state.md](references/effects-and-state.md). Read it whenever an effect sets state.
4. **Updates.** State and props are never mutated (`push`, `sort`, `reverse`, `splice`, property assignment). Updates that depend on the previous value use the updater form. Handlers created inside timers, subscriptions and async code do not read stale values.
5. **Identity.** Keys are stable ids from the data, unique among siblings, on the outermost element returned from the map. No component is defined inside another component. Context values and props passed to memoised children keep their identity between renders.
6. **Data fetching.** Loading, error and empty states exist. A newer request cannot be overwritten by an older response. Requests are cancelled on unmount or parameter change. No request waterfall that could run in parallel. Prefer the project's data layer over a hand-written effect.
7. **Rendering cost.** Only after measuring or with a clear cause: expensive work in render, a provider that re-renders a large tree, long unvirtualised lists, whole-library imports. Do not add `memo`, `useMemo` or `useCallback` by default.
8. **Accessibility and semantics.** Buttons are `button`, links are `a href`; inputs have labels; images have `alt`; status changes are announced; focus is managed when content appears or disappears.
9. **Types and boundaries** (TypeScript): props typed without `any`; discriminated unions for status; event and ref types correct; nothing non-serialisable crosses a server to client boundary.

### 4. Rules for fixes and new code

- Derive, do not sync: `const visible = items.filter(...)` in render (wrapped in `useMemo` only if measured slow). Delete the state and the effect that mirrored it.
- Reset state on identity change with a `key`, not with an effect.
- Event logic goes in event handlers. An effect is not a place to react to a click.
- Every effect that subscribes, listens, starts a timer or fetches returns a cleanup. Async work uses an `AbortController` or an ignore flag set in the cleanup.
- Copy before changing: spread, `map`, `filter`, `toSorted`, or `[...list].sort()`.
- `{count > 0 && <X />}`, never `{count && <X />}`.
- Lazy initial state for anything computed or read from storage: `useState(() => read())`. Browser-only values are read in effects or handlers, not during render.
- New components ship with loading, error and empty states and with keyboard-operable controls.
- Change only what the task needs. Preserve behaviour, public props and file structure unless asked; list any behaviour change explicitly.

### 5. Verify

Re-run the scanner until no `FAIL` remains that you have not dismissed with a reason. Run the project's own type-check, lint and tests when they exist and report the commands and results. If they cannot be run, say so.

### 6. Report

```
## Review: <files>
Context: React <version>, <framework>, compiler <on/off/unknown>, data layer <...>

### Findings
| # | Severity | Where | Problem | What the user sees | Fix | Found by |
(Severity: Bug = wrong behaviour now; Risk = wrong under some sequence of events; Cost = slow or wasteful; Style = no behaviour effect)

### Changes made
### Dismissed scanner findings (with reasons)
### Not verified
<always: runtime behaviour, tests not run, performance not measured, plus anything skipped>
```

Order findings Bug, Risk, Cost, Style. Give each Bug and Risk the concrete sequence of events that triggers it.

## Limits

- The scanner is heuristic: it misses defects that span files or depend on types, and it can flag correct code. It does not replace the official lint plugin for hooks; when that plugin is installed, run it too.
- Nothing is executed. Race conditions, re-render counts and hydration errors are reasoned from the source, not observed.
- Framework-specific conventions (routing, caching, server actions) are covered only where they change how components and hooks must be written.
