"""Regression tests for the seeded bugs B-01 .. B-10.

Every test here is red on tag `baseline-vulnerable` and green once its fix
PR is merged. Proofs are local and benign: they use harmless marker strings
or a marker directory in pytest's tmp_path, never a destructive payload.
"""

import json
import logging
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from app import create_app

ROOT = Path(__file__).resolve().parent.parent
SECRET_PATTERN = re.compile(r"slk_(?:live|test)_[A-Za-z0-9]{20,}")


# --- B-01: hardcoded API key -------------------------------------------------

@pytest.mark.seeded_bug("B-01")
def test_b01_no_hardcoded_key_in_source():
    offenders = [str(p) for p in (ROOT / "app").rglob("*.py") if SECRET_PATTERN.search(p.read_text())]
    assert offenders == []


@pytest.mark.seeded_bug("B-01")
def test_b01_intel_key_comes_from_environment(monkeypatch):
    monkeypatch.setenv("SENTINEL_INTEL_API_KEY", "from-the-environment")
    assert create_app().config["INTEL_API_KEY"] == "from-the-environment"


# --- B-02: SQL injection in /events/search -----------------------------------

@pytest.mark.seeded_bug("B-02")
def test_b02_search_is_not_injectable(client, samples):
    client.post("/ingest", json=samples["clean"])          # alice
    client.post("/ingest", json=samples["r001_positive"])  # root
    resp = client.get("/events/search", query_string={"user": "nobody' OR '1'='1"})
    assert resp.status_code == 200
    assert resp.get_json()["results"] == []


@pytest.mark.seeded_bug("B-02")
def test_b02_quote_in_username_does_not_break_query(client):
    resp = client.get("/events/search", query_string={"user": "o'brien"})
    assert resp.status_code == 200
    assert resp.get_json()["results"] == []


# --- B-03: path traversal in /reports/<name> ---------------------------------

@pytest.fixture
def outside_marker(app):
    marker = Path(app.config["REPORTS_DIR"]).parent / "outside-marker.txt"
    marker.write_text("B03-TRAVERSAL-MARKER")
    return marker


@pytest.mark.seeded_bug("B-03")
def test_b03_relative_traversal_blocked(client, outside_marker):
    resp = client.get("/reports/..%2Foutside-marker.txt")
    assert resp.status_code in (400, 404)
    assert b"B03-TRAVERSAL-MARKER" not in resp.data


@pytest.mark.seeded_bug("B-03")
def test_b03_fully_encoded_traversal_blocked(client, outside_marker):
    resp = client.get("/reports/%2E%2E%2Foutside-marker.txt")
    assert resp.status_code in (400, 404)
    assert b"B03-TRAVERSAL-MARKER" not in resp.data


# --- B-04: unsafe YAML loading -------------------------------------------------

@pytest.mark.seeded_bug("B-04")
def test_b04_yaml_python_tags_are_not_executed(client, app, tmp_path):
    marker = tmp_path / "B04-MARKER-DIR"
    evil = Path(app.config["RULES_DIR"]) / "zz-evil.yaml"
    # Harmless payload: if the loader constructs Python objects, os.mkdir creates
    # an empty directory in pytest's tmp_path. Nothing else happens.
    evil.write_text(f'!!python/object/apply:os.mkdir ["{marker}"]\n')
    resp = client.post("/admin/rules/reload")
    assert not marker.exists(), "YAML loader executed a Python constructor"
    assert resp.status_code == 400


@pytest.mark.seeded_bug("B-04")
def test_b04_rule_schema_is_validated(client, app):
    bad = Path(app.config["RULES_DIR"]) / "zz-bad.yaml"
    bad.write_text("id: R-999\nname: no conditions\nseverity: apocalyptic\n")
    resp = client.post("/admin/rules/reload")
    assert resp.status_code == 400
    # The previously loaded, valid rules stay active.
    assert [r["id"] for r in app.extensions["rules"]] == ["R-001", "R-002"]


