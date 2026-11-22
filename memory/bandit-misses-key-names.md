# bandit does not flag `*_KEY = "..."`; gitleaks needs our key format

**What happened:** while planning the scanners, we checked which tool would
catch B-01. bandit's B105 (hardcoded password) matches names like
`password`, `secret` and `token`, not `INTEL_API_KEY`. Gitleaks' generic rule
depends on entropy and keywords, and a key containing a readable word
(`FAKE`) can fall below the threshold.

**Rule:** secrets are caught by gitleaks with the custom `sentinel-api-key`
rule in `.gitleaks.toml` (`slk_(live|test)_...`), not by bandit. The
regression test `test_b01_no_hardcoded_key_in_source` uses the same pattern.

**Check:** `scripts/demo_gitleaks_refusal.sh` (also the CI `secrets` job).
