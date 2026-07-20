---
name: cleanup
description: Safely stop Multica Codex Sync trackers and prepare the plugin for uninstall without deleting unrelated user data.
---

# Safely Clean Up Multica Codex Sync

First run the non-destructive cleanup:

```bash
python3 "$PLUGIN_ROOT/scripts/multica_codex_track.py" cleanup
```

This stops only processes whose command and saved process identity match plugin-owned tracker state. It preserves tracker history, logs, Multica configuration, Codex tasks, and all unrelated files.

Only when the user explicitly asks for a complete purge, explain that plugin-owned history and logs will be deleted, then run:

```bash
python3 "$PLUGIN_ROOT/scripts/multica_codex_track.py" cleanup --purge
```

The purge may remove only known plugin-created state, log, lock, and temporary files after validating the ownership marker. It must preserve unknown files and report the retained data directory. After cleanup, the user can remove the plugin with the normal Codex plugin manager.
