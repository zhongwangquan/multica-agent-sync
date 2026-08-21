---
name: control
description: Bind the current Codex Desktop task to a Multica issue, inspect or stop its tracker, show help, or run redacted readiness diagnostics by directly invoking the plugin CLI.
---

# Control Multica Codex Sync

Execute the requested action directly with the plugin CLI. Do not resubmit the
action as a `/multica` command and do not wait for Hook output.

Use one action after selecting the Skill. Issue numbers must contain digits
only; `4158` below is an example:

- `<issue-number>` or `bind <issue-number>` binds the current task to the
  normalized `OPE-<issue-number>` key.
- `status` shows the current task's tracker status.
- `stop` stops tracking the current task.
- `help` shows command and setup guidance.
- `doctor` runs redacted readiness diagnostics.

Resolve the tracker entrypoint as `../../scripts/multica_codex_track.py`
relative to this `SKILL.md`. Use `python3` to run it. For every task-scoped
action, require a non-empty `CODEX_THREAD_ID`; never infer a task from rollout
recency or another tracker.

- For `<issue-number>` or `bind <issue-number>`, normalize the issue to
  `OPE-<issue-number>`, check `status "$CODEX_THREAD_ID"`, and run
  `start OPE-<issue-number> --session "$CODEX_THREAD_ID"` only when this task
  has no active tracker. Never switch an existing binding automatically.
- For `status`, run `status "$CODEX_THREAD_ID"` and report only that result.
- For `stop`, run `stop "$CODEX_THREAD_ID"`.
- For `doctor`, run `doctor` and report readiness without exposing filesystem
  paths, configuration contents, or credentials.
- For `help`, explain the five actions without running a command.

The explicit invocations are:

```text
$multica-codex-sync:control 4158
$multica-codex-sync:control status
$multica-codex-sync:control stop
$multica-codex-sync:control help
$multica-codex-sync:control doctor
```

Run the command in the current model turn and use its exit status and output as
the source of truth. Do not claim that an action succeeded before the command
does. After a successful bind, continue any issue work requested by the user;
otherwise report the binding result concisely.

Never invent an issue number, guess a Codex task, stop all trackers, or switch
an existing binding automatically. To bind a different issue, require an
explicit `stop` action first and then a separate bind action.
