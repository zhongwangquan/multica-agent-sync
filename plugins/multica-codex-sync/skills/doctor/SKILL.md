---
name: doctor
description: Diagnose Multica Codex Sync installation, login, private data permissions, Codex sessions, and active trackers. Use when setup or commands do not work.
---

# Diagnose Multica Codex Sync

Run:

```bash
python3 "$PLUGIN_ROOT/scripts/multica_codex_track.py" doctor
```

Summarize the result without printing credentials or private paths. If Multica
is not configured, tell the user to install and sign in to the Multica CLI.
If the environment is ready but commands are ignored, direct the user to
**Settings → Hooks**, review and Trust the plugin's `UserPromptSubmit` Hook,
fully restart Codex Desktop, and start a new task.

For a deterministic redacted result in the current task, the user can submit
`/multica doctor` directly.
