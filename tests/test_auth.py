import subprocess

import httpx
import typer
import pytest

from informe_cli import auth


def test_base_url_default(monkeypatch):
    monkeypatch.delenv("INFORME_API_URL", raising=False)
    assert auth.base_url() == "https://informe-agent.mindlogic.tools"


def test_base_url_env_override_strips_slash(monkeypatch):
    monkeypatch.setenv("INFORME_API_URL", "http://127.0.0.1:8300/")
    assert auth.base_url() == "http://127.0.0.1:8300"


def test_access_token_calls_cloudflared(monkeypatch):
    calls = {}

    def fake_run(cmd, capture_output, text, check):
        calls["cmd"] = cmd

        class R:
            stdout = "tok-123\n"

        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert auth.access_token() == "tok-123"
    assert calls["cmd"][:3] == ["cloudflared", "access", "token"]


def test_access_token_failure_exits_with_hint(monkeypatch, capsys):
    def fake_run(*a, **k):
        raise FileNotFoundError("no cloudflared")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(typer.Exit) as exc:
        auth.access_token()
    assert exc.value.exit_code == 2
    assert "cloudflared access login" in capsys.readouterr().err


def test_build_client_uses_transport_and_header(monkeypatch):
    monkeypatch.setattr(auth, "access_token", lambda: "tok-abc")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("cf-access-token")
        return httpx.Response(200, json={"ok": True})

    auth._transport = httpx.MockTransport(handler)
    try:
        with auth.build_client() as c:
            r = c.get("/health")
        assert r.status_code == 200
        assert seen["auth"] == "tok-abc"
    finally:
        auth._transport = None
