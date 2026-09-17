#!/bin/bash
#
# init.sh — first-time setup for this repo on macOS.
# Run once after you clone: ./init.sh
#
# It will:
#   1. Install uv (the Python package/environment manager) if it's missing
#   2. Install the exact Python version and dependencies pinned in the repo
#
# Safe to re-run: every step is idempotent.

set -euo pipefail

# Move to the repo root (the directory this script lives in) so paths work
# no matter where you call it from.
cd "$(dirname "$0")"

echo "==> Checking for uv..."
if ! command -v uv >/dev/null 2>&1; then
  echo "    uv not found. Installing via the official installer..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # The installer drops uv in ~/.local/bin; make it available for the rest
  # of this script even before you restart your shell.
  export PATH="${HOME}/.local/bin:${PATH}"
  echo "    uv installed. NOTE: open a new terminal (or 'source ~/.zshrc')"
  echo "    later so 'uv' is on your PATH permanently."
else
  uv_version=$(uv --version)
  echo "    uv already installed: ${uv_version}"
fi

python_version=$(cat .python-version)
echo "==> Installing Python ${python_version} and project dependencies..."
# 'uv sync' reads pyproject.toml + uv.lock and builds an exact, reproducible
# .venv — same versions for every teammate. It also installs the dev group
# (ipykernel), which VS Code needs to run notebooks against this venv.
uv sync

echo ""
echo "==> Done. Next steps:"
echo "    - Open a notebook in VS Code and select the ./.venv/bin/python interpreter."
echo "    - Or, for Jupyter Lab in the browser:  uv run --with jupyter jupyter lab"

