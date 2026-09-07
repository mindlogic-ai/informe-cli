import json

import httpx

from informe_cli import auth, files_ws
from conftest import RUN, sse_body


def test_upload_local_returns_artifact_id(mock_api, tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text("hello")
    seen = {}

    def upload(req):
        seen["path"] = req.url.path
        seen["body"] = req.content
        return httpx.Response(201, json={"id": "art1", "name": "notes.txt", "size_bytes": 5})

    mock_api[("POST", "/v1/sessions/new/files")] = upload
    with auth.build_client() as c:
        aid = files_ws.upload_local(c, str(f), "new")
    assert aid == "art1"
    assert b"hello" in seen["body"]


def test_upload_local_missing_file_exits(mock_api):
    import typer
    with auth.build_client() as c:
        try:
            files_ws.upload_local(c, "/nope/missing.txt", "new")
            raise AssertionError("should exit")
        except typer.Exit as e:
            assert e.exit_code == 2


def test_attach_workspace_returns_artifact_id(mock_api):
    seen = {}

    def attach(req):
        seen.update(json.loads(req.content))
        return httpx.Response(201, json={"id": "art2", "name": "x.log", "size_bytes": 9})

    mock_api[("POST", "/v1/workspace/me/attach")] = attach
    with auth.build_client() as c:
        aid = files_ws.attach_workspace(c, "me", "logs/x.log")
    assert aid == "art2"
    assert seen["path"] == "logs/x.log"


def test_cli_attach_flows_into_turn(mock_api, tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x")
    turn_body = {}
    mock_api[("POST", "/v1/sessions/new/files")] = lambda req: httpx.Response(
        201, json={"id": "artX", "name": "a.txt", "size_bytes": 1}
    )

    def turns(req):
        turn_body.update(json.loads(req.content))
        return httpx.Response(202, json={"run_id": "r1", "session_key": "k1"})

    mock_api[("POST", "/v1/turns")] = turns
    mock_api[("GET", "/v1/runs/r1/events")] = lambda req: httpx.Response(
        200, content=sse_body([("done", dict(RUN, status="done"))])
    )
    from typer.testing import CliRunner
    from informe_cli.main import app
    result = CliRunner().invoke(app, ["--attach", str(f), "what is this file"])
    assert result.exit_code == 0
    assert turn_body["attachments"] == ["artX"]


from typer.testing import CliRunner

from informe_cli.main import app

runner = CliRunner()


def test_files_ls(mock_api):
    mock_api[("GET", "/v1/files")] = lambda req: httpx.Response(200, json={
        "files": [{"id": "a1", "name": "report.html", "mimetype": "text/html",
                   "size_bytes": 100, "session_key": "k1", "owner_email": "u@x",
                   "project": None, "created_at": 1e9, "created_by": "u@x"}]
    })
    out = runner.invoke(app, ["files", "ls"]).output
    assert "a1" in out and "report.html" in out


def test_files_get_writes_bytes(mock_api, tmp_path):
    mock_api[("GET", "/v1/files/a1")] = lambda req: httpx.Response(
        200, content=b"<html>hi</html>",
        headers={"content-disposition": 'attachment; filename="report.html"'},
    )
    dest = tmp_path / "out.html"
    result = runner.invoke(app, ["files", "get", "a1", "-o", str(dest)])
    assert result.exit_code == 0
    assert dest.read_bytes() == b"<html>hi</html>"


def test_ws_ls(mock_api):
    mock_api[("GET", "/v1/workspace/me/list")] = lambda req: httpx.Response(
        200, json={"path": "", "entries": [{"name": "logs", "dir": True},
                                             {"name": "a.txt", "dir": False, "size": 5}]}
    )
    out = runner.invoke(app, ["ws", "ls"]).output
    assert "logs" in out and "a.txt" in out


def test_ws_put(mock_api, tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hello")
    seen = {}

    def upload(req):
        seen["path_param"] = dict(req.url.params).get("path", "")
        return httpx.Response(201, json={"entry": {"name": "a.txt", "dir": False, "size": 5}})

    mock_api[("POST", "/v1/workspace/me/upload")] = upload
    result = runner.invoke(app, ["ws", "put", str(f), "docs"])
    assert result.exit_code == 0
    assert seen["path_param"] == "docs"


def test_ws_get(mock_api, tmp_path):
    mock_api[("GET", "/v1/workspace/me/file")] = lambda req: httpx.Response(
        200, content=b"data", headers={"content-disposition": 'attachment; filename="a.txt"'}
    )
    dest = tmp_path / "a.txt"
    result = runner.invoke(app, ["ws", "get", "a.txt", "-o", str(dest)])
    assert result.exit_code == 0
    assert dest.read_bytes() == b"data"


def test_ws_mv_and_rm(mock_api):
    mock_api[("POST", "/v1/workspace/me/move")] = lambda req: httpx.Response(
        200, json={"entry": {"name": "b.txt", "dir": False}}
    )
    mock_api[("DELETE", "/v1/workspace/me/file")] = lambda req: httpx.Response(
        200, json={"deleted": "b.txt"}
    )
    assert runner.invoke(app, ["ws", "mv", "a.txt", "b.txt"]).exit_code == 0
    assert runner.invoke(app, ["ws", "rm", "b.txt"]).exit_code == 0
