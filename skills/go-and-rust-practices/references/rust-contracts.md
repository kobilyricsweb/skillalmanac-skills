# Rust contracts: templates

## Contents
- Errors: library type and application boundary
- Ownership and concurrency
- Layout
- Tests
- Unsafe

## Errors: library type and application boundary

Library crate, typed error with `thiserror`:

```rust
#[derive(Debug, thiserror::Error)]
#[non_exhaustive]
pub enum ConfigError {
    #[error("read config {path}")]
    Read { path: String, #[source] source: std::io::Error },
    #[error("line {line}: missing '='")]
    Syntax { line: usize },
    #[error("key {key}: not a valid port")]
    BadPort { key: String, #[source] source: std::num::ParseIntError },
    #[error("key {0}: not set")]
    Missing(String),
}

pub fn port(cfg: &Config) -> Result<u16, ConfigError> {
    let raw = cfg.values.get("port").ok_or_else(|| ConfigError::Missing("port".into()))?;
    raw.parse().map_err(|source| ConfigError::BadPort { key: "port".into(), source })
}
```

Binary, catch-all with context:

```rust
use anyhow::{Context, Result};

fn main() -> Result<()> {
    let cfg = cfgtool::load("app.conf").context("load app.conf")?;
    let port = cfgtool::port(&cfg).context("read listen port")?;
    println!("listening on {port}");
    Ok(())
}
```

Rules with reasons:
- The library error is a contract: callers `match` on it. `anyhow::Error` cannot be matched, so it stays out of public signatures.
- `#[from]` generates `From<Foreign>` and exposes the foreign type in your API; use a named variant with `#[source]` unless you want that coupling.
- `Display` describes this layer only; the chain printer (`anyhow` with `{:#}` or `{:?}`) shows the sources. Repeating the source text in `Display` prints it twice.
- Messages are lower case, no trailing period, and name the offending key, path or line.
- A constructor that can fail returns `Result<Self, Error>`. A `new` that panics on bad input is a bug.
- `Option<T>` to `Result`: `.ok_or(...)` for a cheap value, `.ok_or_else(|| ...)` when building the error allocates.
- When panic is correct, document it: a `# Panics` section in the doc comment of the public function.

## Ownership and concurrency

Scoped threads when the work only borrows local data:

```rust
let total: u64 = std::thread::scope(|s| {
    let handles: Vec<_> = chunks
        .iter()
        .map(|c| s.spawn(move || c.iter().sum::<u64>()))
        .collect();
    handles.into_iter().map(|h| h.join().expect("worker panicked")).sum()
});
```

Handing off to an owned thread with a bounded channel:

```rust
let (tx, rx) = std::sync::mpsc::sync_channel::<Job>(64);
let worker = std::thread::spawn(move || {
    for job in rx { run(job); }
});
tx.send(job)?;   // blocks while 64 jobs are queued
drop(tx);        // closes the channel; the worker loop ends
worker.join().expect("worker panicked");
```

Async traps:
- `let g = m.lock().unwrap(); fetch().await;` holds a std guard across an await. It can deadlock or fail the `Send` bound of the future. Copy out what you need, drop the guard, then await.
- `tokio::select!` drops the losing futures, so a future that was half way through a write is cancelled. Use only futures documented as cancel safe in a branch that can lose.
- Blocking work inside a task stalls an executor thread: use `tokio::task::spawn_blocking` for blocking IO and long CPU loops.
- `tokio::spawn(async move { ... })` returns a handle; dropping it detaches the task. Collect handles in a `JoinSet` when the parent must wait or cancel.
- Shared state: `Arc<Mutex<T>>` for small critical sections; an actor (one task owns the state and receives messages) when the critical section would span an await.

Cloning:
- `Arc::clone(&a)` is cheap and states intent; `.clone()` on a `String`, `Vec` or struct copies the data. In a loop body that runs per item, ask whether a borrow, an iterator adapter or `Cow` removes the copy. The scanner marks `.clone()` inside loops as low severity for this reason; many are fine.
- `Vec::with_capacity(n)` when `n` is known removes repeated growth.

## Layout

```
crate/
  Cargo.toml
  src/
    lib.rs          modules, public re-exports, docs
    main.rs         parse arguments, call into the lib, map the error to an exit code
    bin/other.rs    extra binaries
    config.rs       a module; a larger one becomes config/ with submodules
  tests/
    cli.rs          one integration crate per file
    common/mod.rs   shared helpers (a directory, so it is not built as a test)
  examples/         runnable with `cargo run --example name`
  benches/
```

- `pub(crate)` is the default visibility; each `pub` is a promise to downstream users.
- Prefer `foo.rs` plus `foo/bar.rs` to `foo/mod.rs`; both work, do not mix them in one crate.
- A workspace (`[workspace]` with `members`) once there are two crates; share versions with `[workspace.dependencies]`.
- Features are additive: enabling one must never remove an API or change the behaviour of another.
- `Cargo.lock` is committed for binaries; for libraries it is optional.

## Tests

- Unit tests in `#[cfg(test)] mod tests { use super::*; ... }` in the same file, so they can reach private items.
- Integration tests in `tests/` use only the public API.
- A doc test is an API example that must compile: keep it short, and use `?` with a hidden `# Ok::<(), Box<dyn std::error::Error>>(())` tail when needed.
- Tests may return `Result<(), Box<dyn std::error::Error>>` and use `?`; `unwrap` in a test is acceptable and the scanner exempts it.
- Keep the order `assert_eq!(got, want)` consistent; add a message when several asserts share one test.
- `#[should_panic(expected = "...")]` with the expected text, never the bare form.
- Property tests (`proptest`) and snapshot tests are extra dependencies; add them only when the project already uses them.

## Unsafe

Every `unsafe` block, `unsafe impl` and `unsafe extern` block is preceded by, or starts with, a comment of this form:

```rust
// SAFETY: `ptr` came from `Vec::as_mut_ptr` on `self.buf`, `len <= self.buf.len()`,
// and `&mut self` guarantees nobody else holds a reference to the buffer.
let s = unsafe { slice::from_raw_parts_mut(ptr, len) };
```

State which invariant holds and who upholds it. A public `unsafe fn` gets a `# Safety` section in its doc comment listing what the caller must guarantee. Keep each `unsafe` block to the single operation that needs it.
