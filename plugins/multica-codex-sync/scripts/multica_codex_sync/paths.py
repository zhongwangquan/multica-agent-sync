from __future__ import annotations

import os
from pathlib import Path


PLUGIN_DATA_DIRECTORY = "multica-codex-sync-multica-agent-sync"


def resolve_plugin_data() -> Path:
    """Resolve Codex-managed plugin data even outside a Hook environment."""
    home = Path.home()
    codex_home = Path(os.environ.get("CODEX_HOME", home / ".codex")).expanduser()
    return Path(
        os.environ.get(
            "PLUGIN_DATA",
            codex_home / "plugins" / "data" / PLUGIN_DATA_DIRECTORY,
        )
    ).expanduser().absolute()
