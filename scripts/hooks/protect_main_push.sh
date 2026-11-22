#!/usr/bin/env bash
# pre-push guard: refuse direct pushes to main, deleting main, and force pushes.
#
# Installed by `pre-commit install` (stage: pre-push, see .pre-commit-config.yaml).
# Works both as a pre-commit hook (reads PRE_COMMIT_* variables) and as a raw
# git pre-push hook (reads "<local ref> <local sha> <remote ref> <remote sha>"
# lines on stdin).
#
# This is a local control. `git push --no-verify` skips it; the governance
# workflow on GitHub is what catches that case.
set -uo pipefail

ZERO=0000000000000000000000000000000000000000
status=0

check() {
  local local_sha="$1" remote_ref="$2" remote_sha="$3"
  if [ "$remote_ref" = "refs/heads/main" ] || [ "$remote_ref" = "main" ]; then
    echo "BLOCKED: direct push to main is not allowed. Push a branch and open a pull request." >&2
    status=1
    return
  fi
  if [ "$local_sha" = "$ZERO" ] || [ "$remote_sha" = "$ZERO" ] || [ -z "$remote_sha" ]; then
    return  # branch deletion (not main) or a brand-new branch
  fi
  if ! git cat-file -e "${remote_sha}^{commit}" 2>/dev/null; then
    echo "BLOCKED: remote ${remote_ref} has commits you do not have locally. Fetch first; this hook refuses possible force pushes." >&2
    status=1
    return
  fi
  if ! git merge-base --is-ancestor "$remote_sha" "$local_sha"; then
    echo "BLOCKED: non-fast-forward (force) push to ${remote_ref} is not allowed." >&2
    status=1
  fi
}

if [ -n "${PRE_COMMIT_REMOTE_BRANCH:-}" ]; then
  check "${PRE_COMMIT_TO_REF:-}" "${PRE_COMMIT_REMOTE_BRANCH}" "${PRE_COMMIT_FROM_REF:-}"
else
  while read -r _local_ref local_sha remote_ref remote_sha; do
    [ -z "${remote_ref:-}" ] && continue
    check "$local_sha" "$remote_ref" "$remote_sha"
  done
fi
exit $status
