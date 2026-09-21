"""Regresión de MOODLE-D0203: main() no debe esconder el traceback sin salida de escape."""

import pytest

import questions.cli as mod


def _romper(monkeypatch):
    def boom(*a, **k):
        raise ValueError("falla interna")
    monkeypatch.setattr(mod, "cli", boom)


def test_main_resume_el_error_y_sale_con_1(monkeypatch, capsys):
    _romper(monkeypatch)
    monkeypatch.delenv("QUESTIONS_DEBUG", raising=False)
    with pytest.raises(SystemExit) as e:
        mod.main()
    assert e.value.code == 1
    assert "falla interna" in capsys.readouterr().err


def test_main_con_questions_debug_propaga_el_traceback(monkeypatch):
    _romper(monkeypatch)
    monkeypatch.setenv("QUESTIONS_DEBUG", "1")
    with pytest.raises(ValueError):
        mod.main()
