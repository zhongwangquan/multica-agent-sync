# Multica Agent 1.2

English | [简体中文](README.zh-CN.md)

This Codex plugin binds the exact current Codex Desktop task to a Multica issue
and continuously syncs new visible messages and token usage.

## Setup

Install through the repository marketplace as described in the
[project README](../../README.md). Fully restart Codex Desktop, enable and trust
the plugin Hook in Settings, then start a new task. Hook Trust cannot be
automated.

The plugin requires Python 3, `curl`, and an authenticated Multica CLI. The
chat command namespace is `/multica`.

## Use

### Recommended: `/multica` commands

Type `/multica 4158`, `/multica status`, `/multica stop`, `/multica help`, or
`/multica doctor` at the beginning of the first line. The issue number is an
example. Hyphen forms such as `/multica-4158` are also supported.

### Optional: `/` Skill picker

Type `/`, choose **Multica Agent**, and enter `4158`, `bind 4158`, `status`,
`stop`, `help`, or `doctor`. No internal invocation syntax is needed.

| Difference | `/multica` commands | `/` Skill picker |
| --- | --- | --- |
| Positioning | Recommended | Optional |
| Input | Complete command on the first line | Choose **Multica Agent**, then enter the action |
| Hook Trust | Required | Not required |
| Result | Fixed controls complete immediately; binding continues with issue context | Runs the action in an Agent turn |

Each Codex task can track only one issue. To switch issues, stop the current
tracking first, then bind the new issue in a separate action.

## Privacy and safety

The tracker starts at the exact offset captured after binding. It does not send
earlier history, control commands, hidden reasoning, or raw tool payloads.
Codex supplies a private `$PLUGIN_DATA` directory for state and logs. Tokens do
not appear in process arguments or logs.

Internal cleanup code validates the plugin ownership marker and tracker process
identity. The public plugin exposes no cleanup/purge chat command. It does not
replace the Multica CLI, edit Hook configuration, alter Hook trust, or delete
unknown data. See the repository
[security model](../../docs/security-model.md).
