# Repository instructions

- The shipped product supports Codex only. Do not add or claim Claude support
  unless a separate, explicitly approved scope introduces and tests it.
- Keep agent-specific code in an adapter module; do not mix Codex rollout
  parsing with Multica API transport.
- Use English for source comments, docstrings, filenames, commit messages,
  Issues, and pull requests.
- Keep `README.md` and `README.zh-CN.md` aligned for user-visible behavior.
- Run `./scripts/test.sh` before completing changes.
- Never log credentials, raw Hook payloads, hidden reasoning, full rollout
  content, or private issue data.
- Never mutate Hook trust state, replace the Multica CLI, guess a Codex task,
  kill a PID without identity verification, follow symlinked private data
  directories, or delete unknown user files.
