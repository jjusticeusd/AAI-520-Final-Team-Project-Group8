#!/usr/bin/env bash
set -euo pipefail

uvx pycodestyle@2.15.0 src/

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
for notebook in src/*.ipynb; do
  python3 - "$notebook" > "$tmp/$(basename "$notebook" .ipynb).py" <<'EOF'
import json
import sys

notebook = json.load(open(sys.argv[1]))
cells = ["".join(c["source"]).strip()
         for c in notebook["cells"] if c["cell_type"] == "code"]
print("\n\n\n".join(c for c in cells if c))
EOF
done
uvx pycodestyle@2.15.0 "$tmp"
echo "PEP 8 check passed."