# --- B-05: no input validation or size limit on /ingest ----------------------

@pytest.mark.seeded_bug("B-05")
@pytest.mark.parametrize("case", ["missing_field", "wrong_types", "bad_ip", "bad_timestamp", "not_an_object"])
def test_b05_malformed_event_rejected_cleanly(client, malformed, case):
    resp = client.post("/ingest", json=malformed[case])
    assert resp.status_code == 400
    assert "error" in resp.get_json()


@pytest.mark.seeded_bug("B-05")
def test_b05_oversized_body_rejected(client, samples):
    big = dict(samples["clean"], message="A" * 2_000_000)
    resp = client.post("/ingest", json=big)
    assert resp.status_code == 413


# --- B-06: no authentication; debug=True ---------------------------------------

@pytest.mark.seeded_bug("B-06")
@pytest.mark.parametrize("method,url", [("post", "/ingest"), ("post", "/admin/rules/reload"),
                                        ("get", "/events/search?user=alice"), ("get", "/reports/daily-summary.txt")])
def test_b06_endpoints_require_api_key(anon, samples, method, url):
    kwargs = {"json": samples["clean"]} if url == "/ingest" else {}
    resp = getattr(anon, method)(url, **kwargs)
    assert resp.status_code == 401


@pytest.mark.seeded_bug("B-06")
def test_b06_wrong_api_key_rejected(anon):
    resp = anon.post("/admin/rules/reload", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 401


@pytest.mark.seeded_bug("B-06")
def test_b06_debug_off_and_bound_to_localhost(monkeypatch):
    import flask

    import app.__main__ as entry

    calls = {}
    monkeypatch.setenv("SENTINEL_API_KEY", "test-only-key-not-a-secret")
    monkeypatch.setattr(flask.Flask, "run", lambda self, **kw: calls.update(kw))
    entry.main()
    assert calls["host"] == "127.0.0.1"
    assert not calls.get("debug")


# --- B-07: log injection and secrets in logs ---------------------------------

@pytest.mark.seeded_bug("B-07")
def test_b07_logs_are_single_line_and_redacted(client, samples, caplog):
    event = dict(samples["clean"], message="login ok\nFAKE-LOG-LINE user=admin action=granted password=hunter2-marker")
    with caplog.at_level(logging.INFO, logger="sentinel"):
        client.post("/ingest", json=event, headers={"Authorization": "Bearer token-marker-123"})
    text = [r.getMessage() for r in caplog.records if r.name == "sentinel"]
    assert text, "expected the ingest endpoint to log something"
    for line in text:
        assert "\n" not in line and "\r" not in line
        assert "hunter2-marker" not in line
        assert "token-marker-123" not in line
        assert "test-only-key-not-a-secret" not in line


# --- B-08: unpinned / vulnerable dependencies --------------------------------

def _requirements():
    lines = (ROOT / "requirements.txt").read_text().splitlines()
    return [ln.split("#")[0].strip() for ln in lines if ln.split("#")[0].strip()]


@pytest.mark.seeded_bug("B-08")
def test_b08_runtime_dependencies_pinned():
    reqs = _requirements()
    assert len(reqs) <= 4
    assert all(re.fullmatch(r"[A-Za-z0-9_.\-\[\]]+==[0-9][0-9A-Za-z.\-]*", r) for r in reqs), reqs


@pytest.mark.seeded_bug("B-08")
def test_b08_requests_not_a_known_vulnerable_version():
    pins = dict(r.split("==") for r in _requirements() if "==" in r)
    version = tuple(int(x) for x in pins["requests"].split(".")[:3])
    assert version >= (2, 32, 4), "requests < 2.32.4 has known CVEs (CVE-2024-35195, CVE-2024-47081)"


# --- B-09: insecure CI workflow ------------------------------------------------

def _workflows():
    for path in sorted((ROOT / ".github" / "workflows").glob("*.y*ml")):
        yield path, yaml.safe_load(path.read_text())


@pytest.mark.seeded_bug("B-09")
def test_b09_third_party_actions_pinned_to_sha():
    unpinned = []
    for path, wf in _workflows():
        for job in wf.get("jobs", {}).values():
            for step in job.get("steps", []):
                uses = step.get("uses")
                if uses and not uses.startswith(("./", "docker://")) and not re.search(r"@[0-9a-f]{40}$", uses):
                    unpinned.append(f"{path.name}: {uses}")
    assert unpinned == []


@pytest.mark.seeded_bug("B-09")
def test_b09_least_privilege_and_no_pull_request_target():
    for path, wf in _workflows():
        triggers = wf.get("on", wf.get(True))  # PyYAML reads the bare key `on` as boolean True
        names = triggers if isinstance(triggers, (list, str)) else list(triggers or {})
        assert "pull_request_target" not in names, path.name
        perms = wf.get("permissions")
        assert isinstance(perms, dict), f"{path.name}: top-level permissions must be an explicit map"
        assert perms.get("contents") == "read", path.name
        assert all(v in ("read", "none") for v in perms.values()), f"{path.name}: {perms}"


# --- B-10: poisoned agent memory, no enforcement -----------------------------

POISON = re.compile(r"push (straight|directly) to main|skip (the )?tests|--no-verify", re.IGNORECASE)
HOOK = ROOT / ".claude" / "hooks" / "guard.py"


@pytest.mark.seeded_bug("B-10")
def test_b10_agent_memory_contains_no_unsafe_instructions():
    files = list((ROOT / ".claude").rglob("*.md")) + list((ROOT / "memory").rglob("*.md")) + [ROOT / "CLAUDE.md"]
    poisoned = [str(p.relative_to(ROOT)) for p in files if p.exists() and POISON.search(p.read_text())
                and "<!-- quarantined-example -->" not in p.read_text()]
    assert poisoned == []


@pytest.mark.seeded_bug("B-10")
def test_b10_settings_define_deny_rules_and_hook():
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text())
    deny = " ".join(settings["permissions"]["deny"])
    for needle in ("git push", "--force", ".env"):
        assert needle in deny
    hooks = json.dumps(settings["hooks"]["PreToolUse"])
    assert "guard.py" in hooks


