from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

from .codex_adapter import (
    find_session,
    latest_model,
    latest_usage_total_before_offset,
    watcher,
)
from .core import (
    CODEX_HOME,
    CONFIG_CANDIDATES,
    LOCKS_DIR,
    LOGS_DIR,
    PLUGIN_DATA,
    PLUGIN_DATA_MARKER,
    PLUGIN_DATA_MARKER_CONTENT,
    PLUGIN_ROOT,
    STATES_DIR,
    TRACK_HOME,
    Api,
    ApiError,
    active_states,
    atomic_json,
    create_local_run,
    ensure_plugin_data,
    load_states,
    pid_alive,
    process_identity,
    read_json,
    reset_current_run_usage,
    secure_mkdir,
    select_states,
    session_lock,
    state_log_path,
    state_path_for_run,
    tracker_process_matches,
)


TRACKER_ENTRYPOINT = Path(__file__).resolve().parents[1] / "multica_codex_track.py"
PLUGIN_MANIFEST_PATH = TRACKER_ENTRYPOINT.parent.parent / ".codex-plugin" / "plugin.json"


def plugin_version() -> str:
    try:
        value = json.loads(PLUGIN_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "unknown"
    return str(value.get("version") or "unknown")


def version_command(_args) -> int:
    print(plugin_version())
    return 0


def start_tracking(issue_key: str, path: Path, meta: dict) -> dict:
    session_id = str(meta.get("id") or "")
    if not session_id:
        raise RuntimeError("Cannot start tracking without an explicit Codex Desktop task id")
    with session_lock(session_id):
        return _start_tracking_locked(issue_key, path, meta)


def _start_tracking_locked(issue_key: str, path: Path, meta: dict) -> dict:
    for existing_path, existing in active_states():
        if existing.get("session_id") != meta.get("id"):
            continue
        if tracker_process_matches(
            existing.get("pid"),
            mode="watch",
            expected_identity=existing.get("process_identity"),
            state_path=existing_path,
        ):
            raise RuntimeError(
                f"Task {meta['id']} is already tracking {existing.get('issue')} "
                f"(run {existing.get('run_id')})"
            )
        existing["status"] = "stale"
        existing["stale_at"] = time.time()
        existing["stale_reason"] = "watcher-process-missing-or-identity-mismatch"
        atomic_json(existing_path, existing)

    api = Api()
    issue = api.request("GET", f"/api/issues/{urllib.parse.quote(issue_key)}")
    issue_id = issue["id"]
    run_id = create_local_run(api, issue_id, meta)
    state = {
        "status": "running",
        "issue": issue_key,
        "issue_id": issue_id,
        "run_id": run_id,
        "last_upload_run_id": run_id,
        "session_id": meta["id"],
        "session_file": str(path),
        "work_dir": str(meta.get("cwd") or Path.cwd()),
        "offset": path.stat().st_size,
        "model": latest_model(path),
        "started_at": time.time(),
        "last_server_run_status": "running",
        "short_lived_runs": False,
        "run_mode": "session",
        "server_run_count": 1,
        "upload_batch_count": 0,
        "plugin_root": str(PLUGIN_ROOT),
        "plugin_version": plugin_version(),
    }
    reset_current_run_usage(state, run_id)
    state["usage_totals"] = latest_usage_total_before_offset(path, int(state["offset"]))
    state["usage_baseline_offset"] = state["offset"]
    state["usage_baseline_at"] = time.time()
    state_path = state_path_for_run(run_id)
    atomic_json(state_path, state)

    secure_mkdir(LOGS_DIR)
    log_path = state_log_path(state)
    descriptor = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(descriptor, "a", encoding="utf-8") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                str(TRACKER_ENTRYPOINT),
                "watch",
                "--state",
                str(state_path),
            ],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    state["pid"] = process.pid
    state["process_identity"] = process_identity(process.pid)
    atomic_json(state_path, state)
    return state


def start(args) -> int:
    path, meta = find_session(args.session)
    state = start_tracking(args.issue, path, meta)
    print(f"Tracking {state['issue']}")
    print(f"run: {state['run_id']}")
    print(f"task: {state['session_id']}")
    print("history before this point will not be uploaded")
    return 0


def stop_one(state_path: Path, state: dict) -> str | None:
    state["status"] = "stopping"
    atomic_json(state_path, state)
    pid = state.get("pid")
    if tracker_process_matches(
        pid,
        mode="watch",
        expected_identity=state.get("process_identity"),
        state_path=state_path,
    ):
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    elif isinstance(pid, int) and pid_alive(pid):
        state["local_stop_warning"] = f"refused to stop unrelated process using stale pid {pid}"

    server_error = None
    try:
        api = Api()
        api.request(
            "PATCH",
            f"/api/local-runs/{state['run_id']}",
            {"status": "completed", "exit_code": 0, "error": ""},
        )
    except ApiError as error:
        if error.status in {404, 410}:
            state["last_server_run_status"] = "missing"
            state.pop("server_stop_error", None)
        else:
            server_error = str(error)
            state["server_stop_error"] = server_error
    except Exception as error:
        server_error = str(error)
        state["server_stop_error"] = server_error

    state["status"] = "stopped"
    state["stopped_at"] = time.time()
    atomic_json(state_path, state)
    print(f"Stopped tracking {state.get('issue')} (run {state.get('run_id')})")
    if server_error:
        print(
            f"Warning: local tracker stopped but server completion failed: {server_error}",
            file=sys.stderr,
        )
    return server_error


