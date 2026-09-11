from __future__ import annotations

import json
import time
import os
import sys

import httpx
import typer

from informe_cli import state
from informe_cli.sse import Renderer, parse_sse

MAX_RECONNECTS = 5


def run_turn(
    client: httpx.Client,
    text: str,
    *,
    session_key: str | None = None,
    project: str | None = None,
    attachments: tuple[str, ...] | list[str] = (),
    model: str | None = None,
    json_out: bool = False,
    quiet: bool = False,
) -> dict:
    body: dict = {"text": text, "client": "cli"}
    if session_key:
        body["session_key"] = session_key
    if project:
        body["project"] = project
    if model:
        # Per-turn, same field the web composer's model chip fills. The server
        # picks the matching thinking effort itself (Fable thinks harder).
        body["model"] = model
    if attachments:
        body["attachments"] = list(attachments)
    r = client.post("/v1/turns", json=body)
    if r.status_code == 409:
        typer.echo(f"session busy: {r.json().get('detail')}", err=True)
        busy_key = session_key or state.load_last_session()
        typer.echo(
            f"stop it with: inf stop{' ' + busy_key if busy_key else ''}", err=True
        )
        raise typer.Exit(1)
    r.raise_for_status()
    run_id = r.json()["run_id"]
    key = r.json()["session_key"]
    state.save_last_session(key)

    silent = json_out or quiet
    devnull = open(os.devnull, "w") if silent else None
    renderer = Renderer(
        out=devnull if silent else sys.stdout,
        err=devnull if silent else sys.stderr,
    )
    try:
        _stream(client, run_id, key, renderer)
    finally:
        if devnull is not None:
            devnull.close()

    snap = dict(renderer.snap or {})
    snap["session_key"] = key
    if json_out:
        typer.echo(json.dumps({
            "session_key": key,
            "run_id": run_id,
            "status": snap.get("status"),
            "text": snap.get("result_text") or snap.get("partial") or "",
            "cost_usd": snap.get("cost_usd"),
            "error": snap.get("error"),
        }, ensure_ascii=False))
    elif not quiet:
        sys.stdout.write("\n")
        sys.stdout.flush()
        typer.echo(f"[session {key}]", err=True)
    if snap.get("status") == "error":
        raise typer.Exit(1)
    return snap


def _stream(client: httpx.Client, run_id: str, session_key: str, renderer: Renderer) -> None:
    attempts = 0
    while not renderer.done:
        try:
            with client.stream("GET", f"/v1/runs/{run_id}/events", timeout=None) as resp:
                if resp.status_code == 404:
                    # A 404 right after the 202 is a race or an edge blip, not
                    # a missing run — the server holds runs past completion.
                    attempts += 1
                    if attempts > MAX_RECONNECTS:
                        resp.raise_for_status()
                    time.sleep(1)
                    continue
                resp.raise_for_status()
                for event, data in parse_sse(resp.iter_lines()):
                    renderer.feed(event, data)
                    if renderer.done:
                        return
            # Stream ended without a terminal event (proxy cut) — reconnect.
            attempts += 1
        except (httpx.TransportError, httpx.RemoteProtocolError):
            attempts += 1
        except KeyboardInterrupt:
            _offer_abort(client, session_key)
            raise typer.Exit(130)
        if attempts > MAX_RECONNECTS:
            typer.echo(
                "\nstream lost; the run continues server-side — "
                f"see it with: inf history {session_key}",
                err=True,
            )
            raise typer.Exit(1)


def _offer_abort(client: httpx.Client, session_key: str) -> None:
    if sys.stdin.isatty() and not typer.confirm("\nabort the running turn?", default=False):
        return
    try:
        client.post(f"/v1/sessions/{session_key}/abort")
        typer.echo("aborted", err=True)
    except httpx.HTTPError as e:
        typer.echo(f"abort failed: {e}", err=True)
