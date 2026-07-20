#!/usr/bin/env python3
# multica-codex-sync-plugin-owned-file-v2
"""Codex UserPromptSubmit hook for Multica Codex Sync control commands."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


HOME = Path.home()
MULTICA_HOME = Path(os.environ.get("MULTICA_HOME", HOME / ".multica")).expanduser()
PLUGIN_ROOT = Path(
    os.environ.get("PLUGIN_ROOT", Path(__file__).resolve().parents[1])
).expanduser().resolve()
PLUGIN_DATA = Path(
    os.environ.get(
        "PLUGIN_DATA",
        MULTICA_HOME / "plugin-data" / "multica-codex-sync",
    )
).expanduser().absolute()
LOG_PATH = PLUGIN_DATA / "hook.log"
TRACK_COMMAND = PLUGIN_ROOT / "scripts" / "multica_codex_track.py"
MULTICA_COMMAND_TIMEOUT_SECONDS = 20

START_RE = re.compile(
    r"^\s*/multica(?:-|\s+)(?:OPE-)?([0-9]+)(?:\s|$)",
    re.IGNORECASE,
)
STOP_RE = re.compile(
    r"^\s*/multica(?:-|\s+)stop(?:\s|$)",
    re.IGNORECASE,
)
STATUS_RE = re.compile(
    r"^\s*/multica(?:-|\s+)status(?:\s|$)",
    re.IGNORECASE,
)


def log(message: str) -> None:
    if LOG_PATH.parent.is_symlink() or (
        LOG_PATH.parent.exists() and not LOG_PATH.parent.is_dir()
    ):
        return
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        LOG_PATH.parent.chmod(0o700)
    except OSError:
        pass
    descriptor = os.open(LOG_PATH, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {message}\n"
        os.write(descriptor, line.encode("utf-8", errors="replace"))
    finally:
        os.close(descriptor)


def block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))


def token_m(value: Any) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0
    return f"{number / 1_000_000:.1f}M"


def compact_id(value: Any) -> str:
    text = str(value or "")
    if len(text) <= 12:
        return text
    return f"{text[:8]}…{text[-4:]}"


def format_status_payload(payload: Any, current_session_id: str) -> str:
    if not isinstance(payload, dict):
        return "Multica 状态返回格式异常。"
    trackers = payload.get("trackers") if isinstance(payload.get("trackers"), list) else []
    if current_session_id:
        trackers = [
            item for item in trackers
            if isinstance(item, dict) and item.get("session_id") == current_session_id
        ]

    lines = ["当前 Codex ↔ Multica 链接状态："]
    if not trackers:
        lines.append("")
        lines.append("当前会话未绑定运行中的 Multica tracker。")
        lines.append("使用 /multica xxxx 可以绑定当前会话。")
        return "\n".join(lines)

    for index, tracker in enumerate(trackers, start=1):
        if not isinstance(tracker, dict):
            continue
        usage = tracker.get("usage_uploaded_totals")
        if not isinstance(usage, dict):
            usage = tracker.get("usage_totals") if isinstance(tracker.get("usage_totals"), dict) else {}
        lines.append("")
        if len(trackers) > 1:
            lines.append(f"tracker #{index}:")
        lines.append(f"issue: {tracker.get('issue') or '-'}")
        lines.append(f"status: {tracker.get('status') or '-'}")
        lines.append(f"run_id: {compact_id(tracker.get('run_id'))}")
        lines.append(f"session_id: {compact_id(tracker.get('session_id'))}")
        lines.append(f"watcher_alive: {str(bool(tracker.get('watcher_alive'))).lower()}")
        lines.append(f"run_mode: {tracker.get('run_mode') or '-'}")
        lines.append(f"short_lived_runs: {str(bool(tracker.get('short_lived_runs'))).lower()}")
        lines.append(f"last_server_run_status: {tracker.get('last_server_run_status') or '-'}")
        lines.append(f"server_run_count: {tracker.get('server_run_count') or tracker.get('upload_run_count') or 0}")
        lines.append(f"reconnect_count: {tracker.get('upload_reconnect_count') or tracker.get('server_run_rotations') or 0}")
        lines.append("token_usage_unit: M")
        lines.append(
            "tokens: "
            f"input={token_m(usage.get('input_tokens'))}, "
            f"output={token_m(usage.get('output_tokens'))}, "
            f"cache_read={token_m(usage.get('cache_read_tokens'))}, "
            f"reasoning={token_m(usage.get('reasoning_tokens'))}"
        )
    return "\n".join(lines)


def continue_with_issue_context(issue_key: str, status: str) -> None:
    context = (
        f"Multica Codex Sync status: {status}. "
        f"This Codex session is bound to Multica issue {issue_key}. "
        "Treat the user's /multica command as a task binding, not as a request to search the repo blindly. "
        "The hook system message has already shown the connection status. "
        "Do not repeat a visible connected banner in normal responses unless the user asks for link status. "
        f"Before inspecting or changing repository files, first run `multica issue get {issue_key} --output json` "
        "to read the issue title, description, status, assignee, labels, and linked context. "
        "If comments or run history are needed, inspect the relevant Multica issue CLI help and fetch them with JSON output. "
        "After reading the issue, briefly summarize your understanding and plan, then proceed with the repository work."
    )
    print(
        json.dumps(
            {
                "systemMessage": f"已连接 {issue_key}，Multica 跟踪已开启。",
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": context,
                }
            },
            ensure_ascii=False,
        )
    )


def first_prompt(value: Any) -> str:
    direct_keys = (
        "prompt",
        "user_prompt",
        "userPrompt",
        "message",
        "text",
        "input",
    )
    if isinstance(value, dict):
        for key in direct_keys:
            item = value.get(key)
            if isinstance(item, str) and item.strip():
                return item
        content = value.get("content")
        if isinstance(content, str) and content.strip():
            return content
        if isinstance(content, list):
            chunks: list[str] = []
            for entry in content:
                if isinstance(entry, dict) and isinstance(entry.get("text"), str):
                    chunks.append(entry["text"])
            if chunks:
                return "".join(chunks)
        for item in value.values():
            found = first_prompt(item)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = first_prompt(item)
            if found:
                return found
    return ""


def first_session_id(value: Any) -> str:
    keys = ("session_id", "sessionId", "thread_id", "threadId", "conversation_id", "conversationId")
    if isinstance(value, dict):
        for key in keys:
            item = value.get(key)
            if isinstance(item, str) and item.strip():
                return item.strip()
        for item in value.values():
            found = first_session_id(item)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = first_session_id(item)
            if found:
                return found
    return ""


def run_tracker(args: list[str]) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(TRACK_COMMAND), *args]
    try:
        return subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=MULTICA_COMMAND_TIMEOUT_SECONDS,
            env=dict(os.environ),
        )
    except subprocess.TimeoutExpired as error:
        return subprocess.CompletedProcess(
            command,
            124,
            error.stdout if isinstance(error.stdout, str) else "",
            f"timeout after {MULTICA_COMMAND_TIMEOUT_SECONDS}s",
        )
    except Exception as error:
        return subprocess.CompletedProcess(command, 1, "", str(error))


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        log("ignored non-json hook input")
        return 0

    prompt = first_prompt(payload)
    if not prompt:
        return 0

    first_line = prompt.strip().splitlines()[0] if prompt.strip() else ""
    start_match = START_RE.match(first_line)
    stop_match = STOP_RE.match(first_line)
    status_match = STATUS_RE.match(first_line)
    if not start_match and not stop_match and not status_match:
        return 0

    session_id = first_session_id(payload)

    if status_match:
        result = run_tracker(["status"])
        log(f"status session={session_id or '-'} rc={result.returncode}")
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "status failed").strip()
            block(f"Multica 状态查询失败：{detail}")
            return 0
        try:
            status_payload = json.loads(result.stdout or "{}")
            block(format_status_payload(status_payload, session_id))
        except json.JSONDecodeError:
            block((result.stdout or "Multica 状态为空").strip())
        return 0

    if stop_match:
        if not session_id:
            block("无法确认当前 Codex Thread ID，未执行停止操作。请重启 Codex Desktop 后再试。")
            return 0
        args = ["stop", session_id]
        result = run_tracker(args)
        log(f"stop session={session_id or '-'} rc={result.returncode}")
        if result.returncode == 0:
            block("已停止当前 Codex 会话的 Multica 跟踪。")
        else:
            detail = (result.stderr or result.stdout or "stop failed").strip()
            block(f"Multica 停止失败：{detail}")
        return 0

    issue_key = f"OPE-{start_match.group(1)}"
    if not session_id:
        block(
            f"无法确认当前 Codex Thread ID，未连接 {issue_key}，以免误传其他聊天内容。"
            "请重启 Codex Desktop 后再试。"
        )
        return 0
    args = ["start", issue_key]
    args.extend(["--session", session_id])
    result = run_tracker(args)
    log(f"start issue={issue_key} session={session_id or '-'} rc={result.returncode}")
    if result.returncode == 0:
        continue_with_issue_context(issue_key, "tracking started")
    else:
        detail = (result.stderr or result.stdout or "").strip()
        if "already tracking" in detail:
            continue_with_issue_context(issue_key, "already tracking")
        else:
            block(f"Multica 跟踪启动失败：{detail or 'unknown error'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