def stop(args) -> int:
    matches = active_states() if args.all else select_states(args.target)
    if not matches:
        print("No matching Codex Desktop tracker is running")
        return 0
    if not args.all and not args.target and len(matches) > 1:
        issues = ", ".join(
            f"{state.get('issue')}:{state.get('run_id')}" for _, state in matches
        )
        raise RuntimeError(
            f"Multiple trackers are running; specify ISSUE/RUN/TASK or use --all: {issues}"
        )
    if not args.all and args.target and len(matches) > 1:
        raise RuntimeError(f"Target {args.target} matches multiple trackers; use a run or task id")
    for state_path, state in matches:
        stop_one(state_path, state)
    return 0


def status(args) -> int:
    matches = select_states(args.target) if args.target else (
        load_states() if args.all else active_states()
    )
    if not matches and args.target:
        print("No Codex Desktop trackers were found")
        return 0
    states = []
    for state_path, state in matches:
        value = dict(state)
        value["watcher_alive"] = tracker_process_matches(
            value.get("pid"),
            mode="watch",
            expected_identity=value.get("process_identity"),
            state_path=state_path,
        )
        states.append(value)
    print(
        json.dumps(
            {"plugin_version": plugin_version(), "trackers": states},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def doctor(_args) -> int:
    """Report local readiness without printing Multica credentials."""
    ensure_plugin_data()
    config_found = False
    config_path = None
    for candidate in CONFIG_CANDIDATES:
        value = read_json(candidate)
        if isinstance(value, dict) and value.get("token") and value.get("server_url"):
            config_found = True
            config_path = str(candidate)
            break
    payload = {
        "plugin_version": plugin_version(),
        "plugin_root": str(PLUGIN_ROOT),
        "plugin_data": str(PLUGIN_DATA),
        "plugin_data_private": (TRACK_HOME.stat().st_mode & 0o077) == 0,
        "multica_configured": config_found,
        "multica_config_path": config_path,
        "codex_sessions_found": (CODEX_HOME / "sessions").is_dir(),
        "active_trackers": len(active_states()),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if config_found else 1


def _unlink_known(path: Path) -> bool:
    try:
        if path.is_file() or path.is_symlink():
            path.unlink()
            return True
    except OSError as error:
        print(f"Warning: unable to remove {path}: {error}", file=sys.stderr)
    return False


def cleanup(args) -> int:
    """Stop plugin-owned processes and optionally purge only known plugin files."""
    ensure_plugin_data()
    for state_path, state in active_states():
        stop_one(state_path, state)
    if not args.purge:
        print("Plugin-owned trackers are stopped; history and logs were preserved")
        return 0

    if read_json(PLUGIN_DATA_MARKER, None) is not None:
        raise RuntimeError("Plugin data marker must be a text ownership marker")
    try:
        marker = PLUGIN_DATA_MARKER.read_text(encoding="utf-8")
    except OSError as error:
        raise RuntimeError(f"Unable to validate plugin data ownership: {error}") from error
    if marker != PLUGIN_DATA_MARKER_CONTENT:
        raise RuntimeError("Refusing to purge an unrecognized plugin data directory")

    for directory, pattern in (
        (STATES_DIR, "*.json"),
        (LOGS_DIR, "*.log"),
        (LOCKS_DIR, "*.lock"),
    ):
        if directory.is_symlink():
            print(f"Unknown symlink was preserved: {directory}")
            continue
        if directory.is_dir():
            for path in directory.glob(pattern):
                _unlink_known(path)
            try:
                directory.rmdir()
            except OSError:
                pass
    for pattern in (".api-body-*", ".curl-*"):
        for path in TRACK_HOME.glob(pattern):
            _unlink_known(path)
    for path in (
        TRACK_HOME / "hook.log",
        PLUGIN_DATA_MARKER,
    ):
        _unlink_known(path)
    try:
        TRACK_HOME.rmdir()
        print(f"Removed empty plugin data directory: {TRACK_HOME}")
    except OSError:
        print(f"Unknown files remain and were preserved: {TRACK_HOME}")
    return 0


def main() -> int:
    ensure_plugin_data()
    parser = argparse.ArgumentParser(prog="multica-codex-sync")
    sub = parser.add_subparsers(dest="command", required=True)

    start_parser = sub.add_parser("start")
    start_parser.add_argument("issue")
    start_parser.add_argument("--session", required=True)
    start_parser.set_defaults(func=start)

    stop_parser = sub.add_parser("stop")
    stop_parser.add_argument("target", nargs="?", help="Issue, run id, or task id")
    stop_parser.add_argument("--all", action="store_true")
    stop_parser.set_defaults(func=stop)

    status_parser = sub.add_parser("status")
    status_parser.add_argument("target", nargs="?", help="Issue, run id, or task id")
    status_parser.add_argument("--all", action="store_true", help="Include stopped history")
    status_parser.set_defaults(func=status)

    version_parser = sub.add_parser("version")
    version_parser.set_defaults(func=version_command)

    doctor_parser = sub.add_parser("doctor")
    doctor_parser.set_defaults(func=doctor)

    cleanup_parser = sub.add_parser("cleanup")
    cleanup_parser.add_argument(
        "--purge",
        action="store_true",
        help="Remove known plugin-owned history and logs while preserving unknown files",
    )
    cleanup_parser.set_defaults(func=cleanup)

    watch_parser = sub.add_parser("watch")
    watch_parser.add_argument("--state", required=True, type=Path)
    watch_parser.set_defaults(func=lambda watch_args: watcher(watch_args.state))

    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
