.PHONY: install test-sol test-py test notebooks clean

# ── Setup ────────────────────────────────────────────────────────────
install:
	git submodule update --init --recursive
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"
	.venv/bin/python -m ipykernel install --user --name=thetaswap \
		--env PYTHONPATH "$(CURDIR)/research"

# ── Solidity ─────────────────────────────────────────────────────────
test-sol:
	forge build
	forge test

# ── Python ───────────────────────────────────────────────────────────
test-py:
	PYTHONPATH=research .venv/bin/pytest research/tests -v

# ── All tests ────────────────────────────────────────────────────────
test: test-sol test-py

# ── Notebooks (headless execute) ─────────────────────────────────────
notebooks:
	@for nb in research/notebooks/*.ipynb; do \
		echo "Executing $$nb ..."; \
		PYTHONPATH=research .venv/bin/jupyter nbconvert \
			--to notebook --execute \
			--ExecutePreprocessor.timeout=300 \
			--ExecutePreprocessor.kernel_name=thetaswap \
			"$$nb" --output /dev/null; \
	done
	@echo "All notebooks passed."

# ── Clean ────────────────────────────────────────────────────────────
clean:
	rm -rf out/ cache/
