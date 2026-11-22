## Contents
- Result
- assertNever
- Narrowing recipes
- Replacing enum
- satisfies
- Boundary parsing
- Module boundaries

# Recipes

Read the section that matches the finding or the task. Code is plain TypeScript with no dependencies.

## Result

```ts
export type Result<T, E> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

export const ok = <T>(value: T): Result<T, never> => ({ ok: true, value });
export const err = <E>(error: E): Result<never, E> => ({ ok: false, error });
```

Rules:
1. `E` is a closed union (`"too-short" | "bad-char"`, or objects with `kind`), never `string` and never `Error` for expected failures, so callers can switch on it exhaustively.
2. Check with `if (!r.ok) { ...r.error }`; the discriminant narrows both branches. Do not destructure before checking: it loses the narrowing.
3. Return `Result` for input that users or other systems control (parsing, validation, not-found, conflict). Throw for bugs and broken invariants. Do not mix: a function that returns `Result` does not also throw for its expected failures.
4. Wrapping something that throws: catch once at the edge, convert to `err({ kind: "io", cause })`, keep the original in `cause`.
5. Async: `Promise<Result<T, E>>`; never reject for an expected failure.

## assertNever

```ts
export function assertNever(x: never, message = "unhandled variant"): never {
  throw new Error(`${message}: ${JSON.stringify(x)}`);
}
```

Use as `default: return assertNever(shape);` in a `switch` over a union. If a member is added and not handled, the argument stops being `never` and compilation fails. An `if/else` chain can end with the same call. Without a helper: `default: { const exhaustive: never = shape; return exhaustive; }`.

Traps: a `default` that returns a fallback value silences the check; a `switch` over a plain `string` is not exhaustive; with `noFallthroughCasesInSwitch` each case must return or break.

## Narrowing recipes

| Need | Write |
|---|---|
| unknown to string or number | `typeof v === "string"`; for numbers also `Number.isFinite(v)` |
| unknown to object | `typeof v === "object" && v !== null`, then `"key" in v` narrows to an object with that key typed `unknown` |
| unknown to array | `Array.isArray(v)` narrows to `any[]`; assign at once to `const xs: unknown[] = v` |
| class instance | `v instanceof Foo` (fails across realms such as iframes) |
| one of several shapes | discriminant field: `if (s.kind === "circle")` |
| reusable check | `function isUser(v: unknown): v is User { ... }`, check every property the type claims, and test it |
| precondition that throws | `function assertUser(v: unknown): asserts v is User` |
| drop undefined from an array | `xs.filter((x): x is T => x !== undefined)`; plain `.filter(Boolean)` does not narrow |
| `Object.keys(o)` | returns `string[]`; iterate `Object.entries(o)`, or cast the key once with a comment for objects you built yourself |

## Replacing enum

```ts
// instead of: enum Role { Admin = "admin", Viewer = "viewer" }
export const Role = { Admin: "admin", Viewer: "viewer" } as const;
export type Role = (typeof Role)[keyof typeof Role];   // "admin" | "viewer"
```

If the values are never needed at runtime, `export type Role = "admin" | "viewer";` is enough. Call sites that wrote `Role.Admin` keep working with the const object. For a numeric enum that is serialised, keep the numbers in a `const` object and document the wire values.

## satisfies

```ts
const routes = {
  home: { path: "/", auth: false },
  admin: { path: "/admin", auth: true },
} satisfies Record<string, { path: string; auth: boolean }>;

type RouteName = keyof typeof routes;   // "home" | "admin"; an annotation would give string
```

Use it when the value must match a type but later code needs the exact literal keys or values. It checks the expression and does not change its type. Combine with `as const` when literals must stay readonly.

## Boundary parsing

```ts
const raw: unknown = JSON.parse(text);   // annotate: JSON.parse returns any
const parsed = parseConfig(raw);         // Result<Config, ConfigError>
if (!parsed.ok) return parsed;
```

Write the guard or schema once per external shape, next to the type it produces. With a schema library, derive the type from the schema so the two cannot drift. Validate at the edge; inside the program, trust the types.

## Module boundaries

- Public surface: one `index.ts` or the package `exports` map. Files outside the module import from that entry only. Enforce with a lint rule (restricted imports or a boundaries rule) rather than convention.
- Barrel files: keep one per package edge. Inside an app, import from the defining file; a barrel at every folder level produces import cycles and loads everything for one symbol.
- Cycles: if A and B import each other, move the shared type or function to C that both import. A type-only cycle is harmless at runtime but still signals a boundary problem.
- Type-only imports use `import type`, so they vanish at emit and cannot create runtime cycles.
- An exported type is public API; do not export types you do not want to support.
- Side-effect imports (`import "./polyfill"`) belong at the entry point only.
