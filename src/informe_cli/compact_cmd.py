from __future__ import annotations

import json as jsonlib

import httpx
import typer

from informe_cli import auth, context, state
from informe_cli.main import app

# Compaction summarizes the whole transcript with a model call, on a session
# that may first have to be resumed from disk. The 60s default client timeout
# is a turn's timeout, not this one's, and expiring here would leave the CLI
# reporting failure for work the server goes on to finish.
COMPACT_TIMEOUT = 600.0


@app.command()
def compact(
    session_key: str = typer.Argument(None, help="session key (default: your last session)"),
    json_out: bool = typer.Option(False, "--json"),
):
    """Summarize this session's context now — the terminal's `/compact`.

    Hits POST /v1/sessions/{key}/compact, the same endpoint the web app's
    button and Slack's `/compact` use, so all three surfaces compact the same
    way. The session key does not change: the point is to keep the thread —
    its file paths, its rules, where you had got to — while dropping the bulk
    the model no longer needs. Starting a fresh session is what this replaces.

    Refused with 409 while a turn is in flight, for the same reason POST
    /v1/turns is: compaction runs its own query on the session's stream, and
    interleaving that with a live turn is a known class of bug. Stop the turn
    first (`inf stop`).
    """
    key = session_key or state.load_last_session()
    if not key:
        typer.echo("no session to compact — pass a key (see `inf sessions`)", err=True)
        raise typer.Exit(2)
    with auth.build_client(timeout=COMPACT_TIMEOUT) as client:
        out = _post(client, key)
    if out is None:
        raise typer.Exit(1)

    ok = bool(out.get("success") and out.get("triggered"))
    before, after = out.get("before"), out.get("after")
    if json_out:
        typer.echo(jsonlib.dumps({
            "session_key": key,
            "compacted": ok,
            "before_tokens": before,
            "after_tokens": after,
            "error": out.get("error"),
        }, ensure_ascii=False))
    elif ok:
        typer.echo(
            f"compacted {key}: {context.short(before)} → {context.short(after)} tokens"
        )
    else:
        # A failed compaction emptied nothing, and saying otherwise would send
        # the next turn into the same full window believing it was cleared.
        typer.echo(
            f"nothing compacted on {key}"
            + (f": {out['error']}" if out.get("error") else ""),
            err=True,
        )
    if not ok:
        raise typer.Exit(1)


def _post(client: httpx.Client, key: str) -> dict | None:
    """The request itself. None when it failed, after saying why."""
    try:
        # Per-request: a REPL's client is built with a turn's timeout, and this
        # one call is allowed to take much longer than a turn.
        r = client.post(f"/v1/sessions/{key}/compact", timeout=COMPACT_TIMEOUT)
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        if code == 409:
            typer.echo(
                f"{key} is busy — a turn is still running. "
                f"stop it first: inf stop {key}",
                err=True,
            )
        elif code in (403, 404):
            typer.echo(
                f"compact failed for {key}: {code} — not yours, or it no longer exists",
                err=True,
            )
        else:
            typer.echo(f"compact failed for {key}: {e}", err=True)
        return None
    except httpx.HTTPError as e:
        typer.echo(f"compact failed for {key}: {e}", err=True)
        return None
    return r.json()


def compact_in_repl(client: httpx.Client, key: str) -> None:
    """`/compact` typed at the `inf>` prompt. Reports, never exits the REPL.

    The session key is unchanged, so the loop keeps going against the same
    session — which is the whole point of compacting instead of starting over.
    """
    typer.echo("compacting…", err=True)
    out = _post(client, key)
    if out is None:
        return
    if out.get("success") and out.get("triggered"):
        typer.echo(
            f"compacted: {context.short(out.get('before'))} → "
            f"{context.short(out.get('after'))} tokens",
            err=True,
        )
    else:
        typer.echo(
            "nothing compacted" + (f": {out['error']}" if out.get("error") else ""),
            err=True,
        )
