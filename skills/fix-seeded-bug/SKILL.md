---
name: fix-seeded-bug
description: Fix one seeded bug (B-01..B-10) end to end in its own branch and PR - reproduce, red test, fix, make check, bug report, risk register, agent review, PR.
---

# Fix a seeded bug

One bug per branch, one branch per PR. Never fix a second seeded bug "while you're there".

## 1. Branch

```bash
git checkout main && git pull --ff-only
git checkout -b fix/b-0X-short-name
```

## 2. Reproduce (red)

```bash
.venv/bin/pytest --runxfail -m seeded_bug -k b0X -q   # must FAIL before the fix
```

If no regression test covers the bug's real exploit path, add one first,
marked `@pytest.mark.seeded_bug("B-0X")`. Proofs stay benign: marker
strings, files in `tmp_path`, `127.0.0.1` only.

## 3. Fix

- Fix the root cause, not the test. Never weaken an assertion or delete a test.
- Respect the banned-patterns table in `CLAUDE.md`.
- Remove any tracked exception for this bug (`# nosec` line plus its
  "tracked exception" comment, or `.pip-audit-ignore` entries).

## 4. Close the bug in the test suite

Delete `"B-0X"` from `tests/open_bugs.py`. Its tests are now must-pass.

## 5. Verify

```bash
make check                                   # ruff + pytest + bandit + pip-audit
.venv/bin/pytest -m seeded_bug -k b0X -q     # green
```

## 6. Document

- `docs/BUG-REPORT.md`: add or complete the `## B-0X` section (every field of
  the template: where, how introduced, exploit, C/I/A, blast radius, scores,
  fix, proof, residual).
- `RISK-REGISTER.xlsx`: update the bug's row (residual L and I, control
  description defending the drop, evidence path or test ID, status
  Implemented). Recalculate and check there are no formula errors. Never set
  Implemented or Verified with empty Evidence.

## 7. Review and open the PR

Run `skills/review-pr/SKILL.md`. Fix what it finds, then:

```bash
git push -u origin fix/b-0X-short-name
gh pr create --base main --title "fix(...): ... (B-0X)" --body-file <filled template>
```

The PR body uses `.github/pull_request_template.md`, with every checklist
item answered and the "Agent review" section pasted in.
