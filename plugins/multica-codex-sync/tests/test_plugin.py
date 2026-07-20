from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
SCRIPTS = PLUGIN_ROOT / "scripts"
HOOK = SCRIPTS / "prompt_submit.py"
CLI_ENTRYPOINT = SCRIPTS / "multica_codex_track.py"
sys.path.insert(0, str(SCRIPTS))

import prompt_submit  # noqa: E402
from multica_codex_sync import cli, codex_adapter, core  # noqa: E402


class PluginSandbox:
    def __init__(self, root: Path):
        self.root = root
        self.home = root / "home"
        self.plugin_data = root / "plugin data"
        self.multica_home = self.home / ".multica"
        self.codex_home = self.home / ".codex"

    def env(self, plugin_root: Path = PLUGIN_ROOT) -> dict[str, str]:
        environment = dict(os.environ)
        environment.update(
            {
                "HOME": str(self.home),
                "MULTICA_HOME": str(self.multica_home),
                "CODEX_HOME": str(self.codex_home),
                "PLUGIN_ROOT": str(plugin_root),
                "PLUGIN_DATA": str(self.plugin_data),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )
        return environment

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(CLI_ENTRYPOINT), *args],
            env=self.env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )

    def fake_tracker(self) -> tuple[Path, Path]:
        fake_root = self.root / "fake plugin"
        scripts = fake_root / "scripts"
        scripts.mkdir(parents=True)
        arguments = self.root / "arguments.json"
        tracker = scripts / "multica_codex_track.py"
        tracker.write_text(
            """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
Path(os.environ['ARGUMENTS_PATH']).write_text(json.dumps(sys.argv[1:]), encoding='utf-8')
if sys.argv[1:] == ['status']:
    print(json.dumps({'plugin_version': '1.1.2', 'trackers': []}))
elif sys.argv[1:] == ['doctor']:
    configured = os.environ.get('FAKE_DOCTOR_CONFIGURED', '1') == '1'
    print(json.dumps({
        'plugin_version': '1.1.2',
        'plugin_root': '/private/plugin/root',
        'plugin_data': '/private/plugin/data',
        'plugin_data_private': True,
        'multica_configured': configured,
        'multica_config_path': '/private/config/with-token-location.json',
        'codex_sessions_found': True,
        'active_trackers': 2,
    }))
    raise SystemExit(0 if configured else 1)
""",
            encoding="utf-8",
        )
        return fake_root, arguments

    def run_hook(
        self,
        payload: dict | str,
        environment_updates: dict[str, str] | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], Path]:
        fake_root, arguments = self.fake_tracker()
        environment = self.env(fake_root)
        environment["ARGUMENTS_PATH"] = str(arguments)
        environment.update(environment_updates or {})
        hook_input = payload if isinstance(payload, str) else json.dumps(payload)
        result = subprocess.run(
            [sys.executable, "-B", str(HOOK)],
            input=hook_input,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        return result, arguments


class PluginManifestTests(unittest.TestCase):
    def test_public_manifest_marketplace_and_hook_are_consistent(self) -> None:
        manifest = json.loads((PLUGIN_ROOT / ".codex-plugin/plugin.json").read_text())
        marketplace = json.loads(
            (REPO_ROOT / ".agents/plugins/marketplace.json").read_text()
        )
        hook = json.loads((PLUGIN_ROOT / "hooks/hooks.json").read_text())

        self.assertEqual(manifest["name"], PLUGIN_ROOT.name)
        self.assertEqual(manifest["version"], "1.1.2")
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(manifest["skills"], "./skills/")
        skills_root = PLUGIN_ROOT / "skills"
        self.assertEqual(
            {path.name for path in skills_root.iterdir() if path.is_dir()},
            {"help", "doctor", "status", "stop"},
        )
        for name in ("help", "doctor", "status", "stop"):
            skill_text = (skills_root / name / "SKILL.md").read_text()
            metadata_text = (skills_root / name / "agents/openai.yaml").read_text()
            self.assertIn(f"name: {name}", skill_text)
            self.assertIn("allow_implicit_invocation: false", metadata_text)
            self.assertIn(f"$multica-codex-sync:{name}", metadata_text)
        self.assertEqual(
            manifest["repository"],
            "https://github.com/zhongwangquan/multica-agent-sync",
        )
        self.assertEqual(marketplace["name"], "multica-agent-sync")
        self.assertEqual(len(marketplace["plugins"]), 1)
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], manifest["name"])
        self.assertEqual(entry["source"]["path"], "./plugins/multica-codex-sync")
        self.assertEqual(entry["policy"]["installation"], "AVAILABLE")
        self.assertEqual(entry["policy"]["authentication"], "ON_USE")

        command = hook["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
        self.assertIn("$PLUGIN_ROOT/scripts/prompt_submit.py", command)
        self.assertNotIn("/Users/", command)
        self.assertNotIn("hooks", manifest)

    def test_source_contains_no_legacy_installer_or_unsafe_global_mutation(self) -> None:
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in PLUGIN_ROOT.rglob("*")
            if path.is_file()
            and "tests" not in path.parts
            and path.suffix in {".py", ".json"}
        )
        forbidden = (
            "49.235.34.145",
            "BRIDGE_RELEASE_BASE_URL",
            "enable-chat-commands",
            "disable-chat-commands",
            "listener_loop",
            ".codex/hooks.json",
            "multica.real",
            "shutil.rmtree",
            "/Users/jason",
        )
        for value in forbidden:
            with self.subTest(value=value):
                self.assertNotIn(value, source)


