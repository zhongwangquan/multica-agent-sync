#!/usr/bin/env python3
"""Validate cross-file release metadata and high-risk repository invariants."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "multica-codex-sync"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"release validation failed: {message}")


def main() -> int:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    require(bool(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version)), "invalid VERSION")

    manifest = json.loads(
        (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    marketplace = json.loads(
        (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
    )
    require(manifest.get("version") == version, "manifest and VERSION differ")
    require(manifest.get("name") == "multica-codex-sync", "unexpected plugin name")
    require("skills" not in manifest, "runtime controls must not be bundled Skills")
    require(not (PLUGIN / "skills").exists(), "runtime Skill directory must be absent")
    require(marketplace.get("name") == "multica-agent-sync", "unexpected marketplace name")
    require(len(marketplace.get("plugins", [])) == 1, "marketplace must expose one plugin")
    require(
        marketplace["plugins"][0].get("name") == manifest["name"],
        "marketplace and manifest plugin names differ",
    )

    runtime = "\n".join(
        path.read_text(encoding="utf-8")
        for path in PLUGIN.rglob("*")
        if path.is_file() and "tests" not in path.parts and path.suffix in {".py", ".json"}
    )
    for forbidden in (
        "49.235.34.145",
        "BRIDGE_RELEASE_BASE_URL",
        "listener_loop",
        ".codex/hooks.json",
        "multica.real",
        "shutil.rmtree",
        "/Users/jason",
    ):
        require(forbidden not in runtime, f"forbidden runtime text: {forbidden}")

    release_tag = f"v{version}"
    default_marketplace_command = (
        "codex plugin marketplace add zhongwangquan/multica-agent-sync"
    )
    for readme in (ROOT / "README.md", ROOT / "README.zh-CN.md"):
        text = readme.read_text(encoding="utf-8")
        lines = text.splitlines()
        require("multica-agent-sync" in text, f"missing public install source in {readme.name}")
        require("/multica status" in text, f"missing command docs in {readme.name}")
        require(
            default_marketplace_command in lines,
            f"default install must omit --ref in {readme.name}",
        )
        require(
            f"--ref {release_tag}" in text,
            f"missing optional exact-tag install for {release_tag} in {readme.name}",
        )
        require("`main`" in text, f"missing stable channel in {readme.name}")
        require("`develop`" in text, f"missing test channel in {readme.name}")
        command_labels = (
            ("# Step 1 of 2:", "# Required:", "# Optional:")
            if readme.name == "README.md"
            else ("# 第 1/2 步：", "# 必做：", "# 可选：")
        )
        for label in command_labels:
            require(label in text, f"missing command annotation {label} in {readme.name}")

    channels = (ROOT / "docs" / "release-channels.md").read_text(encoding="utf-8")
    for expected in (
        "`vX.Y.Z`",
        "`main`",
        "`develop`",
        f"--ref {release_tag}",
        default_marketplace_command,
        "# Step 1 of 2:",
        "# Step 1 of 4:",
    ):
        require(expected in channels, f"release channels missing {expected}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    require(f"## {version}" in changelog, "release version missing from changelog")
    print(f"release metadata and safety invariants are valid for {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
