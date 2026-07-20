---
name: stop
description: Safely stop an active Multica Codex Sync tracker without deleting history. Use when the user asks to stop or disconnect Multica tracking.
---

# Stop Multica Codex Sync

For the exact current Codex task, instruct the user to submit:

```text
/multica stop
```

The trusted Hook supplies the exact task id. If the user explicitly asks this
Skill to stop the only active tracker, run:

```bash
python3 "$PLUGIN_ROOT/scripts/multica_codex_track.py" stop
```

The CLI refuses to choose when multiple trackers are active. In that case, do
not use `--all` or guess a target; tell the user to submit `/multica stop` in
the intended task. Stopping preserves plugin history and unrelated user data.
