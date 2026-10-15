"""Model selection for a turn — the CLI's counterpart of the web composer's
model chip and Slack's sticky `/fable`.

`POST /v1/turns` takes a per-turn `model`, and the server pins whatever is sent
to the conversation (the same store Slack's `/fable` writes), so a later turn
that sends nothing — `inf -c`, another surface — stays on it. Aliases are the
words people type, resolved to the ids the server lists.
`opus` resolves to the bare family id "claude-opus", which the server maps to
whatever its default Opus is. It must be sent rather than omitted: omitting
leaves the chat's pin in place, so `/fable` then `/opus` would stay on Fable.
"""
from __future__ import annotations

import re

FABLE = "claude-fable-5-1[1m]"  # same id as Slack's /fable
SONNET = "claude-sonnet-5[1m]"  # same id as Slack's /sonnet
OPUS = "claude-opus"  # the server's default Opus, whichever it is

# alias → model id sent as `model`.
MODEL_ALIASES: dict[str, str] = {
    "fable": FABLE,
    "fable5": FABLE,
    "fable5.1": FABLE,
    "fable-5": FABLE,
    "fable-5.1": FABLE,
    "sonnet": SONNET,
    "sonnet5": SONNET,
    "sonnet-5": SONNET,
    "opus": OPUS,
    "opus5": OPUS,
    "opus5.5": OPUS,
    "opus-5.5": OPUS,
    "auto": OPUS,
    "default": OPUS,
}


def resolve_model(name: str | None) -> str | None:
    """`--model fable` → "claude-fable-5-1[1m]"; a full `claude-*` id passes through.

    None (no flag) sends nothing, so the chat keeps whatever it is pinned to.
    """
    if name is None:
        return None
    key = name.strip().lower()
    if not key:
        return None
    if key in MODEL_ALIASES:
        return MODEL_ALIASES[key]
    if key.startswith("claude-"):
        return name.strip()
    raise ValueError(f"unknown model {name!r} — use opus, fable, sonnet, or a full claude-* id")


_CMD_RE = re.compile(
    r"^/(fable(?:[- ]?5(?:\.1)?)?|sonnet(?:[- ]?5)?|opus(?:[- ]?5(?:\.5)?)?|model)$", re.I
)


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
    if word.startswith("fable"):
        return True, FABLE, False
    if word.startswith("sonnet"):
        return True, SONNET, False
    return True, OPUS, False


def label(model: str | None) -> str:
    if not model:
        return "this chat's model (default: Opus)"
    if model == OPUS:
        return "Opus (server default)"
    m = re.match(r"claude-([a-z]+)((?:-\d{1,2})+)", model)
    if not m:
        return model
    return f"{m.group(1).capitalize()} {'.'.join(m.group(2)[1:].split('-'))}"
