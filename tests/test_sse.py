import io

from informe_cli.sse import Renderer, parse_sse


def _snap(**kw):
    d = {
        "run_id": "r1", "user_text": "q", "session_key": "k1",
        "status": "running", "partial": "", "activity": [],
        "result_text": None, "cost_usd": None, "started_at": 1.0,
        "finished_at": None, "error": None, "phase": "model", "phase_since": None,
    }
    d.update(kw)
    return d


def test_parse_sse_events_and_pings():
    lines = [
        "event: snapshot",
        'data: {"partial": "he"}',
        "",
        ": ping",
        "",
        "event: append",
        'data: {"run_id": "r1", "append": "llo"}',
        "",
    ]
    out = list(parse_sse(lines))
    assert out == [("snapshot", {"partial": "he"}), ("append", {"run_id": "r1", "append": "llo"})]


def test_renderer_prints_deltas_only():
    out, err = io.StringIO(), io.StringIO()
    r = Renderer(out=out, err=err)
    r.feed("snapshot", _snap(partial="hel"))
    r.feed("append", {"run_id": "r1", "append": "lo "})
    r.feed("snapshot", _snap(partial="hello world"))
    assert out.getvalue() == "hello world"
    assert not r.done


def test_renderer_done_flushes_result_text_and_cost():
    out, err = io.StringIO(), io.StringIO()
    r = Renderer(out=out, err=err)
    r.feed("snapshot", _snap(partial="hi"))
    r.feed("done", _snap(status="done", partial="hi", result_text="hi there", cost_usd=0.01))
    assert out.getvalue() == "hi there"
    assert r.done
    assert r.snap["cost_usd"] == 0.01


def test_renderer_activity_goes_to_err():
    out, err = io.StringIO(), io.StringIO()
    r = Renderer(out=out, err=err)
    r.feed("snapshot", _snap(activity=[{"ts": 1, "kind": "tool", "detail": "Bash", "arg": "ls"}]))
    r.feed("snapshot", _snap(activity=[
        {"ts": 1, "kind": "tool", "detail": "Bash", "arg": "ls"},
        {"ts": 2, "kind": "tool", "detail": "Read", "arg": "x.py"},
    ]))
    assert "Bash" in err.getvalue() and "Read" in err.getvalue()
    assert err.getvalue().count("Bash") == 1
    assert out.getvalue() == ""


def test_renderer_reconnect_snapshot_does_not_duplicate():
    out, err = io.StringIO(), io.StringIO()
    r = Renderer(out=out, err=err)
    r.feed("snapshot", _snap(partial="hello"))
    r.feed("snapshot", _snap(partial="hello"))
    assert out.getvalue() == "hello"
