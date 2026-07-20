# Multica Agent Sync

English | [简体中文](README.zh-CN.md)

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

Add the public marketplace once, then install the plugin:

```bash
codex plugin marketplace add zhongwangquan/multica-agent-sync --ref main
codex plugin add multica-codex-sync@multica-agent-sync
```

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

Refresh the Git marketplace and reinstall the newer plugin snapshot in place:

```bash
codex plugin marketplace upgrade multica-agent-sync
codex plugin add multica-codex-sync@multica-agent-sync
```

This does not delete plugin data or Multica configuration. If Codex marks the
Hook as modified, review and Trust it again, then start a new task.

## Safe uninstall

Before removal, ask Codex to run the plugin's `cleanup` skill, or run the
non-destructive command from the installed plugin root. Cleanup stops only
trackers whose saved process identity still matches and preserves history.

Then remove the plugin and, if no other plugin uses it, the marketplace:

```bash
codex plugin remove multica-codex-sync@multica-agent-sync
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
[release process](RELEASING.md). Source comments, docstrings, commits, Issues,
and pull requests use English; user documentation is maintained in English and
Chinese.

## License

[MIT](LICENSE)
