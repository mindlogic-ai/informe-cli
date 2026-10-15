import json

import httpx
import pytest
from typer.testing import CliRunner

from informe_cli import auth, chat, models
from informe_cli.main import app
from conftest import RUN, sse_body

runner = CliRunner()


def test_resolve_aliases_and_passthrough():
    assert models.resolve_model("fable") == "claude-fable-5-1[1m]"
    assert models.resolve_model("FABLE") == "claude-fable-5-1[1m]"
    assert models.resolve_model("fable5.1") == "claude-fable-5-1[1m]"
    assert models.resolve_model("opus") == "claude-opus"  # server maps to its default
    assert models.resolve_model("auto") == "claude-opus"
    assert models.resolve_model("sonnet") == "claude-sonnet-5[1m]"
    assert models.resolve_model(None) is None
    assert models.resolve_model("claude-opus-5") == "claude-opus-5"
    with pytest.raises(ValueError):
        models.resolve_model("gpt-9")


def test_parse_model_command_whole_line_only():
    assert models.parse_model_command("/fable") == (True, "claude-fable-5-1[1m]", False)
    assert models.parse_model_command(" /Fable5.1 ") == (True, "claude-fable-5-1[1m]", False)
    assert models.parse_model_command("/opus") == (True, "claude-opus", False)
    assert models.parse_model_command("/opus5.5") == (True, "claude-opus", False)
    assert models.parse_model_command("/sonnet") == (True, "claude-sonnet-5[1m]", False)
    assert models.parse_model_command("/model") == (True, None, True)
    # A question that merely mentions the command is a question.
    assert models.parse_model_command("/fable 왜 안 돼?") == (False, None, False)
    assert models.parse_model_command("what is /fable") == (False, None, False)


def _capture_turns(mock_api, session_key="cli:u@x:1"):
    seen = []

    def turns(req):
        seen.append(json.loads(req.content))
        return httpx.Response(202, json={"run_id": "r1", "session_key": session_key})

    mock_api[("POST", "/v1/turns")] = turns
    mock_api[("GET", "/v1/runs/r1/events")] = lambda req: httpx.Response(
        200, content=sse_body([("done", dict(RUN, status="done", session_key=session_key))])
    )
    return seen


def test_run_turn_sends_model_only_when_set(mock_api):
    seen = _capture_turns(mock_api)
    with auth.build_client() as c:
        chat.run_turn(c, "hi", quiet=True)
        chat.run_turn(c, "hi", model="claude-fable-5-1[1m]", quiet=True)
    assert "model" not in seen[0]
    assert seen[1]["model"] == "claude-fable-5-1[1m]"


def test_cli_model_flag_sends_fable(mock_api):
    seen = _capture_turns(mock_api)
    result = runner.invoke(app, ["-m", "fable", "hello"])
    assert result.exit_code == 0, result.output
    assert seen[0]["model"] == "claude-fable-5-1[1m]"


def test_cli_model_flag_rejects_unknown(mock_api):
    result = runner.invoke(app, ["--model", "gpt-9", "hello"])
    assert result.exit_code == 2
    assert "unknown model" in result.output


def test_repl_fable_is_sticky_until_opus(mock_api, monkeypatch):
    seen = _capture_turns(mock_api)
    lines = iter(["/fable", "q1", "q2", "/opus", "q3", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(lines))
    from informe_cli.main import _repl
    with auth.build_client() as c:
        _repl(c, None, None, None)
    # /opus must SEND the default, not omit it: the server pins the chat, and an
    # omitted model would leave it on Fable.
    assert [t.get("model") for t in seen] == ["claude-fable-5-1[1m]", "claude-fable-5-1[1m]", "claude-opus"]
