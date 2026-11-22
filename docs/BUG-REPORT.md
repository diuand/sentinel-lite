# Seeded bug report

Ten bugs were planted on purpose in the commit tagged `baseline-vulnerable`.
Each one was fixed in its own pull request. This file documents every bug:
how it was planted, how it can be exploited (safely, on `127.0.0.1`), what
it does to this app and to everything around it, how it was fixed, and the
proof.

- **Line numbers** refer to the tag `baseline-vulnerable`.
- **Risk IDs** refer to `RISK-REGISTER.xlsx`.
- **Scores** are Likelihood × Impact on the register's 1–5 scales.
- **Regression tests** live in `tests/test_seeded_bugs.py`. On the tag they are red (`make evidence-red`, saved in `docs/evidence/baseline-red.txt`); on `main` they are green.

Sections are added as each fix PR merges, so this file closes in the same order as the register.

---

## B-09, Insecure CI workflow (moving tags, write-all, pull_request_target)

- **Risk IDs / CWE / ATT&CK:** R-08 · CWE-829 (inclusion of functionality from an untrusted control sphere) · ATT&CK T1195.002 (compromise software supply chain), T1552 (unsecured credentials: the workflow token)
- **Where (file:line on tag baseline-vulnerable):** `.github/workflows/ci-baseline.yml:4` (`pull_request_target`), `:7` (`permissions: write-all`), `:13` and `:16` (`actions/checkout@v4`, `actions/setup-python@v5`), `:15` (checks out `github.event.pull_request.head.sha`).
- **How it was introduced:** this is what a "make CI work for fork PRs" copy-paste usually looks like. `pull_request_target` is chosen because it "has access to secrets", `write-all` makes permission errors go away, and `@v4` tags are the README default. Each line looks harmless on its own. Together they hand a write-scoped token to code from whoever opens a PR.
- **How it can be exploited (safe local reproduction):** `pytest tests/test_seeded_bugs.py -k b09` statically detects all three problems; zizmor reports them too (`dangerous-triggers`, `excessive-permissions`, `unpinned-uses`). The real attack, not reproduced on purpose: an outsider forks the repo and opens a PR that changes `tests/conftest.py` to read `GITHUB_TOKEN` from the runner. `pull_request_target` runs in the context of the *base* repo with a `write-all` token, and the job checks out and runs the *PR's* code. The attacker's conftest can then push to `main`, move tags, edit workflows or publish releases. Separately, whoever controls the `v4` tag of a third-party action can change the code that runs, without any change to this repo.
- **Impact on this app (C/I/A):** C high (repository contents, any secrets given to the workflow), I high (attacker can rewrite code, tags and workflows, including the security gates themselves), A medium (can delete branches and disable CI).
- **Blast radius beyond this app:** the repository becomes the supply chain. Anyone who clones `main` or the tag gets the attacker's code. Chains with **B-01**: a hardcoded key in the repo, or a real key stored as a repo secret, is exfiltrated in the same run. Chains with **R-10**: on GitHub Free there is no branch protection to stop the token from pushing to `main`, so the governance workflow would only see it afterwards. It also undermines the AI-agent controls (B-10), because the attacker could rewrite `.claude/settings.json` and the hook directly on `main`.
- **Likelihood × Impact before / after:** 3 × 5 = **15** → 1 × 5 = **5**
- **The fix:** `ci-baseline.yml` deleted. The replacement `ci.yml` (added in the governance PR) uses `pull_request`, so fork PRs get a read-only token and no secrets. Its workflow-level `permissions: contents: read` grants nothing more anywhere. Every third-party action is pinned to a full 40-character commit SHA with the tag in a trailing comment, and checkout uses `persist-credentials: false`. This PR adds a `zizmor` job that lints every workflow on every PR. With a token, its online audits also verify that each pinned SHA really belongs to the tag in its comment. Fixed in PR #4.
- **Proof the fix works:** `tests/test_seeded_bugs.py::test_b09_third_party_actions_pinned_to_sha` and `::test_b09_least_privilege_and_no_pull_request_target` (green on `main`, red on the tag); the CI `zizmor` job on PR #4 and every later PR.
- **Residual risk:** a pinned SHA is only as good as the review of the bump that changes it (no Dependabot on this repo yet). GitHub-hosted runner images and the pip packages that CI installs are still trusted as they are. `schedule` and `push` workflows run with the base repo's token, so a malicious change that does get merged runs with `contents: read` (and `pull-requests: read` for governance). That is little, but not nothing.
