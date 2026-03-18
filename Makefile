.PHONY: build install setup-kernel test notebooks verify-data clean \
       show-build sol-test sol-test-demo test-py

VENV := uhi8
PYTHON := $(VENV)/bin/python
JUPYTER := $(VENV)/bin/jupyter
PYTEST := $(VENV)/bin/pytest

# ── Build (full pipeline: install → verify → notebooks) ──────────────
build: install verify-data test notebooks

# ── Setup ────────────────────────────────────────────────────────────
install:
	git submodule update --init --recursive
	uv venv $(VENV) --python 3.13
	uv pip install --python $(PYTHON) -e ".[dev]"
	$(MAKE) setup-kernel

setup-kernel:
	$(PYTHON) -m ipykernel install --user --name=thetaswap \
		--display-name "thetaswap" \
		--env PYTHONPATH "$(CURDIR)/research"
	@echo "Kernel 'thetaswap' installed. PYTHONPATH=$(CURDIR)/research"

# ── Solidity ──────────────────────────────────────────────────────────
show-build:
	FOUNDRY_PROFILE=lite forge build --no-cache --threads 6

sol-test:
	forge test --no-cache --match-path "test/fci-token-vault/**" -vv
	forge test --no-cache --match-path "test/fee-concentration-index-v2/**" -vv

sol-test-demo:
	forge test --no-cache --match-path "test/fee-concentration-index-v2/protocols/uniswapV4/*" -vvvv

# ── Python ───────────────────────────────────────────────────────────
test-py:
	cd research && ../$(PYTEST) tests/ -v

test: test-py

# ── Notebooks (headless execute) ─────────────────────────────────────
notebooks: setup-kernel
	@tmpdir=$$(mktemp -d); \
	for nb in research/notebooks/*.ipynb; do \
		echo "Executing $$nb ..."; \
		PYTHONPATH=research $(JUPYTER) nbconvert \
			--to notebook --execute \
			--ExecutePreprocessor.timeout=300 \
			--ExecutePreprocessor.kernel_name=thetaswap \
			--output-dir="$$tmpdir" \
			"$$nb"; \
	done; \
	rm -rf "$$tmpdir"
	@echo "All notebooks passed."

# ── Data provenance ──────────────────────────────────────────────────
verify-data:
	$(PYTHON) research/data/scripts/verify_provenance.py

# ── Clean ────────────────────────────────────────────────────────────
clean:
	find research -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find research -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf research/.pytest_cache
