from __future__ import annotations

import json
import os
import fcntl
import hashlib
import shlex
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from .paths import resolve_plugin_data

HOME = Path.home()
MULTICA_HOME = Path(os.environ.get("MULTICA_HOME", HOME / ".multica")).expanduser()
CODEX_HOME = Path(os.environ.get("CODEX_HOME", HOME / ".codex")).expanduser()
PLUGIN_ROOT = Path(
    os.environ.get("PLUGIN_ROOT", Path(__file__).resolve().parents[2])
).expanduser().resolve()
PLUGIN_DATA = resolve_plugin_data()
TRACK_HOME = PLUGIN_DATA
STATES_DIR = TRACK_HOME / "states"
LOGS_DIR = TRACK_HOME / "logs"
LOCKS_DIR = TRACK_HOME / "locks"
CONFIG_CANDIDATES = [MULTICA_HOME / "config.json", MULTICA_HOME / "config-local.json"]
USAGE_TOTAL_KEYS = {
    "input_tokens": ("input_tokens",),
    "output_tokens": ("output_tokens",),
    "cache_read_tokens": ("cached_input_tokens", "cache_read_input_tokens"),
    "reasoning_tokens": ("reasoning_output_tokens", "reasoning_tokens"),
}
LOCAL_RUN_HEARTBEAT_INTERVAL_SECONDS = 30
LOCAL_RUN_IDLE_TIMEOUT_SECONDS = int(os.environ.get("MULTICA_CODEX_IDLE_TIMEOUT_SECONDS", "1800"))
PLUGIN_DATA_MARKER = TRACK_HOME / ".multica-codex-sync-owned"
PLUGIN_DATA_MARKER_CONTENT = "multica-codex-sync-plugin-data-v2\n"

def secure_mkdir(path: Path) -> None:
    if path.is_symlink():
        raise RuntimeError(f"Refusing to use symlinked plugin data directory: {path}")
    if path.exists() and not path.is_dir():
        raise RuntimeError(f"Plugin data path is not a directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass


def ensure_plugin_data() -> None:
    """Create the private plugin data root without touching user hook or CLI files."""
    secure_mkdir(TRACK_HOME)
    if PLUGIN_DATA_MARKER.exists():
        try:
            if PLUGIN_DATA_MARKER.read_text(encoding="utf-8") != PLUGIN_DATA_MARKER_CONTENT:
                raise RuntimeError(
                    f"Refusing to use unrecognized plugin data marker: {PLUGIN_DATA_MARKER}"
                )
        except OSError as error:
            raise RuntimeError(f"Unable to validate plugin data marker: {error}") from error
        return
    descriptor = os.open(
        PLUGIN_DATA_MARKER,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
    )
    try:
        os.write(descriptor, PLUGIN_DATA_MARKER_CONTENT.encode("utf-8"))
    finally:
        os.close(descriptor)


def atomic_json(path: Path, value: dict) -> None:
    secure_mkdir(path.parent)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        tmp.chmod(0o600)
        tmp.replace(path)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
    try:
        path.chmod(0o600)
    except OSError:
        pass


def append_private_log(path: Path, message: str) -> None:
    secure_mkdir(path.parent)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(descriptor, message.encode("utf-8", errors="replace"))
    finally:
        os.close(descriptor)


@contextmanager
def session_lock(session_id: str):
    secure_mkdir(LOCKS_DIR)
    name = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
    lock_path = LOCKS_DIR / f"session-{name}.lock"
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def pid_alive(pid) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def process_identity(pid: int) -> dict:
    if not pid_alive(pid):
        return {}
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "lstart=", "-o", "command="],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if result.returncode != 0 or not result.stdout.strip():
        return {}
    first_line, _, remainder = result.stdout.strip().partition("\n")
    if not remainder:
        # macOS may put both requested columns on the same line. The start time
        # has a stable 24-character format such as "Mon Jul  6 17:04:01 2026".
        first_line = result.stdout.strip()[:24].strip()
        remainder = result.stdout.strip()[24:].strip()
    return {"started": first_line.strip(), "command": remainder.strip()}


def tracker_process_matches(
    pid,
    *,
    mode: str,
    expected_identity: dict | None = None,
    state_path: Path | None = None,
) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    identity = process_identity(pid)
    command = str(identity.get("command") or "")
    if not command:
        return False
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    if not any(Path(token).name == "multica_codex_track.py" for token in tokens):
        return False
    if mode not in tokens:
        return False
    if state_path is not None:
        expected = str(state_path.resolve())
        found = False
        for index, token in enumerate(tokens[:-1]):
            if token == "--state" and str(Path(tokens[index + 1]).resolve()) == expected:
                found = True
                break
        if not found:
            return False
    if isinstance(expected_identity, dict) and expected_identity.get("started"):
        if identity.get("started") != expected_identity.get("started"):
            return False
    return True


