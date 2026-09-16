"""Motor de síntesis de preguntas C — Delegado al engine canónico de alucarD."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from generador_examenes.synthesizer.engine import (
        SnippetGenerado,
        compilar_y_ejecutar,
        PLANTILLAS,
        plantillas_disponibles,
        sintetizar,
        exportar_gift,
        exportar_xml as _exportar_xml_base,
    )
except ImportError:
    sibling = Path(__file__).resolve().parents[4] / "alucarD"
    if sibling.is_dir() and str(sibling) not in sys.path:
        sys.path.insert(0, str(sibling))
    from generador_examenes.synthesizer.engine import (
        SnippetGenerado,
        compilar_y_ejecutar,
        PLANTILLAS,
        plantillas_disponibles,
        sintetizar,
        exportar_gift,
        exportar_xml as _exportar_xml_base,
    )


def exportar_xml(snippets: list[SnippetGenerado]) -> str:
    """Serializa los snippets como Moodle XML reutilizando gift_to_xml si está disponible, o el exportador base."""
    try:
        from questions.core.converter import gift_to_xml
        return gift_to_xml(exportar_gift(snippets))
    except Exception:
        return _exportar_xml_base(snippets)


__all__ = [
    "SnippetGenerado",
    "compilar_y_ejecutar",
    "PLANTILLAS",
    "plantillas_disponibles",
    "sintetizar",
    "exportar_gift",
    "exportar_xml",
]
