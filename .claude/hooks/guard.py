#!/usr/bin/env python3
"""PreToolUse guard for Claude Code (fix for B-10).

Claude Code runs this before every matching tool call. It sends the call as
JSON on stdin ({"tool_name": ..., "tool_input": {...}, "cwd": ...}).
Exit 0 lets the call run. Exit 2 blocks it, and stderr is shown to the agent
as the reason.

Blocked:
  * git push to main (explicit refspec, HEAD:main, --all/--mirror, or a bare
    `git push` while on main)
  * force pushes: --force, -f, --force-with-lease, +refspec
  * --no-verify on commit/push (skipping the pre-commit and pre-push hooks)
  * reading or writing secret files: .env and .env.* (but not .env.example),
    secrets/, *.pem, *.key, *.p12, *.pfx, id_rsa*, id_ed25519*
  * editing the agent's own guardrails: .claude/settings.json, .claude/hooks/

A memory note can ask the agent to do any of these. This file is why the
agent still can't. Stdlib only, so it runs anywhere Python 3 does.
"""

import json
import os
import re
import shlex
import subprocess
import sys

PROTECTED_BRANCH = "main"
FORCE_FLAGS = {"--force", "-f", "--force-with-lease", "--force-if-includes", "--mirror"}
FILE_TOOLS = {"Read", "Edit", "MultiEdit", "Write", "NotebookEdit", "Grep", "Glob"}
WRITE_TOOLS = {"Edit", "MultiEdit", "Write", "NotebookEdit"}


def block(reason: str) -> None:
    print(f"BLOCKED by .claude/hooks/guard.py: {reason}", file=sys.stderr)
    sys.exit(2)


def is_secret_path(path: str) -> bool:
    p = path.strip("'\"").replace("\\", "/")
    name = p.rsplit("/", 1)[-1]
    if name == ".env.example":
        return False
    if name == ".env" or name.startswith(".env."):
        return True
    if p.startswith("secrets/") or "/secrets/" in p:
        return True
    return name.endswith((".pem", ".key", ".p12", ".pfx")) or name.startswith(("id_rsa", "id_ed25519"))


def is_guardrail_path(path: str) -> bool:
    p = path.replace("\\", "/")
    return p.endswith(".claude/settings.json") or "/.claude/hooks/" in p or p.startswith(".claude/hooks/")


def current_branch(cwd: str) -> str:
    try:
        out = subprocess.run(["git", "symbolic-ref", "--short", "-q", "HEAD"], cwd=cwd or None,
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def check_push(args: list[str], cwd: str) -> None:
    flags = [a for a in args if a.startswith("-")]
    for f in flags:
        if f in FORCE_FLAGS or f.startswith("--force-with-lease="):
            block(f"force push ({f}) is not allowed")
        if re.fullmatch(r"-[A-Za-z]{2,}", f) and "f" in f[1:]:
            block(f"force push ({f}) is not allowed")
        if f in ("--all", "--mirror"):
            block(f"`git push {f}` would include {PROTECTED_BRANCH}")
    positional = [a for a in args if not a.startswith("-")]
    refspecs = positional[1:]  # positional[0] is the remote
    if not refspecs or any(r == "HEAD" for r in refspecs):
        if current_branch(cwd) == PROTECTED_BRANCH:
            block(f"you are on {PROTECTED_BRANCH}; push a feature branch and open a PR")
    for ref in refspecs:
        if ref.startswith("+"):
            block(f"force refspec ({ref}) is not allowed")
        dst = ref.split(":")[-1]
        if dst in (PROTECTED_BRANCH, f"refs/heads/{PROTECTED_BRANCH}"):
            block(f"direct push to {PROTECTED_BRANCH} is not allowed; open a pull request")


def check_bash(command: str, cwd: str) -> None:
    for segment in re.split(r"&&|\|\||[;|\n]", command):
        try:
            tokens = shlex.split(segment)
        except ValueError:
            tokens = segment.split()
        while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
            tokens.pop(0)  # VAR=value prefixes
        if not tokens:
            continue
        for tok in tokens[1:]:
            if is_secret_path(tok.lstrip("<>")):
                block(f"command touches a secret file ({tok})")
        if os.path.basename(tokens[0]) != "git":
            continue
        args, i = tokens[1:], 0
        while i < len(args) and args[i].startswith("-"):  # git -C dir / -c k=v
            i += 2 if args[i] in ("-C", "-c", "--git-dir", "--work-tree") else 1
        sub, rest = (args[i], args[i + 1:]) if i < len(args) else ("", [])
        if sub in ("commit", "push", "merge", "rebase", "am") and "--no-verify" in rest:
            block("--no-verify skips the pre-commit/pre-push guardrails")
        if sub == "commit" and "-n" in rest:
            block("-n (--no-verify) skips the pre-commit guardrails")
        if sub == "push":
            check_push(rest, cwd)


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        block("could not parse the hook input; refusing by default")
    tool = event.get("tool_name", "")
    data = event.get("tool_input", {}) or {}
    cwd = event.get("cwd") or os.getcwd()

    if tool == "Bash":
        check_bash(data.get("command", ""), cwd)
    elif tool in FILE_TOOLS:
        for key in ("file_path", "path", "notebook_path", "pattern"):
            value = data.get(key)
            if isinstance(value, str) and value and is_secret_path(value):
                block(f"{tool} on a secret file ({value})")
            if tool in WRITE_TOOLS and isinstance(value, str) and is_guardrail_path(value):
                block("the agent may not edit its own guardrails; change them in a human-reviewed PR")
    sys.exit(0)


if __name__ == "__main__":
    main()
