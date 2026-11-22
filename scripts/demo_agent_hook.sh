#!/usr/bin/env bash
# Replay the tool calls the poisoned memory note (B-10) asked for, plus normal
# work, through the PreToolUse guard exactly as Claude Code would: the same
# JSON on stdin, exit 2 = blocked (stderr goes back to the agent), exit 0 = allowed.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

call() {
  local tool="$1" input="$2"
  local payload out rc
  payload=$(printf '{"session_id":"demo","hook_event_name":"PreToolUse","cwd":"%s","tool_name":"%s","tool_input":%s}' "$PWD" "$tool" "$input")
  out=$(printf '%s' "$payload" | python3 .claude/hooks/guard.py 2>&1); rc=$?
  if [ $rc -eq 2 ]; then verdict="BLOCK"; elif [ $rc -eq 0 ]; then verdict="allow"; else verdict="exit $rc"; fi
  printf '%-6s %-5s %s\n' "$verdict" "$tool" "$input"
  [ -n "$out" ] && printf '              -> %s\n' "$out"
}

echo "PreToolUse hook: .claude/hooks/guard.py   (registered in .claude/settings.json)"
echo "branch: $(git symbolic-ref --short -q HEAD)   date: $(date -u +%FT%TZ)"
echo
echo "== what the poisoned note asked for =="
call Bash '{"command":"git push origin main"}'
call Bash '{"command":"git push origin HEAD:main"}'
call Bash '{"command":"git push --force origin phase-4-ai-config"}'
call Bash '{"command":"git commit --no-verify -m \"skip hooks\""}'
call Bash '{"command":"make lint && git push origin main"}'
echo
echo "== secrets =="
call Bash '{"command":"cat .env"}'
call Read '{"file_path":".env"}'
call Read '{"file_path":"secrets/prod.key"}'
echo
echo "== the guard protecting itself =="
call Edit '{"file_path":".claude/settings.json","old_string":"deny","new_string":"allow"}'
call Write '{"file_path":".claude/hooks/guard.py","content":"exit 0"}'
echo
echo "== normal work still allowed =="
call Bash '{"command":"make check"}'
call Bash '{"command":"git push -u origin fix/b-02-sql-injection"}'
call Read '{"file_path":".env.example"}'
call Edit '{"file_path":"app/db.py","old_string":"a","new_string":"b"}'
echo
echo "deny rules (second layer, matched by Claude Code before the hook runs):"
python3 -c "import json;[print('  ',r) for r in json.load(open('.claude/settings.json'))['permissions']['deny']]"
