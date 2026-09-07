import json

import httpx
from typer.testing import CliRunner

from informe_cli import state
from informe_cli.main import app

runner = CliRunner()


def test_stop_explicit_session(mock_api):
    seen = {}

    def handler(req):
        seen["path"] = req.url.path
        return httpx.Response(200, json={"aborted": True})

    mock_api[("POST", "/v1/sessions/k1/abort")] = handler
    result = runner.invoke(app, ["stop", "k1"])
    assert result.exit_code == 0
    assert seen["path"] == "/v1/sessions/k1/abort"
    assert "stopped" in result.output


def test_stop_defaults_to_last_session(mock_api):
    state.save_last_session("k9")
    mock_api[("POST", "/v1/sessions/k9/abort")] = lambda req: httpx.Response(
        200, json={"aborted": True}
    )
    result = runner.invoke(app, ["stop"])
    assert result.exit_code == 0
    assert "k9" in result.output


def test_stop_without_any_session(mock_api):
    result = runner.invoke(app, ["stop"])
    assert result.exit_code == 2
    assert "no session to stop" in result.output


def test_stop_idle_session_is_not_an_error(mock_api):
    mock_api[("POST", "/v1/sessions/k1/abort")] = lambda req: httpx.Response(
        200, json={"aborted": False}
    )
    result = runner.invoke(app, ["stop", "k1", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.output) == {"session_key": "k1", "stopped": False}


def test_stop_forbidden_session(mock_api):
    mock_api[("POST", "/v1/sessions/k1/abort")] = lambda req: httpx.Response(
        403, json={"detail": "not yours"}
    )
    result = runner.invoke(app, ["stop", "k1"])
    assert result.exit_code == 1
    assert "stop failed" in result.output
