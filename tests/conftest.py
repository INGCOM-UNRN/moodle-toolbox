"""Configuración común de la suite."""

import pytest


@pytest.fixture(autouse=True)
def cache_aislada(tmp_path, monkeypatch):
    """Cada test usa su propia caché de respuestas de modelos (nunca ~/.cache del usuario)."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.delenv("QUESTIONS_SIN_CACHE", raising=False)
