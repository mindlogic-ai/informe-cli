import json

import httpx
import pytest

from informe_cli import auth

RUN = {
    "run_id": "r1", "user_text": "q", "session_key": "web:u@x:1",
    "status": "running", "partial": "", "activity": [],
    "result_text": None, "cost_usd": None, "started_at": 1.0,
    "finished_at": None, "error": None, "phase": "model", "phase_since": None,
}


def sse_body(events):
    """[(name, dict), ...] → one SSE byte stream."""
    return "".join(
        f"event: {n}\ndata: {json.dumps(d)}\n\n" for n, d in events
    ).encode()


@pytest.fixture
def mock_api(monkeypatch, tmp_path):
    """Route table the tests fill in: {(method, path): callable(request) -> Response}."""
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    routes = {}

    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        if key not in routes:
            return httpx.Response(404, json={"detail": f"no route {key}"})
        return routes[key](request)

    monkeypatch.setattr(auth, "access_token", lambda: "tok")
    monkeypatch.setattr(auth, "_transport", httpx.MockTransport(handler))
    return routes