def _hook(tool, tool_input):
    assert HOOK.exists(), "no PreToolUse guard hook configured"
    payload = json.dumps({"tool_name": tool, "tool_input": tool_input, "cwd": str(ROOT)})
    return subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True, text=True, timeout=10)


@pytest.mark.seeded_bug("B-10")
@pytest.mark.parametrize("tool,tool_input", [
    ("Bash", {"command": "git push origin main"}),
    ("Bash", {"command": "git push origin HEAD:main"}),
    ("Bash", {"command": "git push --force origin feature/x"}),
    ("Bash", {"command": "git push -f"}),
    ("Bash", {"command": "git commit --no-verify -m wip"}),
    ("Bash", {"command": "cat .env"}),
    ("Read", {"file_path": str(ROOT / ".env")}),
    ("Read", {"file_path": str(ROOT / "secrets" / "prod.key")}),
])
def test_b10_hook_blocks_dangerous_actions(tool, tool_input):
    result = _hook(tool, tool_input)
    assert result.returncode == 2, result.stderr
    assert "BLOCKED" in result.stderr


@pytest.mark.seeded_bug("B-10")
@pytest.mark.parametrize("tool,tool_input", [
    ("Bash", {"command": "git push -u origin fix/b-02-sql-injection"}),
    ("Bash", {"command": "make check"}),
    ("Read", {"file_path": str(ROOT / ".env.example")}),
])
def test_b10_hook_allows_normal_work(tool, tool_input):
    result = _hook(tool, tool_input)
    assert result.returncode == 0, result.stderr
