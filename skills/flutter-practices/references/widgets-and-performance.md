# Widgets and performance

Read for: jank, needless rebuilds, long `build`, slow lists, image cost. Claims tagged "verify (unconfirmed)" are from memory; see sources.md.

## Rebuild triage table

| Symptom | Usual cause | Fix |
|---|---|---|
| Whole screen rebuilds on every keystroke or tick | `setState` in the page widget for a value only one child uses | Move the state into the child widget, or a `ValueNotifier` read by one `ValueListenableBuilder` |
| Scroll stutters in a long list | `Column` of mapped children, or a heavy row built eagerly | `ListView.builder`; give the row a const-friendly widget class; set `itemExtent` or `prototypeItem` when rows share a height |
| Animation drops frames | `Opacity` or `ClipRRect` over a large changing subtree, which forces an off-screen layer (`saveLayer`) | `AnimatedOpacity` or `FadeTransition`; avoid clipping animated content; check with the performance overlay |
| First frame slow after navigation | Work in `build` or `initState` (parsing, sorting, sync file reads) | Do it in an isolate or ahead of time; show a placeholder |
| Images blur then stutter | Full-resolution decode for a small thumbnail | `cacheWidth` / `cacheHeight`, correct server size, `precacheImage` for the next screen |
| Jank only the first time an animation runs on some devices | Shader compilation | Check whether the current renderer (Impeller) is on for your target; behaviour differs by release (verify (unconfirmed)) |
| State lost when scrolling back | Row removed from the tree | Keep the data in the model, not in the row; use `AutomaticKeepAliveClientMixin` only for a few expensive rows |

## Composition rules

1. A widget class per visual unit. Helper methods that return `Widget` are allowed for two or three lines inside one build, never for a section.
2. Constructors: `const` constructor on every widget whose fields are final; `super.key` passed; required named parameters for anything not optional.
3. Pass data down as small values (ids, strings, ints), pass callbacks up. Do not pass the whole state object to a leaf that needs one field.
4. `const` call sites: when every argument is a literal or a constant, write `const`. Nested children of a const widget are const automatically. The lint `prefer_const_constructors` finds most cases; the scanner reports the leftover heuristic cases as info.
5. Keys: no key for static children; `ValueKey(id)` for rows in a list that reorders or deletes; `GlobalKey` only for a measured need (form state, scaffold) and never created inside `build`.
6. Layout: do not wrap a `Column` or `Row` child in `Expanded` unless the parent has bounded size; an unbounded main axis (a `ListView` inside a `Column`) needs `Expanded` or `shrinkWrap` (shrinkWrap costs layout on every item, so avoid it for long lists).
7. Use `SafeArea`, `MediaQuery.paddingOf` (verify (unconfirmed) for the minimum version of the `...Of` accessors) and `LayoutBuilder` rather than fixed pixel offsets for status bar, notch or keyboard.
8. Avoid `Container` when only one property is needed: `Padding`, `SizedBox`, `DecoratedBox`, `ColoredBox` are cheaper and const-friendly.

## Rebuild scope checklist

```
- [ ] The widget that calls setState is the lowest one that owns the changing value
- [ ] Expensive children are const or live in separate classes with unchanged inputs
- [ ] Provider reads use the narrowest selector available (select, buildWhen)
- [ ] No Future, Stream or controller is created in build
- [ ] No setState in build (the scanner reports direct calls)
```

## Measuring

- Run `flutter run --profile` on a real mid-range device. Debug mode is deliberately slow and a simulator has a different GPU path.
- Use the DevTools performance view: a frame over the budget (about 16.7 ms at 60 Hz, 8.3 ms at 120 Hz) is jank; check whether the UI thread or the raster thread is the slow one before choosing a fix. UI thread slow means too much Dart work in build or layout; raster thread slow means expensive painting (layers, clips, large images, shaders).
- The widget rebuild counter in the IDE inspector shows which widgets rebuild; confirm a const or split change drops the count.
- Record a before and after number. If you did not measure, say "not measured" in the report.

## Thresholds used by the scanner

| Rule | Info | Warn | Basis |
|---|---|---|---|
| Build method length | over 80 lines | over 150 lines | Working values from review practice; not measured optima |
| Null assertions per file | 4 or more | 8 or more and at least 2 per 100 code lines | Working values |

Change a threshold only by editing a copy of the script, never to make a finding vanish.
