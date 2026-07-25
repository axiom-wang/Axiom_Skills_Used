#!/usr/bin/env bash
set -euo pipefail

# Resolve the helper script from the skill directory, not from the target repo.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec python3 "$SCRIPT_DIR/scripts/bcpm.py" "$@"
