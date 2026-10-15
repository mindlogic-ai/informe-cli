import json

import httpx
from typer.testing import CliRunner

from informe_cli import state
from informe_cli.main import app

runner = CliRunner()

OK = {"triggered": True, "success": True, "before": 740_000, "after": 12_000}


def test_compact_explicit_session(mock_api):
    seen = {}

    def handler(req):
        seen["path"] = req.url.path
        return httpx.Response(200, json=OK)

    mock_api[("POST", "/v1/sessions/k1/compact")] = handler
    result = runner.invoke(app, ["compact", "k1"])
    assert result.exit_code == 0
    assert seen["path"] == "/v1/sessions/k1/compact"
    assert "740K → 12K tokens" in result.output


def test_compact_defaults_to_last_session(mock_api):
    state.save_last_session("k9")
    mock_api[("POST", "/v1/sessions/k9/compact")] = lambda req: httpx.Response(200, json=OK)
    result = runner.invoke(app, ["compact"])
    assert result.exit_code == 0
    assert "k9" in result.output


def test_compact_without_any_session(mock_api):
    result = runner.invoke(app, ["compact"])
    assert result.exit_code == 2
    assert "no session to compact" in result.output


def test_compact_json(mock_api):
    mock_api[("POST", "/v1/sessions/k1/compact")] = lambda req: httpx.Response(200, json=OK)
    result = runner.invoke(app, ["compact", "k1", "--json"])
    assert json.loads(result.output) == {
        "session_key": "k1", "compacted": True,
        "before_tokens": 740_000, "after_tokens": 12_000, "error": None,
    }


def test_a_failed_compaction_is_not_reported_as_success(mock_api):
    # It emptied nothing. Saying otherwise sends the next turn into the same
    # full window believing it was cleared.
    mock_api[("POST", "/v1/sessions/k1/compact")] = lambda req: httpx.Response(
        200, json={"triggered": False, "success": False,
                   "error": "no session to compact", "before": 5, "after": 5}
    )
    result = runner.invoke(app, ["compact", "k1"])
    assert result.exit_code == 1
    assert "nothing compacted" in result.output
    assert "no session to compact" in result.output


def test_compact_on_a_busy_session_points_at_stop(mock_api):
    mock_api[("POST", "/v1/sessions/k1/compact")] = lambda req: httpx.Response(
        409, json={"detail": "a turn is still running — stop it before compacting"}
    )
    result = runner.invoke(app, ["compact", "k1"])
    assert result.exit_code == 1
    assert "busy" in result.output
    assert "inf stop k1" in result.output


def test_compact_forbidden_session(mock_api):
    mock_api[("POST", "/v1/sessions/k1/compact")] = lambda req: httpx.Response(
        403, json={"detail": "not yours"}
    )
    result = runner.invoke(app, ["compact", "k1"])
    assert result.exit_code == 1
    assert "compact failed" in result.output


def test_repl_compact_compacts_the_session_you_are_in_and_stays(mock_api, monkeypatch, capsys):
    """`/compact` at the prompt is not a question, and does not end the REPL."""
    calls = []
    mock_api[("POST", "/v1/sessions/k1/compact")] = lambda req: (
        calls.append(req.url.path) or httpx.Response(200, json=OK)
    )
    lines = iter(["/compact", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(lines))
    from informe_cli import auth
    from informe_cli.main import _repl

    with auth.build_client() as c:
        _repl(c, "k1", None, None)
    # No /v1/turns route is registered: "/compact" reaching the server as a
    # question would 404 here.
    assert calls == ["/v1/sessions/k1/compact"]
    assert "740K → 12K tokens" in capsys.readouterr().err


def test_repl_compact_before_the_first_turn_has_nothing_to_do(mock_api, monkeypatch, capsys):
    lines = iter(["/compact", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(lines))
    from informe_cli import auth
    from informe_cli.main import _repl

    with auth.build_client() as c:
        _repl(c, None, None, None)
    assert "nothing to compact yet" in capsys.readouterr().err
