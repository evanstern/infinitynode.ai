#!/usr/bin/env bash
set -euo pipefail

# Create a patch file for the current branch/worktree.
# Default: diff against forgejo/main if present, else origin/main, else main.
# Usage:
#   scripts/make_patch.sh                # writes patches/<branch>-<timestamp>.patch
#   scripts/make_patch.sh --name foo     # writes patches/foo.patch
#   scripts/make_patch.sh --staged       # patch from staged changes only
#   scripts/make_patch.sh --commit HEAD~ # patch for a specific commit range (e.g. HEAD~3..HEAD)

NAME=""
MODE="worktree"   # worktree|staged|commit
COMMIT_RANGE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME="$2"; shift 2;;
    --staged) MODE="staged"; shift;;
    --commit) MODE="commit"; COMMIT_RANGE="$2"; shift 2;;
    -h|--help)
      sed -n '1,40p' "$0"; exit 0;;
    *)
      echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

mkdir -p patches

branch="$(git rev-parse --abbrev-ref HEAD | tr '/' '-')"
ts="$(date -u +%Y%m%d-%H%M%S)"

if [[ -z "$NAME" ]]; then
  out="patches/${branch}-${ts}.patch"
else
  out="patches/${NAME}.patch"
fi

# pick a sensible base
base="main"
if git show-ref --verify --quiet refs/remotes/forgejo/main; then
  base="forgejo/main"
elif git show-ref --verify --quiet refs/remotes/origin/main; then
  base="origin/main"
fi

case "$MODE" in
  worktree)
    # include unstaged + staged changes relative to base
    git diff --binary "$base" > "$out"
    ;;
  staged)
    git diff --binary --staged > "$out"
    ;;
  commit)
    if [[ -z "$COMMIT_RANGE" ]]; then
      echo "--commit requires a range (e.g. HEAD~3..HEAD or <sha>..HEAD)" >&2
      exit 1
    fi
    git format-patch --stdout "$COMMIT_RANGE" > "$out"
    ;;
  *)
    echo "Internal error: MODE=$MODE" >&2
    exit 1
    ;;
esac

echo "Wrote $out"
