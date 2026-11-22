---
name: typescript-practices
description: Writes and reviews strict, maintainable TypeScript. Sets a tsconfig strictness baseline, replaces any, non-null assertions, double casts, enums and bare ts-ignore with unknown plus narrowing, discriminated unions, satisfies, exhaustive switches and Result-style errors, and ships a scanner that lists these anti-patterns by line. Use when the user asks to make TypeScript stricter, remove any, fix type errors the right way, review .ts or .tsx files, set up tsconfig strict, choose type or interface, or model errors in types. Do not use for plain JavaScript, framework-specific design (React, Angular), build-tool configuration, or runtime schema library comparisons.
license: Apache-2.0
compatibility: The optional scanner needs Python 3.9 or newer, standard library only, no network. Running the project's own tsc needs Node and a local TypeScript install. Without Python, search for the patterns in the rule table by hand.
metadata:
  license: Apache-2.0
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# TypeScript practices

Write TypeScript where the compiler does the checking and escape hatches are rare, visible and explained. Fix code by changing the types or the flow, not by silencing the compiler.

## Workflow

```
- [ ] 1 Find the checker commands and the current strictness
- [ ] 2 Scan the target files
- [ ] 3 Fix findings with the replacement table
- [ ] 4 Write new code with the defaults below
- [ ] 5 Run the project's type check and the scan again
- [ ] 6 Report
```

1. **Find the commands.** Read the `package.json` scripts and every `tsconfig*.json` the target files fall under (follow `extends`). Note the type-check command (usually `tsc --noEmit`), the linter, and which flags from [references/tsconfig.md](references/tsconfig.md) are already on. Do not turn flags on in the middle of a bug fix; propose them in the report. If the user asked for strictness work, enable one flag at a time and fix its errors before the next (order in tsconfig.md).
2. **Scan.** `python scripts/ts_scan.py <files or dirs>` prints one JSON object. Use `--profile app` for application code (turns off the default-export rule); keep the default `library` for published packages. Each finding is a candidate: read the line before changing it. Without Python, search for the patterns in the table by hand.
3. **Fix** using the table. Never fix a finding by moving the same escape hatch elsewhere (a type alias of `any`, `!` replaced by `as T`).
4. **New code** follows the defaults below.
5. **Verify.** Run the type-check command, then re-run the scan. Every remaining finding is either fixed or carries `// ts-scan-ignore: <rule> -- <reason>` saying why the hatch is needed. Run the scanner; do not edit it to make it pass.
6. **Report** in the fixed shape at the end.

## Replacement table (scanner rule, what to do)

| Rule | Replace with | Keep only when |
|---|---|---|
| `explicit-any` | `unknown` at boundaries, then narrow; a generic `<T>`; a named interface for the real shape; `Record<string, unknown>` for bags | A third-party type forces it. Comment why and confine it to one function with a precise return type |
| `non-null-assertion` | An `if (x === undefined)` guard that returns or throws; optional chaining with a default; a lookup helper returning `T \| undefined`; a guard function | The invariant is proven in the same function and a check would be dead code; say so in a comment |
| `double-assertion` | A type guard `v is T` with real checks; fixing the upstream type; a schema parse at the I/O edge | Not in app code. In tests, one assertion with a comment |
| `ts-nocheck` | Fix the file, or isolate the untyped part behind a `.d.ts` | Never |
| `ts-suppression-no-reason` | `// @ts-expect-error <what is wrong, ticket or date>` | Never without the reason |
| `ts-ignore-prefer-expect-error` | `@ts-expect-error` (it fails once the error is gone) | The error differs between TypeScript versions you support |
| `enum` | String-literal union, or `as const` object plus `type X = (typeof X)[keyof typeof X]` | A runtime reverse mapping is needed and the whole toolchain is yours |
| `default-export` | `export const name` or `export function name` | A framework or tool requires it (page, route, config, story). The usual file names are exempt already; use `ts-scan-ignore` for the rest |
| `definite-assignment` | Initialise in the constructor, make the field optional, or build through a factory | A framework injects the value after construction; comment it |

## Defaults for new code

