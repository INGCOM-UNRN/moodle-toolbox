"""Acceso uniforme a bancos de preguntas en GIFT y Moodle XML.

Descubre los archivos de un repositorio y los parsea al modelo unificado según su
extensión, para que validate, analyze y health traten ambos formatos por igual.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from questions.core.moodle_xml import parse_xml_file
from questions.core.parser import parse_gift_file

EXTENSIONES = (".gift", ".xml")


def formato_de(ruta: str | Path) -> str | None:
    """'gift' o 'xml' según la extensión (None si no es un banco)."""
    sufijo = Path(ruta).suffix.lower()
    return {".gift": "gift", ".xml": "xml"}.get(sufijo)


def buscar_archivos(directorio: str | Path, recursivo: bool = True,
                    extensiones: Iterable[str] = EXTENSIONES) -> list[Path]:
    """Archivos de preguntas del directorio, ordenados (se ignoran los ocultos)."""
    directorio = Path(directorio)
    patron = "**/*" if recursivo else "*"
    extensiones = tuple(e.lower() for e in extensiones)
    return sorted(
        p for p in directorio.glob(patron)
        if p.is_file() and p.suffix.lower() in extensiones
        and not any(parte.startswith(".") for parte in p.relative_to(directorio).parts)
    )


def expandir_rutas(rutas: Iterable[str | Path], recursivo: bool,
                   extensiones: Iterable[str] = EXTENSIONES) -> list[Path]:
    """Archivos sueltos tal cual y directorios expandidos con `buscar_archivos`."""
    archivos: list[Path] = []
    for ruta in rutas:
        ruta = Path(ruta)
        if ruta.is_dir():
            archivos.extend(buscar_archivos(ruta, recursivo, extensiones))
        elif ruta.is_file():
            archivos.append(ruta)
    return archivos


def parse_archivo(ruta: str | Path) -> dict:
    """Parsea un archivo GIFT o XML; el resultado lleva también `formato`."""
    formato = formato_de(ruta)
    if formato == "xml":
        resultado = parse_xml_file(ruta)
    else:
        resultado = parse_gift_file(str(ruta))
        formato = "gift"
    resultado["formato"] = formato
    return resultado
