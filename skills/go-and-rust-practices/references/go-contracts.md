# Go contracts: templates

## Contents
- Errors: wrapped, sentinel, typed
- Concurrency: bounded fan-out, long-lived worker, stopping
- Layout
- Tests

## Errors: wrapped, sentinel, typed

Wrapped, opaque. Name the action, not the failure:

```go
b, err := os.ReadFile(path)
if err != nil {
    return nil, fmt.Errorf("read manifest: %w", err) // os already adds the path
}
```

Sentinel. Exported, prefixed with the package, compared with `errors.Is`:

```go
var ErrNotFound = errors.New("store: not found")

func (s *Store) Get(id string) (Item, error) {
    it, ok := s.items[id]
    if !ok {
        return Item{}, fmt.Errorf("get %s: %w", id, ErrNotFound)
    }
    return it, nil
}
```

Typed, when the caller needs fields. Pointer receiver, `Unwrap` when it wraps a cause:

```go
type HTTPError struct {
    Status int
    URL    string
    Err    error
}

func (e *HTTPError) Error() string { return fmt.Sprintf("get %s: status %d", e.URL, e.Status) }
func (e *HTTPError) Unwrap() error { return e.Err }

var he *HTTPError
if errors.As(err, &he) && he.Status == http.StatusTooManyRequests {
    // back off for a while
}
```

Traps:
- `var e *HTTPError; return e` from a function returning `error` yields a non-nil interface. Return the literal `nil`.
- `errors.As` needs a pointer to the target variable; `go vet` (errorsas) catches a wrong second argument.
- `fmt.Errorf` with two `%w` verbs works since Go 1.20; below that only one `%w` is allowed.
- Choose sentinel versus typed by what callers do with it: branch only, sentinel; read data, typed. Do not make both for the same condition.
- Return an error for expected failures (bad input, missing file, remote refused). `panic` is for impossible states; `Must` helpers exist for package-level initialisation (`regexp.MustCompile` is the model).

## Concurrency: bounded fan-out, long-lived worker, stopping

Bounded fan-out, first error cancels the rest:

```go
g, ctx := errgroup.WithContext(ctx)
g.SetLimit(8)
for _, it := range items {
    g.Go(func() error { // `it` is per-iteration from Go 1.22
        return process(ctx, it)
    })
}
if err := g.Wait(); err != nil {
    return fmt.Errorf("process batch: %w", err)
}
```

Long-lived worker owned by a type, with an explicit stop:

```go
type Poller struct {
    cancel context.CancelFunc
    done   chan struct{}
}

func StartPoller(parent context.Context, every time.Duration, fn func(context.Context)) *Poller {
    ctx, cancel := context.WithCancel(parent)
    p := &Poller{cancel: cancel, done: make(chan struct{})}
    go func() {
        defer close(p.done)
        t := time.NewTicker(every)
        defer t.Stop()
        for {
            select {
            case <-ctx.Done():
                return
            case <-t.C:
                fn(ctx)
            }
        }
    }()
    return p
}

func (p *Poller) Close() { p.cancel(); <-p.done }
```

Stop means cancel plus wait. A `Close` that only cancels leaves a goroutine still running when it returns.

More rules with reasons:
- A send on an unbuffered channel blocks until someone receives. In a goroutine that can outlive its reader, write `select { case out <- v: case <-ctx.Done(): return }` or the goroutine leaks.
- `time.After` inside a loop creates a timer per iteration; before Go 1.23 an unfired timer is not collected until it fires. Use `time.NewTimer` with `Reset`, or a ticker.
- `sync.WaitGroup`: `Add` before `go`. `Add` inside the goroutine races with `Wait`.
- Do not pass a `sync.Mutex` or a struct containing one by value.
- Tests that start goroutines run with `go test -race` and join them before the test returns; a test that needs `time.Sleep` to pass has a missing synchronisation point.

## Layout

```
module/
  go.mod
  cmd/
    tool/main.go        wiring only: flags, build dependencies, call run(ctx, args)
  internal/
    store/              one package per concept, named for what it provides
    store/testdata/     ignored by the go tool; fixtures and golden files
  README.md
```

- Start flat: one package at the module root until a second concept appears. Do not create `pkg/`, `utils/`, `common/` or `helpers/`.
- `internal/` is enforced by the toolchain: code outside the parent cannot import it. Use it by default; move something out only when an outside user exists.
- Package names are short, lower case, no underscores, and match the directory. The package name is part of every call site (`store.Open`), so do not repeat it in the identifier (`store.StoreOpen`).
- Define an interface in the package that consumes it and keep it to the methods used. Return concrete types from constructors.
- `main` calls `run(ctx, args, stdout) error` so the program is testable and the only `os.Exit` is in `main`.

## Tests

```go
func TestParse(t *testing.T) {
    tests := []struct {
        name    string
        in      string
        want    Config
        wantErr error
    }{
        {name: "empty", in: "", wantErr: ErrEmpty},
        {name: "one key", in: "a=1", want: Config{"a": "1"}},
    }
    for _, tc := range tests {
        t.Run(tc.name, func(t *testing.T) {
            got, err := Parse(tc.in)
            if !errors.Is(err, tc.wantErr) {
                t.Fatalf("Parse(%q) error = %v, want %v", tc.in, err, tc.wantErr)
            }
            if diff := cmp.Diff(tc.want, got); diff != "" {
                t.Errorf("Parse(%q) mismatch (-want +got):\n%s", tc.in, diff)
            }
        })
    }
}
```

- Failure messages say what was called, what came back, what was wanted.
- `t.Helper()` first line in every helper; `t.TempDir()` for files, `t.Setenv` for environment, `t.Cleanup` for teardown; no global state shared between tests.
- Test the public API from `package foo_test` when possible; use an internal test file only for what cannot be reached.
- Golden files live in `testdata/` and are regenerated by an `-update` flag, never by hand.
- `go test -race -count=1 ./...` before declaring a concurrent change done. `-count=1` bypasses the test cache.
- Fuzz targets (`FuzzXxx`, Go 1.18+) suit parsers and decoders.
