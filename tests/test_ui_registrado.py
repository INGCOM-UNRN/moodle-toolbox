"""Regresión de MOODLE-D0201: el editor web (`commands/ui.py`) no estaba registrado en la CLI.

`questions ui` respondía "No such command 'ui'" aunque el módulo, sus tests y el propio
mensaje de alucarD ("editarlas con questions ui") lo daban por existente.
"""

import sys

from click.testing import CliRunner

from questions.cli import cli

runner = CliRunner()


def test_ui_figura_entre_los_comandos():
    assert "ui" in cli.list_commands(None)
    assert cli.get_command(None, "ui") is not None


def test_ui_aparece_en_la_ayuda_y_tiene_la_suya(tmp_path):
    assert "ui" in runner.invoke(cli, ["--help"]).output.split()
    res = runner.invoke(cli, ["ui", "--help"])
    assert res.exit_code == 0
    assert "--port" in res.output and "--host" in res.output


def test_sin_flask_el_error_indica_como_instalar_las_dependencias(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "questions.ui.app", None)  # hace fallar el import
    res = runner.invoke(cli, ["ui", str(tmp_path)])
    assert res.exit_code != 0
    assert "Faltan dependencias del editor web" in res.output
    assert "--extra ui" in res.output


def test_todos_los_comandos_listados_se_pueden_resolver():
    for nombre in cli.list_commands(None):
        assert cli.get_command(None, nombre) is not None, nombre
