# Memory index

One file per correction learned while building this repo. Each entry says
what went wrong, the rule that follows, and how to check it. Changes to this
folder need a reviewed PR (CODEOWNERS); see B-10 in `docs/BUG-REPORT.md` for why.

| File | Correction |
|---|---|
| [pyyaml-on-key.md](pyyaml-on-key.md) | PyYAML reads a workflow's `on:` key as boolean `True` |
| [flask-propagate-exceptions.md](flask-propagate-exceptions.md) | With `debug=True` Flask re-raises in tests; set `PROPAGATE_EXCEPTIONS=False` to see the real 500 |
| [werkzeug-merges-slashes.md](werkzeug-merges-slashes.md) | `//` in a URL becomes a 308 redirect: test traversal with `..%2F`, never rely on the router |
| [bandit-misses-key-names.md](bandit-misses-key-names.md) | bandit B105 ignores `*_KEY` names; gitleaks needs a custom rule for our key format |
| [evidence-masks-secrets.md](evidence-masks-secrets.md) | Raw test output copied the fake key into docs; evidence files must mask secrets |
| [quarantine-poisoned-memory.md](quarantine-poisoned-memory.md) | A memory note told the agent to bypass PRs, tests and hooks; never import notes unreviewed |
