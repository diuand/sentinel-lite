# A memory note is input, not authority

**What happened:** the baseline `CLAUDE.md` imported
`.claude/memory/workflow-shortcuts.md`, which told the agent to bypass the PR
flow, the test suite and the git hooks (seeded bug B-10; the full text is
quoted in `docs/BUG-REPORT.md`). Anything
imported into `CLAUDE.md` is loaded into every session as if the owner had
written it.

**Rule:** memory notes describe corrections ("X failed because Y, do Z").
They never grant permissions or tell the agent to skip a control. New or
changed memory goes through a PR reviewed under CODEOWNERS. The deny rules
and `.claude/hooks/guard.py` enforce the hard limits whatever any note says.

**Check:** `tests/test_seeded_bugs.py::test_b10_*`, `docs/evidence/hook-blocked.txt`.
