from __future__ import annotations

import os
import shutil
from pathlib import Path

import typer

from informe_cli import auth
from informe_cli.main import app


def skill_source() -> Path:
    packaged = Path(__file__).resolve().parent / "skill" / "SKILL.md"
    if packaged.is_file():
        return packaged
    # Running from the repo: cli/src/informe_cli/ → cli/skill/SKILL.md
    return Path(__file__).resolve().parents[2] / "skill" / "SKILL.md"


def _skills_dir() -> Path:
    override = os.environ.get("CLAUDE_SKILLS_DIR")
    return Path(override) if override else Path.home() / ".claude" / "skills"


@app.command()
def setup():
    """One-time onboarding: check cloudflared, install the Claude Code skill."""
    if shutil.which("cloudflared"):
        typer.echo("✓ cloudflared found")
    else:
        typer.echo("✗ cloudflared missing — install and log in:")
        typer.echo("    brew install cloudflared")
        typer.echo(f"    cloudflared access login {auth.base_url()}")
    src = skill_source()
    if src.is_file():
        dest = _skills_dir() / "informe-cli"
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest / "SKILL.md")
        typer.echo(f"✓ Claude Code skill installed → {dest / 'SKILL.md'}")
    else:
        typer.echo(f"✗ skill source missing at {src} — copy it from the repo: cli/skill/SKILL.md")
    typer.echo("upgrade later:  uv tool upgrade informe-cli && inf setup")
    typer.echo('try:  inf "안녕"   then  inf open')
