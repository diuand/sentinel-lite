# PyYAML reads the workflow key `on:` as `True`

**What happened:** the B-09 test parsed `.github/workflows/*.yml` with
`yaml.safe_load` and looked up `wf["on"]`. It got nothing, because YAML 1.1
treats a bare `on` as a boolean, so the key is `True`.

**Rule:** when reading GitHub workflow YAML in Python, use
`wf.get("on", wf.get(True))`.

**Check:** `tests/test_seeded_bugs.py::test_b09_least_privilege_and_no_pull_request_target`.
