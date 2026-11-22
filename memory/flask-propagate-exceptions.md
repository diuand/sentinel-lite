# Flask re-raises exceptions in tests when debug (or testing) is on

**What happened:** with `debug=True` (seeded bug B-06), Flask sets
`PROPAGATE_EXCEPTIONS`, so a crash in `/ingest` raised inside the test
instead of returning the 500 a real client would get. The B-05 evidence
showed a Python traceback, not the HTTP behaviour we wanted to prove.

**Rule:** the test `app` fixture sets `PROPAGATE_EXCEPTIONS=False`, so tests
observe what clients observe. Don't set `TESTING=True` for the same reason.

**Check:** `tests/conftest.py` (`app` fixture).
