"""Seeded bugs that are still open.

While a bug ID is listed here, its regression tests are marked
xfail(strict=True): they must fail. That keeps the suite green on the
deliberately vulnerable baseline without hiding anything. If a test starts
passing while its bug is still listed, strict xfail turns that into a failure.

Each fix PR removes exactly one ID from this set, which turns its tests
into normal, must-pass tests. `make evidence-red` runs them with xfail
switched off to show the red state.
"""

OPEN_BUGS = {
    "B-08",
}
