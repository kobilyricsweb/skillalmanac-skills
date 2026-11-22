.PHONY: build test lint sqlc db-up
build:
	go build ./...
test:
	go test ./...
lint:
	golangci-lint run
sqlc:
	sqlc generate
db-up:
	docker compose up -d db
