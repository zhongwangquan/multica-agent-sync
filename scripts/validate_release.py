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

    for readme in (ROOT / "README.md", ROOT / "README.zh-CN.md"):
        text = readme.read_text(encoding="utf-8")
        require("multica-agent-sync" in text, f"missing public install source in {readme.name}")
        require("/multica status" in text, f"missing command docs in {readme.name}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    require(f"## {version}" in changelog, "release version missing from changelog")
    print(f"release metadata and safety invariants are valid for {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
