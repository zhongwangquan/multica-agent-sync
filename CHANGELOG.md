# Changelog

All notable changes are documented here. This project follows Semantic
Versioning.

## Unreleased

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
