"""Tracked exceptions may not outlive the seeded bug they belong to.

The security gates (bandit, pip-audit) were switched on in phase 3, while
the seeded bugs were still open on purpose. Each existing finding was
recorded as a tracked exception that names its bug ID. These tests make that
safe:
- every `# nosec` in app/ needs a "tracked exception: seeded bug B-xx" line above it,
- every .pip-audit-ignore entry needs a B-xx,
- and that bug must still be listed in OPEN_BUGS.
When a fix PR closes a bug, any exception left behind for it fails the suite.
Any new finding that is not a tracked exception fails CI as usual.
"""

import re
from pathlib import Path

from tests.open_bugs import OPEN_BUGS

ROOT = Path(__file__).resolve().parent.parent
BUG_ID = re.compile(r"\bB-\d{2}\b")


def test_every_nosec_is_a_tracked_open_bug():
    problems = []
    for path in (ROOT / "app").rglob("*.py"):
        lines = path.read_text().splitlines()
        for i, line in enumerate(lines):
            if "nosec" not in line:
                continue
            above = lines[i - 1] if i else ""
            ids = BUG_ID.findall(above) if "tracked exception" in above else []
            if not ids or not set(ids) <= OPEN_BUGS:
                problems.append(f"{path.relative_to(ROOT)}:{i + 1}: {line.strip()}")
    assert problems == [], "nosec without an open seeded bug:\n" + "\n".join(problems)


def test_every_pip_audit_ignore_is_a_tracked_open_bug():
    path = ROOT / ".pip-audit-ignore"
    if not path.exists():
        return
    problems = []
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        ids = BUG_ID.findall(line)
        if not ids or not set(ids) <= OPEN_BUGS:
            problems.append(line)
    assert problems == [], "pip-audit ignore without an open seeded bug:\n" + "\n".join(problems)
