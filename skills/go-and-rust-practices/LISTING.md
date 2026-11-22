# Listing page content: go-and-rust-practices

**One line:** Idiomatic Go and Rust contracts for errors, concurrency, layout and tests, with a line-numbered anti-pattern scanner.

## What it does

The skill gives an agent a six-step procedure for writing or reviewing Go and Rust: read the project's own rules and versions, scan, write with decision tables, run the project's linters, re-scan, report. The tables fix the choices that models usually improvise: sentinel, typed or wrapped errors in Go; `thiserror` or `anyhow` in Rust; who stops and who waits for every goroutine; what a `SAFETY` comment must state. A scanner reads `.go` and `.rs` files as text, blanks comments and string literals, and reports nine documented patterns with file and line. A reference page lists which problems `go vet`, staticcheck, errcheck, rustc and clippy already catch, so the agent leaves those to the tools.

## Capabilities

- `scripts/gorust_scan.py scan <path>`: JSON with findings by file and line, counts by rule and severity, skipped files, suppression count, verdict
- `scripts/gorust_scan.py rules`: the nine rules with severity and meaning
- Go error table, concurrency contract (nine rules), Rust error decision table, ownership and async rules
- Templates for typed errors, bounded fan-out, stoppable workers, table tests, thiserror libraries, anyhow binaries, scoped threads, SAFETY comments
- A coverage table: which default linter owns which problem, and which problems only the scanner sees
- A fixed report with the line "Not checked"

## When to use

You ask for idiomatic Go or Rust, a code review of a Go or Rust change, help with error handling, or you notice the agent writing `unwrap()`, `panic(`, ignored errors or bare `go` statements in library code.

## When not to use

Other languages, CI or build setup (golangci-lint pipelines, cargo caching), choosing between Go and Rust, porting code from one to the other, performance tuning, cgo, `no_std`.

How it differs from the sibling language skills in the catalogue (Python, TypeScript): it covers two compiled languages with a shared scanner; the scope is limited to error, concurrency, layout, test conventions and unsafe documentation.

## Requirements

Python 3.9 or newer for the scanner (standard library only). No network, no Go or Rust toolchain needed for the scanner. Running `go vet`, `staticcheck`, `cargo clippy` or the tests needs the project's own toolchain.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved edit to show. What exists is the scanner on the saved fixtures (`python scripts/gorust_scan.py scan evals/fixtures/bad_lib.rs`, exit code 1):

```
rust-unwrap            high    line 4   let text = fs::read_to_string(path).unwrap();
rust-expect            medium  line 5   let first = text.lines().next().expect("file has a line");
rust-clone-in-loop     low     line 12  out.push(item.clone());
rust-unsafe-no-safety  high    line 20  unsafe { *p }
rust-clone-in-loop     low     line 53  let _x = v.clone();
```

Not reported, by design: the `unwrap`, `clone` and `for` loop inside the `#[cfg(test)]` module, the `unsafe` blocks that carry a `SAFETY:` comment (lines 25 and 29), `unwrap_or`, and `.unwrap()` in a comment and a string literal.

Go, `python scripts/gorust_scan.py scan evals/fixtures/bad_lib.go` (exit 1): line 12 `go-errorf-no-wrap`, 14 and 42 `go-ignored-error`, 15 `go-blank-result` (low), 17 `go-panic-in-library`, 19 and 22 `go-goroutine-no-context`. `MustLoad` on line 29 and the goroutine that waits on `ctx.Done()` on line 35 are not reported.

## Limits

- Lexical scan, no types or macros; every finding is a place to look.
- Misses contexts stored in struct fields, goroutines started through helpers, unwrap inside macros, bare `http.Get(...)` statements (errcheck's job).
- False positives: closed-over stop channels, `Arc` clones, `expect` on a proven invariant.
- Numeric defaults (8 workers, 50-line `main`, 100 microseconds) are working values.
- Lint sets differ per project and release; the coverage table lists usual defaults.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL and 0 WARN; 9 scanner fixture cases pass with expected values derived by hand. Not tested: any with/without efficacy comparison, trigger behaviour, native discovery, any cross-tool install, human review, behaviour on real repositories.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Prompt: "review this Rust crate; the agent keeps unwrapping". Agent runs the scan: two high findings, one medium, two low.
2. Agent replaces `unwrap` with a typed `thiserror` error in the library and `anyhow` context in `main`.
3. Agent adds `SAFETY:` comments that state invariants; marks one proven `expect` with `gorust:ignore` and a reason.
4. Re-scan: verdict clean or review; report lists "Left to linters" and "Not checked".

## FAQ seeds

- Does it need Go or Rust installed? Not for the scanner. The project's own linters and tests do.
- Does it replace `go vet`, staticcheck or clippy? No. It tells the agent which problems those tools already cover and adds checks they leave off by default.
- Will it flag every unwrap in my tests? No. Test modules, `tests/`, `benches/`, `examples/` and Go `_test.go` files are exempt for the relevant rules.
- Can I silence a finding? Yes, with `gorust:ignore` and a reason on that line; the count is reported.
- How reliable is the goroutine check? It is a text check for any stop signal inside the goroutine; expect false positives where the signal lives elsewhere.
- Does it work with generics, macros, build tags? The scan ignores them; findings inside macro bodies are not seen.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
