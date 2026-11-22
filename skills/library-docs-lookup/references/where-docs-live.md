## Contents

- npm, pnpm, Yarn
- Python
- Go
- Sources checked

# Where a package's own docs live, by ecosystem

Read only the section for the ecosystem in use.

## npm, pnpm, Yarn

- **Installed copy.** `node_modules/<pkg>/`. Under pnpm that path is usually a symlink into `node_modules/.pnpm/<name>@<version>/node_modules/<name>`; the script follows both. The lockfile line (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`) gives the version that was resolved at install time and a line to cite.
- **Which type file applies.** Open the package's `package.json`. If it has an `exports` map, the entry for the exact import specifier decides which file is loaded, and the nested `types` condition names its declaration file. Without `exports`, the top-level `types` or `typings` field applies, then `index.d.ts` beside `main`. `typesVersions` can redirect declarations by compiler version, so a path in `types` may not be the final file. The script lists the declared files and warns when a declared path is missing.
- **Subpaths.** `import x from "pkg/server"` resolves through `exports["./server"]`, not through the root declaration. Read that file for that import.
- **`@types/*`.** Types for packages that ship none. Scoped names are flattened with a double underscore (`@scope/name` becomes `@types/scope__name`). Its version number follows the library by major and minor only, so a patch difference between the two is normal and is not a mismatch. The script reports it as `installed_types`.
- **README and changelog** sit in the package root when the author published them. Many packages leave the changelog out of the tarball and keep it only on the project site; then there is nothing local to read.
- **Plug'n'Play (Yarn).** No `node_modules` exists. Packages are zip files under `.yarn/cache`. The script warns; ask the user to unplug the package or install with a node_modules linker, or label the answer `UNVERIFIED`.
- **Workspaces.** A hoisted dependency may sit in a parent folder's `node_modules`. The script looks up to 3 parents. Two copies with different versions can exist; the nearest one wins at runtime for code in that folder.
- A `deprecated` message in the installed `package.json` is surfaced as a warning. Report it.

## Python

- **Names.** Distribution name (what you install) and import name (what you import) can differ. Names compare after lowercasing and collapsing runs of `-`, `_`, `.` to one hyphen, so `Acme.Tools`, `acme_tools` and `acme-tools` are one distribution. The import name comes from `top_level.txt` or from the first path segments in `RECORD` inside the `.dist-info` folder.
- **Installed copy.** `site-packages/<name>-<version>.dist-info/` holds `METADATA` (headers such as Version, Requires-Python, Project-URL, then the long description) and `RECORD` (every installed file). The `Version:` header is the installed version.
- **Which file answers what.** `__init__.py` shows what the package exports and its module docstring. A `py.typed` file next to it means the package's own annotations are meant to be used by type checkers. `.pyi` stub files, or a sibling `<name>-stubs` folder, give signatures for checkers; the `.py` file is what actually runs, so read both when behaviour and signature may differ.
- **Lazy exports.** If a name is absent from `__init__.py`, search the package folder and look for a module-level `__getattr__` before saying it does not exist.
- **Virtualenv locations.** Windows `Lib/site-packages`, POSIX `lib/python3.x/site-packages`, plus `__pypackages__`. The script checks `.venv`, `venv`, `env`, `.env`, `virtualenv` and the project folder itself. A system interpreter's packages are not searched.
- **Lock files.** `poetry.lock` and `uv.lock` list `[[package]]` tables with `name` and `version`. `requirements*.txt` gives a pinned version only when written with `==`; any other specifier is a range and says nothing about what is installed.
- **Cross-check, optional.** In the project's own environment, `inspect.signature` on an imported function shows the real signature. Importing runs package code, so do it only for packages the project already imports.

## Go

- **Which version builds.** `go.mod` `require` lines select it. `go.sum` can list several versions, including old ones kept for checksums, so it is evidence of existence, not of selection. A `replace` line in `go.mod` means the build uses different code than the published module; the script warns.
- **Source on disk.** With vendoring, `vendor/<module path>/` and `vendor/modules.txt` (which carries the version). Without it, the module cache. The script does not read the cache; use `go list -m -f "{{.Version}} {{.Dir}}" <module>` to learn the folder, and `go doc <module path>.Symbol` to print the documentation comment and signature from local source.
- **Docs are comments.** Exported identifiers are documented by the comment directly above them; the package comment is usually in `doc.go` or the top of a file. Test files (`*_test.go`) often hold the best usage examples (`Example...` functions).

## Sources checked

Read in the platform's research pass; the facts above are restated in the editors' own words.

- Node.js package `exports` and conditions: https://nodejs.org/api/packages.html
- TypeScript, publishing declarations and `typesVersions`: https://www.typescriptlang.org/docs/handbook/declaration-files/publishing.html
- DefinitelyTyped naming and versioning of `@types`: https://github.com/DefinitelyTyped/DefinitelyTyped#readme
- pnpm symlinked `node_modules` layout: https://pnpm.io/symlinked-node-modules-structure
- Yarn Plug'n'Play: https://yarnpkg.com/features/pnp
- PEP 503, name normalisation: https://peps.python.org/pep-0503/
- PEP 561, `py.typed` and stub packages: https://peps.python.org/pep-0561/
- Installed distribution layout (`.dist-info`, `METADATA`, `RECORD`): https://packaging.python.org/en/latest/specifications/recording-installed-packages/
- Go modules reference (`go.mod`, `go.sum`, vendoring): https://go.dev/ref/mod
- `go doc`: https://pkg.go.dev/cmd/go#hdr-Show_documentation_for_package_or_symbol
