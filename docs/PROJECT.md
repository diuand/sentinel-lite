# Sentinel-Lite: project definition

## 1. Definition and scope

**What it is.** A small log-enrichment service for a security team: it
receives log events, normalizes them, tags events from known-bad IPs using a
local threat-intel feed, applies detection rules, and keeps the results
searchable. It stands in for the ingestion and enrichment stage of a SIEM
pipeline (Logstash + OpenSearch + MISP in the syllabus), cut down to what
runs on an 8 GB laptop.

**Why it exists.** It is the subject of a risk and damage management
exercise. The scope was derived from the risk register (`RISK-REGISTER.xlsx`,
filled in *before* any code, in PR #1; the course template was not available, so the workbook was built from scratch with the same structure, as its Read me sheet explains): every component exists either
because the service needs it or because a register row needs something real
to protect and test.

**In scope.** The Flask service and its six endpoints; the ten seeded bugs
and their fixes; repository, CI and AI-agent guardrails; the evidence that
each control works.

**Out of scope (deliberately).** See §8: production deployment, real
intel platforms, dashboards, containers, signing.

## 2. Risks addressed

Scores are Likelihood × Impact (1–5 each) from the register's Scales sheet.

| ID | Register | Risk | Bugs | Inherent | Residual | Main controls | Evidence |
|---|---|---|---|---|---|---|---|
| R-01 | External | Credential leaked from source or history | B-01 | 4×4 = 16 | 2×4 = 8 | env/.env config, gitleaks (pre-commit + CI + custom rule), `.gitleaksignore` by fingerprint | `test_b01_*`, `docs/evidence/gitleaks-refused.txt` |
| R-02 | Internal | Query-API input reaches SQL / filesystem unchecked | B-02, B-03 | 4×4 = 16 | 1×4 = 4 | parameterized SQL; name allowlist + resolve containment | `test_b02_*`, `test_b03_*`, `test_reports_hardening.py` |
| R-03 | Internal | Rule loading executes code; a bad rule silently disables detection | B-04 | 3×5 = 15 | 1×5 = 5 | `yaml.safe_load`, pydantic schema, all-or-nothing reload, CODEOWNERS on `rules/` | `test_b04_*`, `test_rules_schema.py` |
| R-04 | External | Malformed or flood traffic from hostile / known-bad sources crashes or blinds ingest | B-05 | 4×3 = 12 | 2×3 = 6 | pydantic validation, 64 KiB cap, 400/413, no tracebacks; enrichment flags known-bad sources | `test_b05_*`, `docs/evidence/enrichment.txt` |
| R-05 | Internal | Unauthenticated ingest/admin; debug console exposed | B-06 | 4×5 = 20 | 2×5 = 10 | deny-by-default API key (`hmac.compare_digest`), random key from `make setup`, debug hard-off, `127.0.0.1` | `test_b06_*` |
| R-06 | Internal | Forged log lines and secrets in logs | B-07 | 3×3 = 9 | 1×3 = 3 | `logsafe.clean()`, no header logging, `SanitizingFilter` | `test_b07_*`, `test_logsafe.py` |
| R-07 | External | Vulnerable or unpinned third-party dependency | B-08 | 3×4 = 12 | 2×4 = 8 | exact pins, `requests` upgraded, pip-audit (full tree) in `make check` and CI | `test_b08_*`, CI `pip-audit` job |
| R-08 | Operational | CI pipeline compromise through an insecure workflow | B-09 | 3×5 = 15 | 1×5 = 5 | `pull_request` only, `contents: read`, SHA-pinned actions, `persist-credentials: false`, zizmor | `test_b09_*`, CI `zizmor` job |
| R-09 | Operational | AI agent acts on poisoned memory or exceeds its permissions | B-10 | 3×4 = 12 | 2×4 = 8 | memory via PR + CODEOWNERS, deny rules, `PreToolUse` guard hook | `test_b10_*`, `test_agent_guard.py`, `docs/evidence/hook-blocked.txt` |
| R-10 | Operational | Unreviewed or weakly reviewed change reaches `main` | none | 4×4 = 16 | 3×4 = 12 | PR-only workflow, pre-commit/pre-push guards, governance workflow (detective), PR checklist, agent-assisted review | `docs/evidence/push-refused-*.txt`, governance runs, PR descriptions |

R-10 keeps the highest residual on purpose. On GitHub Free nothing on the
server *prevents* a bad merge or a direct push; the controls make one
unlikely and visible, but the review itself is not automated (§6).

## 3. Architecture

See the Mermaid diagram in `README.md`. Components:

| File | Role | Lines |
|---|---|---|
| `app/__init__.py` | app factory, logging, wires provider + rules | 29 |
| `app/config.py` | settings from environment / `.env` | 42 |
| `app/routes.py` | endpoints, deny-by-default auth, error handlers | 115 |
| `app/normalize.py` | pydantic `RawEvent`, ECS-like mapping | 44 |
| `app/intel.py` | `IntelProvider`, `LocalFeedProvider`, `MispProvider` stub, `enrich()` | 74 |
| `app/rules.py` | rule schema, `safe_load` loader, matcher | 85 |
| `app/db.py` | SQLite (parameterized only) | 66 |
| `app/logsafe.py` | log sanitizing and redaction | 38 |
| `app/reports.py` | `make report` summary generator | 35 |
| `app/__main__.py` | `make run` entry point (loopback, debug off) | 15 |

543 lines of app code (limit ~600); 4 runtime dependencies (Flask, pydantic,
PyYAML, requests). Threat intel comes from `data/intel_feed.json` (RFC 5737
documentation addresses only) through the `IntelProvider` interface.
`MispProvider` shows how a real MISP would plug in (REST `restSearch`, key
from `SENTINEL_INTEL_API_KEY`), but it is never enabled by default and never
called in tests. Shodan is a possible future provider (host context for
source IPs: open ports, banners), documented here only.

## 4. How the seeded bugs are kept honest

- **Regression tests first.** Each bug has tests marked `@pytest.mark.seeded_bug("B-xx")` that exercise the real exploit path with a harmless marker.
- **`tests/open_bugs.py` + strict xfail.** While a bug ID is listed, its tests are `xfail(strict=True)`: they *must* fail, so the suite is green on the vulnerable baseline without hiding anything. If one passed early, strict xfail would turn it red. Each fix PR deletes exactly one ID; the diff shows the bug being closed.
- **Red/green evidence.** `make evidence-red` runs the seeded tests with xfail disabled: 38 failures on `baseline-vulnerable` (`docs/evidence/baseline-red.txt`), 38 passes on `main` (`docs/evidence/final-green.txt`).
- **Tracked exceptions.** The scanners went live in phase 3, while bugs B-01..B-08 were still open on purpose. Their existing findings were recorded as exceptions tied to a bug ID (an annotated `# nosec`, a `.pip-audit-ignore` line). `tests/test_tracked_exceptions.py` fails if an exception names a closed bug, so none can outlive its bug. On `main` there are none.

## 5. GitHub route 4: what is enforced and what is only detected

Private repository on GitHub Free: **branch protection and rulesets are not
available**, and CODEOWNERS review cannot be made required.

| Goal | Free-plan equivalent here | Enforced? |
|---|---|---|
| No direct commits to `main` | `no-commit-to-branch` pre-commit hook | locally, skippable with `--no-verify` |
| No direct or force pushes | `protect-main-push` pre-push hook; agent `PreToolUse` hook | locally, skippable by a human with `--no-verify` |
| Every change via a merged PR | `governance.yml` checks main's first-parent history against merged PRs after every push (root commit is the only exception) | **detective**: red run plus notification, not a block |
| Required status checks | CI runs on every PR; "merge only when green" is a written rule | by discipline |
| Owner review of sensitive paths | CODEOWNERS auto-requests the owner | not required |
| Secret scanning / push protection | gitleaks in pre-commit and CI | locally + CI (detective after push) |

**If the plan changes** (public repo, GitHub Pro, or the ULBS organization):
add a ruleset on `main` with *require a pull request* (1 approval, code-owner
review), *require status checks* (`ruff + pytest + import check`, `bandit`,
`pip-audit`, `gitleaks`, `zizmor`), *block force pushes*, *restrict
deletions*; enable secret scanning push protection. The governance workflow
then becomes a second line rather than the only one, and R-10's likelihood
drops from 3 to 2.

## 6. AI workflow

- **`CLAUDE.md`**: role, voice, banned-patterns table, stack conventions, default commands. It imports only `memory/MEMORY.md`.
- **`memory/`**: one file per real correction made while building (six so far: PyYAML's `on:` key, Flask exception propagation, Werkzeug slash merging, bandit's blind spot for `*_KEY`, masking secrets in evidence, the poisoned note itself).
- **`skills/fix-seeded-bug`**: reproduce → red test → fix → close in `open_bugs.py` → `make check` → bug report + register → review → PR.
- **`skills/review-pr`** (+ `review.py`): run locally before every PR. A mechanical pass flags banned patterns in added lines and sensitive paths; a judgement pass answers nine questions; the result is pasted into the PR as "Agent review". Findings are fixed before the PR is opened.
- **Enforcement**: `.claude/settings.json` deny rules and the `PreToolUse` hook (`.claude/hooks/guard.py`). This is what stops the agent; the prose only explains it (see B-10, "Why prose alone is not a control").

### PR review without an API key (honest limits)

There is **no automated reviewer gate**. No model API key was available, and
Copilot code review is not part of Copilot Free. What exists instead is an
**agent-assisted** review: `skills/review-pr` runs locally before each PR and
writes its findings into the PR description, and the PR template's
self-review checklist is mandatory by convention. Nothing in GitHub stops a
PR from being merged without either. That is why R-10's residual stays at
3 × 4 = 12.

**How an Actions-based reviewer would be wired later:**
1. Store the model API key as an encrypted repository secret (e.g. `REVIEW_API_KEY`). Never commit it, and never print it in logs.
2. Add `.github/workflows/ai-review.yml` on `pull_request` (not `pull_request_target`), with `permissions: contents: read, pull-requests: write` at job level only and every action SHA-pinned.
3. Fork PRs receive no secrets on `pull_request`, so the job skips them (`if: github.event.pull_request.head.repo.full_name == github.repository`) instead of failing.
4. The job sends the diff plus `CLAUDE.md`'s banned patterns to the model and posts a review comment. On a plan with rulesets, its status becomes a required check.

**Effect on the register:** R-10 likelihood 3 → 2 (every PR reviewed by a
second pass that cannot be forgotten), residual 12 → 8. With branch
protection as well, likelihood → 1. The new secret would add a small R-01
exposure (a key in CI), contained by the fork-PR rule and minimal
permissions.

## 7. Enrichment evidence

From `docs/evidence/enrichment.txt` (`python3 scripts/demo_enrichment.py`,
real app in-process):

| Event | Source IP | Tags | risk_score |
|---|---|---|---|
| intel_match | 203.0.113.66 (in feed: SSH brute-force scanner) | `threat.indicator.matched` + `threat.*` fields | **70** |
| clean | 192.0.2.10 | none | **10** |
| r001_positive | 192.0.2.77, "Failed password for root" | `rule:R-001` | 35 |
| r002_positive | 192.0.2.90, svc_backup "Accepted password" | `rule:R-002` | 40 |

The negative samples (`r001_negative`, `r002_negative`) stay untagged
(`tests/test_app.py`).

## 8. Limits: what was deliberately not built

| Not built | Why | What stands in |
|---|---|---|
| OpenSearch, Logstash, Grafana, Prometheus | won't fit next to a browser and an IDE in 8 GB | SQLite, a Flask normalizer, a text report |
| MISP, Shodan | not installed; no external traffic allowed | local JSON feed behind `IntelProvider`; MISP stub; Shodan documented |
| Docker image, Hadolint, Trivy | no Dockerfile (not required, and Docker is not required locally) | pip-audit for dependencies |
| Syft SBOM, Cosign signing | nothing is published or released | pinned requirements; could be added to CI later |
| Semgrep | optional heavy scanner | bandit + ruff + regression tests |
| Rate limiting, TLS, per-client keys | out of scope for a loopback lab service | single API key, `127.0.0.1` bind (R-04/R-05 residuals) |
| Branch protection, required reviews | not on GitHub Free for private repos | §5 |
| Automated AI PR reviewer | no API key | §6 |

## 9. What the owner must do by hand

- Keep merging only when CI is green and the checklist is complete; nothing on the server enforces it (§5).
- If the repo ever moves to a plan with rulesets, apply the ruleset in §5.
- Run `.venv/bin/pre-commit install` once per clone (git hooks are not cloned).
- If an AI reviewer is wanted, add the API key as a repository secret and the workflow in §6.
