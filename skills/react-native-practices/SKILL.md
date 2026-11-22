---
name: react-native-practices
description: Guides an agent writing or reviewing React Native and Expo mobile app code to avoid common mistakes in lists, navigation, state and data fetching, platform code, permissions, accessibility and release, with a scanner script that flags ScrollView map lists, inline renderItem, missing keyExtractor, leftover console.log and wrong Platform.OS values. Use when the user works on a React Native or Expo app, asks about FlatList lag, Platform.OS, permission prompts, EAS builds, or a mobile code review. Do not use for React web apps, Next.js, Flutter, native Swift or Kotlin, or app store marketing.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, run the manual checks in step 4.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# React Native practices

Mobile-only rules for React Native (RN) and Expo code. Web React rules (DOM, hydration, bundle splitting for browsers) are out of scope.

## Version rule

Before giving any API advice, read `package.json` and note the `react-native` minor, the `expo` SDK major (if present), the navigation library (`expo-router` or `@react-navigation/native` and its major) and whether the New Architecture is on (`newArchEnabled` in app config; recent SDKs default to on). State these in your answer. A claim tagged "verify (unconfirmed)" in the references is from memory: say so to the user and point to [references/sources.md](references/sources.md) instead of presenting it as fact.

## Workflow

```
- [ ] 1 Read versions and project layout
- [ ] 2 Classify the task
- [ ] 3 Apply the matching rules
- [ ] 4 Run the scanner (or the manual checks)
- [ ] 5 Fix, re-run, report
```

1. **Read versions** as above. Find where screens, components and navigation config live.
2. **Classify** the task with this table and read only the matching reference.

| Task | Rules in | Read |
|---|---|---|
| Slow list, janky scroll, long screen | Lists section below | [references/lists-and-rendering.md](references/lists-and-rendering.md) |
| New screen, deep link, login flow, params | Navigation and data below | [references/navigation-state-data.md](references/navigation-state-data.md) |
| Fetching, caching, storing tokens | Navigation and data below | [references/navigation-state-data.md](references/navigation-state-data.md) |
| iOS vs Android difference, web target | Platform below | [references/platform-permissions-a11y.md](references/platform-permissions-a11y.md) |
| Camera, photos, location, notifications | Permissions below | [references/platform-permissions-a11y.md](references/platform-permissions-a11y.md) |
| Screen reader support, tap targets | Accessibility below | [references/platform-permissions-a11y.md](references/platform-permissions-a11y.md) |
| Preparing a store or OTA release | Release below | [references/release-checklist.md](references/release-checklist.md) |

3. **Apply** the rules below. Prefer the smallest change that fixes the stated problem; do not restructure navigation in a list-performance task.
4. **Scan.** Run `python scripts/rn_scan.py <folder>` on the changed folders and read the JSON (contract below). Without Python, search the changed files for: `ScrollView` blocks containing `.map(`, `renderItem={(`, list tags without `keyExtractor`, `console.log`, and `Platform.OS ===` with a capital letter. Never edit the script to make a finding go away.
5. **Fix and report.** Resolve every `warn`; for each `info` either fix or give a one-line reason it is fine. Re-run until the warn count is 0 or each remaining warn is explained. End with the report format at the bottom.

## Lists

- ScrollView is for short, fixed content. A `.map` over an API array, user data or anything that can grow goes in FlatList (or FlashList when measured need exists).
- Always give `keyExtractor` returning a stable unique id. Never the index when rows can be added, removed, reordered or filtered.
- The row is its own `React.memo` component. `renderItem` is a module-level function or `useCallback`. Do not create per-row arrows or style objects in the parent.
- Do not nest a vertical list in a vertical ScrollView; use `ListHeaderComponent` and `ListFooterComponent`.
- Tuning props (`initialNumToRender`, `windowSize`, `getItemLayout`, `removeClippedSubviews`) one at a time, measured on a release build on a mid-range Android device. The table with defaults and costs is in [references/lists-and-rendering.md](references/lists-and-rendering.md).

## Navigation and data

