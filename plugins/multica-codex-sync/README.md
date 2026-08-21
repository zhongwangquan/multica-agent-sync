# Multica Codex Sync 1.2

English | [简体中文](README.zh-CN.md)

This Codex plugin binds the exact current Codex Desktop task to a Multica issue
and continuously syncs new visible messages and token usage.

## Setup

Install through the repository marketplace as described in the
[project README](../../README.md). Fully restart Codex Desktop and start a new
task. Hook Trust is needed only for the legacy `/multica ...` commands; Skill
actions invoke the tracker CLI directly. Hook Trust cannot and should not be
automated.

The plugin requires Python 3, `curl`, and an authenticated Multica CLI by
default. An authenticated Wujie CLI is accepted as a compatibility fallback.
Configuration discovery checks Multica first, then Wujie; the chat command
namespace remains `/multica`.

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

Choose **Multica Codex Sync** from the `/` Skill picker and submit `4158`,
`bind 4158`, `status`, `stop`, `help`, or `doctor`. Explicit invocations are:

```text
$multica-codex-sync:control 4158
$multica-codex-sync:control bind 4158
$multica-codex-sync:control status
$multica-codex-sync:control stop
$multica-codex-sync:control help
$multica-codex-sync:control doctor
```

| Behavior | Skill action | Legacy `/multica` command |
| --- | --- | --- |
| Execution | Agent calls the tracker CLI directly | Hook intercepts the first prompt line |
| Hook Trust | Not required | Required |
| Model turn | Runs in the current Agent turn | Informational actions finish before a model turn; binding continues with issue context |
| Positioning | Recommended interface | Compatibility interface |

Skill actions call the installed tracker CLI directly and use
`CODEX_THREAD_ID` to target the exact current task. They bypass the Hook. The
Hook remains only as a compatibility path for `/multica ...` commands.

Each Codex task can track only one issue. If a task is already tracking a
different issue, the plugin does not switch it automatically. Stop and bind in
two separate actions through the same interface.

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
