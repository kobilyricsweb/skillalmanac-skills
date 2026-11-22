# Theming, accessibility and platform channels

Read for: theme setup, dark mode, screen readers, text scale, tap targets, native integration. Claims tagged "verify (unconfirmed)" are from memory; see sources.md.

## Theming

- One `ThemeData` per brightness, built in one file. Seed a `ColorScheme` (for example from a seed color) rather than assigning dozens of colors by hand; override only the roles a design really changes.
- Screens read `Theme.of(context).colorScheme.<role>` and `textTheme.<style>`. A literal `Color(0xFF...)` or `fontSize:` in a screen is a finding unless it is a brand asset.
- Material 3 is the default for new apps in recent releases (verify (unconfirmed): the release where `useMaterial3` became true by default); set it explicitly if the project must not change look on upgrade.
- Opacity helpers on colors changed in recent releases (`withOpacity` deprecated in favour of an alpha-based method; verify (unconfirmed)): check the analyzer message rather than guessing.
- Dark mode: supply `darkTheme` and `themeMode`; test with the platform setting and with a user override. Images and icons with baked-in white backgrounds break dark mode.
- Custom tokens (spacing, radii) go in a `ThemeExtension` or a small constants class, not copied numbers.

## Accessibility checklist

```
- [ ] Every icon-only button has a tooltip or Semantics label that names the action ("Delete note", not "trash")
- [ ] Images that carry meaning have semanticLabel; decorative images are excluded from semantics
- [ ] Tap targets at least 48 x 48 logical pixels (Material); never below 44 x 44 (iOS guideline)
- [ ] Text contrast at least 4.5:1, large text at least 3:1; information is never colour alone
- [ ] Layout survives text scale 1.5 and 2.0 without clipped text or overflow stripes
- [ ] Focus order follows reading order; custom widgets are reachable with a keyboard or switch control
- [ ] State changes announced when the user needs to know (error appears, item deleted)
- [ ] Verified with TalkBack on Android and VoiceOver on iOS on a device
```

Semantics tools: `Semantics` (label, button, header, selected, enabled, value), `MergeSemantics` to read a row as one item, `ExcludeSemantics` for decoration, `tooltip` on `IconButton`. Use `tester.getSemantics` or the semantics debugger overlay while developing. Do not put a label on a widget that already derives one from its text.

Text scale: layouts use `Flexible`/`Expanded`, `Wrap`, minimum heights rather than fixed heights for text containers. Read the scale with the current accessor for text scaling (verify (unconfirmed): `MediaQuery.textScalerOf` replaced the scalar factor in newer releases).

## Platform channels: boundaries

When to write one: no maintained plugin covers the native capability. Check the plugin ecosystem and the federated plugin interfaces first. If the need is a C library, consider FFI instead of a channel (verify (unconfirmed) current tooling).

Contract rules:

1. One channel name per feature, reverse-domain style (`com.example.app/battery`), defined as a constant in Dart and in native code.
2. Arguments and results use only types the standard message codec supports (null, bool, numbers, strings, byte arrays, lists, maps). Convert dates to ISO strings or integers; send ids, not objects.
3. Errors use typed codes: the native side returns an error with a short code and message; Dart maps `PlatformException.code` to a domain failure. A missing implementation raises `MissingPluginException`; handle it for platforms you do not support.
4. Calls are asynchronous. Never call a channel from `build`; call from an event handler, notifier or repository.
5. Native handlers run on the platform main thread by default, so blocking native work freezes the UI; hop to a background thread there. Calling channels from a background isolate needs explicit setup (verify (unconfirmed): `BackgroundIsolateBinaryMessenger` and its minimum version).
6. When more than three methods exist, generate the Dart and native sides from one interface definition (a code generator such as Pigeon) so types cannot drift.
7. Wrap the channel in a small Dart class behind an interface so tests can fake it. Test the native side separately.
8. Streams of native events use an event channel; cancel the subscription in `dispose`.

Permission flow: check status first, ask in context, handle three outcomes (granted, denied but can ask again, denied permanently with a link to settings), re-check when the app returns to the foreground, keep a degraded path. A new sensitive permission needs a native manifest or plist entry and therefore a new build; a Dart-only hot reload does not apply it.
