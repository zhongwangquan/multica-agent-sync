# Security Policy

## Supported versions

Security fixes are applied to the latest release line. Older immutable tags may
remain available but are not guaranteed to receive fixes.

## Reporting a vulnerability

Use GitHub private vulnerability reporting or a private Security Advisory. Do
not open a public Issue for file deletion, Hook trust, command injection,
credential exposure, unsafe process termination, release integrity, symlink,
path traversal, or private conversation data vulnerabilities.

Use synthetic data and never attach:

- Multica access tokens or configuration files;
- Codex rollout files or raw Hook payloads;
- logs with private paths or issue identifiers;
- private Multica issue content.

Maintainers aim to acknowledge a complete report within seven days and
coordinate validation, remediation, and disclosure with the reporter.

## Important boundary

Codex plugin Hooks can run outside the sandbox. Installation does not trust a
Hook automatically: users must review the command and click Trust in Codex
Settings. This project will not read, write, or bypass persisted Hook trust.

For runtime and uninstall guarantees, see
[docs/security-model.md](docs/security-model.md).
