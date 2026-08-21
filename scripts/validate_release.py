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
    require(manifest.get("skills") == "./skills/", "unexpected plugin skills path")
    skill_root = PLUGIN / "skills" / "control"
    bundled_skills = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
    require(
        bundled_skills == [skill_root / "SKILL.md"],
        "plugin must bundle only the Multica control Skill",
    )
    require(
        (skill_root / "agents" / "openai.yaml").is_file(),
        "Multica control Skill is missing UI metadata",
    )
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
        require("Multica Agent" in text, f"missing optional Skill picker docs in {readme.name}")
        require(
            default_marketplace_command in lines,
            f"default install must omit --ref in {readme.name}",
        )
        require(
            f"--ref {release_tag}" in text,
            f"missing optional exact-tag install for {release_tag} in {readme.name}",
        )
        require("`main`" in text, f"missing stable channel in {readme.name}")
        require("`develop`" not in text, f"unexpected develop channel in {readme.name}")
        command_labels = (
            ("# Step 1 of 2:", "# Required:", "# Optional:")
            if readme.name == "README.md"
            else ("# 第 1/2 步：", "# 必做：", "# 可选：")
        )
        for label in command_labels:
            require(label in text, f"missing command annotation {label} in {readme.name}")

    for markdown_path in ROOT.rglob("*.md"):
        markdown = markdown_path.read_text(encoding="utf-8")
        require(
            "$multica-codex-sync:control" not in markdown,
            f"internal Skill invocation leaked into {markdown_path.relative_to(ROOT)}",
        )
        require(
            "wujie" not in markdown.lower(),
            f"provider-specific fallback leaked into {markdown_path.relative_to(ROOT)}",
        )

    channels = (ROOT / "docs" / "release-channels.md").read_text(encoding="utf-8")
    for expected in (
        "`vX.Y.Z`",
        "`main`",
        f"--ref {release_tag}",
        default_marketplace_command,
        "# Step 1 of 2:",
        "# Step 1 of 4:",
    ):
        require(expected in channels, f"release channels missing {expected}")
    require("`develop`" not in channels, "release channels still mention develop")

    for policy_file in (ROOT / "CONTRIBUTING.md", ROOT / "RELEASING.md"):
        policy = policy_file.read_text(encoding="utf-8")
        require("`main`" in policy, f"missing main branch policy in {policy_file.name}")
        require("`develop`" not in policy, f"unexpected develop branch in {policy_file.name}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    require(f"## {version}" in changelog, "release version missing from changelog")
    print(f"release metadata and safety invariants are valid for {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
