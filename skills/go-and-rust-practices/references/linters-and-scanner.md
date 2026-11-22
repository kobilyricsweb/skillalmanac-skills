# What linters cover, and what the scanner adds

## Contents
- Go: vet, staticcheck, errcheck
- Rust: rustc and clippy
- The nine scanner rules
- Suppression and false positives
- Manual fallback

Lint sets change between releases and configs. Treat the lists as the usual defaults and confirm with `go tool vet help`, the staticcheck check list, or the clippy lint index (see sources.md). A project config overrides everything here.

## Go: vet, staticcheck, errcheck

| Problem | Usual owner | Agent action |
|---|---|---|
| printf verb or argument mismatch | go vet `printf` | leave to vet |
| copying a lock by value | go vet `copylocks` | leave to vet |
| cancel function from `WithCancel`/`WithTimeout` dropped | go vet `lostcancel` | leave to vet |
| wrong second argument to `errors.As` | go vet `errorsas` | leave to vet |
| result of `fmt.Sprintf`, `errors.New` and similar discarded | go vet `unusedresult` | leave to vet |
| `wg.Add` called inside the goroutine | staticcheck SA2000 | leave to staticcheck |
| assigned value never used | staticcheck SA4006 | leave to staticcheck |
| use of a deprecated API | staticcheck SA1019 | leave to staticcheck |
| nil passed as a context | staticcheck SA1012 | leave to staticcheck |
| error string capitalised or ends with punctuation | staticcheck ST1005 | write it right the first time |
| unchecked error from a call used as a statement (`f.Close()`) | errcheck (separate tool, part of common golangci-lint setups) | leave to errcheck |
| `_ = f()` explicit discard | errcheck skips it unless blank checking is switched on | scanner rule `go-ignored-error` |
| `fmt.Errorf` with `%v` on an error | none by default | scanner rule `go-errorf-no-wrap` |
| `panic` in a library | none by default | scanner rule `go-panic-in-library` |
| goroutine with no stop signal | none by default (vet checks only a few misuse shapes) | scanner rule `go-goroutine-no-context`, then the concurrency contract |

## Rust: rustc and clippy

| Problem | Usual owner | Agent action |
|---|---|---|
| dropped `Result` or other `#[must_use]` value | rustc `unused_must_use` (warn) | leave to the compiler; `let _ =` is the explicit opt-out, so give it a reason |
| `clone()` on a `Copy` type, needless borrow, redundant closure, needless `return` | clippy default groups | leave to clippy |
| public `unsafe fn` without a `# Safety` section | clippy `missing_safety_doc` (default) | write the section |
| `unwrap()` and `expect()` in non-test code | clippy `unwrap_used`, `expect_used` (restriction, off by default) | scanner rules `rust-unwrap`, `rust-expect` |
| `unsafe` block with no `// SAFETY:` comment | clippy `undocumented_unsafe_blocks` (restriction, off by default) | scanner rule `rust-unsafe-no-safety` |
| `panic!` in library code | clippy `panic` (restriction, off by default) | error contract in SKILL.md |
| `.clone()` inside a hot loop | no general lint | scanner rule `rust-clone-in-loop`, a heuristic |
| guard held across `.await` | clippy `await_holding_lock` | leave to clippy, but apply the rule when writing |

Restriction-group lints are opt-in: the project may have switched some on in `Cargo.toml` `[lints.clippy]` or `clippy.toml`. If the project enables `unwrap_used`, expect clippy to report the same lines as the scanner; fix once.

## The nine scanner rules

| Rule | Severity | Fires on | Common false positive |
|---|---|---|---|
| `go-ignored-error` | high | line that starts with `_ = call(` or `_, _ = call(` | discarding a value on purpose (for example `_ = w.Close()` after a failed write); fix by handling, or suppress with the reason |
| `go-blank-result` | low | `v, _ := call(` or `v, _ = call(` | map or cache helpers, `strconv` calls whose failure is handled by a default; review only |
| `go-errorf-no-wrap` | medium | one-line `fmt.Errorf("...%v/%s...", ..., err)` with no `%w` | intentional chain break (add a comment and suppress) |
| `go-panic-in-library` | medium | `panic(` in a package other than `main`, outside `Must*` functions and test files | start-up invariants in `init`; suppress with reason |
| `go-goroutine-no-context` | medium | `go func(){...}()` or `go name(...)` whose text mentions no `ctx`, `context.`, `errgroup`, `g.Go`, or a channel receive | stop signal in a struct field or closed-over channel not received inside the body |
| `rust-unwrap` | high | `.unwrap()` outside test code | none by design; `unwrap_or*` is not matched |
| `rust-expect` | medium | `.expect(` outside test code | proven invariants; keep with a reason message and suppress |
| `rust-clone-in-loop` | low | `.clone()` textually inside `for`, `while` or `loop` bodies | `Arc` and `Rc` handles, `String` keys that must be owned |
| `rust-unsafe-no-safety` | high | `unsafe {`, `unsafe impl`, `unsafe extern ... {` with no `SAFETY:` on the same line, the contiguous comment lines above, or the first line inside | comment placed above a multi-line statement that begins before the `unsafe` line |

Exit code 1 comes from high and medium findings only; low findings are printed and the verdict is `review`.

## Suppression and false positives

- Put `gorust:ignore` in a comment on the flagged line, with the reason: `// gorust:ignore - closed by Close(), see poller.go`. The count appears as `suppressed` in the JSON, so a reviewer can see it.
- A suppression without a reason is a defect in the report.
- Suppress a rule only on lines you have read. Do not add the marker to whole files.
- The scan skips `vendor`, `target`, `node_modules`, `.git` and `testdata` directories, Go files ending in `_test.go`, Go files whose first 20 lines say `Code generated ... DO NOT EDIT`, and for Rust the `tests`, `benches`, `examples` directories and `build.rs` (test-style code), plus `#[test]` and `#[cfg(test)]` items.

## Manual fallback

Without Python, search the files for these, and read each hit in context:

- Go: lines starting with `_ =`; `, _ :=`; `panic(`; `go func` and `go ` followed by a call; `Errorf(` lines with `%v` or `%s` and `err`.
- Rust: `.unwrap()`; `.expect(`; `.clone()` near `for `, `while `, `loop`; `unsafe` and look one to three lines up for `SAFETY:`.

Say in the report that the manual search has no test-region or comment filtering.
