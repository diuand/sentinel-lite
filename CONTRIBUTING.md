# Contributing

## Ground rules

1. **Never commit to `main`.** Work on a branch: `fix/b-0x-short-name`, `phase-n-topic`, `docs/...`.
2. **Every change reaches `main` through a pull request** that cites the risk IDs (`R-xx`) and bug IDs (`B-xx`) it addresses.
3. **`make check` must pass** before you open the PR. Paste its output into the PR.
4. **No force pushes**, no `--no-verify`, no disabling a check to make it pass, no weakening a test to make it green.
5. One seeded bug per fix PR. Never fix a seeded bug quietly inside another change.

## Setup

```bash
make setup                      # .venv + runtime and dev dependencies
.venv/bin/pre-commit install    # installs the pre-commit AND pre-push hooks
```

The hooks:

| Hook | Stage | What it stops |
|---|---|---|
| `no-commit-to-branch` | commit | commits made directly on `main` |
| `gitleaks` | commit | secrets in staged changes (default rules + the `slk_` key format) |
| `detect-private-key`, `check-added-large-files` | commit | keys and large binaries |
| `protect-main-push` | push | pushing to `main`, deleting `main`, force pushes |

## Commit messages: Conventional Commits

```
<type>(<optional scope>): <summary in the imperative>

<why, in plain language>

Refs: R-03 B-02
```

Types used here: `feat`, `fix`, `docs`, `test`, `ci`, `chore`, `refactor`, `security`.

## Fixing a seeded bug

Follow `skills/fix-seeded-bug/SKILL.md` (added in phase 4). In short:
reproduce → regression test is red → fix → remove the ID from
`tests/open_bugs.py` → `make check` → update `docs/BUG-REPORT.md` and
`RISK-REGISTER.xlsx` → run `skills/review-pr` → open the PR.

## Pull request checklist

The PR template (`.github/pull_request_template.md`) holds the mandatory
self-review checklist. Fill in every item; "n/a" is fine where it applies.
