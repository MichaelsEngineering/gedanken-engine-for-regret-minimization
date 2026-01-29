#!/usr/bin/env bash
set -euo pipefail

BASE="${1:-origin/main}"
HEAD="${2:-HEAD}"

printf 'base=%s\n' "$BASE"
printf 'head=%s\n' "$HEAD"

printf '\n## branch\n'
git rev-parse --abbrev-ref "$HEAD"

printf '\n## commits\n'
git log --oneline --decorate "$BASE..$HEAD"

printf '\n## diffstat\n'
git diff --stat "$BASE..$HEAD"

printf '\n## files\n'
git diff --name-only "$BASE..$HEAD"

if command -v gh >/dev/null 2>&1 && [[ -n "${PR_NUMBER:-}" ]]; then
  printf '\n## gh pr view\n'
  gh pr view "$PR_NUMBER" --json title,body,baseRefName,headRefName,files,commits

  printf '\n## gh pr diff --stat\n'
  gh pr diff "$PR_NUMBER" --stat
fi
