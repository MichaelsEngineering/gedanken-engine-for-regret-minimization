# ==== Configuration ====
PYTHON := python
PKG ?= src
TESTS ?= tests
SMOKE_CFG ?= tests/fixtures/modular_addition.yaml
SYNC_DELETE_REMOTE ?= 0

# ==== Meta ====
.PHONY: help default init lint type format format-check test test-fast test-watch coverage tdd check gate replay analyze swarm smoke train unit integration new-test clean sync

default: help

help:
	@echo "Targets:"
	@echo "   init            Install deps (and optional requirements-dev.txt)"
	@echo "   lint            Ruff check + Ruff format check"
	@echo "   type            Mypy type check"
	@echo "   format          Apply Ruff formatting (replaces Black + isort)"
	@echo "   test            Run full test suite"
	@echo "   test-fast       Fail-fast unit tests (-x --maxfail=1)"
	@echo "   test-watch      Watch tests with pytest-watch (if installed)"
	@echo "   coverage        Run pytest with coverage reports"
	@echo "   tdd             Lint + type + fail-fast unit tests (inner loop)"
	@echo "   check           Lint + type + tests (pre-push)"
	@echo "   gate            Run the agent orchestrator gate validator"
	@echo "   replay          Run deterministic replay and emit runs/<id>/events.jsonl"
	@echo "   analyze         Analyze runs/<id>/events.jsonl and emit runs/<id>/report.json"
	@echo "   swarm           Launch manager + 5 worker swarm"
	@echo "   smoke           CPU-only smoke training run with tiny epochs"
	@echo "   train           Example short train call (override ARGS=...)"
	@echo "   unit            Only unit tests (mark=unit)"
	@echo "   integration     Only integration tests (mark=integration)"
	@echo "   new-test NAME=feature  Scaffold tests/test_feature.py"
	@echo "   clean           Remove caches and build artifacts"

# ==== Setup ====
init:
	uv sync --dev

# ==== Quality gates ====
SRC := $(PKG) $(TESTS)
GATE_RUN ?= runs/1
GATE_CMD ?= python -m scripts.swarm_gate
RUN_ID ?= 1
TRACE ?= traces/fixtures/fixture_five_agent.jsonl
SEED ?= 7
REPLAY_OUT ?= runs/$(RUN_ID)
REPLAY_ENV ?= src.replay_fixtures:make_env
REPLAY_POLICIES ?= src.replay_fixtures:make_policies
REPLAY_METRICS ?= src.replay_fixtures:make_metrics
ANALYZE_IN ?= runs/$(RUN_ID)/events.jsonl
ANALYZE_OUT ?= runs/$(RUN_ID)/report.json
ANALYZE_CMD ?= $(PYTHON) -m src.analyze

lint:
	@echo "Running Ruff lint..."
	@ruff check src tests || (echo "❌ Ruff check failed"; exit 1)
	@echo "Running Ruff format check..."
	@ruff format --check src tests || (echo "❌ Some files need formatting. Run: ruff format src tests"; exit 1)
	@echo "✅ All lint checks passed!"

type:
	@if find $(TESTS) -type f -name "*.py" | grep -q .; then \
		mypy $(PKG) $(TESTS); \
	else \
		mypy $(PKG); \
	fi

format:
	ruff format $(SRC)

# ==== Tests ====
test:
	pytest -q

test-fast:
	pytest -q -x --maxfail=1 -m "not integration"

test-watch:
	@if command -v ptw >/dev/null 2>&1; then \
		ptw $(TESTS) -- -q -x --maxfail=1 -m "not integration"; \
	else \
		echo "pytest-watch (ptw) not found. Install with: pip install pytest-watch"; \
	fi

coverage:
	pytest -q --cov=$(PKG) --cov=$(TESTS) --cov-report=term-missing --cov-report=xml

# Inner TDD loop: quick, strict, no long runs
tdd: lint type test-fast

# Pre-push: everything important
check: lint type test coverage

# Gate orchestration (placeholder)
gate:
	$(GATE_CMD) --run $(GATE_RUN)

replay:
	uv run rc --env $(REPLAY_ENV) --policies $(REPLAY_POLICIES) --metrics $(REPLAY_METRICS) --trace $(TRACE) --seed $(SEED) --out $(REPLAY_OUT) --tee

analyze:
	$(ANALYZE_CMD) --in $(ANALYZE_IN) --out $(ANALYZE_OUT) --run-id $(RUN_ID)

swarm:
	./scripts/swarm_run.sh

# ==== Training shortcuts ====
smoke:
	$(PYTHON) -m src.scripts.train --config $(SMOKE_CFG) $(ARGS)

train:
	$(PYTHON) -m src.scripts.train $(ARGS)

unit:
	pytest -q -m "unit"

integration:
	pytest -q -m "integration"

analytic:
	pytest -k "norm_min_dynamics" -v

# ==== Scaffolding ====
# Create a basic unit test file: make new-test NAME=feature_x
new-test:
	@if [ -z "$(NAME)" ]; then \
		echo "Usage: make new-test NAME=feature_name"; exit 1; \
	fi
	@mkdir -p $(TESTS)
	@if [ -f "$(TESTS)/test_$(NAME).py" ]; then \
		echo "$(TESTS)/test_$(NAME).py already exists"; \
	else \
		echo "Creating $(TESTS)/test_$(NAME).py"; \
		printf "%s\n" \
"import pytest" \
"" \
"pytestmark = pytest.mark.unit" \
"" \
"def test_$(NAME)_behavior():\n    # Arrange\n    # TODO: set up inputs\n\n    # Act\n    # TODO: call function under test\n\n    # Assert\n    # TODO: assert on outputs\n    assert True" \
		> $(TESTS)/test_$(NAME).py; \
	fi

# ==== Hygiene ====
clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml dist build \
		$(PKG)/*.egg-info .benchmarks
	find . -type d -name "__pycache__" -exec rm -rf {} +

sync:
	@echo "Syncing local main with origin/main and cleaning merged branches..."
	git fetch origin
	git checkout main
	git rebase origin/main
	@git branch --merged main | grep -v "main" | xargs -r git branch -d
	@if [ "$(SYNC_DELETE_REMOTE)" = "1" ]; then \
		echo "Deleting merged remote branches on origin..."; \
		git branch -r --merged origin/main | grep -vE "origin/(main|HEAD)" | sed "s|origin/||" | xargs -r -n1 git push origin --delete; \
	else \
		echo "Skipping remote branch deletion (set SYNC_DELETE_REMOTE=1 to enable)"; \
	fi
	@git remote prune origin
