---
name: doctor
description: Diagnose Multica Codex Sync installation, Multica login, private data permissions, Codex sessions, and active trackers.
---

# Diagnose Multica Codex Sync

Run this plugin's diagnostic command:

```bash
python3 "$PLUGIN_ROOT/scripts/multica_codex_track.py" doctor
```

Summarize the result in plain language. Never print, read aloud, or copy a Multica token. If `multica_configured` is false, tell the user to install or sign in to the Multica CLI first. If the plugin looks ready but commands are ignored, tell the user to open Codex Settings → Hooks, Trust and enable the plugin's `UserPromptSubmit` hook, fully restart Codex Desktop, and try from a new task.
