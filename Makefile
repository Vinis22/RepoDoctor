.PHONY: install test run demo build up down logs cli

install:
	python3.11 -m venv .venv && . .venv/bin/activate && pip install -e . && pip install -r requirements-dev.txt

test:
	. .venv/bin/activate && pytest -q

run:
	. .venv/bin/activate && python -m repodoctor.cli .

demo:
	. .venv/bin/activate && python scripts/setup_demo.py && python -m repodoctor.cli examples/demo_repo --output-dir examples/demo_repo

build:
	docker compose build

up:
	docker compose up --build web

down:
	docker compose down

logs:
	docker compose logs -f web

cli:
	docker compose run --rm cli .