- **Boundaries.** Data from `JSON.parse`, `fetch().json()`, `process.env`, storage, `postMessage` and query strings is `unknown` until a guard or schema validates it. `JSON.parse` and `Response.json()` return `any`: annotate the result as `unknown` on the same line. Under `strict`, `catch (e)` is `unknown`; narrow with `e instanceof Error`.
- **Expected failures are values, bugs are throws.** A function whose failure is part of normal input returns `Result<T, E>` with `E` a closed union (string literals or `{ kind: ... }` objects). Invariant violations throw. Recipe in [references/patterns.md](references/patterns.md#result).
- **Discriminated unions** with one literal field (`kind`, `type`, `ok`) model states. Do not use several optional fields that are only valid together.
- **Exhaustive switches** end in `default: return assertNever(x)` (patterns.md). Adding a union member must break the build in every switch that ignores it.
- **`satisfies`** checks a value against a type while keeping its narrow inferred type (config maps, route tables, `as const` data). Use an annotation to get the wide type. Use `as` only for narrowing the compiler cannot see, after a runtime check.
- **Narrowing** order of preference: control flow (`typeof`, `in`, `instanceof`, equality, discriminant), then a guard `v is T`, then `asserts v is T`, then `as`. A guard that returns `true` without checking every property its type claims is a lie; test it.
- **Index access.** With `noUncheckedIndexedAccess` on, `arr[i]` is `T | undefined`: handle it, do not add `!`. Prefer `for...of`, `.at()`, `Map.get`.
- **Immutability.** `readonly` properties and `ReadonlyArray<T>` for parameters you do not mutate; `as const` for literal tables.
- **Module boundaries.** One public entry per package (`index.ts` or the `exports` map); other modules import only from it, never from internals. `import type` for type-only imports (required by `verbatimModuleSyntax`). One barrel at the package edge, none inside an app. No import cycles: move the shared type to a third module. Details in patterns.md.

## type or interface

| Situation | Use |
|---|---|
| Union, intersection of unions, tuple, primitive alias, mapped or conditional type, function type | `type` (interface cannot express these) |
| Object shape that other code extends, a class implements, or a package user may augment by declaration merging | `interface` |
| Object shape that must be assignable to `Record<string, unknown>` or an index-signature type | `type` (interfaces have no implicit index signature; object-literal type aliases do) |
| Plain object shape, none of the above | Either; follow what the project already does and stay consistent |
| Deep `extends` chains of large shapes where compile or editor speed matters | `interface` with `extends` (resolved by name and cached; intersections are recomputed) |

## Report format

```
Scanned: <files, profile>; findings before -> after: <n -> n>
Fixed: <rule: count, how>
Kept on purpose: <file:line, rule, reason>
Type check: <command and result, or "not run: reason">
Suggested next (not done): <tsconfig flags, remaining areas>
Not checked: <what the scanner cannot see>
```

## Scripts

`scripts/ts_scan.py <paths> [--profile library|app] [--min-severity low|medium|high] [--ignore-rule R] [--include-dts] [--max-findings N]`: run it. Strict JSON with `total_findings`, `counts_by_rule`, `findings[]` (`file`, `line`, `column`, `rule`, `severity`, `message`, `snippet`), `suppressed[]`, `files_scanned`, `rules`, `limits`. Exit 0 no findings, 1 findings, 2 usage error or no files. Skips `node_modules`, build output and `.d.ts`. Reads only; writes nothing.

## Limits

- The scanner is a tokenizer plus regular expressions with no type information. It finds the written word `any`, not values that are `any` by inference: `JSON.parse` results and untyped library returns slip past it. The full list is in the `limits` field of its output.
- It can flag JSX text, an identifier named `any`, or a default export a framework requires, and can miss a `!` at a line end in `.tsx`. Treat each finding as a question.
- A clean scan is not a type-safety proof. Only the project's own `tsc` run is.
- Flag advice assumes TypeScript 5.x; check the project's version before enabling a flag that needs a newer one (tsconfig.md marks them).
- Library choices (schema validators, error-handling libraries) are out of scope; the recipes use plain TypeScript.
- Reference files: read [references/tsconfig.md](references/tsconfig.md) for tsconfig work and [references/patterns.md](references/patterns.md) for the recipe you need; [references/sources.md](references/sources.md) lists where each fact comes from.
