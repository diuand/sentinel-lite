#!/usr/bin/env python3
"""Mechanical half of skills/review-pr: scan this branch's diff against main.

Flags *added* lines that match the banned patterns in CLAUDE.md, plus changes
to sensitive paths. Exit 1 if anything is flagged. Stdlib only.

Usage: python3 skills/review-pr/review.py [base-ref]   (default: main)
"""

import re
import subprocess
import sys

BANNED = [
    ("hardcoded key", re.compile(r"slk_(?:live|test)_[A-Za-z0-9]{20,}|(?i:(api_?key|secret|token|password)\s*=\s*['\"][^'\"]{8,}['\"])")),
    ("string-built SQL", re.compile(r"(?i)(execute\(\s*f['\"]|f['\"][^'\"]*\b(select|insert|update|delete)\b[^'\"]*\{)")),
    ("unsafe YAML", re.compile(r"yaml\.(load|unsafe_load)\(|yaml\.(Loader|UnsafeLoader|FullLoader)\b")),
    ("debug=True", re.compile(r"debug\s*=\s*True|FLASK_DEBUG\s*=\s*1")),
    ("bind 0.0.0.0", re.compile(r"0\.0\.0\.0")),
    ("action by tag", re.compile(r"uses:\s*[\w.-]+/[\w./-]+@(?![0-9a-f]{40}\b)")),
    ("pull_request_target", re.compile(r"pull_request_target")),
    ("write-all", re.compile(r"write-all|:\s*write\b")),
    ("logs headers", re.compile(r"log\w*\.(info|debug|warning|error)\(.*request\.headers")),
    ("new nosec", re.compile(r"#\s*nosec")),
    ("unpinned requirement", re.compile(r"^[A-Za-z0-9_.\-\[\]]+\s*$")),
]
SENSITIVE = (".github/", ".claude/", "memory/", "skills/", "rules/", "CLAUDE.md", "requirements",
             ".pre-commit-config.yaml", ".gitleaks.toml", ".pip-audit-ignore")
# Files where the banned strings legitimately appear as documentation, tests or detectors.
DOC_PATHS = ("docs/", "CLAUDE.md", "skills/review-pr/", "tests/", "memory/", ".claude/hooks/", "README.md",
             "SECURITY.md", "CONTRIBUTING.md", ".github/pull_request_template.md",
             "scripts/demo_gitleaks_refusal.sh")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "main"
    merge_base = git("merge-base", base, "HEAD").strip()
    files = git("diff", "--name-status", merge_base, "HEAD").splitlines()
    print(f"Reviewing {git('rev-parse', '--abbrev-ref', 'HEAD').strip()} against {base} ({merge_base[:7]})")
    print(f"{len(files)} file(s) changed:")
    for line in files:
        print(f"  {line}")

    findings = []
    current = None
    for line in git("diff", "-U0", merge_base, "HEAD").splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else None
            continue
        if not current or not line.startswith("+") or current.startswith(DOC_PATHS) or current.endswith(".md"):
            continue  # Markdown is documentation: it names banned patterns to explain them
        text = line[1:]
        if text.lstrip().startswith("#") and not current.startswith("requirements"):
            continue  # comments may name banned patterns to explain them
        for label, pattern in BANNED:
            if label == "unpinned requirement" and not current.startswith("requirements"):
                continue
            if label == "write-all" and not current.startswith(".github/workflows/"):
                continue
            if pattern.search(text) and not text.lstrip().startswith("#!"):
                findings.append(f"{current}: [{label}] {text.strip()[:120]}")

    sensitive = sorted({ln.split("\t")[-1] for ln in files if ln.split("\t")[-1].startswith(SENSITIVE)})
    print("\nSensitive paths touched (need owner review):", ", ".join(sensitive) or "none")
    print(f"\nBanned-pattern findings in added lines: {len(findings)}")
    for f in findings:
        print(f"  - {f}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
