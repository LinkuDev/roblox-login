.PHONY: install dev api worker test lint fmt run-login

install:
	python -m venv .venv && .venv/bin/pip install -e ".[dev,worker]"

api:
	.venv/bin/uvicorn app.main:api --app-dir src --reload --port 8000

worker:
	.venv/bin/python -m app.worker.main

# Chay thu flow login truc tiep, khong qua API/DB
run-login:
	.venv/bin/rlx run roblox.login --username "$(U)" --password "$(P)" --no-headless

test:
	.venv/bin/pytest -q

lint:
	.venv/bin/ruff check src tests && .venv/bin/mypy src

fmt:
	.venv/bin/ruff format src tests && .venv/bin/ruff check --fix src tests
