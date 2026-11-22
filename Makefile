# Sentinel-Lite developer commands. Linux/macOS (or WSL on Windows).
VENV ?= .venv

ifeq ($(wildcard $(VENV)/bin/python),)
  BIN :=
  PYTHON := python3
else
  BIN := $(VENV)/bin/
  PYTHON := $(VENV)/bin/python
endif

.PHONY: setup run test lint sast audit check report evidence-red demo-push demo-gitleaks demo-hook

setup:  ## create .venv and install runtime + dev dependencies
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -q --upgrade pip
	$(VENV)/bin/pip install -q -r requirements.txt -r requirements-dev.txt
	$(VENV)/bin/python scripts/init_env.py

run:  ## start the service on 127.0.0.1:5000
	$(PYTHON) -m app

test:
	$(PYTHON) -m pytest -q

lint:
	$(BIN)ruff check app tests

sast:  ## static analysis of the app code
	$(BIN)bandit -q -r app

AUDIT_IGNORES := $(shell sed -n 's/^\([A-Za-z0-9-]\{1,\}\).*/--ignore-vuln \1/p' .pip-audit-ignore 2>/dev/null)
audit:  ## known-vulnerability scan of runtime dependencies (tracked exceptions: .pip-audit-ignore)
	$(BIN)pip-audit -r requirements.txt --progress-spinner off $(AUDIT_IGNORES)

check: lint test sast audit  ## everything CI runs except gitleaks (gitleaks runs in pre-commit and CI)

report:  ## write reports/summary.txt from the stored events
	$(PYTHON) -m app.reports

evidence-red:  ## seeded-bug tests with xfail disabled: red while a bug is open, green once fixed
	PYTHON=$(PYTHON) scripts/evidence_red.sh docs/evidence/latest-red.txt

demo-push:  ## show the pre-push guard refusing direct and force pushes (throwaway local remote)
	scripts/demo_push_refusal.sh

demo-gitleaks:  ## show a commit with a fake key being refused
	scripts/demo_gitleaks_refusal.sh

demo-hook:  ## replay the poisoned note's actions through the agent's PreToolUse guard
	scripts/demo_agent_hook.sh
