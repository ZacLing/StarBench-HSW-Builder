#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

if [[ -d .git ]]; then
  git pull --ff-only
else
  echo "No .git directory found. Skipping git pull and reinstalling current files." >&2
fi

./install.sh
