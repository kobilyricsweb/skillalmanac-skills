package main

import "os"

func main() {
	if len(os.Args) > 5 {
		panic("too many arguments")
	}
}
