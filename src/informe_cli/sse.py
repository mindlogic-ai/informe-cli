from __future__ import annotations

import json
import sys
from collections.abc import Iterable, Iterator

TERMINAL = ("done", "error", "aborted")


def parse_sse(lines: Iterable[str]) -> Iterator[tuple[str, dict]]:
    event, data = None, []
    for line in lines:
        line = line.rstrip("\n")
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            event = line[6:].strip()
        elif line.startswith("data:"):
            data.append(line[5:].strip())
        elif not line:
            if event and data:
                yield event, json.loads("\n".join(data))
            event, data = None, []
    if event and data:
        yield event, json.loads("\n".join(data))


class Renderer:
    """Applies snapshot/append/done events and prints only what is new.

    Text goes to `out`, tool activity to `err` — stdout stays pipeable.
    Reconnects are safe: a re-sent full snapshot prints nothing already shown.
    """

    def __init__(self, out=None, err=None):
        self.out = out or sys.stdout
        self.err = err or sys.stderr
        self.snap: dict | None = None
        self.shown = ""
        self.activity_seen = 0
        self.done = False

    def _print_text(self, text: str) -> None:
        if not text:
            return
        if text.startswith(self.shown):
            delta = text[len(self.shown):]
            self.shown = text
        elif self.shown.startswith(text):
            delta = ""
        else:
            delta = ("\n" if self.shown else "") + text
            self.shown = text
        if delta:
            self.out.write(delta)
            self.out.flush()

    def _print_activity(self, activity: list[dict]) -> None:
        for a in activity[self.activity_seen:]:
            arg = f" {a['arg']}" if a.get("arg") else ""
            self.err.write(f"· {a.get('detail') or a.get('kind')}{arg}\n")
            self.err.flush()
        self.activity_seen = max(self.activity_seen, len(activity))

    def feed(self, event: str, data: dict) -> None:
        if event == "append":
            self.snap = dict(self.snap or {})
            self.snap["partial"] = (self.snap.get("partial") or "") + data["append"]
            self._print_text(self.snap["partial"])
            return
        self.snap = data
        self._print_activity(data.get("activity") or [])
        self._print_text(data.get("partial") or "")
        if data.get("status") in TERMINAL:
            final = data.get("result_text")
            if final:
                self._print_text(final)
            self.done = True
