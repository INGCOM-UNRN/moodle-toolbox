import click
from pathlib import Path

from questions.core import tree as core_tree
from questions.commands.common import llm_option


@click.group()
@llm_option
def tree():
    """Organiza bancos en árboles de directorios por categoría.

    Reemplaza a moodle-reorganizer: un banco monolítico GIFT/XML se exporta a
    una carpeta con 1 archivo por pregunta (organizado por categorías) y puede
    recolectarse nuevamente a un archivo único.
    """


@tree.command(name="export")
@click.argument("archivo", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output-dir", "dir_salida", required=True, type=click.Path(path_type=Path),
              help="Directorio de destino del árbol de preguntas.")
@click.option("--formato", type=click.Choice(["gift", "xml"]), default=None,
              help="Forzar el formato (por defecto se deduce de la extensión).")
def export_cmd(archivo, dir_salida, formato):
    """Exporta ARCHIVO (banco monolítico) a un árbol de directorios."""
    cantidad = core_tree.exportar(archivo, dir_salida, formato)
    if cantidad < 0:
        raise click.ClickException("La exportación falló.")
    click.echo(f"\nÁrbol generado en: {dir_salida}")


@tree.command(name="collect")
@click.argument("directorio", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("-o", "--output", "archivo_salida", required=True, type=click.Path(path_type=Path),
              help="Archivo monolítico de destino (.gift o .xml; define el formato).")
@click.option("--formato", type=click.Choice(["gift", "xml"]), default=None,
              help="Forzar el formato (por defecto se deduce de la extensión de salida).")
def collect_cmd(directorio, archivo_salida, formato):
    """Recolecta DIRECTORIO en un banco monolítico único."""
    cantidad = core_tree.recolectar(directorio, archivo_salida, formato)
    if cantidad == 0:
        click.echo("No se recolectó ninguna pregunta.", err=True)
        raise click.Exit(code=1)
