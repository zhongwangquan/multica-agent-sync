# Multica Codex Sync 1.1

English | [简体中文](README.zh-CN.md)

This Codex plugin binds the exact current Codex Desktop task to a Multica issue
and continuously syncs new visible messages and token usage.

## Setup

Install through the repository marketplace as described in the
[project README](../../README.md). Fully restart Codex Desktop, open
**Settings → Hooks**, review the `UserPromptSubmit` command, click **Trust**,
enable it, and start a new task. Hook trust cannot and should not be automated.

The plugin requires Python 3, `curl`, and an authenticated Multica CLI.

## Chat commands

Commands must begin the first line:

```text
/multica 4158
/multica status
/multica stop
/multica help
/multica doctor
```

Equivalent hyphen forms are `/multica-4158`, `/multica-status`,
`/multica-stop`, `/multica-help`, and `/multica-doctor`. No other command
namespace is recognized.

## Privacy and safety

The tracker starts at the exact offset captured after binding. It does not send
earlier history, control commands, hidden reasoning, or raw tool payloads.
Codex supplies a private `$PLUGIN_DATA` directory for state and logs. Tokens do
not appear in process arguments or logs.

Internal cleanup code validates the plugin ownership marker and tracker process
identity. The public plugin exposes no cleanup/purge chat command and no runtime
Skills. It does not replace the Multica CLI, edit Hook configuration, alter Hook
trust, or delete unknown data. See the repository
[security model](../../docs/security-model.md).
