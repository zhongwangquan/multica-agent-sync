# Multica Agent Sync

English | [简体中文](README.zh-CN.md)

[![CI](https://github.com/zhongwangquan/multica-agent-sync/actions/workflows/ci.yml/badge.svg)](https://github.com/zhongwangquan/multica-agent-sync/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/zhongwangquan/multica-agent-sync)](https://github.com/zhongwangquan/multica-agent-sync/releases/latest)
[![GitHub stars](https://img.shields.io/github/stars/zhongwangquan/multica-agent-sync)](https://github.com/zhongwangquan/multica-agent-sync/stargazers)
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
- Multica CLI installed and authenticated. The plugin reuses the existing
  Multica configuration and never prints its access token.

## Install

For a reproducible install, add the public marketplace at an exact release tag,
then install the plugin:

```bash
# Step 1 of 2: register the GitHub marketplace at this exact release tag.
codex plugin marketplace add zhongwangquan/multica-agent-sync --ref v1.0.0

# Step 2 of 2: install and enable the plugin from that marketplace.
codex plugin add multica-codex-sync@multica-agent-sync
```

The Git tag is the package boundary; Codex does not require a separately built
ZIP or binary. GitHub automatically provides source archives for every release.

Then:

1. Fully quit and reopen Codex Desktop.
2. Open **Settings → Hooks**.
3. Review the plugin's `UserPromptSubmit` command, click **Trust**, and enable
   the Hook. Codex intentionally requires this manual security decision.
4. Start a new Codex task.

Do not type `/hooks` in the chat box; Hook trust is managed in Settings.

## Use

Place one of these commands at the beginning of the first line:

```text
/multica 4158
/multica status
/multica stop
```

Hyphen forms are also supported:

```text
/multica-4158
/multica-status
/multica-stop
```

Only the `/multica` namespace is recognized. The plugin deliberately does not
claim generic issue or stop command names that may collide with Codex features,
templates, or other plugins.

The plugin also contributes `help`, `doctor`, `status`, and `cleanup` skills.

## Upgrade

Choose a release channel when adding the marketplace:

| Ref | Purpose | Update behavior |
| --- | --- | --- |
| `v1.0.0` | Exact stable release | Remains pinned to that version |
| `main` | Latest stable channel | Changes only after marketplace upgrade |
| `develop` | Test channel | May contain unreleased changes |

For convenient stable upgrades, add the marketplace with `--ref main`. Refresh
the marketplace and reinstall the new snapshot in place with:

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

This does not delete plugin data or Multica configuration. If Codex marks the
Hook as modified, review and Trust it again, then start a new task.

## Safe uninstall

Before removal, ask Codex to run the plugin's `cleanup` skill, or run the
non-destructive command from the installed plugin root. Cleanup stops only
trackers whose saved process identity still matches and preserves history.

Then remove the plugin and, if no other plugin uses it, the marketplace:

```bash
# Required: uninstall the plugin from Codex.
codex plugin remove multica-codex-sync@multica-agent-sync

# Optional: also forget this marketplace if you will not use it again.
codex plugin marketplace remove multica-agent-sync
```

Normal cleanup and removal never delete Multica login data, Codex tasks, or
unrelated files. A complete purge is available only through the `cleanup` skill
after the user explicitly requests deletion of plugin-owned history and logs.
See [the security model](docs/security-model.md) for exact boundaries.

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

## Project trends

The plugin contains no analytics or telemetry. Public adoption and maintenance
trends come only from GitHub:

- [Stars over time](https://www.star-history.com/#zhongwangquan/multica-agent-sync&Date)
- [Contributors](https://github.com/zhongwangquan/multica-agent-sync/graphs/contributors)
- [Pull request and issue activity](https://github.com/zhongwangquan/multica-agent-sync/pulse)
- [Releases](https://github.com/zhongwangquan/multica-agent-sync/releases)

[![Star History Chart](https://api.star-history.com/svg?repos=zhongwangquan/multica-agent-sync&type=Date)](https://www.star-history.com/#zhongwangquan/multica-agent-sync&Date)

## License

[MIT](LICENSE)
