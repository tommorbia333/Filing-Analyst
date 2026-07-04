.PHONY: install lint test index ask eval db-up db-down db-schema db-load
install:
	uv venv && uv pip install -e ".[dev]"
lint:
	uv run ruff check src tests
test:
	uv run pytest -q
index:
	uv run python scripts/build_index.py
ask:
	uv run python scripts/ask.py
eval:
	uv run python scripts/eval_retrieval.py
db-up:
	docker compose up -d
db-down:
	docker compose down
db-schema:
	uv run python -c "from rag.store.db import init_schema; init_schema()"
db-load:
	uv run python scripts/load_to_postgres.py
