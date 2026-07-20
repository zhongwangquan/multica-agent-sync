# Contributing to Multica Agent Sync

Thank you for improving the Codex plugin. Keep pull requests focused and add
tests for behavior that affects Hooks, private data, process control, network
requests, upgrades, or uninstall safety.

## Before opening an Issue

- Search existing Issues.
- Remove tokens, rollout content, logs, usernames, home paths, and private issue
  data from reproductions.
- Use GitHub private vulnerability reporting for security-sensitive findings.
- Include the plugin version, macOS version, Codex Desktop version, and exact
  command form for Hook or command problems.

## Development setup

The runtime uses the Python standard library. Run:

```bash
./scripts/test.sh
./scripts/smoke-install.sh .
```

Tests isolate home, Codex, Multica, and plugin data directories. New behavior
must not depend on the developer's real user data.

## Pull requests

1. Create a focused branch from `develop`.
2. Add regression coverage for user-visible or high-risk behavior.
3. Keep source comments and docstrings in English.
4. Align English and Chinese documentation when behavior changes.
5. Update `CHANGELOG.md` under `Unreleased`.
6. Run the complete release gate and include the result in the PR.
7. Obtain review before merging behavior-changing work.

Normal changes merge into `develop`. A release pull request promotes the tested
state from `develop` to `main`. Urgent fixes may branch from `main`, but must be
merged back into `develop` after release. See
[release channels](docs/release-channels.md).

## Versioning

The project follows Semantic Versioning:

- `PATCH`: compatible fixes and documentation corrections.
- `MINOR`: backward-compatible features.
- `MAJOR`: incompatible commands, state, API, privacy, or install boundaries.

Release PRs update `VERSION`, the plugin manifest, and `CHANGELOG.md`. Follow
[RELEASING.md](RELEASING.md); never move or replace a published tag.

## Safety invariants

- Never guess the current Codex task when the Hook task id is missing.
- Never log raw Hook payloads, credentials, hidden reasoning, or full rollout
  content.
- Never stop a PID without validating the plugin script, mode, state path, and
  process start identity.
- Never follow symlinked private data directories.
- Never replace the Multica CLI or write Hook configuration or Hook trust.
- Never delete Multica configuration, Codex tasks, enclosing directories, or
  unknown files.

## Scope

The shipped product currently supports Codex only. Host-specific code belongs
in an adapter. A new host requires its own design, threat review, tests, and
release; do not add untested compatibility claims.
