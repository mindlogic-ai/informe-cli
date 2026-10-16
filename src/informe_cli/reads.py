from __future__ import annotations

import json as jsonlib

import typer

from informe_cli import auth, context
from informe_cli.main import app


def _emit(data, json_out: bool, human) -> None:
    if json_out:
        typer.echo(jsonlib.dumps(data, ensure_ascii=False, indent=2))
    else:
        human(data)


def _get(endpoint: str, **params) -> dict | list:
    with auth.build_client() as c:
        r = c.get(endpoint, params={k: v for k, v in params.items() if v is not None})
        r.raise_for_status()
        return r.json()


@app.command()
def whoami(json_out: bool = typer.Option(False, "--json")):
    """Who the API thinks you are."""
    data = _get("/v1/me")

    def human(d):
        admin = " (admin)" if d.get("is_admin") else ""
        typer.echo(f"{d['email']}{admin}")
        for p in d.get("projects") or []:
            typer.echo(f"  project: {p.get('id')}  {p.get('name', '')}")

    _emit(data, json_out, human)


@app.command()
def sessions(
    search: str = typer.Option(None, "--search", help="full-text search your turns"),
    limit: int = typer.Option(20, "--limit"),
    json_out: bool = typer.Option(False, "--json"),
):
    """Your sessions, newest first — same list as the web sidebar."""
    if search:
        data = _get("/v1/sessions/search", q=search, limit=limit)

        def human(d):
            for r in d.get("results") or []:
                typer.echo(f"{r['session_key']}  {r.get('title') or ''}")
                typer.echo(f"    {r.get('snippet') or ''}")

        _emit(data, json_out, human)
        return
    # include_context is opt-in server-side: the web sidebar polls this endpoint
    # every 6-30s and does not want the field. One `inf sessions` is not a poll.
    data = _get("/v1/sessions", limit=limit, include_context=True)
    # The listing reports context per row and the two limits once, so the
    # per-row block is assembled against the shared limits here.
    limits = {k: data.get(k) for k in ("context_window", "context_compact_at")}
    for row in data.get("sessions") or []:
        row["context"] = context.block({**limits, **row})

    def human(d):
        for s in d.get("sessions") or []:
            run = "▶" if s.get("running") else " "
            cost = f" ${s['cost_usd']:.2f}" if s.get("cost_usd") else ""
            ctx = context.brief(s.get("context"))
            typer.echo(f"{run} {s['session_key']}  {s.get('title') or ''}  "
                       f"({s.get('turns') or 0} turns{cost}"
                       f"{', ' + ctx if ctx else ''})")

    _emit(data, json_out, human)


@app.command()
def history(session_key: str, json_out: bool = typer.Option(False, "--json")):
    """Full turn history of one session, and how full its context window is."""
    data = _get(f"/v1/sessions/{session_key}/history")
    # The endpoint already carries the three raw fields; normalising them into
    # the same `context` object `inf -p --json` emits means one shape to parse.
    data["context"] = context.block(data)

    def human(d):
        for t in d.get("turns") or []:
            typer.echo(f"you: {t.get('question') or ''}")
            typer.echo(f"informe: {t.get('answer') or ''}\n")
        ctx_line = context.line(d.get("context"))
        if ctx_line:
            typer.echo(ctx_line, err=True)

    _emit(data, json_out, human)


def _install_skill(name: str, data: dict) -> None:
    """SKILL.md plus the text files the API ships beside it (references/…).

    Paths come from the server, so each one must stay inside the skill dir.
    """
    from informe_cli.setup_cmd import _skills_dir

    dest = (_skills_dir() / name).resolve()
    content = data.get("content") or ""
    if not content.startswith("---"):
        # personal skills come back as a bare body; give Claude Code its frontmatter
        desc = (data.get("description") or "").replace("\n", " ")
        content = f"---\nname: {name}\ndescription: {desc}\n---\n\n{content}"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "SKILL.md").write_text(content, encoding="utf-8")
    written = ["SKILL.md"]
    for rel, text in sorted((data.get("files") or {}).items()):
        target = (dest / rel).resolve()
        if not target.is_relative_to(dest):
            typer.echo(f"  skipped {rel} (outside the skill dir)", err=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        written.append(rel)
    typer.echo(f"✓ {dest}  ({', '.join(written)})")


@app.command()
def skills(
    name: str = typer.Argument(None),
    mine: bool = typer.Option(False, "--mine", help="your personal skills"),
    install: bool = typer.Option(
        False, "--install",
        help="write NAME (SKILL.md + references/) into ~/.claude/skills/NAME/"),
    json_out: bool = typer.Option(False, "--json"),
):
    """Shared (or --mine personal) skills; give a NAME for its full SKILL.md."""
    if install and not name:
        raise typer.BadParameter("--install needs a skill NAME")
    if name:
        data = _get(f"/v1/my/skills/{name}" if mine else f"/v1/skills/{name}")
        if install:
            _install_skill(name, data)
            return
        _emit(data, json_out,
              lambda d: typer.echo(d.get("content") or jsonlib.dumps(d, ensure_ascii=False)))
        return
    data = _get("/v1/my/skills" if mine else "/v1/skills")

    def human(d):
        for s in d.get("skills") or []:
            n = s.get("name") if isinstance(s, dict) else str(s)
            desc = s.get("description", "") if isinstance(s, dict) else ""
            typer.echo(f"{n}  {desc}")

    _emit(data, json_out, human)


memory_app = typer.Typer(help="Org memory (read-only).", invoke_without_command=True)
app.add_typer(memory_app, name="memory")


@memory_app.callback()
def memory_index(ctx: typer.Context, json_out: bool = typer.Option(False, "--json")):
    if ctx.invoked_subcommand is not None:
        return
    data = _get("/v1/memory")

    def human(d):
        for f in d.get("files") or []:
            typer.echo(f.get("path") if isinstance(f, dict) else str(f))

    _emit(data, json_out, human)


@memory_app.command("show")
def memory_show(path: str, json_out: bool = typer.Option(False, "--json")):
    data = _get("/v1/memory/file", path=path)
    _emit(data, json_out, lambda d: typer.echo(d.get("content") or ""))


@app.command()
def usage(json_out: bool = typer.Option(False, "--json")):
    """Your own spend this month."""
    data = _get("/v1/usage/me")

    def human(d):
        b = d.get("budget") or {}
        ceiling = f" (ceiling ${b['ceiling_usd']})" if b.get("ceiling_usd") else ""
        typer.echo(f"{d.get('email')}: ${d.get('cost_usd', 0):.2f} this month{ceiling}")

    _emit(data, json_out, human)


@app.command()
def projects(json_out: bool = typer.Option(False, "--json")):
    """Projects you belong to."""
    data = _get("/v1/projects")
    rows = data.get("projects", data) if isinstance(data, dict) else data

    def human(_):
        for p in rows or []:
            typer.echo(f"{p.get('id')}  {p.get('name', '')}")

    _emit(rows, json_out, human)


@app.command()
def crons(json_out: bool = typer.Option(False, "--json")):
    """Your schedules."""
    data = _get("/v1/my/crons")

    def human(d):
        for c in d.get("crons") or []:
            on = "on " if c.get("enabled") else "off"
            typer.echo(f"[{on}] {c.get('schedule', '')}  {c.get('name') or c.get('id')}")

    _emit(data, json_out, human)
