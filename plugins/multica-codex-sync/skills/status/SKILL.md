---
name: status
description: Inspect active Multica Codex Sync trackers and explain their issue, run, watcher, and token usage status.
---

# Multica Codex Sync Status

Run:

```bash
python3 "$PLUGIN_ROOT/scripts/multica_codex_track.py" status
```

Summarize active trackers without exposing raw message content, authentication tokens, or full local rollout paths. For the status of only the current Codex task, recommend the chat command `/multica status`, because the trusted hook has the exact current task id.
