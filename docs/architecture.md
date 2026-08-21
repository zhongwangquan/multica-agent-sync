# Architecture

The current product is a Codex plugin with one host adapter and one Multica
transport.

```text
/multica Hook ----------------> lifecycle CLI ----> Multica local-run API
                                  |
bundled multica-sync Skill -------+
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

The recommended user entry point is the `/multica` namespace handled by the
`UserPromptSubmit` Hook. The plugin also bundles one `multica-sync` Skill as an
integration path. It invokes the lifecycle CLI directly in the agent turn and
uses `CODEX_THREAD_ID` for exact task-scoped status, stop, and binding
operations. The Hook does not intercept Skill chips or explicit Skill
invocations.

Users trigger the Skill as `/multica-sync` through the Codex `/` picker. Its
distinct name leaves `/multica` available for manual Hook commands. Any
host-generated invocation encoding is an internal integration detail, not a
public command interface.

## Extension boundary

Agent-specific event and conversation parsing belongs in an adapter. Multica
authentication, local-run calls, ownership markers, and file safety remain
host-independent. This boundary makes a future host adapter possible without
pretending that different products expose equivalent Hooks or conversation
formats.

No Claude adapter, manifest, marketplace, Hook, or test is shipped in 1.0.0.
Adding one requires a separate design, threat review, test matrix, and release.
