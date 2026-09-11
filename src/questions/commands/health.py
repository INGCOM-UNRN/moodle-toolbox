"""Comando de auditoría de salud e higiene de bancos Moodle."""

from pathlib import Path
import click
from questions.core.moodle_health import (
    verificar_porcentajes_opciones,
    auditar_retroalimentaciones,
    limpiar_html_y_estilos_obsoletos,
    auditar_enlaces_y_multimedia,
    generar_reporte_salud_markdown,
)


@click.command("health")
@click.argument("archivo", type=click.Path(exists=True, path_type=Path))
@click.option("--md", "output_md", type=click.Path(path_type=Path), help="Exportar reporte en Markdown.")
@click.option("--clean-html", is_flag=True, help="Limpiar etiquetas HTML obsoletas y estilos inline.")
def health_cmd(archivo: Path, output_md: Path | None, clean_html: bool):
    """Audita la salud, porcentajes de opciones, feedback y enlaces en el banco de preguntas."""
    contenido = archivo.read_text(encoding="utf-8", errors="replace")
    es_xml = archivo.suffix.lower() == ".xml"

    if clean_html and not es_xml:
        limpio = limpiar_html_y_estilos_obsoletos(contenido)
        archivo.write_text(limpio, encoding="utf-8")
        click.echo(f"✓ Archivo limpio de etiquetas obsoletas y estilos CSS inline: {archivo}")
        contenido = limpio

    reporte = generar_reporte_salud_markdown(archivo, contenido, es_xml=es_xml)

    if output_md:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(reporte, encoding="utf-8")
        click.echo(f"✓ Reporte Markdown exportado en: {output_md}")
    else:
        click.echo(reporte)
