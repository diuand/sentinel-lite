"""Extra cases for the PreToolUse guard (.claude/hooks/guard.py), beyond the B-10 regression tests."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / ".claude" / "hooks" / "guard.py"


def run(tool, tool_input, cwd=ROOT):
    payload = json.dumps({"tool_name": tool, "tool_input": tool_input, "cwd": str(cwd)})
    return subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True, text=True, timeout=10)


@pytest.mark.parametrize("command", [
    "make test && git push origin main",
    "git -C . push origin refs/heads/main",
    "git push origin +feature/x",
    "git push -uf origin feature/x",
    "git push --force-with-lease=main:abc origin feature/x",
    "git push --all origin",
    "GIT_TRACE=1 git push origin main",
    "source .env && make run",
    "cat secrets/prod.key",
])
def test_blocked_variants(command):
    result = run("Bash", {"command": command})
    assert result.returncode == 2, command
    assert "BLOCKED" in result.stderr


def test_bare_push_on_main_blocked(tmp_path):
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    assert run("Bash", {"command": "git push"}, cwd=tmp_path).returncode == 2


def test_bare_push_on_feature_branch_allowed(tmp_path):
    subprocess.run(["git", "init", "-q", "-b", "fix/b-02", str(tmp_path)], check=True)
    assert run("Bash", {"command": "git push"}, cwd=tmp_path).returncode == 0


@pytest.mark.parametrize("tool,path", [
    ("Edit", ".claude/settings.json"),
    ("Write", str(ROOT / ".claude" / "hooks" / "guard.py")),
    ("Write", ".env"),
    ("Grep", ".env.local"),
])
def test_guardrails_and_secrets_protected_from_file_tools(tool, path):
    assert run(tool, {"file_path": path}).returncode == 2


def test_unparseable_input_fails_closed():
    result = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
