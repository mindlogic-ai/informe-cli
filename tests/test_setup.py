import shutil

from typer.testing import CliRunner

from informe_cli import setup_cmd
from informe_cli.main import app

runner = CliRunner()


def test_skill_source_exists():
    src = setup_cmd.skill_source()
    assert src.is_file()
    text = src.read_text()
    assert text.startswith("---")
    assert "name: informe-cli" in text


def test_setup_installs_skill(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_SKILLS_DIR", str(tmp_path / "skills"))
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/local/bin/cloudflared")
    result = runner.invoke(app, ["setup"])
    assert result.exit_code == 0
    installed = tmp_path / "skills" / "informe-cli" / "SKILL.md"
    assert installed.is_file()
    assert "informe-cli" in installed.read_text()


def test_setup_installs_design_page_skill_with_references(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_SKILLS_DIR", str(tmp_path / "skills"))
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/local/bin/cloudflared")
    result = runner.invoke(app, ["setup"])
    assert result.exit_code == 0
    skill = tmp_path / "skills" / "mindlogic-design-page"
    assert "name: mindlogic-design-page" in (skill / "SKILL.md").read_text()
    assert (skill / "references" / "DESIGN.md").is_file()
    assert (skill / "references" / "boilerplate.md").is_file()


def test_setup_warns_without_cloudflared(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_SKILLS_DIR", str(tmp_path / "skills"))
    monkeypatch.setattr(shutil, "which", lambda name: None)
    result = runner.invoke(app, ["setup"])
    assert result.exit_code == 0
    assert "brew install cloudflared" in result.output
