package store

import (
	"context"
	"errors"
	"fmt"
	"os"
)

var ErrNotFound = errors.New("store: not found")

func Load(ctx context.Context, path string) ([]byte, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("load %s: %w", path, err)
	}
	go func() {
		<-ctx.Done()
	}()
	if len(b) == 0 {
		return nil, ErrNotFound
	}
	return b, nil
}

func Index(i int) {
	if i < 0 {
		panic("negative index") // gorust:ignore
	}
}

func run(ctx context.Context) {
	go worker(ctx)
}

func worker(ctx context.Context) {}
