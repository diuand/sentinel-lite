# Sentinel-Lite developer commands. Linux/macOS (or WSL on Windows).
VENV ?= .venv

ifeq ($(wildcard $(VENV)/bin/python),)
  BIN :=
  PYTHON := python3
else
  BIN := $(VENV)/bin/
  PYTHON := $(VENV)/bin/python
endif

.PHONY: setup run test lint check report evidence-red

setup:  ## create .venv and install runtime + dev dependencies
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -q --upgrade pip
	$(VENV)/bin/pip install -q -r requirements.txt -r requirements-dev.txt

run:  ## start the service on 127.0.0.1:5000
	$(PYTHON) -m app

test:
	$(PYTHON) -m pytest -q

lint:
	$(BIN)ruff check app tests

check: lint test

report:  ## write reports/summary.txt from the stored events
	$(PYTHON) -m app.reports

evidence-red:  ## run the seeded-bug regression tests with xfail disabled (red while a bug is open)
	$(PYTHON) -m pytest -q --runxfail -m seeded_bug -p no:cacheprovider
