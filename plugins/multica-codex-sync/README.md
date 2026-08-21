# Multica Codex Sync 1.2

English | [简体中文](README.zh-CN.md)

This Codex plugin binds the exact current Codex Desktop task to a Multica issue
and continuously syncs new visible messages and token usage.

## Setup

Install through the repository marketplace as described in the
[project README](../../README.md). Fully restart Codex Desktop and start a new
task. Using **Multica Codex Sync** from the `/` Skill picker needs no additional
setup. Hook Trust is needed only for the legacy `/multica ...` commands and
cannot be automated.

The plugin requires Python 3, `curl`, and an authenticated Multica CLI by
default. An authenticated Wujie CLI is accepted as a compatibility fallback.
Configuration discovery checks Multica first, then Wujie; the chat command
namespace remains `/multica`.

## Use

Type `/` in the Codex chat box, choose **Multica Codex Sync**, then enter one
action: `4158`, `bind 4158`, `status`, `stop`, `help`, or `doctor`. The issue
number is an example. This recommended method does not require Hook Trust.

For compatibility, you can enable the plugin Hook and type `/multica 4158`,
`/multica status`, `/multica stop`, `/multica help`, or `/multica doctor` at
the beginning of the first line. Hyphen forms such as `/multica-4158` are also
supported.

Each Codex task can track only one issue. To switch issues, stop the current
tracking first, then bind the new issue in a separate action.

## Privacy and safety

The tracker starts at the exact offset captured after binding. It does not send
earlier history, control commands, hidden reasoning, or raw tool payloads.
Codex supplies a private `$PLUGIN_DATA` directory for state and logs. Tokens do
not appear in process arguments or logs.

Internal cleanup code validates the plugin ownership marker and tracker process
identity. The public plugin exposes no cleanup/purge chat command. It does not
replace the Multica or Wujie CLI, edit Hook configuration, alter Hook trust, or
delete unknown data. See the repository
[security model](../../docs/security-model.md).
