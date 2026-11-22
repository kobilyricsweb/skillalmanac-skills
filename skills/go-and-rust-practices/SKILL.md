---
name: go-and-rust-practices
description: "Use when the user asks for idiomatic Go or Rust, a Go or Rust code review, error handling help, or says the agent keeps writing unwrap, panic or bare goroutines. Gives fixed contracts for errors (Go wrapped, sentinel or typed; Rust thiserror versus anyhow), concurrency (goroutine lifetime and context; ownership across threads), layout and tests, plus a script listing anti-patterns by line: ignored errors, panic or unwrap in library code, goroutines without context, unsafe without SAFETY, clone in loops. Do not use for other languages, build or CI setup, language comparisons, or rewrites between languages."
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only. No network access, no compiler, no Go or Rust toolchain. Without Python, apply the tables below by hand and grep for the patterns in references/linters-and-scanner.md.
metadata:
  license: Apache-2.0
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Go and Rust practices

Write Go and Rust the way the project's best code already reads, and do not repeat what the compiler and the default linters report. This skill supplies decision tables, numeric limits and a scanner for the patterns linters leave off.

## Workflow

```
- [ ] 1 Read the project's own rules
- [ ] 2 Baseline scan
- [ ] 3 Write or edit with the tables
- [ ] 4 Run the project's linters and tests if they exist
- [ ] 5 Re-scan and resolve every finding
- [ ] 6 Report
```

1. **Project first.** Read `go.mod` (the `go` line), `Cargo.toml` (`edition`, `rust-version`, `[lints]`), `.golangci.yml`, `clippy.toml`, CI config, and two or three existing files. Project conventions beat this skill. Record the Go and Rust versions; several rules below change with them.
2. **Baseline.** `python scripts/gorust_scan.py scan <path>` on the files you will touch. Keep the output to compare later.
3. **Write** using the tables in this file. Open a reference only for the matching language: [references/go-contracts.md](references/go-contracts.md) for code templates (typed errors, errgroup fan-out, table tests, layout), [references/rust-contracts.md](references/rust-contracts.md) for thiserror and anyhow templates, scoped threads, async traps, layout and tests.
4. **Linters.** Run what the project has: `go vet ./...`, `staticcheck ./...`, `go test -race ./...`; `cargo clippy --all-targets`, `cargo test`. Do not hand-fix what they print by default; fix what they report, nothing more. If a tool is missing or cannot run, say so in the report. Which tool covers which problem: [references/linters-and-scanner.md](references/linters-and-scanner.md). Pages behind the facts: [references/sources.md](references/sources.md), read only to confirm a version-dependent rule.
5. **Re-scan** the same paths. Each finding is fixed, or suppressed with `gorust:ignore` on that line plus a reason in the same comment. Never delete the script's rules or edit the script to get a clean result.
6. **Report** in the shape at the end.

## Go: error contract

| The caller needs | Use | Shape |
|---|---|---|
| Only to know it failed and read why | wrapped, opaque | `fmt.Errorf("read manifest: %w", err)` |
| To branch on a condition, no data | sentinel | `var ErrNotFound = errors.New("store: not found")`, test with `errors.Is` |
| Data from the error (status, path, retry delay) | typed error | struct with `Error()` on a pointer receiver and `Unwrap()`, test with `errors.As` |
| Several independent failures at once | join | `errors.Join(errs...)` (Go 1.20+) |
| To not depend on your cause | break the chain on purpose | `%v` with a comment saying why; the only valid use of `%v` on an error |

- Context says what this function was doing ("read manifest"), in lower case, no trailing punctuation, no "failed to" or "error:". Do not repeat what the callee already says: `os.Open` errors already carry the path.
- Handle an error or return it, never both. A log line plus `return err` reports the same failure twice.
- Never compare `err.Error()` strings. Exported sentinels and types are API: adding one is a commitment.
- A function returning `error` returns the literal `nil` on success, never a typed nil pointer in an interface variable.
- `panic` only for a violated programmer invariant at start-up or inside a function named `Must...`. Library code returns errors.

## Go: concurrency contract

1. Every `go` statement must answer in code, "who stops it and who waits for it". Stop means a `ctx` or a closed channel; wait means `sync.WaitGroup`, `errgroup` or a done channel. If you cannot name both, do not start the goroutine.
2. `ctx context.Context` is the first parameter, never stored in a struct that outlives a request, never `nil`. `context.Background()` appears only in `main`, tests and server start-up.
3. `defer cancel()` goes on the line right after `WithCancel`, `WithTimeout` or `WithDeadline`.
4. Fan-out with `errgroup.WithContext` and `g.SetLimit(n)`. Unbounded `go` in a loop over input is a defect; pick `n` from the downstream limit (connections, file handles), default 8 when unknown.
5. The sender closes a channel, never the receiver. Capacity is 0 or 1 unless you can state the bound in a comment. A send inside a goroutine that may outlive its reader uses `select` with `<-ctx.Done()`.
6. `wg.Add` runs before `go`, never inside the goroutine.
7. A mutex sits next to the fields it guards, locked with `defer mu.Unlock()`. Never copy a struct that contains one. Never hold it across a channel operation or a call into code you do not own.
8. Loop variables are per-iteration only when `go.mod` says `go 1.22` or newer; below that, copy the variable before the closure.
9. Libraries do not start goroutines in `init` or at import, and expose `Close()` or take a `ctx` to stop what they start. Tests of concurrent code run with `-race`; never synchronise with `time.Sleep`.

## Rust: error decision table

