#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

python3 scripts/validate_release.py
python3 -m compileall -q plugins/multica-codex-sync/scripts
python3 -m unittest discover -s plugins/multica-codex-sync/tests -v

if python3 -m ruff --version >/dev/null 2>&1; then
  python3 -m ruff check plugins/multica-codex-sync/scripts plugins/multica-codex-sync/tests scripts
else
  echo "ruff is not installed; functional and release tests completed"
fi
