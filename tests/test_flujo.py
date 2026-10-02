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


def test_hooks_de_pre_commit_ejecutan_comandos_reales(tmp_path):
    import re
    import shlex
    from pathlib import Path

    texto = (Path(__file__).resolve().parents[1] / ".pre-commit-hooks.yaml").read_text(encoding="utf-8")
    hooks = dict(re.findall(r"^- id: (\S+)\n(?:  .*\n)*?  entry: (.+)$", texto, re.MULTILINE))
    assert set(hooks) == {"questions-format", "questions-health", "questions-health-estricto", "questions-validate"}
    sano = tmp_path / "sano.gift"
    sano.write_text("::P::\n¿Cuál?\n{\n    =a #bien\n    ~b #no\n    ~c #no\n    ####general\n}\n", encoding="utf-8")
    roto = tmp_path / "roto.gift"
    roto.write_text("::P:: ¿Cuál? {~a ~b ~c}\n", encoding="utf-8")  # sin correcta, sin formato
    for hook, entry in hooks.items():
        argumentos = shlex.split(entry)
        assert argumentos[0] == "questions"
        assert runner.invoke(cli, argumentos[1:] + [str(sano)]).exit_code == 0, hook
        assert runner.invoke(cli, argumentos[1:] + [str(roto)]).exit_code == 1, hook
