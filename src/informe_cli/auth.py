from __future__ import annotations

import os
import subprocess

import httpx
import typer

_transport = None  # tests inject httpx.MockTransport


def base_url() -> str:
    return os.environ.get(
        "INFORME_API_URL", "https://informe-agent.mindlogic.tools"
    ).rstrip("/")


def access_token() -> str:
    try:
        out = subprocess.run(
            ["cloudflared", "access", "token", "-app", base_url()],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as e:
        typer.echo(
            f"no Access token: run `cloudflared access login {base_url()}` ({e})",
            err=True,
        )
        raise typer.Exit(2)
    return out.stdout.strip()


def build_client(timeout: float = 60) -> httpx.Client:
    return httpx.Client(
        base_url=base_url(),
        headers={"cf-access-token": access_token()},
        timeout=timeout,
        transport=_transport,
    )
