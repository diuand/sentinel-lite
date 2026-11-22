#!/usr/bin/env bash
# Show that the pre-push guard refuses (1) a direct push to main and
# (2) a force push to any branch. Uses a throwaway bare repo in /tmp as the
# remote, so nothing is sent anywhere.
set -uo pipefail

repo_root="$(git rev-parse --show-toplevel)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

git init -q --bare -b main "$work/remote.git"
git clone -q "$work/remote.git" "$work/clone" 2>/dev/null
cd "$work/clone"
git config user.email demo@example.invalid
git config user.name "push demo"
# Seed the remote the way the real repo was seeded (root commit), before the hook exists.
git commit -q --allow-empty -m "root"
git push -q origin main 2>/dev/null
# Install the same guard pre-commit installs as the pre-push hook.
cp "$repo_root/scripts/hooks/protect_main_push.sh" .git/hooks/pre-push
chmod +x .git/hooks/pre-push

echo "== 1. direct push to main =="
git commit -q --allow-empty -m "change made on main"
echo "\$ git push origin main"
git push origin main 2>&1 && echo "UNEXPECTED: push accepted" || echo "-> refused (exit $?)"

echo
echo "== 2. force push to a branch =="
git checkout -q -b feature/x
git reset -q --hard origin/main
git commit -q --allow-empty -m "v1"
git push -q origin feature/x
git commit -q --amend --allow-empty -m "v1 rewritten"
echo "\$ git push --force origin feature/x"
git push --force origin feature/x 2>&1 && echo "UNEXPECTED: push accepted" || echo "-> refused (exit $?)"

echo
echo "== 3. normal branch push (allowed) =="
git commit -q --allow-empty -m "v2"
echo "\$ git push origin feature/y"
git push -q origin HEAD:feature/y 2>&1 && echo "-> accepted"

echo
echo "remote main is still at: $(git --git-dir="$work/remote.git" log --oneline -1 main)"
