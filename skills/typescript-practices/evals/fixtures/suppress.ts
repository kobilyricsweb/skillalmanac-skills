// ts-scan-ignore: non-null-assertion -- the element is created two lines above
const el = document.getElementById("root")!;
const el2 = document.getElementById("other")!; // ts-scan-ignore
const el3 = document.getElementById("third")!; // ts-scan-ignore: explicit-any
const cfg: any = el3; // ts-scan-ignore: explicit-any -- third-party payload, validated below
