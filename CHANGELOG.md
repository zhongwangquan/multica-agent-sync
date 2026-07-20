# Changelog

All notable changes are documented here. This project follows Semantic
Versioning.

## Unreleased

## 1.1.4 - 2026-07-20

### Changed

- Remove the bundled `help`, `doctor`, `status`, and `stop` runtime Skills so
  deterministic controls no longer enter a model-driven Skill workflow.
- Keep `/multica help`, `/multica doctor`, `/multica status`, and
  `/multica stop` as direct `UserPromptSubmit` Hook commands that block the
  control prompt before it reaches the model. Issue binding still continues
  into the model with the bound issue context by design.

## 1.1.3 - 2026-07-20

### Fixed

- Let the plugin Hook exit successfully when an upgrade has already removed
  its old versioned cache directory but Codex has not restarted yet. This
  prevents a stale Hook from blocking messages in every open task.

### Changed

- Clarify that the marketplace **Upgrade** button is a persistent refresh
  action, not an update-available indicator.

## 1.1.2 - 2026-07-20

### Changed

- Publish a maintenance release for validating Codex Desktop's manual
  marketplace Upgrade flow. Runtime behavior and Hook commands are unchanged.

## 1.1.1 - 2026-07-20

### Fixed

- Restore `help`, `doctor`, `status`, and `stop` as explicit Skill picker
  entries while keeping their direct `/multica` commands.
- Keep cleanup and plugin-development entries out of the public runtime Skill
  list.

## 1.1.0 - 2026-07-20

### Added

- Add direct `/multica help` and `/multica doctor` commands, including their
  hyphen forms.

### Changed

- Remove all runtime Skills from the public plugin so fixed operations no
  longer occupy the Codex Skill list.
- Keep cleanup as an internal lifecycle safeguard rather than a public chat or
  Skill entry.

## 1.0.1 - 2026-07-20

### Fixed

- Resolve Codex-managed `$PLUGIN_DATA` when operational Skills run outside the
  Hook environment, so `status`, `doctor`, and `cleanup` see the real trackers.

### Changed

- Make the default installation follow the latest stable `main` snapshot;
  exact release tags remain available as an optional pin or rollback target.

## 1.0.0 - 2026-07-20

### Added

- Public Codex marketplace and Plugin-only installation flow.
- `/multica` space and hyphen command forms.
- Plugin-bundled `UserPromptSubmit` Hook and four operational skills.
- Private tracker state, safe process identity checks, and ownership-aware
  cleanup.
- English and Chinese documentation, CI, release validation, and isolated
  installation smoke tests.

### Security

- Hash externally supplied run identifiers before using them in filenames.
- Refuse symlinked private state directories and preserve unknown files.
- Keep Multica tokens out of process arguments and delete temporary curl
  configuration after each request.
- Fail closed when the exact Codex task id is unavailable.
