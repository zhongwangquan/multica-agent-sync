from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

from .core import (
    CODEX_HOME,
    LOCAL_RUN_HEARTBEAT_INTERVAL_SECONDS,
    LOCAL_RUN_IDLE_TIMEOUT_SECONDS,
    PLUGIN_ROOT,
    USAGE_TOTAL_KEYS,
    Api,
    append_private_log,
    atomic_json,
    complete_local_run,
    create_local_run,
    int_field,
    read_json,
    reset_current_run_usage,
    state_log_path,
    with_upload_run,
)

def desktop_session_meta(path: Path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            for _ in range(30):
                line = handle.readline()
                if not line:
                    break
                entry = json.loads(line)
                if entry.get("type") == "session_meta":
                    payload = entry.get("payload") or {}
                    if payload.get("originator") == "Codex Desktop":
                        return payload
                    return None
    except (OSError, json.JSONDecodeError):
        return None
    return None


def find_session(session_id: str | None = None):
    if not session_id:
        raise RuntimeError("A Codex Desktop session id is required; refusing to guess the latest chat")
    root = CODEX_HOME / "sessions"
    candidates = sorted(root.glob("**/rollout-*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        meta = desktop_session_meta(path)
        if not meta:
            continue
        if session_id and meta.get("id") != session_id:
            continue
        return path, meta
    raise RuntimeError("No matching Codex Desktop session was found")


def latest_model(path: Path) -> str:
    model = "codex"
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                entry = json.loads(line)
                payload = entry.get("payload") or {}
                if entry.get("type") == "turn_context" and isinstance(payload.get("model"), str):
                    model = payload["model"]
    except (OSError, json.JSONDecodeError):
        pass
    return model


def text_from_content(content) -> str:
    if not isinstance(content, list):
        return ""
    chunks = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") in {"input_text", "output_text", "text"}:
            value = item.get("text")
            if isinstance(value, str):
                chunks.append(value)
    return "".join(chunks).strip()


def issue_from_track_command(text: str) -> str | None:
    """Return an issue id for a supported Multica chat command."""
    first_line = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    match = re.match(
        r"^/multica(?:-|\s+)(?:OPE-)?([0-9]+)(?:\s|$)",
        first_line,
        re.IGNORECASE,
    )
    if not match:
        return None
    return f"OPE-{match.group(1)}"


def is_track_command_text(text: str) -> bool:
    return issue_from_track_command(text) is not None


def is_stop_command_text(text: str) -> bool:
    first_line = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    return bool(
        re.match(
            r"^/multica(?:-|\s+)stop(?:\s|$)",
            first_line,
            re.IGNORECASE,
        )
    )


def is_status_command_text(text: str) -> bool:
    first_line = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    return bool(
        re.match(
            r"^/multica(?:-|\s+)status(?:\s|$)",
            first_line,
            re.IGNORECASE,
        )
    )


def is_informational_command_text(text: str) -> bool:
    first_line = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    return bool(
        re.match(
            r"^/multica(?:-|\s+)(?:help|doctor)(?:\s|$)",
            first_line,
            re.IGNORECASE,
        )
    )


def is_control_command_text(text: str) -> bool:
    return (
        is_track_command_text(text)
        or is_stop_command_text(text)
        or is_status_command_text(text)
        or is_informational_command_text(text)
    )


def is_business_user_message(entry: dict) -> bool:
    payload = entry.get("payload") or {}
    if entry.get("type") != "response_item" or payload.get("type") != "message":
        return False
    if payload.get("role") != "user":
        return False
    text = text_from_content(payload.get("content"))
    return bool(text and not is_control_command_text(text))


def source_key(session_id: str, timestamp: str, kind: str, text: str) -> str:
    digest = hashlib.sha256(f"{session_id}\0{timestamp}\0{kind}\0{text}".encode()).hexdigest()[:24]
    return f"codex-desktop:{session_id}:{kind}:{digest}"


def normalized_usage_total(usage) -> dict[str, int] | None:
    if not isinstance(usage, dict):
        return None
    total = {}
    for normalized_key, source_keys in USAGE_TOTAL_KEYS.items():
        total[normalized_key] = 0
        for source_key_name in source_keys:
            if source_key_name in usage:
                total[normalized_key] = int_field(usage.get(source_key_name))
                break
    return total


def total_usage_from_entry(entry: dict) -> dict[str, int] | None:
    payload = entry.get("payload") or {}
    if entry.get("type") != "event_msg" or payload.get("type") != "token_count":
        return None
    info = payload.get("info") or {}
    return normalized_usage_total(info.get("total_token_usage"))


def latest_usage_total_before_offset(path: Path, offset: int) -> dict[str, int]:
    latest = {key: 0 for key in USAGE_TOTAL_KEYS}
    try:
        with path.open("r", encoding="utf-8") as handle:
            while handle.tell() < offset:
                line = handle.readline()
                if not line:
                    break
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                total = total_usage_from_entry(entry)
                if total is not None:
                    latest = total
    except OSError:
        pass
    return latest


def add_usage_totals(base: dict | None, increment: dict) -> dict[str, int]:
    if not isinstance(base, dict):
        base = {}
    return {
        key: int_field(base.get(key)) + int_field(increment.get(key))
        for key in USAGE_TOTAL_KEYS
    }


def usage_payload_item(state: dict, totals: dict) -> dict:
    item = {
        "provider": "codex",
        "model": state.get("model") or "codex",
        "input_tokens": int_field(totals.get("input_tokens")),
        "output_tokens": int_field(totals.get("output_tokens")),
        "cache_read_tokens": int_field(totals.get("cache_read_tokens")),
        "cache_write_tokens": 0,
    }
    if int_field(totals.get("reasoning_tokens")):
        item["reasoning_tokens"] = int_field(totals.get("reasoning_tokens"))
    return item


def current_run_usage_after_delta(state: dict, run_id: str, delta: dict) -> dict[str, int]:
    current = state.get("usage_current_run_totals")
    if state.get("usage_current_run_id") != str(run_id):
        current = {}
    return add_usage_totals(current, delta)


def ensure_usage_baseline(state: dict, path: Path, offset: int) -> None:
    if isinstance(state.get("usage_totals"), dict):
        return
    state["usage_totals"] = latest_usage_total_before_offset(path, offset)
    state["usage_baseline_offset"] = offset
    state["usage_baseline_at"] = time.time()

def reconnect_local_run(api: Api, state: dict, reason: str) -> bool:
    if not state.get("issue_id"):
        raise RuntimeError("Cannot reconnect without a Multica issue id")
    previous = state.setdefault("previous_run_ids", [])
    if state.get("run_id") and state["run_id"] not in previous:
        previous.append(state["run_id"])
    if not state.get("work_dir") and state.get("session_file"):
        meta = desktop_session_meta(Path(state["session_file"])) or {}
        if meta.get("cwd"):
            state["work_dir"] = str(meta["cwd"])
    meta = {
        "cwd": state.get("work_dir")
        or state.get("cwd")
        or str(Path.cwd())
    }
    state["run_id"] = create_local_run(api, state["issue_id"], meta)
    state["last_upload_run_id"] = state["run_id"]
    reset_current_run_usage(state, state["run_id"])
    state["server_run_rotations"] = int_field(state.get("server_run_rotations")) + 1
    state["server_run_count"] = int_field(state.get("server_run_count")) + 1
    state["last_server_run_status"] = "running"
    state["short_lived_runs"] = False
    state["run_mode"] = "session"
    state["last_heartbeat_at"] = time.time()
    state["last_reconnect_at"] = state["last_heartbeat_at"]
    state["last_reconnect_reason"] = reason
    return True


def ensure_session_run_mode(api: Api, state: dict) -> bool:
    if state.get("run_mode") == "session" and state.get("short_lived_runs") is False:
        return False
    # Older plugin versions used one short local-run per upload and completed
    # the run immediately. Migrate an already-running watcher to a single
    # session run once; after that, messages and usage stay attached to that
    # run unless heartbeat proves it is gone.
    return reconnect_local_run(api, state, "migrate-short-lived-run")


def refresh_local_run(api: Api, state: dict, force: bool = False) -> bool:
    if ensure_session_run_mode(api, state):
        return True
    if state.get("run_paused_at"):
        return False
    now = time.time()
    last_attempt = max(
        float(state.get("last_heartbeat_at") or 0),
        float(state.get("last_heartbeat_attempt_at") or 0),
    )
    if not force and now - last_attempt < LOCAL_RUN_HEARTBEAT_INTERVAL_SECONDS:
        return False
    state["last_heartbeat_attempt_at"] = now
    response = api.request("PATCH", f"/api/local-runs/{state['run_id']}", {"status": "running"})
    state["last_heartbeat_at"] = now
    state["last_server_run_status"] = response.get("status") if isinstance(response, dict) else None
    if isinstance(response, dict) and response.get("status") == "running":
        return True
    return reconnect_local_run(api, state, f"heartbeat-status-{state.get('last_server_run_status')}")


def maybe_pause_idle_run(api: Api, state: dict) -> bool:
    if LOCAL_RUN_IDLE_TIMEOUT_SECONDS <= 0:
        return False
    if state.get("last_server_run_status") != "running" or state.get("run_paused_at"):
        return False
    if not state.get("run_id"):
        return False
    now = time.time()
    last_activity = max(
        float(state.get("last_event_at") or 0),
        float(state.get("last_upload_at") or 0),
        float(state.get("started_at") or 0),
    )
    if last_activity <= 0 or now - last_activity < LOCAL_RUN_IDLE_TIMEOUT_SECONDS:
        return False
    complete_local_run(api, state["run_id"])
    state["last_server_run_status"] = "completed"
    state["run_paused_at"] = now
    state["run_pause_reason"] = f"idle-timeout-{LOCAL_RUN_IDLE_TIMEOUT_SECONDS}s"
    state["last_idle_completed_run_id"] = state["run_id"]
    state["idle_pause_count"] = int_field(state.get("idle_pause_count")) + 1
    return True


def post_message(api: Api, state: dict, entry: dict) -> None:
    payload = entry.get("payload") or {}
    if entry.get("type") != "response_item" or payload.get("type") != "message":
        return
    role = payload.get("role")
    text = text_from_content(payload.get("content"))
    if role not in {"user", "assistant"} or not text:
        return
    if role == "user" and is_control_command_text(text):
        return
    timestamp = str(entry.get("timestamp") or "")
    body = {
        "type": "user_input" if role == "user" else "final",
        "content": text,
        "source": "multica-codex-sync",
        "source_key": source_key(state["session_id"], timestamp, role, text),
    }
    with_upload_run(
        api,
        state,
        lambda run_id: api.request("POST", f"/api/local-runs/{run_id}/messages", body),
    )


def post_usage(api: Api, state: dict, entry: dict) -> None:
    payload = entry.get("payload") or {}
    if entry.get("type") != "event_msg" or payload.get("type") != "token_count":
        return
    info = payload.get("info") or {}
    total = normalized_usage_total(info.get("total_token_usage"))
    if total is None:
        usage = normalized_usage_total(info.get("last_token_usage"))
        if usage is None:
            return
        if usage["input_tokens"] == 0 and usage["output_tokens"] == 0 and usage["cache_read_tokens"] == 0:
            return
        uploaded = state.get("usage_uploaded_totals")
        next_uploaded = add_usage_totals(uploaded, usage)

        def upload_usage(run_id: str) -> None:
            next_current_run = current_run_usage_after_delta(state, run_id, usage)
            api.request(
                "PUT",
                f"/api/local-runs/{run_id}/usage",
                {"usage": [usage_payload_item(state, next_current_run)]},
            )
            state["usage_current_run_id"] = str(run_id)
            state["usage_current_run_totals"] = next_current_run

        with_upload_run(
            api,
            state,
            upload_usage,
        )
        state["usage_uploaded_totals"] = next_uploaded
        state["usage_upload_events"] = int_field(state.get("usage_upload_events")) + 1
        return

    previous = state.get("usage_totals")
    if not isinstance(previous, dict):
        previous = {key: 0 for key in USAGE_TOTAL_KEYS}
    if any(total.get(key, 0) < int_field(previous.get(key)) for key in USAGE_TOTAL_KEYS):
        state["usage_totals"] = total
        state["usage_reset_events"] = int_field(state.get("usage_reset_events")) + 1
        return

    delta = {
        key: total.get(key, 0) - int_field(previous.get(key))
        for key in USAGE_TOTAL_KEYS
    }
    if all(value == 0 for value in delta.values()):
        state["usage_duplicate_events"] = int_field(state.get("usage_duplicate_events")) + 1
        return

    uploaded = state.get("usage_uploaded_totals")
    next_uploaded = add_usage_totals(uploaded, delta)

    def upload_usage(run_id: str) -> None:
        next_current_run = current_run_usage_after_delta(state, run_id, delta)
        api.request(
            "PUT",
            f"/api/local-runs/{run_id}/usage",
            {"usage": [usage_payload_item(state, next_current_run)]},
        )
        state["usage_current_run_id"] = str(run_id)
        state["usage_current_run_totals"] = next_current_run

    with_upload_run(
        api,
        state,
        upload_usage,
    )
    state["usage_totals"] = total
    state["usage_upload_events"] = int_field(state.get("usage_upload_events")) + 1
    state["usage_uploaded_totals"] = next_uploaded


def update_model(state: dict, entry: dict) -> None:
    payload = entry.get("payload") or {}
    if entry.get("type") == "turn_context" and isinstance(payload.get("model"), str):
        state["model"] = payload["model"]


def plugin_installation_available(state: dict) -> bool:
    """Return whether the plugin root that launched this watcher still exists."""
    root = Path(str(state.get("plugin_root") or PLUGIN_ROOT))
    return (root / ".codex-plugin" / "plugin.json").is_file()


def watcher(state_path: Path) -> int:
    api = Api()
    state = read_json(state_path)
    if not isinstance(state, dict) or state.get("status") != "running":
        return 0
    path = Path(state["session_file"])
    position = int(state.get("offset") or 0)
    ensure_usage_baseline(state, path, position)
    atomic_json(state_path, state)
    with path.open("r", encoding="utf-8") as handle:
        handle.seek(position)
        while True:
            current = read_json(state_path, {})
            if current.get("status") != "running":
                break
            if not plugin_installation_available(current):
                try:
                    complete_local_run(api, str(state.get("run_id") or ""))
                    state["last_server_run_status"] = "completed"
                except Exception as error:
                    state["server_stop_error"] = str(error)
                state["status"] = "stopped"
                state["stopped_at"] = time.time()
                state["stop_reason"] = "plugin-root-missing"
                atomic_json(state_path, state)
                break
            line_start = handle.tell()
            line = handle.readline()
            if not line:
                try:
                    if maybe_pause_idle_run(api, state) or refresh_local_run(api, state):
                        state["updated_at"] = time.time()
                        atomic_json(state_path, state)
                except Exception as error:
                    append_private_log(
                        state_log_path(state),
                        f"{time.strftime('%Y-%m-%dT%H:%M:%S')} heartbeat {error}\n",
                    )
                time.sleep(0.25)
                continue
            position = handle.tell()
            try:
                entry = json.loads(line)
                state["last_event_at"] = time.time()
                update_model(state, entry)
                if state.get("suppress_until_next_user"):
                    if is_business_user_message(entry):
                        state["suppress_until_next_user"] = False
                    else:
                        current = read_json(state_path, {})
                        if current.get("status") != "running":
                            break
                        if current.get("pid"):
                            state["pid"] = current["pid"]
                        state["offset"] = position
                        state["updated_at"] = time.time()
                        atomic_json(state_path, state)
                        continue
                if refresh_local_run(api, state):
                    state["updated_at"] = time.time()
                    atomic_json(state_path, state)
                post_message(api, state, entry)
                post_usage(api, state, entry)
                current = read_json(state_path, {})
                if current.get("status") != "running":
                    break
                if current.get("pid"):
                    state["pid"] = current["pid"]
                state["offset"] = position
                state["updated_at"] = time.time()
                atomic_json(state_path, state)
            except Exception as error:  # keep the watcher alive and make failures inspectable
                handle.seek(line_start)
                append_private_log(
                    state_log_path(state),
                    f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {error}\n",
                )
                time.sleep(1)
    return 0
