# Werkzeug turns `//` into a redirect, so it is not a traversal defence

**What happened:** the first B-03 test tried an absolute path
(`/reports//tmp/...`). Werkzeug merged the slashes and answered
`308 PERMANENT REDIRECT`, which looked like a block but was only the
router's slash merging. `..%2F` and `%2E%2E%2F` reach the view unchanged and
do exploit the bug.

**Rule:** test traversal with encoded `../` sequences. The fix must stand on
its own (resolve + containment + allowlist) and must not count on the router
normalizing anything.

**Check:** `tests/test_seeded_bugs.py::test_b03_*`.
