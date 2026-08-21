#!/bin/sh
set -eu

if [ "$#" -gt 2 ]; then
  echo "usage: $0 [marketplace-path-or-git-source] [git-ref]" >&2
  exit 2
fi

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SOURCE=${1:-$ROOT}
REF=${2:-}
TEMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/multica-agent-sync-smoke.XXXXXX")
trap 'rm -rf "$TEMP_ROOT"' EXIT HUP INT TERM

export CODEX_HOME="$TEMP_ROOT/codex"
mkdir -p "$CODEX_HOME"

if [ -d "$SOURCE" ] || [ -z "$REF" ]; then
  codex plugin marketplace add "$SOURCE"
else
  codex plugin marketplace add "$SOURCE" --ref "$REF"
fi
codex plugin add multica-codex-sync@multica-agent-sync
codex plugin list

CACHE_ROOT="$CODEX_HOME/plugins/cache/multica-agent-sync/multica-codex-sync"
MANIFEST=$(find "$CACHE_ROOT" -path '*/.codex-plugin/plugin.json' -type f -print -quit)
if [ -z "$MANIFEST" ]; then
  echo "installed plugin manifest was not found" >&2
  exit 1
fi
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["name"] == "multica-codex-sync"; print("installed", data["name"], data["version"])' "$MANIFEST"

INSTALLED_PLUGIN=$(CDPATH= cd -- "$(dirname -- "$MANIFEST")/.." && pwd)
SKILL="$INSTALLED_PLUGIN/skills/multica-sync/SKILL.md"
if [ ! -f "$SKILL" ]; then
  echo "installed multica-sync Skill was not found" >&2
  exit 1
fi

HOOK_OUTPUT=$(
  printf '%s' '{"prompt":"[$multica-codex-sync\\:multica-sync](/tmp/plugin/skills/multica-sync/SKILL.md) help","session_id":"smoke-task"}' |
    PLUGIN_ROOT="$INSTALLED_PLUGIN" \
    PLUGIN_DATA="$CODEX_HOME/plugin-data" \
    python3 "$INSTALLED_PLUGIN/scripts/prompt_submit.py"
)
if [ -n "$HOOK_OUTPUT" ]; then
  echo "Skill action was unexpectedly intercepted by the Hook" >&2
  exit 1
fi

DIRECT_OUTPUT=$(python3 "$INSTALLED_PLUGIN/scripts/multica_codex_track.py" status smoke-task)
python3 -c 'import json,sys; data=json.loads(sys.argv[1]); assert data["trackers"] == []; print("installed Skill CLI action bypassed the Hook")' "$DIRECT_OUTPUT"