- One root navigator; tabs in it; stacks in tabs. Auth is two separate trees chosen at the root, not a login screen pushed on top.
- Route params hold ids and small primitives. Never whole objects or functions.
- State goes to the lowest owner: local, then route params, then query cache for server data, then a small store only for non-server shared state. Do not copy server data into a store.
- In RN, query-library focus and online refetching must be wired to AppState and a network package; set `staleTime` deliberately.
- Tokens go in keychain-backed storage (`expo-secure-store` in Expo), never AsyncStorage.

## Platform code

- Whole component differs: `.ios.tsx` / `.android.tsx` files. One value: `Platform.select` in one module. A few checks per file at most (the scanner reports above 3).
- `Platform.OS` values are lowercase `ios`, `android`, `web`. A capitalised string is always false.
- No bare numbers for status bar, notch or keyboard height; use safe-area insets.

## Permissions

Ask in context, read status first, handle three outcomes (granted, denied but can ask again, denied and cannot ask again), and in the last case offer `Linking.openSettings()`. Re-check on app foreground. Provide a degraded path. iOS needs a purpose string per sensitive API, and a new permission needs a new native build. Full procedure: [references/platform-permissions-a11y.md](references/platform-permissions-a11y.md).

## Accessibility

Every icon-only touchable needs `accessibilityLabel` (the action, not the icon) and a role. Keep `accessibilityState` in step with visual state. Touch targets at least 44 by 44 points (iOS) and 48 by 48 dp (Android); use `hitSlop` for small visuals. Verify with VoiceOver and TalkBack on a device, not only a simulator.

## Release

Walk [references/release-checklist.md](references/release-checklist.md) item by item. Store requirements (target API level, privacy manifests) change often: tag them "verify (unconfirmed)" and tell the user to confirm on the store page on release day.

## Script contract

`python scripts/rn_scan.py <file-or-folder> [...]`: run it, do not edit it. Reads .tsx and .jsx only; writes nothing; no network. Prints one JSON object:

```
{"schema_version": 1, "tool": "rn_scan", "files_scanned": int,
 "findings": [{"file", "line", "rule", "severity": "warn"|"info",
               "confidence": "high"|"medium"|"low", "match", "why", "fix"}],
 "counts_by_rule": {rule: int}, "summary": {"warn": int, "info": int},
 "skipped": [{"file", "reason"}], "limits": [str]}
```

Rules: `scrollview-map`, `inline-renderitem`, `missing-keyextractor`, `index-as-key`, `console-log`, `platform-literal-invalid`, `platform-magic-number`, `platform-branch-density`. Exit 0: no warn. Exit 1: at least one warn. Exit 2: no readable .tsx/.jsx, with a plain message on stderr. Severity and confidence come from fixed rules (names that look like data lists, a literal `length: 50` or more, an inline `renderItem` body over 400 characters); they are guesses, not measurements. A finding is a place to look, not a proven defect.

## Report format

```
Versions: <react-native, expo SDK, navigation lib, new architecture on/off/unknown>
Changed: <files and the rule each change follows>
Scan: <warn and info counts before and after; remaining findings with reason>
Verified on device: <what was run on a device or simulator, or "nothing">
Unconfirmed claims: <the verify (unconfirmed) items you relied on>
Not checked: <e.g. performance not measured, store requirements not re-read>
```

## Limits

- Regex scan, not a parser. It misses dynamically built props and list tags in other file types, and cannot see props that arrive through a spread.
- It cannot know array length; the `scrollview-map` severity is a naming guess.
- `console.log` is flagged unless `__DEV__` appears on the same or previous line; a different guard is flagged.
- Comments are masked, and `console.log` or `Platform.OS` text that begins inside a quoted string literal is ignored (fixture `bad/Strings.tsx`). A `Platform.OS` check inside a template literal `${...}` is missed.
- Thresholds (3 platform checks, 400 characters, length 50) are working values, not measured optima.
- Library details (React Navigation 6 vs 7, FlashList 1 vs 2, TanStack Query majors, EAS field names, store requirements) change; the references mark what was not confirmed.
- Nothing here measures runtime performance. Profile on a release build before claiming a speed-up.
- Not for web React (use a web-focused skill), Flutter, or native iOS/Android code.
