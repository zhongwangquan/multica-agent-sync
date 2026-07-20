# Architecture

The current product is a Codex plugin with one host adapter and one Multica
transport.

```text
Codex UserPromptSubmit Hook
          |
          v
command parser ----> lifecycle CLI ----> Multica local-run API
                          |
                          v
                 Codex rollout adapter
                          |
                          v
               private tracker state/logs
```

## Components

- `hooks/hooks.json` registers the plugin-bundled Hook.
- `scripts/prompt_submit.py` parses the narrow `/multica` control namespace,
  serves help and redacted diagnostics, requires an explicit task id for
  tracker mutations, and injects issue context.
- `scripts/multica_codex_sync/codex_adapter.py` reads Codex Desktop rollout
  records, extracts visible user/assistant messages and usage, and watches for
  appended records.
- `scripts/multica_codex_sync/core.py` owns Multica authentication, HTTP calls,
  private file primitives, locks, and process identity verification.
- `scripts/multica_codex_sync/cli.py` owns tracker lifecycle, status, doctor,
  and conservative cleanup.

The plugin does not bundle runtime Skills. Fixed control commands (`status`,
`stop`, `help`, and `doctor`) return Hook `decision: block` output before a
model turn starts. The issue-binding command is different by design: it starts
the tracker and continues the prompt with exact issue context so Codex can do
the bound work.

## Extension boundary

Agent-specific event and conversation parsing belongs in an adapter. Multica
authentication, local-run calls, ownership markers, and file safety remain
host-independent. This boundary makes a future host adapter possible without
pretending that different products expose equivalent Hooks or conversation
formats.

No Claude adapter, manifest, marketplace, Hook, or test is shipped in 1.0.0.
Adding one requires a separate design, threat review, test matrix, and release.
