.PHONY: env clean-env deps format lint test

PYTHON ?= 3.12

UV = UV_CACHE_DIR=.uv-cache uv
UV_RUN = $(UV) run --no-sync

MODULES = \
	plugins/agents/model-client \
	plugins/agents/mcp-bridge \
	examples/plugins/example-tool \
	examples/apps/agent-example

MYPY_TARGETS = \
	plugins/agents/model-client:hopeit.agents.model_client \
	plugins/agents/mcp-bridge:hopeit.agents.mcp_bridge \
	examples/plugins/example-tool:hopeit.agents.example_tool \
	examples/apps/agent-example:agent_example

env:
	$(UV) venv --seed --python $(PYTHON)
	$(UV) sync --all-packages

clean-env:
	rm -rf .venv
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -f uv.lock

install-dev: env
	$(UV) sync --all-packages
	for module in $(MODULES); do \
		$(UV) pip install -U --no-deps -e $$module; \
	done

format:
	$(UV_RUN) ruff format $(MODULES:%=%/src/) $(MODULES:%=%/test/)
	$(UV_RUN) ruff check $(MODULES:%=%/src/) $(MODULES:%=%/test/) --fix

lint:
	$(UV_RUN) ruff format --check $(MODULES:%=%/src/) $(MODULES:%=%/test/)
	$(UV_RUN) ruff check $(MODULES:%=%/src/) $(MODULES:%=%/test/)
	for target in $(MYPY_TARGETS); do \
		module=$${target%%:*}; \
		package=$${target##*:}; \
		PYTHONPATH=$$module/src MYPYPATH=$$module/src $(UV_RUN) mypy --namespace-packages -p $$package; \
		PYTHONPATH=$$module/src MYPYPATH=$$module/src:$$module/test $(UV_RUN) mypy --namespace-packages $$module/test; \
	done

test:
	for module in $(MODULES); do \
		PYTHONPATH=$$module/src $(UV_RUN) pytest -v --cov-report=term --cov=$$module/src $$module/test; \
	done

ci:
	$(UV) sync --all-packages
	make lint
	make test
