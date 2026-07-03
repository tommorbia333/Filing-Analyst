.PHONY: install lint test index ask eval
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
