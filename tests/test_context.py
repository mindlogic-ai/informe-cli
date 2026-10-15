import json

import httpx
from typer.testing import CliRunner

from informe_cli import context
from informe_cli.main import app
from conftest import RUN, sse_body

runner = CliRunner()

WINDOW = 1_000_000
COMPACT_AT = 700_000


def test_block_absent_is_none_not_zero():
    """An older server sends nothing; that must not read as an empty window."""
    assert context.block({"status": "done"}) is None
    assert context.block(None) is None


def test_block_shapes_the_three_server_fields():
    assert context.block({
        "context_tokens": 142_000,
        "context_window": WINDOW,
        "context_compact_at": COMPACT_AT,
    }) == {
        "input_tokens": 142_000,
        "limit_tokens": WINDOW,
        "compact_at_tokens": COMPACT_AT,
        # 142K of the 700K threshold, not of the 1M window.
        "fraction": 0.2029,
        "fraction_of_window": 0.142,
    }


def test_fraction_paces_to_the_compaction_not_the_window():
    """The number answers "how long until this compacts", so it counts to 700K.

    Sitting exactly on the threshold is 100% here and a comfortable-looking
    70% against the window — which is the reading that gets someone surprised
    by a compaction they thought was far away.
    """
    b = context.block({
        "context_tokens": COMPACT_AT, "context_window": WINDOW,
        "context_compact_at": COMPACT_AT,
    })
    assert b["fraction"] == 1.0
    assert b["fraction_of_window"] == 0.7


def test_fraction_can_exceed_one_when_a_turn_lands_past_the_threshold():
    # Compaction fires between turns, so a snapshot may legitimately be read
    # above the threshold. Clamping it would hide exactly that moment.
    b = context.block({
        "context_tokens": 812_000, "context_window": WINDOW,
        "context_compact_at": COMPACT_AT,
    })
    assert b["fraction"] > 1.0


def test_block_without_limits_has_no_fractions():
    b = context.block({"context_tokens": 5, "context_window": 0})
    assert b["input_tokens"] == 5
    assert b["limit_tokens"] is None
    assert b["fraction"] is None and b["fraction_of_window"] is None


def test_line_and_brief():
    b = context.block({
        "context_tokens": 142_000, "context_window": WINDOW,
        "context_compact_at": COMPACT_AT,
    })
    assert context.line(b) == (
        "context: 142K / 700K before auto-compact (20%) · window 1M"
    )
    assert context.brief(b) == "142K ctx"
    assert context.brief(context.block({"context_tokens": 0})) == ""
    assert context.line(None) is None


def _done_run(**extra):
    return {**RUN, "status": "done", "result_text": "hi", "cost_usd": 6.9, **extra}


def _wire_turn(mock_api, snap):
    mock_api[("POST", "/v1/turns")] = lambda req: httpx.Response(
        200, json={"run_id": "r1", "session_key": "web:u@x:1"}
    )
    mock_api[("GET", "/v1/runs/r1/events")] = lambda req: httpx.Response(
        200, content=sse_body([("done", snap)]), headers={"content-type": "text/event-stream"}
    )


def test_json_turn_carries_context(mock_api):
    _wire_turn(mock_api, _done_run(
        context_tokens=142_000, context_window=WINDOW, context_compact_at=COMPACT_AT,
    ))
    result = runner.invoke(app, ["-p", "--json", "q"])
    assert result.exit_code == 0
    out = json.loads(result.stdout)
    assert out["cost_usd"] == 6.9
    assert out["context"] == {
        "input_tokens": 142_000, "limit_tokens": WINDOW,
        "compact_at_tokens": COMPACT_AT,
        "fraction": 0.2029, "fraction_of_window": 0.142,
    }


def test_json_turn_context_is_null_when_server_is_silent(mock_api):
    _wire_turn(mock_api, _done_run())
    result = runner.invoke(app, ["-p", "--json", "q"])
    assert json.loads(result.stdout)["context"] is None


def test_sessions_listing_shows_context(mock_api):
    mock_api[("GET", "/v1/sessions")] = lambda req: httpx.Response(200, json={
        "sessions": [
            {"session_key": "k1", "title": "heavy", "turns": 22,
             "cost_usd": 6.9, "context_tokens": 610_000},
            {"session_key": "k2", "title": "cold", "turns": 1, "context_tokens": 0},
        ],
        "more": False,
        "context_window": WINDOW,
        "context_compact_at": COMPACT_AT,
    })
    result = runner.invoke(app, ["sessions", "--json"])
    assert result.exit_code == 0
    rows = json.loads(result.stdout)["sessions"]
    assert rows[0]["context"]["fraction"] == 0.8714  # 610K of the 700K threshold
    assert rows[0]["context"]["fraction_of_window"] == 0.61
    # Never held in memory: reported, but nothing to show in the human column.
    assert rows[1]["context"]["input_tokens"] == 0

    human = runner.invoke(app, ["sessions"])
    assert "610K ctx" in human.stdout
    assert "ctx" not in human.stdout.splitlines()[1]


def test_history_normalises_context(mock_api):
    mock_api[("GET", "/v1/sessions/k1/history")] = lambda req: httpx.Response(200, json={
        "turns": [{"question": "q", "answer": "a"}],
        "context_tokens": 700_000, "context_window": WINDOW,
        "context_compact_at": COMPACT_AT,
    })
    out = json.loads(runner.invoke(app, ["history", "k1", "--json"]).stdout)
    assert out["context"]["input_tokens"] == 700_000
    assert out["context_tokens"] == 700_000  # raw fields still pass through
