import json

import httpx
from typer.testing import CliRunner

from informe_cli.main import app

runner = CliRunner()


def test_whoami_json(mock_api):
    mock_api[("GET", "/v1/me")] = lambda req: httpx.Response(
        200, json={"email": "u@mindlogic.ai", "is_admin": False, "member": None, "projects": []}
    )
    result = runner.invoke(app, ["whoami", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.output)["email"] == "u@mindlogic.ai"


def test_whoami_human(mock_api):
    mock_api[("GET", "/v1/me")] = lambda req: httpx.Response(
        200, json={"email": "u@mindlogic.ai", "is_admin": True, "member": None, "projects": []}
    )
    result = runner.invoke(app, ["whoami"])
    assert result.exit_code == 0
    assert "u@mindlogic.ai" in result.output and "admin" in result.output


def test_sessions_table(mock_api):
    mock_api[("GET", "/v1/sessions")] = lambda req: httpx.Response(200, json={
        "sessions": [{"session_key": "k1", "surface": "web", "principal": "u@x",
                      "project": None, "last_activity_ts": 1e9, "title": "About logs",
                      "turns": 3, "cost_usd": 0.5, "running": False}],
        "more": False,
    })
    result = runner.invoke(app, ["sessions"])
    assert result.exit_code == 0
    assert "k1" in result.output and "About logs" in result.output


def test_sessions_search(mock_api):
    mock_api[("GET", "/v1/sessions/search")] = lambda req: httpx.Response(
        200, json={"results": [{"session_key": "k2", "title": "t", "snippet": "…logs…",
                                 "matched": "question", "ts": None}]}
    )
    result = runner.invoke(app, ["sessions", "--search", "logs"])
    assert result.exit_code == 0
    assert "k2" in result.output


def test_history(mock_api):
    mock_api[("GET", "/v1/sessions/k1/history")] = lambda req: httpx.Response(
        200, json={"turns": [{"question": "q1", "answer": "a1"}]}
    )
    result = runner.invoke(app, ["history", "k1"])
    assert result.exit_code == 0
    assert "q1" in result.output and "a1" in result.output


def test_skills_list_and_one(mock_api):
    mock_api[("GET", "/v1/skills")] = lambda req: httpx.Response(
        200, json={"skills": [{"name": "publish", "description": "d"}]}
    )
    mock_api[("GET", "/v1/skills/publish")] = lambda req: httpx.Response(
        200, json={"name": "publish", "content": "# SKILL"}
    )
    assert "publish" in runner.invoke(app, ["skills"]).output
    assert "# SKILL" in runner.invoke(app, ["skills", "publish"]).output


def test_skills_mine(mock_api):
    mock_api[("GET", "/v1/my/skills")] = lambda req: httpx.Response(
        200, json={"skills": [{"name": "my-thing", "description": "d"}]}
    )
    assert "my-thing" in runner.invoke(app, ["skills", "--mine"]).output


def test_memory_index_and_file(mock_api):
    mock_api[("GET", "/v1/memory")] = lambda req: httpx.Response(
        200, json={"sections": [], "cold_sections": [], "files": [{"path": "team/x.md"}], "own_memory": None}
    )
    mock_api[("GET", "/v1/memory/file")] = lambda req: httpx.Response(
        200, json={"path": "team/x.md", "content": "remember this"}
    )
    assert "team/x.md" in runner.invoke(app, ["memory"]).output
    assert "remember this" in runner.invoke(app, ["memory", "show", "team/x.md"]).output


def test_usage(mock_api):
    mock_api[("GET", "/v1/usage/me")] = lambda req: httpx.Response(
        200, json={"cost_usd": 1.25, "turns": 10, "email": "u@x",
                   "budget": {"spent_usd": 1.25, "ceiling_usd": 100}}
    )
    out = runner.invoke(app, ["usage"]).output
    assert "1.25" in out


def test_projects_and_crons(mock_api):
    mock_api[("GET", "/v1/projects")] = lambda req: httpx.Response(
        200, json=[{"id": "p1", "name": "P One"}]
    )
    mock_api[("GET", "/v1/my/crons")] = lambda req: httpx.Response(
        200, json={"crons": [{"id": 1, "name": "daily", "schedule": "0 9 * * *", "enabled": True}]}
    )
    assert "p1" in runner.invoke(app, ["projects"]).output
    assert "daily" in runner.invoke(app, ["crons"]).output
