// Everything below hides a pattern inside text that must NOT be reported.
// any enum Foo { A } export default x as unknown as T
/* const v: any = y!; export default z; */
const s1 = "const x: any = y!; enum E { A }";
const s2 = 'export default class {} as unknown as Q';
const t1 = `type any ${"nested"} enum E { A } as unknown as T`;
const t2 = `outer ${`inner any ${1}`} tail y!`;
const r1 = /any|enum\s+\w+|as unknown as/g;
const r2 = "a".replace(/[/]any!/, "x");
const ratio = 10 / 2 / 5;
const company = "any";
const ok = ratio !== 2 && ratio != 3;
const fn = (v: string) => /any!/.test(v);
const msg = `done: ${ok ? "yes" : "no"}`;
