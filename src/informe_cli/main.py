from __future__ import annotations

import os
import sys
import urllib.parse
import webbrowser

import typer
from typer.core import TyperGroup

from informe_cli import auth, chat, state

_PASSTHROUGH = {"--help", "-h", "--install-completion", "--show-completion"}


class DefaultChatGroup(TyperGroup):
    """`inf <anything that isn't a subcommand>` is a chat message."""

    def parse_args(self, ctx, args):
        if args and args[0] not in self.commands and args[0] not in _PASSTHROUGH:
            args = ["chat", *args]
        return super().parse_args(ctx, args)


app = typer.Typer(
    cls=DefaultChatGroup,
    help='Informe in your terminal. `inf "question"` asks; `inf` opens a REPL; '
         "subcommands read what the web app shows.",
    invoke_without_command=True,
    no_args_is_help=False,
)


@app.callback()
def cli(ctx: typer.Context):
    if ctx.invoked_subcommand is not None:
        return
    if not sys.stdin.isatty():
        typer.echo("no question given and stdin is not a terminal", err=True)
        raise typer.Exit(2)
    with auth.build_client() as client:
        _repl(client, None, None)


@app.command("chat", hidden=True)
def chat_cmd(
    question: list[str] = typer.Argument(None, help="what to ask"),
    continue_: bool = typer.Option(False, "-c", "--continue", help="continue your last session"),
    session: str = typer.Option(None, "--session", help="continue a specific session key"),
    project: str = typer.Option(None, "--project", help="start/continue in a project scope"),
    plain: bool = typer.Option(False, "-p", "--print", help="non-interactive one-shot (for scripts)"),
    json_out: bool = typer.Option(False, "--json", help="emit a JSON summary instead of streaming"),
    attach: list[str] = typer.Option(None, "--attach", help="local file to attach (repeatable)"),
    attach_ws: list[str] = typer.Option(None, "--attach-ws", help="workspace path to attach (repeatable)"),
):
    """Ask Informe (the default when no subcommand matches)."""
    key = session or (state.load_last_session() if continue_ else None)
    if continue_ and not key:
        typer.echo("no last session — ask something first", err=True)
        raise typer.Exit(2)
    text = " ".join(question or []).strip()
    with auth.build_client() as client:
        ids = _resolve_attachments(client, key, attach or [], attach_ws or [], project)
        if text:
            chat.run_turn(
                client, text, session_key=key, project=project,
                attachments=ids, json_out=json_out,
            )
            return
        if plain or not sys.stdin.isatty():
            typer.echo("no question given and stdin is not a terminal", err=True)
            raise typer.Exit(2)
        _repl(client, key, project)


def _resolve_attachments(client, session_key, attach, attach_ws, project) -> list[str]:
    if not attach and not attach_ws:
        return []
    from informe_cli import files_ws  # imported here: files_ws imports this module

    ids: list[str] = []
    for path in attach:
        ids.append(files_ws.upload_local(client, path, session_key or "new"))
    scope = project or "me"
    for wpath in attach_ws:
        ids.append(files_ws.attach_workspace(client, scope, wpath))
    return ids


def _repl(client, key: str | None, project: str | None) -> None:
    typer.echo("Informe REPL — empty line or Ctrl-D to leave.", err=True)
    while True:
        try:
            line = input("inf> ").strip()
        except (EOFError, KeyboardInterrupt):
            typer.echo("", err=True)
            return
        if not line or line in ("exit", "quit"):
            return
        snap = chat.run_turn(client, line, session_key=key, project=project)
        key = snap["session_key"]


@app.command("open")
def open_session(session: str = typer.Argument(None, help="session key (default: last)")):
    """Open a session in the web app."""
    key = session or state.load_last_session()
    if not key:
        typer.echo("no session to open", err=True)
        raise typer.Exit(2)
    url = f"{auth.base_url()}/chats/{urllib.parse.quote(key, safe='')}"
    typer.echo(url)
    if not os.environ.get("INFORME_NO_BROWSER"):
        webbrowser.open(url)


# Subcommand modules register themselves on import.
from informe_cli import reads as _reads  # noqa: E402,F401
from informe_cli import files_ws as _files_ws  # noqa: E402,F401
from informe_cli import setup_cmd as _setup_cmd  # noqa: E402,F401
from informe_cli import db_cmd as _db_cmd  # noqa: E402,F401
from informe_cli import stop_cmd as _stop_cmd  # noqa: E402,F401
