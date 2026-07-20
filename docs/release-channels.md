# Release channels

The repository exposes three explicit installation choices. Codex snapshots a
Git marketplace when it is added or upgraded; an installed plugin does not
continuously read the GitHub working tree.

| Ref | Stability | Recommended use |
| --- | --- | --- |
| `vX.Y.Z` | Immutable | Production, audit, rollback, and reproducible installs |
| `main` | Stable | Users who want the latest released version through upgrades |
| `develop` | Unreleased | Contributors and opt-in testers |

## Install an exact tag

```bash
codex plugin marketplace add zhongwangquan/multica-agent-sync --ref v1.0.0
codex plugin add multica-codex-sync@multica-agent-sync
```

Replace `v1.0.0` with any published tag. A pinned marketplace remains on that
tag when upgraded, which is intentional.

## Follow the stable channel

```bash
codex plugin marketplace add zhongwangquan/multica-agent-sync --ref main
codex plugin add multica-codex-sync@multica-agent-sync
```

When a new stable release is published:

```bash
codex plugin marketplace upgrade multica-agent-sync
codex plugin add multica-codex-sync@multica-agent-sync
```

The second command replaces the installed plugin snapshot. It does not purge
plugin-owned runtime history or Multica configuration.

## Test an unreleased version

```bash
codex plugin marketplace add zhongwangquan/multica-agent-sync --ref develop
codex plugin add multica-codex-sync@multica-agent-sync
```

Do not use `develop` when reproducibility is required. The branch may advance
without a version tag.

## Switch refs

Codex stores one configured source for the `multica-agent-sync` marketplace.
To switch that source to another branch or tag, remove the installed snapshot
and marketplace registration, then add the desired ref:

```bash
codex plugin remove multica-codex-sync@multica-agent-sync
codex plugin marketplace remove multica-agent-sync
codex plugin marketplace add zhongwangquan/multica-agent-sync --ref v1.0.0
codex plugin add multica-codex-sync@multica-agent-sync
```

This uses Codex's plugin manager; do not manually delete plugin directories.
Run the plugin cleanup skill first only when an active tracker must be stopped.
Explicit purge remains a separate, user-confirmed operation.

## Branch policy

- Feature and fix pull requests normally target `develop`.
- CI must pass before merging.
- Release pull requests promote `develop` to `main`.
- Every public release tags the exact `main` commit as `vX.Y.Z`.
- Urgent fixes start from `main` and are merged back to `develop`.

The plugin source itself is the Codex package. No extra ZIP, wheel, or binary is
required. GitHub Release source archives are useful for inspection and offline
retention but are not a different install format.
