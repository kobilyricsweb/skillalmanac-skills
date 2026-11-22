## Contents

- Where each ecosystem keeps its declaration
- Name mapping rules
- Licence-file fingerprints
- Sources

## Where each ecosystem keeps its declaration

| Ecosystem | File read | Order of use |
|---|---|---|
| npm | `node_modules/<pkg>/package.json` (scoped packages under `@scope/`) | `license` string; else `license` object with `type` (old form); else `licenses` array (old form, read as alternatives). Missing means none. |
| npm lock | `package-lock.json` `packages` entries | Only when the package is not installed locally; the lock `license` value is used if present. |
| Python | `*.dist-info/METADATA` header block (before the first blank line) | `License-Expression`; else `License` when it is a short single line; else `Classifier: License ::` lines (several are read as alternatives and the note says so). A `License` value of UNKNOWN, None or empty counts as absent. A long or multi-line `License` is treated as pasted text: not a declaration, but its opening is fingerprinted. |
| Python lock | `poetry.lock` | Name and version only. |
| Go | `go.sum` | Module path and version only; the `/go.mod` hash lines are merged into the module line. `go.mod` marks which modules are direct (no `// indirect`). |
| Rust | `Cargo.lock` | Name and version only. |

Direct versus transitive: npm uses all four dependency sections of any `package.json` found outside installed trees; Python uses names in `requirements*.txt` (normalised: lower case, runs of `-`, `_`, `.` become `-`); Go uses `go.mod`. When no manifest exists for an ecosystem the field is null, not false.

## Name mapping rules

Matching is done on a simplified form: lower case, the words licence, license and the removed, punctuation other than dots and plus signs turned into spaces. Exact SPDX ids (any letter case) are tried first.

| Stated | Normalised as | Bucket |
|---|---|---|
| MIT, MIT License, Expat | MIT | permissive |
| Apache 2.0, Apache License, Version 2.0, ASL 2.0, Apache Software License 2 | Apache-2.0 | permissive |
| Apache Software License (no version) | Apache (version unstated) | permissive |
| BSD, BSD License | BSD (clause count unstated) | permissive |
| BSD 3-Clause, New BSD, Modified BSD | BSD-3-Clause | permissive |
| BSD 2-Clause, Simplified BSD, FreeBSD | BSD-2-Clause | permissive |
| GPLv3, GNU General Public License v3 | GPL-3.0 | strong-copyleft |
| GPLv3+, GPL v3 or later | GPL-3.0-or-later | strong-copyleft |
| GPL with no number | GPL (version unstated) | strong-copyleft |
| LGPL 2.1, GNU Lesser General Public License v3 or later | LGPL-2.1, LGPL-3.0-or-later | weak-copyleft |
| MPL 2.0, Mozilla Public License 2.0 | MPL-2.0 | weak-copyleft |
| AGPL v3, GNU Affero General Public License v3 | AGPL-3.0 | strong-copyleft |
| Public Domain | public-domain | permissive |
| SEE LICENSE IN file, UNLICENSED, Proprietary, Commercial | as stated | custom |
| `MIT/Apache-2.0` (slash) | MIT OR Apache-2.0, note "slash read as alternatives" | dual |
| `(A AND (B OR C))` | kept as stated | unrecognised, note "read by hand" |

A version number with no "only" or "or later" stays bare (`GPL-3.0`); the script does not choose between only and or-later for the author.

## Licence-file fingerprints

The first 6000 characters of the first file named like LICENSE, LICENCE, COPYING or UNLICENSE (or inside a `licenses/` folder) are checked for these openings, case and whitespace ignored. A match is a hint about what the file looks like, not a determination.

| Opening phrase | Hint |
|---|---|
| "permission is hereby granted, free of charge" | MIT |
| "apache license" with "version 2.0" | Apache-2.0 |
| "redistribution and use in source and binary forms", plus "endorse or promote" or "neither the name" | BSD-3-Clause; without them BSD-2-Clause |
| "permission to use, copy, modify, and/or distribute this software for any purpose with or without fee", plus "provided that the above copyright notice" | ISC; without it 0BSD |
| "gnu general public license" with "version 3" or "version 2"; the earliest of the GNU names in the text decides between GPL, LGPL and AGPL | GPL-3.0, GPL-2.0, LGPL-3.0, LGPL-2.1, AGPL-3.0 |
| "mozilla public license" with "2.0" | MPL-2.0 |
| "eclipse public license" | EPL-2.0 or EPL-1.0 |
| "unencumbered software released into the public domain" | Unlicense |

A conflict is raised only when the hint is not compatible with any recognised declared member. An unstated version or clause count matches any value in that family.

## Sources

- SPDX licence list and expression syntax: https://spdx.org/licenses/ and https://spdx.github.io/spdx-spec/v2.3/SPDX-license-expressions/
- npm `license` field forms and the SEE LICENSE IN convention: https://docs.npmjs.com/cli/v10/configuring-npm/package-json#license
- Python core metadata fields (License, Classifier) and the License-Expression field: https://packaging.python.org/en/latest/specifications/core-metadata/ and https://peps.python.org/pep-0639/
- Go `go.sum` contents and the `// indirect` marker: https://go.dev/ref/mod#go-sum-files