def cleanup_stale_api_temp_files(max_age_seconds: int = 300) -> None:
    now = time.time()
    for pattern in (".api-body-*", ".curl-*"):
        for path in TRACK_HOME.glob(pattern):
            try:
                if path.is_file() and now - path.stat().st_mtime >= max_age_seconds:
                    path.unlink()
            except OSError:
                pass


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def state_files() -> list[Path]:
    if STATES_DIR.is_symlink():
        raise RuntimeError(f"Refusing to read symlinked state directory: {STATES_DIR}")
    if not STATES_DIR.is_dir():
        return []
    return sorted(STATES_DIR.glob("*.json"))

def load_states() -> list[tuple[Path, dict]]:
    values = []
    for path in state_files():
        state = read_json(path)
        if isinstance(state, dict):
            values.append((path, state))
    return values


def active_states() -> list[tuple[Path, dict]]:
    return [(path, state) for path, state in load_states() if state.get("status") == "running"]


def opaque_file_id(value: object) -> str:
    """Return a stable filename-safe identifier without trusting external IDs as paths."""
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:32]


def state_path_for_run(run_id: object) -> Path:
    return STATES_DIR / f"run-{opaque_file_id(run_id)}.json"


def state_log_path(state: dict) -> Path:
    return LOGS_DIR / f"run-{opaque_file_id(state.get('run_id'))}.log"


def select_states(target: str | None) -> list[tuple[Path, dict]]:
    candidates = active_states()
    if not target:
        return candidates
    normalized = target.strip().lower()
    return [
        (path, state)
        for path, state in candidates
        if normalized
        in {
            str(state.get("issue") or "").lower(),
            str(state.get("issue_id") or "").lower(),
            str(state.get("run_id") or "").lower(),
            str(state.get("session_id") or "").lower(),
        }
    ]


def load_config() -> dict:
    for path in CONFIG_CANDIDATES:
        value = read_json(path)
        if isinstance(value, dict) and value.get("token") and value.get("server_url"):
            return value
    raise RuntimeError("Multica config with server_url/token was not found")

class Api:
    def __init__(self):
        config = load_config()
        self.base = str(config["server_url"]).rstrip("/")
        self.token = str(config["token"])
        self.workspace_id = str(config.get("workspace_id") or "")

    def request(self, method: str, path: str, body=None):
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = [
            f"Authorization: Bearer {self.token}",
            "Accept: application/json",
            "Content-Type: application/json",
            "X-Client-Platform: multica-codex-sync",
        ]
        if self.workspace_id:
            headers.append(f"X-Workspace-ID: {self.workspace_id}")

        # Use curl instead of urllib for better compatibility with Multica's
        # HTTPS edge. urllib intermittently hits TLS handshake timeouts /
        # connection resets on long-running watcher processes, while the same
        # request succeeds through curl.
        secure_mkdir(TRACK_HOME)
        cleanup_stale_api_temp_files()
        body_path = None
        config_path = None
        try:
            if payload is not None:
                body_file = tempfile.NamedTemporaryFile(
                    mode="wb",
                    delete=False,
                    dir=TRACK_HOME,
                    prefix=".api-body-",
                )
                body_path = Path(body_file.name)
                try:
                    os.chmod(body_path, 0o600)
                except OSError:
                    pass
                with body_file:
                    body_file.write(payload)

            config_file = tempfile.NamedTemporaryFile(
                mode="w",
                delete=False,
                dir=TRACK_HOME,
                prefix=".curl-",
                encoding="utf-8",
            )
            config_path = Path(config_file.name)
            try:
                os.chmod(config_path, 0o600)
            except OSError:
                pass
            with config_file:
                config_file.write("silent\n")
                config_file.write("show-error\n")
                config_file.write("fail-with-body\n")
                config_file.write("max-time = 30\n")
                config_file.write("retry = 2\n")
                config_file.write("retry-delay = 1\n")
                config_file.write("retry-all-errors\n")
                config_file.write(f"request = \"{method}\"\n")
                config_file.write(f"url = \"{self.base + path}\"\n")
                for header in headers:
                    config_file.write(f"header = {json.dumps(header)}\n")

            command = [
                "curl",
                "--config",
                str(config_path),
                "--write-out",
                "\n%{http_code}",
            ]
            if body_path is not None:
                command.extend(["--data-binary", f"@{body_path}"])
            result = subprocess.run(
                command,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=45,
            )
            output = result.stdout or ""
            raw_body, separator, raw_status = output.rpartition("\n")
            status = int(raw_status) if separator and raw_status.isdigit() else 0
            if result.returncode != 0:
                detail = (raw_body or result.stderr or f"curl exit {result.returncode}").strip()
                if status:
                    raise ApiError(method, path, detail, status)
                raise ApiError(method, path, detail)
            if status < 200 or status >= 300:
                raise ApiError(method, path, raw_body.strip(), status)
            return json.loads(raw_body) if raw_body.strip() else None
        finally:
            for temp_path in (body_path, config_path):
                if temp_path is not None:
                    try:
                        temp_path.unlink()
                    except FileNotFoundError:
                        pass


