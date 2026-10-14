#!/usr/bin/env bash
# Thin wrapper: install Claude skill via install-claude-skill.py
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$ROOT/install-claude-skill.py" "$@"
