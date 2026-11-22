#!/usr/bin/env bash
# Run the seeded-bug regression tests with xfail disabled and save the output.
# Usage: scripts/evidence_red.sh docs/evidence/baseline-red.txt
set -euo pipefail
out="${1:?output file}"
py="${PYTHON:-python3}"
{
  echo "# Seeded-bug regression tests, xfail disabled"
  echo "# commit: $(git rev-parse HEAD)  ref: $(git describe --tags --always)"
  echo "# command: pytest --runxfail -m seeded_bug"
  echo "# date: $(date -u +%FT%TZ)  python: $($py -V 2>&1)"
  echo "# Seeded secrets are masked in this file so the fake key is not copied around."
  echo
  $py -m pytest -q --runxfail -m seeded_bug -p no:cacheprovider -rfE --tb=line --show-capture=no 2>&1 || true
} | sed -E "s#$PWD/##g; s#/tmp/pytest-of-[^/]+/pytest-[0-9]+/#<tmp>/#g; s#slk_(live|test)_[A-Za-z0-9.]+#slk_\1_****MASKED****#g" > "$out"
tail -n 1 "$out"
