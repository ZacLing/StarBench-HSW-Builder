# StarBench-HSW Skills

## Install For Codex

These instructions are intended for Codex to execute.

Clone this repository, then run:

```bash
./install.sh
```

The installer links the skills in this repository into:

```text
${CODEX_HOME:-$HOME/.codex}/skills/
```

Installed skills:

```text
starbench-hsw-builder
jsg-task-miner
expert-boost-loop
rubric-crystallizer
```

After installation, start with:

```text
Use $starbench-hsw-builder
```

## Install From A GitHub URL

When given a GitHub repository URL, Codex should:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skill-packs"
cd "${CODEX_HOME:-$HOME/.codex}/skill-packs"
git clone <github-repo-url> starbench-hsw
cd starbench-hsw
./install.sh
```

If `starbench-hsw` already exists, update it instead:

```bash
cd "${CODEX_HOME:-$HOME/.codex}/skill-packs/starbench-hsw"
git pull --ff-only
./install.sh
```

## Update

From the cloned repository:

```bash
./update.sh
```

Or manually:

```bash
git pull --ff-only
./install.sh
```

## Copy Install

Symlink install is the default and recommended mode. If symlinks are not desired:

```bash
./install.sh --copy
```

Copy installs do not update automatically when the repository is pulled; run `./install.sh --copy` again after updates.
