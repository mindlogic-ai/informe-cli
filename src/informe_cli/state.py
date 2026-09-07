from __future__ import annotations

import os
from pathlib import Path


def _state_dir() -> Path:
    root = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
    return Path(root) / "informe"


def load_last_session() -> str | None:
    f = _state_dir() / "last_session"
    try:
        return f.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def save_last_session(key: str) -> None:
    d = _state_dir()
    d.mkdir(parents=True, exist_ok=True)
    (d / "last_session").write_text(key, encoding="utf-8")
