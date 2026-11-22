.PHONY: install lint fmt test dev-db gen

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check geo tests

fmt:
	ruff format geo tests

dev-db:
	docker compose up -d db

test:
	pytest -q

gen:
	python tools/gen_schema.py schema/geo.yaml geo/generated/schema.py
