from __future__ import annotations

import json as jsonlib

import httpx
import typer

from informe_cli import auth, state
from informe_cli.main import app


@app.command()
def stop(
    session_key: str = typer.Argument(None, help="session key (default: your last session)"),
    json_out: bool = typer.Option(False, "--json"),
):
    """Stop the turn running on a session — the terminal's `/stop`.

    Hits POST /v1/sessions/{key}/abort, the same endpoint the web app's Stop
    button and Slack's `/stop` use. A session holds at most one run, so there
    is nothing finer to name: stopping an idle session is a no-op, not an
    error, matching the endpoint's own idempotence.
    """
    key = session_key or state.load_last_session()
    if not key:
        typer.echo("no session to stop — pass a key (see `inf sessions`)", err=True)
        raise typer.Exit(2)
    with auth.build_client() as client:
        try:
            r = client.post(f"/v1/sessions/{key}/abort")
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (403, 404):
                typer.echo(
                    f"stop failed for {key}: {e.response.status_code} — "
                    "not yours, or it no longer exists",
                    err=True,
                )
            else:
                typer.echo(f"stop failed for {key}: {e}", err=True)
            raise typer.Exit(1)
        stopped = bool(r.json().get("aborted"))
    if json_out:
        typer.echo(jsonlib.dumps({"session_key": key, "stopped": stopped}))
    elif stopped:
        typer.echo(f"stopped the active run on {key}")
    else:
        typer.echo(f"nothing running on {key}")
