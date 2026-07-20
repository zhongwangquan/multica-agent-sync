# Security model

## Trusted inputs

- Codex supplies `PLUGIN_ROOT`, `PLUGIN_DATA`, the trusted Hook definition, and
  the exact current task id.
- The user explicitly Trusts the Hook in Codex Settings.
- Multica authentication is read from the existing user configuration.

## Untrusted inputs

- Chat text, Hook payload shape, Multica API responses, issue ids, run ids,
  rollout contents, saved state files, PIDs, and all files already present in
  the plugin data directory are treated as untrusted.

## Data sent to Multica

After binding, the tracker sends visible user and assistant message text plus
token usage associated with the current Codex task. It does not upload history
before the binding offset, control commands, hidden reasoning, or raw tool
payloads.

## Local protections

- State directories use mode `0700`; files and logs use `0600`.
- API tokens are passed through a private temporary curl configuration, not
  command-line arguments, and the temporary file is removed.
- External run ids are hashed before becoming filenames.
- Session locks are keyed by a hash of the task id.
- Symlinked private state directories are rejected.
- Tracker termination requires the saved PID, command, mode, state path, and
  process start identity to match.
- Missing task ids fail closed; the plugin never guesses the latest task.

## Safe removal

Normal cleanup stops matching trackers and preserves all state and logs. An
explicit purge validates a plugin-specific ownership marker and removes only
known state, log, lock, and temporary filename patterns. Symlinks and unknown
files are preserved and reported. The plugin never removes Multica
configuration, Codex tasks, shared Hook configuration, or an enclosing user
directory.

## Remaining trust

A trusted Hook runs outside the Codex sandbox. Users should inspect the command
and install only from a Git ref they trust. Network confidentiality and server
authorization depend on the user's configured Multica server. Report suspected
vulnerabilities through GitHub private vulnerability reporting.
