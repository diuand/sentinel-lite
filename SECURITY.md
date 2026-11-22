# Security policy

## This repository is deliberately vulnerable in its history

Sentinel-Lite is a teaching project. Ten bugs (B-01 to B-10) were planted on
purpose in the commit tagged `baseline-vulnerable` and fixed one by one in
later pull requests. They are documented in `docs/BUG-REPORT.md` and tracked
in `RISK-REGISTER.xlsx`. **Do not deploy the `baseline-vulnerable` tag.**

Every secret that appears anywhere in the history is a fake placeholder
(`slk_live_FAKE…`). No real credential has ever been committed.

## Supported version

Only the current `main` branch is supported.

## Reporting a vulnerability

Please report anything that is **not** one of the documented seeded bugs
privately, through GitHub's "Report a vulnerability" (Security tab), or by
contacting the repository owner directly. Do not open a public issue.

Include the affected endpoint or file, steps to reproduce against
`127.0.0.1`, and the impact you expect. You can expect an answer within
7 days.

## Rules for testing

- Run the service on `127.0.0.1` only. Never expose it on `0.0.0.0` or a public interface.
- Proofs of concept must be benign (marker strings, files in a temp dir).
- Never send traffic to hosts you do not own.

## Tracked exceptions

While seeded bugs were still open, the security gates (bandit, pip-audit)
were already switched on. Each existing finding was recorded as a
**tracked exception** naming its bug ID: an annotated `# nosec` line or a
`.pip-audit-ignore` entry. `tests/test_tracked_exceptions.py` fails if an
exception names a bug that has already been closed. On a finished `main`
there are none left.
