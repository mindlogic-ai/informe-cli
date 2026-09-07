from __future__ import annotations

from pathlib import Path

import httpx
import typer


def upload_local(client: httpx.Client, path: str, session_key: str) -> str:
    p = Path(path)
    if not p.is_file():
        typer.echo(f"not a file: {path}", err=True)
        raise typer.Exit(2)
    with p.open("rb") as fh:
        r = client.post(
            f"/v1/sessions/{session_key}/files",
            files={"file": (p.name, fh)},
        )
    r.raise_for_status()
    return r.json()["id"]


def attach_workspace(client: httpx.Client, scope: str, path: str) -> str:
    r = client.post(f"/v1/workspace/{scope}/attach", json={"path": path})
    r.raise_for_status()
    return r.json()["id"]


import json as jsonlib

from informe_cli import auth
from informe_cli.main import app

files_app = typer.Typer(help="Artifacts produced in / attached to chats.")
ws_app = typer.Typer(help="Your persistent workspace (or a project's with --project).")
app.add_typer(files_app, name="files")
app.add_typer(ws_app, name="ws")


def _save_response(resp: httpx.Response, out: str | None, fallback_name: str) -> Path:
    name = fallback_name
    cd = resp.headers.get("content-disposition", "")
    if 'filename="' in cd:
        name = cd.split('filename="', 1)[1].split('"', 1)[0]
    dest = Path(out) if out else Path(name)
    if dest.is_dir():
        dest = dest / name
    dest.write_bytes(resp.content)
    typer.echo(str(dest))
    return dest


@files_app.command("ls")
def files_ls(limit: int = typer.Option(100, "--limit"),
             json_out: bool = typer.Option(False, "--json")):
    with auth.build_client() as c:
        r = c.get("/v1/files", params={"limit": limit})
        r.raise_for_status()
        data = r.json()
    if json_out:
        typer.echo(jsonlib.dumps(data, ensure_ascii=False, indent=2))
        return
    for f in data.get("files") or []:
        kb = (f.get("size_bytes") or 0) // 1024
        typer.echo(f"{f['id']}  {f['name']}  {kb}KB  {f.get('session_key') or ''}")


@files_app.command("get")
def files_get(artifact_id: str, out: str = typer.Option(None, "-o", "--out")):
    with auth.build_client(timeout=300) as c:
        r = c.get(f"/v1/files/{artifact_id}")
        r.raise_for_status()
        _save_response(r, out, artifact_id)


def _scope(project: str | None) -> str:
    return project or "me"


@ws_app.command("ls")
def ws_ls(path: str = typer.Argument(""),
          project: str = typer.Option(None, "--project"),
          json_out: bool = typer.Option(False, "--json")):
    with auth.build_client() as c:
        r = c.get(f"/v1/workspace/{_scope(project)}/list", params={"path": path})
        r.raise_for_status()
        data = r.json()
    if json_out:
        typer.echo(jsonlib.dumps(data, ensure_ascii=False, indent=2))
        return
    for e in data.get("entries") or []:
        mark = "/" if e.get("dir") else ""
        typer.echo(f"{e['name']}{mark}")


@ws_app.command("put")
def ws_put(local: str, remote_dir: str = typer.Argument(""),
           project: str = typer.Option(None, "--project")):
    p = Path(local)
    if not p.is_file():
        typer.echo(f"not a file: {local}", err=True)
        raise typer.Exit(2)
    with auth.build_client(timeout=300) as c, p.open("rb") as fh:
        r = c.post(f"/v1/workspace/{_scope(project)}/upload",
                   params={"path": remote_dir}, files={"file": (p.name, fh)})
        r.raise_for_status()
    typer.echo(f"{remote_dir + '/' if remote_dir else ''}{p.name}")


@ws_app.command("get")
def ws_get(remote: str, out: str = typer.Option(None, "-o", "--out"),
           project: str = typer.Option(None, "--project")):
    with auth.build_client(timeout=300) as c:
        r = c.get(f"/v1/workspace/{_scope(project)}/file", params={"path": remote})
        r.raise_for_status()
        _save_response(r, out, Path(remote).name)


@ws_app.command("mv")
def ws_mv(from_path: str, to_path: str, project: str = typer.Option(None, "--project")):
    with auth.build_client() as c:
        r = c.post(f"/v1/workspace/{_scope(project)}/move",
                   json={"from": from_path, "to": to_path})
        r.raise_for_status()
    typer.echo(to_path)


@ws_app.command("rm")
def ws_rm(path: str, project: str = typer.Option(None, "--project")):
    with auth.build_client() as c:
        r = c.delete(f"/v1/workspace/{_scope(project)}/file", params={"path": path})
        r.raise_for_status()
    typer.echo(f"deleted {path}")
