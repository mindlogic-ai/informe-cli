from __future__ import annotations

import json as jsonlib
import pathlib
import stat

import typer

from informe_cli import auth
from informe_cli.main import app

db = typer.Typer(help="Database access for your laptop.")
app.add_typer(db, name="db")

CONFIG_DIR = pathlib.Path.home() / ".config" / "mindlogic"


SKILL_DIR = pathlib.Path.home() / ".claude" / "skills" / "db-access"


def _install_skill() -> None:
    """Drop the db-access skill next to the config.

    `inf setup` only ships the informe-cli skill, so without this a person ends
    up connected but with none of the guidance that stops the common mistakes -
    querying staging thinking it is prod, or reaching for MCP on a 50k-row export.
    Best-effort: failing to fetch it must not fail the setup that already worked.
    """
    try:
        with auth.build_client() as c:
            r = c.get("/v1/skills/db-access")
            r.raise_for_status()
            content = r.json().get("content")
        if not content:
            return
        SKILL_DIR.mkdir(parents=True, exist_ok=True)
        (SKILL_DIR / "SKILL.md").write_text(content)
        typer.echo(f"✓ {SKILL_DIR / 'SKILL.md'}")
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"  (skill not installed: {exc}; run `inf skills db-access` to read it)",
                   err=True)


@db.command("profiles")
def profiles() -> None:
    """Which database sets you can mount."""
    with auth.build_client() as c:
        r = c.get("/v1/db/profiles")
        r.raise_for_status()
        for p in r.json()["profiles"]:
            typer.echo(f"{p['name']:<10} {len(p['sources']):>2}  {' '.join(p['sources'])}")


@db.command("setup")
def setup(
    profile: str = typer.Option("all", "--profile", "-p", help="see `inf db profiles`"),
) -> None:
    """Fetch a ready dbhub config and print the .mcp.json block to paste.

    No password is handed over or stored anywhere you have to protect by hand:
    the credential comes down over your own Access session and lands in a 0600
    file. Re-run this after a rotation and you are current again.
    """
    with auth.build_client() as c:
        r = c.get("/v1/db/config", params={"profile": profile})
        if r.status_code == 404:
            typer.echo(r.json().get("detail", "unknown profile"), err=True)
            raise typer.Exit(2)
        r.raise_for_status()
        body = r.text

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "" if profile == "all" else f"-{profile}"
    cfg = CONFIG_DIR / f"dbhub{suffix}.toml"
    cfg.write_text(body)
    cfg.chmod(stat.S_IRUSR | stat.S_IWUSR)

    name = "mindlogic-db" if profile == "all" else f"db-{profile}"
    block = {
        "mcpServers": {
            name: {
                "command": "npx",
                "args": ["-y", "@bytebase/dbhub", "--transport", "stdio",
                         "--config", str(cfg)],
            }
        }
    }
    (CONFIG_DIR / f"dbhub{suffix}-mcp.json").write_text(
        jsonlib.dumps(block, indent=2) + "\n"
    )

    count = body.count("[[sources]]")
    typer.echo(f"✓ {cfg}  ({count} sources, mode 600)")
    _install_skill()
    typer.echo("\nAdd this to .mcp.json (or ~/.claude/settings.json), then restart:\n")
    typer.echo(jsonlib.dumps(block, indent=2))