class ApiError(RuntimeError):
    def __init__(self, method: str, path: str, detail: str, status: int | None = None):
        self.method = method
        self.path = path
        self.status = status
        suffix = f" ({status})" if status else ""
        super().__init__(f"{method} {path} failed{suffix}: {detail}")


def run_is_unavailable(error: Exception) -> bool:
    return isinstance(error, ApiError) and error.status in {404, 409, 410}

def int_field(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def reset_current_run_usage(state: dict, run_id: str | None = None) -> None:
    state["usage_current_run_id"] = str(run_id or state.get("run_id") or "")
    state["usage_current_run_totals"] = {key: 0 for key in USAGE_TOTAL_KEYS}


def create_local_run(api: Api, issue_id: str, meta: dict) -> str:
    created = api.request(
        "POST",
        f"/api/issues/{issue_id}/local-runs",
        {
            "cli_name": "codex",
            "comments_mode": "thread",
            # The plugin treats one Codex Desktop task as one Multica
            # local-run. A watcher keeps the run alive with heartbeat and only
            # creates a replacement run when the previous one is no longer
            # accepted by the server.
            "no_status_update": True,
            "work_dir": str(meta.get("cwd") or Path.cwd()),
        },
    )
    run_id = created.get("id") or created.get("run", {}).get("id")
    if not run_id:
        raise RuntimeError(f"Multica did not return a local run id: {created}")
    api.request("PATCH", f"/api/local-runs/{run_id}", {"status": "running"})
    return run_id


def complete_local_run(api: Api, run_id: str) -> None:
    api.request(
        "PATCH",
        f"/api/local-runs/{run_id}",
        {"status": "completed", "exit_code": 0, "error": ""},
    )


def upload_run_meta(state: dict) -> dict:
    return {
        "cwd": state.get("work_dir")
        or state.get("cwd")
        or str(Path.cwd())
    }


def record_session_upload(state: dict, run_id: str) -> None:
    state["last_upload_run_id"] = run_id
    state["last_server_run_status"] = "running"
    state["last_upload_at"] = time.time()
    state["upload_batch_count"] = int_field(state.get("upload_batch_count")) + 1


def with_upload_run(api: Api, state: dict, upload) -> None:
    if not state.get("issue_id"):
        raise RuntimeError("Cannot upload without a Multica issue id")
    run_id = state.get("run_id")
    if not run_id or state.get("last_server_run_status") != "running" or state.get("run_paused_at"):
        previous = state.setdefault("previous_run_ids", [])
        if run_id and run_id not in previous:
            previous.append(run_id)
        run_id = create_local_run(api, state["issue_id"], upload_run_meta(state))
        state["run_id"] = run_id
        state["last_upload_run_id"] = run_id
        reset_current_run_usage(state, str(run_id))
        state["last_server_run_status"] = "running"
        state["short_lived_runs"] = False
        state["run_mode"] = "session"
        state.pop("run_paused_at", None)
        state.pop("run_pause_reason", None)
        state["last_reconnect_at"] = time.time()
        state["last_reconnect_reason"] = "resume-after-idle"
        state["server_run_rotations"] = int_field(state.get("server_run_rotations")) + 1
        state["server_run_count"] = int_field(state.get("server_run_count")) + 1
    try:
        upload(str(run_id))
    except Exception as error:
        state["last_upload_error"] = str(error)
        if not run_is_unavailable(error):
            raise
        previous = state.setdefault("previous_run_ids", [])
        if run_id and run_id not in previous:
            previous.append(run_id)
        run_id = create_local_run(api, state["issue_id"], upload_run_meta(state))
        state["run_id"] = run_id
        state["last_upload_run_id"] = run_id
        reset_current_run_usage(state, str(run_id))
        state["last_server_run_status"] = "running"
        state["short_lived_runs"] = False
        state["run_mode"] = "session"
        state["server_run_rotations"] = int_field(state.get("server_run_rotations")) + 1
        state["server_run_count"] = int_field(state.get("server_run_count")) + 1
        state["upload_reconnect_count"] = int_field(state.get("upload_reconnect_count")) + 1
        state["last_reconnect_at"] = time.time()
        state["last_reconnect_reason"] = "upload-failed"
        upload(str(run_id))
    record_session_upload(state, str(run_id))