| Situation | Choose |
|---|---|
| Library crate, caller may react to the cause | own enum with `thiserror`, one variant per cause callers tell apart; `#[source]` on the wrapped error; `#[non_exhaustive]` when variants will be added |
| Library, one kind of failure | a struct error, or an enum with one variant; still a concrete type |
| Binary, CLI entry, request handler, top of an app | `anyhow::Result<T>` with `.context("what was being done")`; `main` returns `anyhow::Result<()>` |
| Private helper used inside the crate only | the crate's own error type, not `anyhow` |
| Test, prototype, example | `Result<(), Box<dyn std::error::Error>>` with `?` |
| `Option` that should have been a value | `.ok_or(Error::Missing(key))?` or `.ok_or_else(...)` |
| Invariant that provably holds | `.expect("<why it cannot fail>")`; the message gives the reason ("regex literal is valid"), not the symptom |
| Broken precondition, a bug | `panic!` or `assert!`, documented under `# Panics` |

- `anyhow::Error` never appears in a public library signature; callers cannot match on it.
- Do not put `#[from]` on a foreign error type you do not want in your public API; wrap it in a private field instead.
- Error types are `Send + Sync + 'static`. Messages are lower case with no trailing period. When a variant has a `#[source]`, leave the cause out of its own message, or chain reporters print it twice.
- `unwrap()` and `expect()` are for tests and proven invariants only. `lock().unwrap()` on a poisoned mutex is the one common case: write `.expect("<name> mutex poisoned")` and suppress with `gorust:ignore` and that reason.

## Rust: ownership and concurrency

- Hand work to a thread by moving owned data into it. Share read-only data with `Arc<T>`; add `Mutex` or `RwLock` only for mutation. Prefer a channel when the data is handed off once.
- `std::thread::scope` when threads only borrow local data: no `'static`, no `Arc`, no clones.
- `thread::spawn` and `tokio::spawn` need `'static`. Clone the `Arc` or sender outside the closure (`let tx = tx.clone();`), then `move`.
- Never hold a `std::sync::Mutex` guard across `.await`: end the guard in an inner block first. Use an async mutex only when the lock must span an await.
- No blocking calls in async code (`std::thread::sleep`, heavy `std::fs`, CPU loops over about 100 microseconds): `spawn_blocking` or a dedicated thread.
- Dropping a `JoinHandle` detaches the task; a panic inside it is seen only if the handle is awaited. Keep the handle or use a `JoinSet`.
- Channels between stages are bounded (`mpsc::channel(n)`, with `n` taken from the memory you can afford); an unbounded queue needs a comment proving the producer is bounded.
- `Rc`, `RefCell` and raw pointers are not `Send`; if the compiler says so, change the design, do not wrap in `unsafe impl Send` without a `SAFETY` argument.
- Every `unsafe` block or impl has a `// SAFETY:` comment stating the invariant (validity, alignment, length, aliasing, who guarantees it). "This is safe" is not an invariant.

## Layout and tests, one line each

- Go: `cmd/<binary>/main.go` stays under about 50 lines of wiring; packages live under `internal/` unless an external user needs them; package name equals directory name, short, no `util` or `common`; define interfaces in the package that uses them, return concrete types; tests are table-driven with `t.Run`, helpers call `t.Helper()`, temp state uses `t.TempDir()` and `t.Cleanup`, fixtures in `testdata/`.
- Rust: `src/lib.rs` holds the logic and `src/main.rs` or `src/bin/*.rs` only parses arguments and calls it; `pub(crate)` by default; unit tests in `#[cfg(test)] mod tests` beside the code; integration tests in `tests/` (each file is its own crate, shared helpers in `tests/common/mod.rs`); examples in doc comments run as tests; commit `Cargo.lock` for binaries.

## Script

`scripts/gorust_scan.py`: run it, do not edit it.

- `scan <path>... [--only go|rust]`: JSON with `findings` (file, line, rule, severity, text), `counts_by_rule`, `counts_by_severity`, `files_skipped`, `suppressed`, `verdict` (`findings`, `review` or `clean`), `limits`. Exit 1 when any high or medium finding exists, 0 otherwise, 2 on a missing path or nothing to scan. Skips `vendor`, `target`, `node_modules`, `.git`, `testdata`, Go test and generated files; Rust files under `tests/`, `benches/`, `examples/` and test modules are exempt from the unwrap, expect and clone rules.
- `rules`: JSON list of the nine rules with severity and meaning.

Without Python, search by hand for the patterns listed in `references/linters-and-scanner.md`; the manual result is weaker, so say that in the report.

## Report format

```
Scanner: <findings before> -> <after>, <files scanned>
Fixed: <what changed, grouped by contract: errors, concurrency, unsafe, layout, tests>
Suppressed on purpose: <file:line, reason> or none
Left to linters: <which lints cover what, and whether they were run>
Heuristic findings kept: <low-severity items reviewed and left, with reason>
Not checked: <build, tests, race detector, clippy, vet, versions assumed>
```

## Limits

- The scanner is regex based on a copy of the file with comments and strings blanked. It sees no types, macros, build tags or generics. Every finding is a place to look.
- Misses: a context stored in a struct field, a goroutine started through a helper, `unwrap` hidden in a macro, `http.Get` results dropped as a bare statement (that is errcheck's job), unsafe code reached through macros.
- False positives: a goroutine that stops by a channel closed elsewhere and is not received from inside it; `Arc::clone` spelled as a method; `expect` on a proven invariant; Go `go.mod` files below 1.22 differ in loop-variable behaviour.
- The numeric defaults (8 workers, 50-line `main`, 100 microseconds) are working values, not measured optima.
- Version-dependent facts (loop variables, `errors.Join`, `thread::scope`) are stated with the version they need; check the project's own versions.
- Not covered: cgo, WebAssembly targets, `no_std`, generics-heavy API design, performance tuning, build and CI setup.
