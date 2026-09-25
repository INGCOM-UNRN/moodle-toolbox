"""google-genai debe ser opcional (N-MOODLE-02).

Como dependencia obligatoria arrastraba a toda instalación cryptography,
urllib3, pyasn1, idna y anyio, con avisos de seguridad conocidos, aunque solo
`questions ai` la usa.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def test_google_genai_esta_en_el_extra_ai_y_no_en_las_dependencias_base():
    proyecto = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    assert not any(d.startswith("google-genai") for d in proyecto["dependencies"])
    assert any(d.startswith("google-genai") for d in proyecto["optional-dependencies"]["ai"])


def test_el_modulo_ai_se_importa_aunque_falte_google_genai(monkeypatch):
    import importlib
    import sys

    monkeypatch.setitem(sys.modules, "google", None)
    modulo = importlib.reload(importlib.import_module("questions.core.ai"))
    try:
        assert modulo.genai is None
    finally:
        monkeypatch.undo()
        importlib.reload(modulo)
