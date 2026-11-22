#!/usr/bin/env bash
# Show that a commit containing a (freshly generated, fake) key is refused.
#
# Locally: needs `gitleaks` on PATH, or the venv's pre-commit (make setup).
# In CI:   the `secrets` job runs this after installing gitleaks.
# Exit 0 = the commit was refused (good). Exit 1 = it got through (bad).
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

cd "$work"
git init -q -b feature/demo
git config user.email demo@example.invalid
git config user.name "gitleaks demo"
cp "$repo_root/.gitleaks.toml" .

# The key is generated at run time, so no key-shaped literal lives in this repo.
suffix="$(LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 28 || true)"
printf 'INTEL_API_KEY = "slk_live_%s"\n' "$suffix" > config.py
git add config.py .gitleaks.toml

echo "\$ git commit -m 'add config'   (staged config.py contains slk_live_<random>)"
if command -v gitleaks >/dev/null 2>&1; then
  if gitleaks git --pre-commit --staged --redact --config .gitleaks.toml --verbose; then
    echo "NOT REFUSED: gitleaks found nothing (this is a failure)"; exit 1
  fi
elif [ -x "$repo_root/.venv/bin/pre-commit" ]; then
  cp "$repo_root/.pre-commit-config.yaml" .
  sed -i.bak '/repo: local/,$d' .pre-commit-config.yaml && rm -f .pre-commit-config.yaml.bak
  git add .pre-commit-config.yaml
  "$repo_root/.venv/bin/pre-commit" install -q -t pre-commit
  if git commit -q -m "add config"; then
    echo "NOT REFUSED: the commit went through (this is a failure)"; exit 1
  fi
else
  echo "Neither gitleaks nor .venv/bin/pre-commit is available. Run 'make setup' first." >&2
  exit 2
fi
echo "REFUSED: the commit was blocked because it contained a key."
