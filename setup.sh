#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if command -v python3.12 >/dev/null 2>&1; then
    exec python3.12 scripts/manage.py setup
elif command -v python3 >/dev/null 2>&1; then
    exec python3 scripts/manage.py setup
else
    echo 'Install 64-bit Python 3.12 (including pip and venv), then rerun setup.' >&2
    exit 1
fi
