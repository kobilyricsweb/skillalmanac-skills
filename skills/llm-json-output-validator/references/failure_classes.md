# Failure classes and remedies

## Contents

- Syntax and extraction classes
- Schema classes
- Order of fixes

The class names below are exactly the keys in `failures_by_class`.

## Syntax and extraction classes

| Class | What the script saw | Usual cause | Remedy | Do not |
|---|---|---|---|---|
| empty_output | empty or whitespace reply | refusal with no text, stop token first, stream error | Retry once; if repeated, check the request (filters, max tokens, stop sequences) | Treat as "no data" and continue |
| no_json_found | no `{` or `[` that starts a value | the model answered in words or refused | Tighten the prompt ("reply with JSON only; if you cannot, return the schema's empty form"); give the refusal a place in the schema (an `error` field) | Parse refusals as data |
| truncated | an opening bracket never closes | output token limit hit, stream cut | Raise the output limit or shrink the request (fewer items per call); retry once | Auto-close brackets: the missing part is invented |
| invalid_syntax | text is there but not strict JSON; the message may end with `would parse with rung: ...` | trailing commas, single quotes, comments, Python literals, a fence or prose that the policy forbids | If the same rung repeats on 5 or more records, enable that rung and log it; otherwise add a valid example to the prompt | Enable `all` to make the number look good |
| duplicate_key | a key twice in one object; `field` shows `$..key` (any depth) | model restating a field | Prompt fix; a parser silently keeps the last value, which may be the wrong one | Accept it because `json.loads` succeeded |

A strict-parse failure on NaN or Infinity is also `invalid_syntax`; JSON has no such values, so ask for `null`.

## Schema classes

| Class | What the script saw | Usual cause | Remedy | Do not |
|---|---|---|---|---|
| wrong_type | value of another JSON type | `null` for "unknown", object where a list was wanted | Say in the prompt how to express "unknown" (null, empty string, or omit); allow `null` in the schema if it is legitimate | Coerce silently |
| number_as_string | a string that reads as a number where a number is required | model quoting numbers | Prompt example with an unquoted number; coerce in code only for fields documented as lenient, and count how often | Coerce `"1,200"` or `"3 items"`: those are not numbers |
| missing_field | a required key is absent | the model skipped a field it thought empty | List every key in the prompt example; say what to put when unknown | Fill a default and mark the record good |
| extra_field | a key not in `properties` when `additionalProperties` is false | model adds `notes`, `reasoning` | Either allow the key if harmless, or say "no other keys"; if it adds explanations, give it a legal place | Strip it and hide the rate |
| out_of_range | number outside `minimum` or `maximum` | model ignores bounds | State bounds in the prompt text next to the field | Clamp: that fabricates a value |
| enum_violation | value not in `enum` or not equal to `const` | synonyms, different case, a new label | List the exact allowed strings in the prompt; map near-synonyms in code only from a reviewed table | Fuzzy-match unseen labels |
| pattern_mismatch | string fails `pattern` | spaces, capitals, wrong format | Show the pattern in words and one example that matches | Rewrite the string in code without logging |
| length_violation | string shorter than `minLength` or longer than `maxLength` | empty strings, long free text | Ask for a length in words or characters | Truncate: it can cut a word or a number |
| empty_array | empty list where `minItems` is 1 or more | model found nothing | Decide if empty is legitimate; if so lower `minItems`, otherwise ask for a reason field | Pad with a placeholder |
| array_size | list shorter than `minItems` (not empty) or longer than `maxItems` | counts drift | Put the exact number in the prompt; ask for fewer items per call | Drop or duplicate items |

## Order of fixes

1. `truncated`, `empty_output`, `no_json_found`: the reply is not a value yet; fix the call first.
2. `invalid_syntax`, `duplicate_key`: fix or whitelist the syntax rung.
3. Schema classes: fix the one with the highest record count, then re-run on the same records.

## Sources

Facts below, stated in our own words, were read on 2026-11-21.

- https://www.rfc-editor.org/rfc/rfc8259 : JSON text rules. Strings use double quotes only, no trailing commas, no comments, no NaN or Infinity; object member names "should" be unique, and behaviour with duplicates is unpredictable, which is why the script reports them.
- https://json-schema.org/draft/2020-12/json-schema-validation : meaning of `type`, `enum`, `const`, `minimum`, `maximum`, `minLength`, `maxLength`, `pattern` (a match anywhere in the string counts), `minItems`, `maxItems`, `required`, `properties`, `additionalProperties`. Also that `format` is an annotation by default and need not be enforced, which is why this script lists it as unsupported rather than guessing.
