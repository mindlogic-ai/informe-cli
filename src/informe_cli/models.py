"""Model selection for a turn — the CLI's counterpart of the web composer's
model chip and Slack's sticky `/fable`.

The server (`POST /v1/turns`) already takes a per-turn `model`; only the CLI
had no way to send one. Aliases are the words people type ("fable", "opus"),
resolved to the id Slack's sticky `/fable` sends (Fable 5.1, 1M context) so
the terminal and the thread switch land on the same model.
`opus` resolves to None on purpose: the server default *is* Opus, and sending
no override keeps whatever context-window variant the server is configured
with, exactly like Slack's `/opus` ("back to default").
"""
from __future__ import annotations

import re

FABLE = "claude-fable-5-1[1m]"  # same id as Slack's /fable

# alias → model id sent as `model`; None means "server default".
MODEL_ALIASES: dict[str, str | None] = {
    "fable": FABLE,
    "fable5": FABLE,
    "fable5.1": FABLE,
    "fable-5": FABLE,
    "fable-5.1": FABLE,
    "opus": None,
    "opus5": None,
    "auto": None,
    "default": None,
}


def resolve_model(name: str | None) -> str | None:
    """`--model fable` → "claude-fable-5-1[1m]"; a full `claude-*` id passes through."""
    if name is None:
        return None
    key = name.strip().lower()
    if not key:
        return None
    if key in MODEL_ALIASES:
        return MODEL_ALIASES[key]
    if key.startswith("claude-"):
        return name.strip()
    raise ValueError(f"unknown model {name!r} — use fable, opus, auto, or a full claude-* id")


_CMD_RE = re.compile(r"^/(fable(?:[- ]?5(?:\.1)?)?|opus(?:[- ]?5)?|model)$", re.I)


def parse_model_command(line: str) -> tuple[bool, str | None, bool]:
    """REPL line → (is_command, model, show_only).

    Whole-line only, like the web app's `/stop` and `/compact`: "/fable" is a
    command, "/fable 왜 이래" is a question. `/model` just reports the current
    choice (show_only=True).
    """
    m = _CMD_RE.match(line.strip())
    if not m:
        return False, None, False
    word = m.group(1).lower()
    if word == "model":
        return True, None, True
    return True, (FABLE if word.startswith("fable") else None), False


def label(model: str | None) -> str:
    return "Fable 5.1" if model and model.startswith("claude-fable") else "Opus 5 (server default)"
