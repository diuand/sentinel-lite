---
name: review-pr
description: Review the current branch against main before opening a PR - banned patterns from CLAUDE.md, risk register coverage, tests, evidence - and write the "Agent review" section of the PR description.
---

# Review a branch before opening its PR

This is an **agent-assisted** review run locally. It is not an enforced gate:
no model API key is available for a CI reviewer, and Copilot code review is
not part of Copilot Free. Its value comes from running it every time and
fixing what it finds *before* the PR is opened.

## 1. Mechanical pass

```bash
python3 skills/review-pr/review.py            # diff of this branch vs main
```

The script lists changed files and flags **added** lines that match the
banned patterns in `CLAUDE.md`: hardcoded keys, string-built SQL,
`yaml.load`, `debug=True`, `0.0.0.0`, unpinned or tag-referenced actions,
`pull_request_target`, `write-all`, logging of headers, and new `# nosec` /
`.pip-audit-ignore` entries. It also flags changes to sensitive paths
(`.github/`, `.claude/`, `memory/`, `skills/`, `rules/`, requirements). It
exits 1 when it finds something.

## 2. Judgement pass (read the diff yourself)

Answer each question in one line:

1. **Scope:** does the diff fix exactly the bug or phase it claims, and nothing else?
2. **Root cause:** is the fix at the cause (e.g. parameterized query) rather than a filter on symptoms?
3. **Tests:** is there a regression test that was red before and is green now? Was any test weakened, skipped or deleted?
4. **Controls:** was any check disabled, ignored or loosened? (Allowed only as a tracked exception tied to an open bug.)
5. **Secrets and data:** any secret, token, real hostname or personal data added (code, tests, docs, evidence)?
6. **Supply chain:** new dependency or action? Pinned? Within the 4-runtime-dependency limit?
7. **Agent surface:** were memory, skills, `CLAUDE.md` or `.claude/` changed? If yes, does the change grant the agent any new power?
8. **Register:** does the bug's row in `RISK-REGISTER.xlsx` have updated residual scores, a control that defends the drop, real evidence, and the right status?
9. **Blast radius:** is the bug-report entry's blast-radius note current?

## 3. Write the result into the PR description

```markdown
## Agent review
Ran `skills/review-pr` on <branch> vs main (<short sha>).
- Mechanical pass: <N> findings (<list, or "none">)
- Scope / root cause / tests / controls / secrets / supply chain / agent surface / register / blast radius: <one line each>
- Fixed before opening: <what changed because of this review, or "nothing">
- Residual concerns for the human reviewer: <or "none">
```

Fix every finding before you open the PR, or explain in the PR why it stands.
