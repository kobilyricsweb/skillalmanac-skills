# Backtracking risks and pitfalls (documented list)

The script's `static_flags[].id` values map to the rows below. Severity decides whether the verdict can be "pass": any `high` flag, or a confirmed growth in the probe, makes the verdict `risky`.

## Speed risks

| id | severity | Example | Why it blows up | Safer shape |
|---|---|---|---|---|
| `nested_quantifier` | high | `^(a+)+$`, `(\w+\s?)*$`, `(.*a)+x` | An unbounded repeat wraps a body that itself starts or ends with an unbounded repeat over the same characters, so a failing input can be split between loop passes in exponentially many ways. | Remove one level: `^a+$`, `^(\w+\s?)*$` becomes `^\w+(\s\w+)*$` (the separator is now mandatory) |
| `nullable_repeat_body` | high | `(a?)+b`, `(\s*)*x` | The loop body can match nothing. Python guards the empty loop, so the probe may show no blow-up here, but other engines can loop or backtrack heavily (verify (unconfirmed)). | Make the body consume at least one character |
| `overlapping_alternation` | high or medium | `(a\|a)+b`, `(.\|a)+x` | Two alternatives inside an unbounded repeat can both match the same text. High when both alternatives are a single token. | Make alternatives start with different characters, or merge them |
| `overlapping_alternation_prefix` | medium | `(a\|ab)+c` | One alternative is a prefix of another inside a loop. Often only linear; the probe decides. | Order and shape alternatives so a longer one cannot be shadowed, or anchor what follows |
| `nested_quantifier_delimited` | medium | `(\d+,)+` | Loop around an inner repeat, but a mandatory delimiter separates the passes. Usually safe. | Keep the delimiter mandatory; confirm with the probe |
| `adjacent_overlapping_repeats` | medium | `\d+\d+x`, `\s*\s*$` | Two unbounded repeats in a row can claim the same characters; time grows as a power of the length (quadratic for two). | Delete the redundant one, or put a literal between them |
| `multiple_dot_repeats` | low | `.*a.*b` | Several `.*` in one sequence; polynomial on long non-matching text. | Use a negated class (`[^,]*`) or an anchored, lazy shape |

Shapes the scan does not flag, so check them by eye: a bounded repeat around an unbounded one (`(.*,){11}P`, polynomial of high degree), backreferences, and lookaheads containing loops.

Python merges single-character alternatives into a class when it compiles, so `(\d|\w)+` is a plain class loop there. Engines that do not merge may blow up on it (verify (unconfirmed)). The scan reports what Python sees.

## Correctness pitfalls

| id | severity | Pitfall | Fix |
|---|---|---|---|
| `unanchored_in_search_mode` | medium | In search mode a pattern without `^` and `$` accepts any text that contains a valid value | Anchor both ends, or use fullmatch |
| `dollar_allows_trailing_newline` | medium | In Python `$` also matches just before a final `\n`, so `^abc$` accepts `"abc\n"` under search | Use `\Z`, or fullmatch |
| `range_A_to_z` | medium | `[A-z]` includes `[ \ ] ^ _` and a backtick | `[A-Za-z]` |
| `single_dot_between_tokens` | low | An unescaped `.` such as `\d+.\d+` or `example.com` matches any character | `\.` |
| `pipe_in_class` | low | `[a\|b\|c]` matches a pipe character, it is not alternation | `[abc]` or `(?:a\|b\|c)` |

## Other traps, not scanned

- Greedy versus lazy: `<.+>` on `<a><b>` takes the whole string; `<.+?>` or `<[^>]+>` takes one tag.
- Case: matching is case-sensitive unless the `i` flag is set; the adversarial case `case_flipped` shows which way the pattern behaves.
- `\d`, `\w`, `\s` in Python str patterns are Unicode-aware (`٣` matches `\d`); `re.ASCII` or `[0-9]` narrows them. The adversarial case `arabic_indic_digits` tests this.
- Empty input: a pattern built from `*` and `?` alone matches `""`; the adversarial case `empty` shows it.
