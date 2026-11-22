## Contents
- Baseline and order of enabling
- Flag table
- Module settings by project kind
- Expected fallout

# tsconfig strictness baseline

Read this when setting up or tightening a tsconfig. Each row says what the flag makes the compiler reject, so you can predict the fallout.

## Baseline and order of enabling

Target set for a new project: `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `noImplicitReturns`, `noFallthroughCasesInSwitch`, `noPropertyAccessFromIndexSignature`, `verbatimModuleSyntax`, `isolatedModules`, `skipLibCheck`.

For an existing code base, enable in this order and commit after each step, so every step is a reviewable error list:
1. `noImplicitAny`, then `strictNullChecks` (the two that find real bugs; separate steps if the error count is large)
2. the rest of `strict` (`strictFunctionTypes`, `strictBindCallApply`, `strictPropertyInitialization`, `noImplicitThis`, `useUnknownInCatchVariables`, `alwaysStrict`)
3. `noUncheckedIndexedAccess`
4. `noImplicitReturns`, `noFallthroughCasesInSwitch`, `noImplicitOverride`
5. `exactOptionalPropertyTypes` and `noPropertyAccessFromIndexSignature` (most intrusive; last)

`"strict": true` enables the whole group of eight at once. An explicit entry for one member overrides the group, so during migration set `"strict": true` only after every member passes individually.

## Flag table

| Flag | Rejects | Typical fallout |
|---|---|---|
| `strict` | The group of eight checks above | The bulk of errors in a loose code base |
| `noUncheckedIndexedAccess` | Treating `arr[i]` or `obj[key]` as defined | Many "possibly undefined" errors where code indexes arrays |
| `exactOptionalPropertyTypes` | Assigning `undefined` to `a?: T` unless the type says `T \| undefined` | Spread/merge code and payload builders |
| `noImplicitOverride` | Overriding a base method without the `override` keyword | One keyword per override |
| `noImplicitReturns` | A function that returns a value on some paths only | Few; usually real bugs |
| `noFallthroughCasesInSwitch` | A non-empty `case` that falls into the next | Few; add `break` or `return` |
| `noPropertyAccessFromIndexSignature` | `obj.key` on a type that only has an index signature; forces `obj["key"]` | Env and config bags |
| `verbatimModuleSyntax` | Imports used only as types without `import type`; emit follows the source exactly | Import lines across the code base |
| `isolatedModules` | Constructs that cannot be compiled one file at a time (re-exporting a type without `export type`) | Few |
| `noUncheckedSideEffectImports` (5.6 and later) | `import "x"` of a module that does not resolve | Rare |
| `erasableSyntaxOnly` (5.8 and later) | Syntax that is more than type annotations: `enum`, runtime `namespace`, constructor parameter properties, `import x = require()` | Needed to run TypeScript directly with Node's type stripping; every `enum` the scanner reports |
| `useUnknownInCatchVariables` | `catch (e)` typed as `any` | Part of `strict` |
| `skipLibCheck` | Skips checking `.d.ts` files, so broken third-party typings do not fail the build | Keep on; hides only dependency typings, not your own code |
| `noUnusedLocals`, `noUnusedParameters` | Unused declarations | Prefer the linter, which can autofix and allows `_` prefixes |

## Module settings by project kind

| Project | `module` | `moduleResolution` | Notes |
|---|---|---|---|
| Node package or service run by Node | `nodenext` | `nodenext` | Relative imports need the `.js` extension in source; the package `type` field decides ESM or CJS per file |
| App built by a bundler (Vite, webpack, esbuild) | `esnext` or `preserve` | `bundler` | Extensionless imports allowed; set `noEmit` and let the bundler emit |
| Library published to npm | `nodenext` | `nodenext` | Set `declaration` and an `exports` map; test the built package from a clean project |

## Expected fallout

On a code base with no strictness, expect the first two steps to produce roughly one error per 20 to 50 lines of code. This is a planning guess, not a measurement. Do not bulk-fix with `any`, `!` or `// @ts-ignore`: it turns a visible error list into invisible debt, and the scanner will report each one.
