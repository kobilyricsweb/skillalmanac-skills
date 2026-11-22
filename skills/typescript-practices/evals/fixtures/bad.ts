import { readFileSync } from "node:fs";

export enum Status {
  Active,
  Closed,
}

const enum Mode { Fast = "fast" }

export default function load(path: string): any {
  const raw = JSON.parse(readFileSync(path, "utf8")) as any;
  const el = document.getElementById("root")!;
  const cfg = (raw as unknown as Config).settings;
  return { el, cfg };
}

// @ts-ignore
const a: number = "x";

// @ts-ignore legacy typings break here until the vendor ships v3
const b: number = "y";

// @ts-expect-error
const c: number = "z";

// @ts-expect-error vendor type is wrong for empty arrays, see ticket 4412
const d: number = [];

/* @ts-nocheck */

class Box {
  value!: string;
  items: Array<any> = [];
  find(x: unknown, y: Record<string, any>) {
    return this.items.find((i) => i.id === x)!.name;
  }
}

function cast<T = any>(v: unknown) {
  return <any>v;
}

export { cast as default };
