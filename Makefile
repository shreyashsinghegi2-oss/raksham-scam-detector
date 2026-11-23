.PHONY: help install train test lint format serve clean

PYTHON ?= python3
VENV   ?= .venv
BIN     = $(VENV)/bin

help:  ## Show this list
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-8s %s\n", $$1, $$2}'

install:  ## Create .venv and install the package with dev tools
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -e ".[dev]"

train:  ## Train the model (needs data/raksham_scam_dataset.csv, see README)
	$(BIN)/raksham-train

test:  ## Run the test suite (dataset tests skip themselves when the data is absent)
	$(BIN)/pytest -q

lint:  ## Check style with ruff
	$(BIN)/ruff check .

format:  ## Apply ruff's safe auto-fixes
	$(BIN)/ruff check --fix .

serve:  ## Serve the API on port 8000 (run `make train` once first)
	$(BIN)/uvicorn raksham.api:app --host 127.0.0.1 --port 8000

clean:  ## Remove caches and build output
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info src/*.egg-info
