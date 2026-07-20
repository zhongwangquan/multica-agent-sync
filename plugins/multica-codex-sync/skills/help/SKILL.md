---
name: help
description: Explain Multica Codex Sync commands, setup, Hook Trust, privacy, and safe removal. Use when the user asks how to use or configure the plugin.
---

# Explain Multica Codex Sync

Explain these supported chat commands concisely:

- `/multica 4158` or `/multica-4158`: bind this Codex task to `OPE-4158`.
- `/multica status` or `/multica-status`: show this task's tracker status.
- `/multica stop` or `/multica-stop`: stop this task's tracker.
- `/multica help` or `/multica-help`: show command and setup guidance.
- `/multica doctor` or `/multica-doctor`: run redacted local diagnostics.

State that cleanup and development commands are not public runtime methods.
For first use or a modified Hook, direct the user to **Settings → Hooks**,
review and Trust the `UserPromptSubmit` command, fully restart Codex Desktop,
and start a new task. Never tell the user to type `/hooks`.

Explain that the plugin reuses the existing Multica login, reads only the
bound Codex task after binding, and keeps private state under Codex-managed
plugin data.
