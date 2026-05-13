#!/usr/bin/env bash
set -euo pipefail

MODE="link"
if [[ "${1:-}" == "--copy" ]]; then
  MODE="copy"
elif [[ "${1:-}" != "" ]]; then
  echo "Usage: ./install.sh [--copy]" >&2
  exit 2
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO_DIR/skills"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
SKILLS_DEST="$CODEX_HOME_DIR/skills"

if [[ ! -d "$SKILLS_SRC" ]]; then
  echo "Missing skills directory: $SKILLS_SRC" >&2
  exit 1
fi

mkdir -p "$SKILLS_DEST"

install_skill() {
  local src="$1"
  local name
  name="$(basename "$src")"
  local dest="$SKILLS_DEST/$name"

  if [[ ! -f "$src/SKILL.md" ]]; then
    echo "Skipping $name: missing SKILL.md" >&2
    return
  fi

  if [[ -L "$dest" ]]; then
    rm "$dest"
  elif [[ -e "$dest" ]]; then
    local backup="$dest.backup.$(date +%Y%m%d%H%M%S)"
    echo "Backing up existing skill: $dest -> $backup"
    mv "$dest" "$backup"
  fi

  if [[ "$MODE" == "copy" ]]; then
    cp -R "$src" "$dest"
    echo "Installed copy: $name"
  else
    ln -s "$src" "$dest"
    echo "Installed link: $name -> $src"
  fi
}

for src in "$SKILLS_SRC"/*; do
  [[ -d "$src" ]] || continue
  install_skill "$src"
done

echo
echo "Done. Installed skills into: $SKILLS_DEST"
echo "Recommended first prompt: Use \$starbench-hsw-builder"
