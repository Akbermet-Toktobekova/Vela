PY=.venv/bin/python
.PHONY: setup run test lint seed eval build
setup:
	python3 -m venv .venv
	$(PY) -m pip install -c requirements.lock -e '.[dev]'
	cd frontend && npm ci
run: build
	$(PY) -m uvicorn finagent.api.app:app --host 127.0.0.1 --port 8000
build:
	cd frontend && npm run build
seed:
	$(PY) -m finagent.cli seed
eval:
	$(PY) -m finagent.cli evaluate
test:
	$(PY) -m pytest
	cd frontend && npm test
lint:
	.venv/bin/ruff check src tests
	.venv/bin/ruff format --check src tests
	.venv/bin/mypy --strict src/finagent/domain
