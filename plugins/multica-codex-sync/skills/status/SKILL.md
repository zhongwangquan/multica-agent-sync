---
name: status
description: Inspect Multica Codex Sync tracker status, issue bindings, watcher health, runs, and token usage. Use when the user asks what is currently being tracked.
---

# Inspect Multica Codex Sync Status

Run:

```bash
python3 "$PLUGIN_ROOT/scripts/multica_codex_track.py" status
```

Summarize active trackers without exposing credentials, conversation content,
or full local rollout paths. Explain the issue, run status, watcher health, and
token totals that are present.

For only the exact current Codex task, recommend `/multica status`; the trusted
Hook receives the current task id and does not need to guess it.
