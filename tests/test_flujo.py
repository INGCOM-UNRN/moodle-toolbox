"""Flujo de trabajo: format --check/--diff, pre-commit, configuración por repositorio."""

from click.testing import CliRunner

from questions.cli import cli

runner = CliRunner()


def test_format_check_y_diff_no_escriben(tmp_path):
    sucio = tmp_path / "a.gift"
    sucio.write_text("::A::Q {=a ~b}\n", encoding="utf-8")
    limpio = tmp_path / "b.gift"
    limpio.write_text("::B::\nQ\n{\n    =a\n    ~b\n}\n", encoding="utf-8")

    res = runner.invoke(cli, ["format", str(tmp_path), "--check"])
    assert res.exit_code == 1 and "[CAMBIARÍA]" in res.output and "a.gift" in res.output
    assert sucio.read_text(encoding="utf-8") == "::A::Q {=a ~b}\n"

    res = runner.invoke(cli, ["format", str(sucio), "--diff"])
    assert res.exit_code == 0
    assert f"--- a/{sucio}" in res.output and "+    =a" in res.output
    assert sucio.read_text(encoding="utf-8") == "::A::Q {=a ~b}\n"

    assert runner.invoke(cli, ["format", str(limpio), "--check"]).exit_code == 0
    runner.invoke(cli, ["format", str(tmp_path)])
    assert runner.invoke(cli, ["format", str(tmp_path), "--check"]).exit_code == 0
