## Contents
- Choosing the list component
- FlatList tuning table
- Row component rules
- Images in rows
- Animation and heavy work

# Lists and rendering

Version tags: RN = React Native minor, SDK = Expo SDK major. "verify (unconfirmed)" means the claim was written from memory and not re-read against the docs for that version.

## Choosing the list component

| Situation | Use | Why |
|---|---|---|
| Fixed content, roughly one or two screens, no data growth (settings, a form, a detail page) | ScrollView | Simple; every child mounts at once, which is fine when the child count is small and fixed |
| Rows come from an array that can grow, any API result, any user-generated data | FlatList | Mounts only rows near the viewport |
| Grouped rows with sticky headers | SectionList | Same virtualisation, section API |
| Very long or fast-scrolling lists, or FlatList still janks after the row is memoised | FlashList (separate package) | Recycles row views instead of unmounting them. Its API changed between its 1.x and 2.x lines: 1.x asks for estimatedItemSize, 2.x targets the New Architecture and drops that prop. verify (unconfirmed) against the installed version before copying props |
| A list nested inside a vertical ScrollView | Avoid. Put the other content in the list's ListHeaderComponent / ListFooterComponent | A vertical list inside a vertical ScrollView loses virtualisation and logs a warning |
| A short horizontal strip (tabs, chips, up to roughly 15 static items) | ScrollView horizontal with a plain map | Virtualisation gains nothing at that size |

Rule of thumb used by the scanner: `.map` under ScrollView on a name that looks like data (items, results, posts, rows...) is a warn; on a name that looks like a static list (tabs, options, steps...) it is only info; `Array.from({length: N})` with N of 50 or more is a warn.

## FlatList tuning table

Defaults quoted are the documented ones for RN 0.7x; verify (unconfirmed) for RN 0.80 and later.

| Prop | Default | Change it when | Cost of changing |
|---|---|---|---|
| keyExtractor | item.key, then item.id, then index | Always set it unless items carry a unique `key` or `id` you are happy to rely on | none |
| initialNumToRender | 10 | Set to the number of rows that fill the first screen; lower for heavy rows | Too low: blank flash on first frame |
| windowSize | 21 (10 screens above, 10 below, 1 visible) | Lower (5 to 9) on memory-bound screens with heavy rows | Lower: more blank area during fast scroll |
| maxToRenderPerBatch | 10 | Lower for heavy rows if scroll drops frames | Lower: more blank area while scrolling |
| removeClippedSubviews | platform-dependent | Try on Android with long lists of simple rows | Can cause content to disappear or flicker in some layouts; test on device |
| getItemLayout | not set | Rows have one fixed height (or a computable one); enables scrollToIndex without measuring and cheaper scroll maths | Wrong heights cause misplaced scrolling |
| extraData | not set | The row depends on state that is not inside `data` (selected id, theme) | Changing it every render defeats virtualisation: keep its identity stable |

Do one change at a time and measure on a release build on a mid-range Android device. Development builds are much slower and mislead.

## Row component rules

1. The row is its own component wrapped in React.memo. An inline arrow in renderItem that builds the whole row re-creates it for every row on every parent render.
2. Pass primitive props (id, title) or stable references. A new object or arrow created in the parent for each row (style={{...}}, onPress={() => select(item.id)} built per render) breaks memoisation. Pass `id` and `onSelect` once and call `onSelect(id)` inside the row.
3. renderItem is a module-level function or wrapped in useCallback. The scanner reports an inline renderItem as info, and as warn when its body is over 400 characters (a working value, not measured).
4. Never use the index as key if rows can be added, removed, reordered or filtered.
5. Keep per-row work out of render: format dates and money once when the data arrives, not inside every row on every render.
6. A separator belongs in ItemSeparatorComponent, not as an extra element inside every row.

## Images in rows

- Give every remote image an explicit width and height; without them layout shifts as images load.
- Use a caching image component (expo-image in Expo projects; verify (unconfirmed) it is installed) rather than the core Image for long remote lists.
- Request thumbnails sized for the displayed size, not the original upload.

## Animation and heavy work

- Animated (core) needs `useNativeDriver: true` set explicitly for transforms and opacity; layout props such as width and height cannot use it.
- Reanimated runs animation logic on the UI thread; do not call JS-only functions from a worklet without the documented bridge (`runOnJS`, name valid for Reanimated 3; verify (unconfirmed) for 4).
- Defer heavy work after a screen transition with `InteractionManager.runAfterInteractions` (still present; its use shrank as the New Architecture matured; verify (unconfirmed) it fits your case).
- JSON parsing or sorting of thousands of rows on the JS thread blocks touch handling. Page the data or do the work once on arrival.
