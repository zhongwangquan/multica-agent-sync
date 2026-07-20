---
name: help
description: Explain the Multica Codex Sync chat commands, setup, privacy model, and safe uninstall flow.
---

# Multica Codex Sync Help

Explain the supported chat commands concisely:

- `/multica 4158` or `/multica-4158`: bind this Codex task to `OPE-4158`.
- `/multica status` or `/multica-status`: show the tracker for this Codex task.
- `/multica stop` or `/multica-stop`: stop only the tracker for this Codex task.

For first use, tell the user to open Codex Settings, find Hooks, review the `UserPromptSubmit` command for this plugin, click Trust, enable it, and then start a new task. Do not tell them to type `/hooks` because that chat command may not exist.

Explain that the plugin reads the existing Multica login from `~/.multica`, reads only the current Codex rollout after binding, and stores its own logs and state under Codex-managed plugin data. It does not replace the `multica` executable or edit `~/.codex/hooks.json`.
