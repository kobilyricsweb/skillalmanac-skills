package store

import (
	"context"
	"fmt"
	"os"
)

func Save(path string, data []byte) error {
	f, err := os.Create(path)
	if err != nil {
		return fmt.Errorf("create %s: %v", path, err)
	}
	_ = f.Close()
	n, _ := f.Write(data)
	if n == 0 {
		panic("empty write")
	}
	go func() {
		flush(path)
	}()
	go refresh(path)
	return nil
}

func MustLoad(path string) []byte {
	b, err := os.ReadFile(path)
	if err != nil {
		panic(err)
	}
	return b
}

func Watch(ctx context.Context, path string) {
	go func() {
		<-ctx.Done()
		fmt.Println("stopped", path)
	}()
	// panic("this is a comment and must not be flagged")
	msg := "panic(\"in a string\") and _ = f()"
	fmt.Println(msg)
	_ = fmt.Sprint(path)
}
