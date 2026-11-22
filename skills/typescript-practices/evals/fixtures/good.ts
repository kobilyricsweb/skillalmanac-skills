export type Status = "active" | "closed";

export const MODES = ["fast", "slow"] as const;
export type Mode = (typeof MODES)[number];

export type Result<T, E = Error> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

export function parsePort(raw: string): Result<number, "not-a-number" | "out-of-range"> {
  const n = Number(raw);
  if (!Number.isInteger(n)) return { ok: false, error: "not-a-number" };
  if (n < 1 || n > 65535) return { ok: false, error: "out-of-range" };
  return { ok: true, value: n };
}

export function assertNever(x: never): never {
  throw new Error(`unexpected value: ${String(x)}`);
}

export function label(s: Status): string {
  switch (s) {
    case "active":
      return "Active";
    case "closed":
      return "Closed";
    default:
      return assertNever(s);
  }
}

const company = "any company";
const a = 1 !== 2;
const ok = !!company && !a;
const notEqual = company != "x";
export const config = { port: 80 } satisfies { port: number };
