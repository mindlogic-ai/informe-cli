import json

import httpx

from informe_cli import auth, chat
from conftest import RUN, sse_body


def test_run_turn_streams_and_returns_final(mock_api, capsys):
    done = dict(RUN, status="done", partial="hello", result_text="hello", cost_usd=0.02)
    mock_api[("POST", "/v1/turns")] = lambda req: httpx.Response(
        202, json={"run_id": "r1", "session_key": "web:u@x:1"}
    )
    mock_api[("GET", "/v1/runs/r1/events")] = lambda req: httpx.Response(
        200,
        headers={"content-type": "text/event-stream"},
        content=sse_body([
            ("snapshot", dict(RUN, partial="hel")),
            ("append", {"run_id": "r1", "append": "lo"}),
            ("done", done),
        ]),
    )
    with auth.build_client() as c:
        result = chat.run_turn(c, "hi")
    assert result["status"] == "done"
    assert result["session_key"] == "web:u@x:1"
    assert capsys.readouterr().out.rstrip("\n") == "hello"


def test_run_turn_sends_session_and_attachments(mock_api):
    seen = {}

    def turns(req):
        seen.update(json.loads(req.content))
        return httpx.Response(202, json={"run_id": "r1", "session_key": "k9"})

    mock_api[("POST", "/v1/turns")] = turns
    mock_api[("GET", "/v1/runs/r1/events")] = lambda req: httpx.Response(
        200, content=sse_body([("done", dict(RUN, status="done", session_key="k9"))])
    )
    with auth.build_client() as c:
        chat.run_turn(c, "hi", session_key="k9", attachments=["a1", "a2"], quiet=True)
    assert seen["session_key"] == "k9"
    assert seen["attachments"] == ["a1", "a2"]


def test_run_turn_json_mode_prints_summary_only(mock_api, capsys):
    done = dict(RUN, status="done", partial="x", result_text="x", cost_usd=0.01)
    mock_api[("POST", "/v1/turns")] = lambda req: httpx.Response(
        202, json={"run_id": "r1", "session_key": "web:u@x:1"}
    )
    mock_api[("GET", "/v1/runs/r1/events")] = lambda req: httpx.Response(
        200, content=sse_body([("done", done)])
    )
    with auth.build_client() as c:
        chat.run_turn(c, "hi", json_out=True)
    out = json.loads(capsys.readouterr().out)
    assert out == {
        "session_key": "web:u@x:1", "run_id": "r1", "status": "done",
        "text": "x", "cost_usd": 0.01, "error": None,
    }


def test_run_turn_busy_409_reports(mock_api, capsys):
    mock_api[("POST", "/v1/turns")] = lambda req: httpx.Response(
        409, json={"detail": {"detail": "session busy", "active_run_id": "r0"}}
    )
    import typer
    with auth.build_client() as c:
        try:
            chat.run_turn(c, "hi", session_key="k9")
            raise AssertionError("should have exited")
        except typer.Exit as e:
            assert e.exit_code == 1
    assert "busy" in capsys.readouterr().err


def test_state_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    from informe_cli import state
    assert state.load_last_session() is None
    state.save_last_session("web:u@x:42")
    assert state.load_last_session() == "web:u@x:42"


from typer.testing import CliRunner

from informe_cli.main import app

runner = CliRunner()


def _wire_simple_turn(mock_api, session_key="web:u@x:1"):
    done = dict(RUN, status="done", partial="ok", result_text="ok", session_key=session_key)
    mock_api[("POST", "/v1/turns")] = lambda req: httpx.Response(
        202, json={"run_id": "r1", "session_key": session_key}
    )
    mock_api[("GET", "/v1/runs/r1/events")] = lambda req: httpx.Response(
        200, content=sse_body([("done", done)])
    )


def test_cli_one_shot_question(mock_api):
    _wire_simple_turn(mock_api)
    result = runner.invoke(app, ["hello there"])
    assert result.exit_code == 0
    assert "ok" in result.output


def test_cli_continue_uses_last_session(mock_api):
    from informe_cli import state
    state.save_last_session("web:u@x:7")
    seen = {}

    def turns(req):
        seen.update(json.loads(req.content))
        return httpx.Response(202, json={"run_id": "r1", "session_key": "web:u@x:7"})

    mock_api[("POST", "/v1/turns")] = turns
    mock_api[("GET", "/v1/runs/r1/events")] = lambda req: httpx.Response(
        200, content=sse_body([("done", dict(RUN, status="done", session_key="web:u@x:7"))])
    )
    result = runner.invoke(app, ["-c", "follow up"])
    assert result.exit_code == 0
    assert seen["session_key"] == "web:u@x:7"


def test_cli_open_prints_url(mock_api, monkeypatch):
    monkeypatch.setenv("INFORME_NO_BROWSER", "1")
    from informe_cli import state
    state.save_last_session("web:u@x:7")
    result = runner.invoke(app, ["open"])
    assert result.exit_code == 0
    assert "/chats/web%3Au%40x%3A7" in result.output


def test_stream_retries_transient_404(mock_api, capsys, monkeypatch):
    import time as _time
    monkeypatch.setattr(_time, "sleep", lambda s: None)
    done = dict(RUN, status="done", partial="ok", result_text="ok")
    mock_api[("POST", "/v1/turns")] = lambda req: httpx.Response(
        202, json={"run_id": "r1", "session_key": "web:u@x:1"}
    )
    calls = {"n": 0}

    def events(req):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(404, json={"detail": "unknown run"})
        return httpx.Response(200, content=sse_body([("done", done)]))

    mock_api[("GET", "/v1/runs/r1/events")] = events
    with auth.build_client() as c:
        result = chat.run_turn(c, "hi")
    assert result["status"] == "done"
    assert calls["n"] == 2


def test_run_turn_marks_client_cli(mock_api):
    seen = {}

    def turns(req):
        seen.update(json.loads(req.content))
        return httpx.Response(202, json={"run_id": "r1", "session_key": "cli:u@x:1"})

    mock_api[("POST", "/v1/turns")] = turns
    mock_api[("GET", "/v1/runs/r1/events")] = lambda req: httpx.Response(
        200, content=sse_body([("done", dict(RUN, status="done", session_key="cli:u@x:1"))])
    )
    with auth.build_client() as c:
        chat.run_turn(c, "hi", quiet=True)
    assert seen["client"] == "cli"
