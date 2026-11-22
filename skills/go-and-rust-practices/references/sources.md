# Sources

Facts in this skill were written in the authors' own words from the pages below, read as background; no text is copied. The pages were not re-fetched while authoring this version (see VERIFICATION.md), so check them when a rule matters.

| Topic | Page | What it fixes |
|---|---|---|
| Go error wrapping, `Is`, `As`, `%w` | https://go.dev/blog/go1.13-errors | wrapping with `%w`, `Unwrap`, when to expose a cause |
| `errors` package, `Join` | https://pkg.go.dev/errors | `errors.Is`, `errors.As`, `errors.Join` |
| Go style and naming | https://go.dev/doc/effective_go | package names, interfaces, error strings, naming |
| Go module layout | https://go.dev/doc/modules/layout | `cmd/`, `internal/`, flat start |
| Go concurrency pipelines and cancellation | https://go.dev/blog/pipelines | sender closes, cancellation by a done signal |
| `context` package | https://pkg.go.dev/context | ctx as first parameter, cancel functions, no nil context |
| Loop variable semantics change | https://go.dev/blog/loopvar-preview | per-iteration variables from Go 1.22 |
| `go vet` analyzers | https://pkg.go.dev/cmd/vet | printf, copylocks, lostcancel, errorsas, unusedresult |
| staticcheck checks | https://staticcheck.dev/docs/checks/ | SA2000, SA4006, SA1019, SA1012, ST1005 |
| errcheck | https://github.com/kisielk/errcheck | unchecked errors; blank assignments are opt-in |
| `testing` package | https://pkg.go.dev/testing | `t.Run`, `t.Helper`, `t.TempDir`, `t.Cleanup`, `t.Setenv` |
| Rust error handling | https://doc.rust-lang.org/book/ch09-00-error-handling.html | `Result`, `?`, when to panic |
| Rust API guidelines | https://rust-lang.github.io/api-guidelines/ | error type guidance, naming, documentation of panics and safety |
| thiserror | https://docs.rs/thiserror | derive, `#[source]`, `#[from]`, display formats |
| anyhow | https://docs.rs/anyhow | `Context`, `Result`, chain display |
| Clippy lint index | https://rust-lang.github.io/rust-clippy/master/index.html | lint groups, which are restriction (off by default) |
| Scoped threads | https://doc.rust-lang.org/std/thread/fn.scope.html | borrowing in threads without `'static` |
| Unsafe Rust | https://doc.rust-lang.org/nomicon/ | invariants an unsafe block must uphold |
| Cargo package layout | https://doc.rust-lang.org/cargo/guide/project-layout.html | `src/`, `tests/`, `examples/`, `benches/`, `src/bin/` |
| Tokio spawn, select, blocking | https://tokio.rs/tokio/tutorial | `spawn`, `JoinSet`, `spawn_blocking`, cancel safety |
