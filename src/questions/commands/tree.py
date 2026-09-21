import click
import typer
from pathlib import Path
from typing import Optional

from questions.core import tree as core_tree
from questions.commands.common import LLM_OPTION, fail

tree_app = typer.Typer(help="Organiza bancos en árboles de directorios por categoría.")


@tree_app.callback()
def tree(llm: bool = LLM_OPTION):
    """Organiza bancos en árboles de directorios por categoría.

    Reemplaza a moodle-reorganizer: un banco monolítico GIFT/XML se exporta a
    una carpeta con 1 archivo por pregunta (organizado por categorías) y puede
    recolectarse nuevamente a un archivo único.
    """


@tree_app.command(name="export")
def export_cmd(
    archivo: Path = typer.Argument(..., exists=True),
    dir_salida: Path = typer.Option(
        ..., "-o", "--output-dir",
        help="Directorio de destino del árbol de preguntas."),
    formato: Optional[str] = typer.Option(
        None, "--formato",
        click_type=click.Choice(["gift", "xml"]),
        help="Forzar el formato (por defecto se deduce de la extensión)."),
):
    """Exporta ARCHIVO (banco monolítico) a un árbol de directorios."""
    cantidad = core_tree.exportar(archivo, dir_salida, formato)
    if cantidad < 0:
        fail("La exportación falló.")
    click.echo(f"\nÁrbol generado en: {dir_salida}")


@tree_app.command(name="collect")
def collect_cmd(
    directorio: Path = typer.Argument(..., exists=True, file_okay=False),
    archivo_salida: Path = typer.Option(
        ..., "-o", "--output",
        help="Archivo monolítico de destino (.gift o .xml; define el formato)."),
    formato: Optional[str] = typer.Option(
        None, "--formato",
        click_type=click.Choice(["gift", "xml"]),
        help="Forzar el formato (por defecto se deduce de la extensión de salida)."),
):
    """Recolecta DIRECTORIO en un banco monolítico único."""
    cantidad = core_tree.recolectar(directorio, archivo_salida, formato)
    if cantidad == 0:
        click.echo("No se recolectó ninguna pregunta.", err=True)
        raise typer.Exit(code=1)