class PluginHookTests(unittest.TestCase):
    def test_start_forms_target_the_exact_task(self) -> None:
        for command in ("/multica 4158", "/multica-4158", "/multica OPE-4158"):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                sandbox = PluginSandbox(Path(directory))
                result, arguments = sandbox.run_hook(
                    {"prompt": command, "session_id": "task-exact"}
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    json.loads(arguments.read_text()),
                    ["start", "OPE-4158", "--session", "task-exact"],
                )
                output = json.loads(result.stdout)
                self.assertEqual(
                    output["hookSpecificOutput"]["hookEventName"],
                    "UserPromptSubmit",
                )

    def test_stop_and_status_support_space_and_hyphen_forms(self) -> None:
        cases = {
            "/multica stop": ["stop", "current-task"],
            "/multica-stop": ["stop", "current-task"],
            "/multica status": ["status"],
            "/multica-status": ["status"],
        }
        for command, expected in cases.items():
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                sandbox = PluginSandbox(Path(directory))
                result, arguments = sandbox.run_hook(
                    {"prompt": command, "session_id": "current-task"}
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(arguments.read_text()), expected)
                self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_help_supports_space_and_hyphen_forms_without_running_cli(self) -> None:
        for command in ("/multica help", "/multica-help"):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                sandbox = PluginSandbox(Path(directory))
                result, arguments = sandbox.run_hook({"prompt": command})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(arguments.exists())
                reason = json.loads(result.stdout)["reason"]
                self.assertIn("/multica 4158", reason)
                self.assertIn("/multica doctor", reason)
                self.assertNotIn("cleanup", reason.lower())

    def test_doctor_supports_space_and_hyphen_forms_and_redacts_paths(self) -> None:
        for command in ("/multica doctor", "/multica-doctor"):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                sandbox = PluginSandbox(Path(directory))
                result, arguments = sandbox.run_hook({"prompt": command})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(arguments.read_text()), ["doctor"])
                reason = json.loads(result.stdout)["reason"]
                self.assertIn("version: 1.1.2", reason)
                self.assertIn("multica_login: ready", reason)
                self.assertIn("active_trackers: 2", reason)
                self.assertNotIn("/private/", reason)
                self.assertNotIn("token", reason.lower())

    def test_doctor_explains_missing_login_even_when_cli_returns_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sandbox = PluginSandbox(Path(directory))
            result, arguments = sandbox.run_hook(
                {"prompt": "/multica doctor"},
                {"FAKE_DOCTOR_CONFIGURED": "0"},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(arguments.read_text()), ["doctor"])
            reason = json.loads(result.stdout)["reason"]
            self.assertIn("multica_login: missing", reason)
            self.assertIn("请先安装并登录 Multica CLI", reason)

    def test_other_namespaces_and_embedded_commands_are_ignored(self) -> None:
        commands = (
            "/multica-sync 9",
            "/multica-sync-stop",
            "/ope 9",
            "/ope-stop",
            "$ope-9",
            "$opc-stop",
            "/multica cleanup",
            "/multica-cleanup",
            "/multica dev",
            "/multica-dev",
            "please run /multica 9",
            "explain this\n/multica 9",
        )
        for command in commands:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                sandbox = PluginSandbox(Path(directory))
                result, arguments = sandbox.run_hook(
                    {"prompt": command, "session_id": "task-1"}
                )
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertFalse(arguments.exists())

    def test_missing_task_id_fails_closed(self) -> None:
        for command in ("/multica 9", "/multica stop"):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                sandbox = PluginSandbox(Path(directory))
                result, arguments = sandbox.run_hook({"prompt": command})
                self.assertEqual(result.returncode, 0)
                self.assertFalse(arguments.exists())
                self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_nested_supported_payload_fields_are_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sandbox = PluginSandbox(Path(directory))
            result, arguments = sandbox.run_hook(
                {
                    "event": {
                        "content": [{"type": "text", "text": "/multica-88"}],
                        "sessionId": "nested-task",
                    }
                }
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                json.loads(arguments.read_text()),
                ["start", "OPE-88", "--session", "nested-task"],
            )

    def test_empty_and_malformed_hook_inputs_do_not_execute(self) -> None:
        for value in ("", "not-json", "{}", "[]"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                sandbox = PluginSandbox(Path(directory))
                result, arguments = sandbox.run_hook(value)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertFalse(arguments.exists())

    def test_hook_log_is_private_and_never_contains_prompt_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sandbox = PluginSandbox(Path(directory))
            result, _arguments = sandbox.run_hook(
                {
                    "prompt": "/multica-8\nSECRET-PROMPT",
                    "session_id": "task-1",
                    "private": "SECRET-METADATA",
                }
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            log = sandbox.plugin_data / "hook.log"
            self.assertEqual(stat.S_IMODE(log.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(log.parent.stat().st_mode), 0o700)
            content = log.read_text()
            self.assertNotIn("SECRET-PROMPT", content)
            self.assertNotIn("SECRET-METADATA", content)

    def test_status_formatter_shows_only_current_task(self) -> None:
        payload = {
            "plugin_version": "1.1.2",
            "trackers": [
                {
                    "issue": "OPE-1",
                    "session_id": "current-task",
                    "run_id": "run-current",
                    "status": "running",
                    "watcher_alive": True,
                    "usage_totals": {"input_tokens": 1_000_000},
                },
                {
                    "issue": "OPE-2",
                    "session_id": "other-task",
                    "run_id": "run-other",
                    "status": "running",
                },
            ],
        }
        text = prompt_submit.format_status_payload(payload, "current-task")
        self.assertIn("OPE-1", text)
        self.assertNotIn("OPE-2", text)
        self.assertNotIn("other-task", text)

    def test_control_messages_are_not_uploaded(self) -> None:
        class RecordingApi:
            def __init__(self):
                self.requests = []

            def request(self, *args):
                self.requests.append(args)
                return {}

        api = RecordingApi()
        state = {
            "issue_id": "issue-1",
            "run_id": "run-1",
            "last_server_run_status": "running",
            "session_id": "task-1",
        }
        for command in (
            "/multica 4158",
            "/multica status",
            "/multica stop",
            "/multica help",
            "/multica doctor",
        ):
            with self.subTest(command=command):
                entry = {
                    "type": "response_item",
                    "timestamp": "now",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": command}],
                    },
                }
                codex_adapter.post_message(api, state, entry)
        self.assertEqual(api.requests, [])


class PluginFileSafetyTests(unittest.TestCase):
    def test_cli_falls_back_to_codex_managed_plugin_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sandbox = PluginSandbox(Path(directory))
            environment = sandbox.env()
            environment.pop("PLUGIN_DATA")
            expected = (
                sandbox.codex_home
                / "plugins"
                / "data"
                / "multica-codex-sync-multica-agent-sync"
            )

            version = subprocess.run(
                [sys.executable, "-B", str(CLI_ENTRYPOINT), "version"],
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
            )
            self.assertEqual(version.returncode, 0, version.stderr)
            self.assertTrue((expected / ".multica-codex-sync-owned").is_file())

            states = expected / "states"
            states.mkdir()
            (states / "run-test.json").write_text(
                json.dumps({"status": "running", "issue": "OPE-5987"}),
                encoding="utf-8",
            )
            status_result = subprocess.run(
                [sys.executable, "-B", str(CLI_ENTRYPOINT), "status"],
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
            )
            self.assertEqual(status_result.returncode, 0, status_result.stderr)
            payload = json.loads(status_result.stdout)
            self.assertEqual(payload["trackers"][0]["issue"], "OPE-5987")
            self.assertFalse(
                (sandbox.multica_home / "plugin-data" / "multica-codex-sync").exists()
            )

    def test_external_run_ids_are_hashed_before_becoming_paths(self) -> None:
        malicious = "../../outside/secret"
        state_path = core.state_path_for_run(malicious)
        log_path = core.state_log_path({"run_id": malicious})
        self.assertEqual(state_path.parent, core.STATES_DIR)
        self.assertEqual(log_path.parent, core.LOGS_DIR)
        self.assertNotIn("..", state_path.name)
        self.assertNotIn("outside", state_path.name)
        self.assertRegex(state_path.name, r"^run-[0-9a-f]{32}\.json$")
        self.assertRegex(log_path.name, r"^run-[0-9a-f]{32}\.log$")

    def test_atomic_json_and_session_lock_use_private_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "private" / "state.json"
            core.atomic_json(path, {"value": 1})
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)

            locks = root / "locks"
            with mock.patch.object(core, "LOCKS_DIR", locks):
                with core.session_lock("task-id"):
                    lock = next(locks.glob("*.lock"))
                    self.assertEqual(stat.S_IMODE(lock.stat().st_mode), 0o600)

    def test_symlinked_private_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "outside"
            target.mkdir()
            link = root / "plugin-data"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(RuntimeError):
                core.secure_mkdir(link)

    def test_symlinked_plugin_data_root_is_not_followed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sandbox = PluginSandbox(Path(directory))
            external = Path(directory) / "external"
            external.mkdir()
            sandbox.plugin_data.symlink_to(external, target_is_directory=True)

            result = sandbox.run_cli("version")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlinked plugin data directory", result.stderr)
            self.assertEqual(list(external.iterdir()), [])
            self.assertTrue(sandbox.plugin_data.is_symlink())

    def test_process_identity_requires_script_mode_state_and_start_time(self) -> None:
        state_path = Path("/tmp/plugin state/run.json")
        identity = {
            "started": "Mon Jul 20 10:00:00 2026",
            "command": (
                f"/usr/bin/python3 /tmp/multica_codex_track.py watch "
                f"--state '{state_path}'"
            ),
        }
        with mock.patch.object(core, "process_identity", return_value=identity):
            self.assertTrue(
                core.tracker_process_matches(
                    42,
                    mode="watch",
                    expected_identity={"started": identity["started"]},
                    state_path=state_path,
                )
            )
            self.assertFalse(
                core.tracker_process_matches(42, mode="listen", state_path=state_path)
            )
            self.assertFalse(
                core.tracker_process_matches(
                    42,
                    mode="watch",
                    expected_identity={"started": "different"},
                    state_path=state_path,
                )
            )
            self.assertFalse(
                core.tracker_process_matches(
                    42,
                    mode="watch",
                    state_path=Path("/tmp/different.json"),
                )
            )

    def test_api_token_is_not_exposed_in_process_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config.json"
            secret = "TOKEN-MUST-STAY-IN-PRIVATE-CONFIG"
            config.write_text(
                json.dumps({"server_url": "https://multica.test", "token": secret}),
                encoding="utf-8",
            )
            track_home = root / "plugin-data"
            captured_config = None

            def fake_run(command, **_kwargs):
                nonlocal captured_config
                self.assertNotIn(secret, " ".join(command))
                config_path = Path(command[command.index("--config") + 1])
                captured_config = config_path
                self.assertEqual(stat.S_IMODE(config_path.stat().st_mode), 0o600)
                self.assertIn(secret, config_path.read_text(encoding="utf-8"))
                return subprocess.CompletedProcess(command, 0, "{}\n200", "")

            with (
                mock.patch.object(core, "CONFIG_CANDIDATES", [config]),
                mock.patch.object(core, "TRACK_HOME", track_home),
                mock.patch.object(core.subprocess, "run", side_effect=fake_run),
            ):
                response = core.Api().request("GET", "/api/test")
            self.assertEqual(response, {})
            self.assertIsNotNone(captured_config)
            self.assertFalse(captured_config.exists())


class PluginLifecycleTests(unittest.TestCase):
    def test_watcher_detects_removed_plugin_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertFalse(
                codex_adapter.plugin_installation_available({"plugin_root": str(root)})
            )
            manifest = root / ".codex-plugin/plugin.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text("{}\n", encoding="utf-8")
            self.assertTrue(
                codex_adapter.plugin_installation_available({"plugin_root": str(root)})
            )

    def test_doctor_reuses_login_without_printing_token(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sandbox = PluginSandbox(Path(directory))
            sandbox.multica_home.mkdir(parents=True)
            sandbox.codex_home.joinpath("sessions").mkdir(parents=True)
            secret = "TOKEN-MUST-NOT-LEAK"
            sandbox.multica_home.joinpath("config.json").write_text(
                json.dumps({"server_url": "https://multica.test", "token": secret}),
                encoding="utf-8",
            )
            result = sandbox.run_cli("doctor")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn(secret, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["multica_configured"])
            self.assertTrue(payload["plugin_data_private"])
            self.assertEqual(payload["plugin_version"], "1.1.2")

    def test_doctor_fails_cleanly_when_multica_is_not_configured(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = PluginSandbox(Path(directory)).run_cli("doctor")
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["multica_configured"])
            self.assertNotIn("token", result.stdout.lower())

    def test_purge_removes_only_owned_files_and_preserves_unknown_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sandbox = PluginSandbox(Path(directory))
            first = sandbox.run_cli("version")
            self.assertEqual(first.returncode, 0, first.stderr)
            sandbox.plugin_data.joinpath("states").mkdir()
            sandbox.plugin_data.joinpath("states/run-known.json").write_text("{}")
            sandbox.plugin_data.joinpath("logs").mkdir()
            sandbox.plugin_data.joinpath("logs/run-known.log").write_text("owned\n")
            unknown = sandbox.plugin_data / "colleague-notes.txt"
            unknown.write_text("keep me\n", encoding="utf-8")

            result = sandbox.run_cli("cleanup", "--purge")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(unknown.read_text(), "keep me\n")
            self.assertFalse(sandbox.plugin_data.joinpath("states").exists())
            self.assertFalse(sandbox.plugin_data.joinpath("logs").exists())
            self.assertFalse(
                sandbox.plugin_data.joinpath(".multica-codex-sync-owned").exists()
            )
            self.assertIn("Unknown files remain and were preserved", result.stdout)

    def test_purge_preserves_symlinked_known_directory_and_external_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sandbox = PluginSandbox(Path(directory))
            self.assertEqual(sandbox.run_cli("version").returncode, 0)
            external = Path(directory) / "external"
            external.mkdir()
            protected = external / "must-stay.json"
            protected.write_text("keep\n", encoding="utf-8")
            sandbox.plugin_data.joinpath("states").symlink_to(
                external,
                target_is_directory=True,
            )

            result = sandbox.run_cli("cleanup", "--purge")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(protected.read_text(), "keep\n")
            self.assertTrue(sandbox.plugin_data.joinpath("states").is_symlink())
            self.assertIn("Refusing to read symlinked state directory", result.stderr)

    def test_unrecognized_data_marker_blocks_all_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sandbox = PluginSandbox(Path(directory))
            sandbox.plugin_data.mkdir(parents=True)
            marker = sandbox.plugin_data / ".multica-codex-sync-owned"
            marker.write_text("someone-else\n", encoding="utf-8")
            unknown = sandbox.plugin_data / "unknown.txt"
            unknown.write_text("keep\n", encoding="utf-8")

            result = sandbox.run_cli("cleanup", "--purge")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(marker.read_text(), "someone-else\n")
            self.assertEqual(unknown.read_text(), "keep\n")

    def test_stop_refuses_to_kill_an_unrelated_reused_pid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            state = {
                "status": "running",
                "pid": 4242,
                "run_id": "run-1",
                "issue": "OPE-1",
            }

            class FakeApi:
                def request(self, *_args, **_kwargs):
                    return {}

            with (
                mock.patch.object(cli, "tracker_process_matches", return_value=False),
                mock.patch.object(cli, "pid_alive", return_value=True),
                mock.patch.object(cli, "Api", return_value=FakeApi()),
                mock.patch.object(cli.os, "kill") as kill,
            ):
                cli.stop_one(state_path, state)
            kill.assert_not_called()
            saved = json.loads(state_path.read_text())
            self.assertEqual(saved["status"], "stopped")
            self.assertIn("refused to stop unrelated process", saved["local_stop_warning"])

    def test_offline_stop_still_completes_local_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            state = {"status": "running", "run_id": "run-1", "issue": "OPE-1"}
            with (
                mock.patch.object(cli, "tracker_process_matches", return_value=False),
                mock.patch.object(cli, "pid_alive", return_value=False),
                mock.patch.object(cli, "Api", side_effect=RuntimeError("offline")),
            ):
                error = cli.stop_one(state_path, state)
            self.assertEqual(error, "offline")
            saved = json.loads(state_path.read_text())
            self.assertEqual(saved["status"], "stopped")
            self.assertEqual(saved["server_stop_error"], "offline")

    def test_missing_server_run_is_an_idempotent_stop(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            state = {"status": "running", "run_id": "missing", "issue": "OPE-1"}

            class MissingApi:
                def request(self, *_args, **_kwargs):
                    raise core.ApiError("PATCH", "/api/local-runs/missing", "gone", 404)

            with (
                mock.patch.object(cli, "tracker_process_matches", return_value=False),
                mock.patch.object(cli, "pid_alive", return_value=False),
                mock.patch.object(cli, "Api", return_value=MissingApi()),
            ):
                error = cli.stop_one(state_path, state)
            self.assertIsNone(error)
            saved = json.loads(state_path.read_text())
            self.assertEqual(saved["status"], "stopped")
            self.assertEqual(saved["last_server_run_status"], "missing")
            self.assertNotIn("server_stop_error", saved)


if __name__ == "__main__":
    unittest.main()
