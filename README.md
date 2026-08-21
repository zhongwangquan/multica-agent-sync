# Multica Agent Sync

English | [简体中文](README.zh-CN.md)

[![CI](https://github.com/zhongwangquan/multica-agent-sync/actions/workflows/ci.yml/badge.svg)](https://github.com/zhongwangquan/multica-agent-sync/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/zhongwangquan/multica-agent-sync)](https://github.com/zhongwangquan/multica-agent-sync/releases/latest)
[![GitHub stars](https://img.shields.io/github/stars/zhongwangquan/multica-agent-sync)](https://github.com/zhongwangquan/multica-agent-sync)
[![Open issues](https://img.shields.io/github/issues/zhongwangquan/multica-agent-sync)](https://github.com/zhongwangquan/multica-agent-sync/issues)

Multica Agent Sync is an open-source Codex plugin that binds one Codex Desktop
task to one Multica issue. After binding, it continuously sends new visible
conversation messages and token usage to the issue's local run.

The repository currently ships **Codex support only**. Its runtime separates the
Codex adapter from the Multica transport so other agent hosts can be considered
later, but no Claude integration is included or claimed in this release.

## Why a plugin

- Codex installs, updates, and removes the package through its plugin manager.
- The Hook is bundled with the plugin; no installer edits user Hook files.
- The plugin never replaces or wraps the `multica` executable.
- Runtime state is private and isolated in Codex-provided `$PLUGIN_DATA`.
- Cleanup verifies ownership, process identity, and known filenames before it
  removes anything. Unknown files are preserved.
- Source, versions, Issues, and pull requests are public and reviewable.

## Requirements

- macOS and a Codex Desktop version with plugin support.
- Python 3 and `curl`.
- An authenticated Multica CLI installation. The plugin never prints an access
  token.

## Install

For a normal install, add the public marketplace without selecting a version,
then install the plugin. Codex uses the repository's default `main` branch, so
the first installation gets its latest stable snapshot:

```bash
# Step 1 of 2: register the GitHub marketplace at its latest stable version.
codex plugin marketplace add zhongwangquan/multica-agent-sync

# Step 2 of 2: install and enable the plugin from that marketplace.
codex plugin add multica-codex-sync@multica-agent-sync
```

To pin or roll back to an exact version, optionally select a published tag when
registering the marketplace:

```bash
# Optional step 1 of 2: register an exact version instead of latest stable.
codex plugin marketplace add zhongwangquan/multica-agent-sync --ref v1.2.0

# Step 2 of 2: install and enable that exact plugin version.
codex plugin add multica-codex-sync@multica-agent-sync
```

The Git tag is the reproducible package boundary; Codex does not require a
separately built ZIP or binary. GitHub automatically provides source archives
for every release.

Then:

1. Fully quit and reopen Codex Desktop.
2. Open **Settings → Hooks**, review the plugin's `UserPromptSubmit` command,
   click **Trust**, and enable it. Codex intentionally requires this manual
   security decision.
3. Start a new Codex task and send a `/multica ...` command.

Do not type `/hooks` in the chat box; Hook trust is managed in Settings.

## Use

Place one command at the beginning of the first line. You do not need to select
or run a Skill first:

```text
/multica 4158
/multica status
/multica stop
/multica help
/multica doctor
```

`4158` is an example issue number. Hyphen forms such as `/multica-4158` and
`/multica-status` are also supported.

As an optional alternative, type `/`, choose **Multica Agent**, and enter one
action such as `4158`, `status`, `stop`, `help`, or `doctor`. No internal
invocation syntax is needed.

Only the `/multica` namespace is recognized. The plugin deliberately does not
claim generic issue or stop command names that may collide with Codex features,
templates, or other plugins.

Authentication is read from `MULTICA_HOME` or `~/.multica`. Credentials are
never forwarded to an untrusted redirect origin.

Each Codex task can track only one Multica issue. To switch issues, first send
`/multica stop`, then send the new issue number in a separate command. The
plugin never switches an existing task automatically.

## Upgrade

Choose between the latest `main` snapshot and an exact release tag:

| Ref | Purpose | Update behavior |
| --- | --- | --- |
| omitted (default `main`) | Latest stable channel | Changes only after marketplace upgrade |
| `v1.2.0` | Optional exact release | Remains pinned to that version |

The default installation above follows the stable channel. In Codex Desktop,
open **Settings → Plugins → Marketplaces**, find **Multica Agent Sync**,
and click **Upgrade**. After the refresh, confirm that the installed plugin
shows the new version. If it still shows the previous snapshot, open the plugin
entry and install it again. The **Upgrade** button remains visible when the
marketplace is current because it is a manual refresh action, not an
update-available indicator.

The equivalent command-line flow is:

```bash
# Step 1 of 2: refresh the configured Git marketplace snapshot.
codex plugin marketplace upgrade multica-agent-sync

# Step 2 of 2: reinstall the plugin from the refreshed snapshot.
codex plugin add multica-codex-sync@multica-agent-sync
```

To install or roll back to an exact version, configure the marketplace with
`--ref vX.Y.Z`. See [release channels](docs/release-channels.md) for switching
commands and the branch policy. A marketplace snapshot is not continuously
synchronized with GitHub, so installed code changes only after these commands.

This does not delete plugin data or Multica configuration. Fully quit and
reopen Codex Desktop after every plugin upgrade so running tasks reload the new
versioned plugin root. Starting with `1.1.3`, a stale Hook safely exits if the
old cache has already been removed, so it cannot block unrelated messages.
If Codex marks the Hook as modified, review and Trust it again, then start a new
task.

## Safe uninstall

In each task that is actively tracking, run `/multica stop`. This stops only the
tracker for that exact Codex task and preserves its history. A remaining
verified watcher also stops and finalizes its own run when its plugin snapshot
is removed.

Then remove the plugin and, if no other plugin uses it, the marketplace:

```bash
# Required: uninstall the plugin from Codex.
codex plugin remove multica-codex-sync@multica-agent-sync

# Optional: also forget this marketplace if you will not use it again.
codex plugin marketplace remove multica-agent-sync
```

Normal removal does not delete plugin runtime history, Multica login data,
Codex tasks, or unrelated files. The public plugin exposes no cleanup or purge
chat command and no cleanup Skill. See
[the security model](docs/security-model.md) for exact boundaries.

## Develop

```bash
./scripts/test.sh
./scripts/smoke-install.sh .
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [architecture](docs/architecture.md), and
[release process](RELEASING.md). To smoke-test a public branch or tag, run
`./scripts/smoke-install.sh zhongwangquan/multica-agent-sync <ref>`. Source
comments, docstrings, commits, Issues, and pull requests use English; user
documentation is maintained in English and Chinese.

## Project activity

The plugin contains no analytics or telemetry. Public adoption and maintenance
signals come only from GitHub. These links use GitHub's native pages so the
README does not depend on a third-party star-history renderer:

- [Repository overview](https://github.com/zhongwangquan/multica-agent-sync)
- [Contributors](https://github.com/zhongwangquan/multica-agent-sync/graphs/contributors)
- [Commit activity](https://github.com/zhongwangquan/multica-agent-sync/graphs/commit-activity)
- [Pull request and issue activity](https://github.com/zhongwangquan/multica-agent-sync/pulse)
- [Releases](https://github.com/zhongwangquan/multica-agent-sync/releases)

## License

[MIT](LICENSE)
