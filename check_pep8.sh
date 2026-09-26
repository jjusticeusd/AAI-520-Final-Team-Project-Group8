#!/usr/bin/env bash
set -euo pipefail

uvx pycodestyle@2.15.0 src/
echo "PEP 8 check passed."
