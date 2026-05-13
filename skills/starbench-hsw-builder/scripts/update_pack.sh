#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_DIR="$(cd "$SKILL_DIR/../.." && pwd)"

echo "repo_dir=$REPO_DIR"

if ! git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "status=not_git"
  echo "message=This skill pack is not inside a Git repository."
  exit 0
fi

if ! git -C "$REPO_DIR" diff --quiet || ! git -C "$REPO_DIR" diff --cached --quiet; then
  echo "status=dirty"
  echo "message=Local changes are present; update was skipped to avoid overwriting work."
  exit 0
fi

BEFORE="$(git -C "$REPO_DIR" rev-parse HEAD)"

if ! git -C "$REPO_DIR" fetch --all --prune; then
  echo "status=remote_error"
  echo "message=Could not reach the remote repository."
  exit 0
fi

if ! git -C "$REPO_DIR" pull --ff-only; then
  echo "status=pull_failed"
  echo "message=Could not fast-forward to the latest version."
  exit 0
fi

AFTER="$(git -C "$REPO_DIR" rev-parse HEAD)"

if [[ -x "$REPO_DIR/install.sh" ]]; then
  "$REPO_DIR/install.sh" >/dev/null
else
  echo "status=install_missing"
  echo "message=Updated repository, but install.sh was not found or is not executable."
  exit 0
fi

if [[ "$BEFORE" == "$AFTER" ]]; then
  echo "status=current"
  echo "message=Already up to date."
  exit 0
fi

echo "status=updated"
echo "before=$BEFORE"
echo "after=$AFTER"
echo "changed_files<<EOF"
git -C "$REPO_DIR" diff --name-only "$BEFORE" "$AFTER" || true
echo "EOF"
echo "commits<<EOF"
git -C "$REPO_DIR" log --oneline "$BEFORE..$AFTER" || true
echo "EOF"
