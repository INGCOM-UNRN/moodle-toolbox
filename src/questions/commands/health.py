"""Comando de auditoría de salud e higiene de bancos Moodle."""

from pathlib import Path
from typing import Optional

import click
import typer

from questions.commands.common import emitir_json

from questions.core.moodle_health import (
    verificar_porcentajes_opciones,
    auditar_retroalimentaciones,
    limpiar_html_y_estilos_obsoletos,
    auditar_enlaces_y_multimedia,
    generar_reporte_salud_markdown,
)


def health_cmd(
    archivo: Path = typer.Argument(..., exists=True),
    output_md: Optional[Path] = typer.Option(
        None, "--md", help="Exportar reporte en Markdown."
    ),
    clean_html: bool = typer.Option(
        False, "--clean-html", help="Limpiar etiquetas HTML obsoletas y estilos inline."
    ),
    output_json: bool = typer.Option(False, "--json", help="Emite el diagnóstico como JSON versionado."),
):
    """Audita la salud, porcentajes de opciones, feedback y enlaces en el banco de preguntas."""
    contenido = archivo.read_text(encoding="utf-8", errors="replace")
    es_xml = archivo.suffix.lower() == ".xml"

    if clean_html and not es_xml:
        limpio = limpiar_html_y_estilos_obsoletos(contenido)
        archivo.write_text(limpio, encoding="utf-8")
        click.echo(f"✓ Archivo limpio de etiquetas obsoletas y estilos CSS inline: {archivo}")
        contenido = limpio

    if output_json:
        datos = {"archivo": str(archivo), "formato": "xml" if es_xml else "gift"}
        if not es_xml:
            datos["porcentajes"] = verificar_porcentajes_opciones(contenido)
            datos["retroalimentacion"] = auditar_retroalimentaciones(contenido)
            datos["enlaces"] = auditar_enlaces_y_multimedia(contenido)
        emitir_json("health", datos)
        return

    reporte = generar_reporte_salud_markdown(archivo, contenido, es_xml=es_xml)

    if output_md:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(reporte, encoding="utf-8")
        click.echo(f"✓ Reporte Markdown exportado en: {output_md}")
    else:
        click.echo(reporte)
