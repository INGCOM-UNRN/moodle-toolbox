import click
from pathlib import Path
from typing import Optional

from questions.commands.common import llm_option
from questions.core.unifier import unificar


@click.command(name="unify")
@llm_option
@click.argument("paths", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o", "--output", "output_file",
    required=True,
    type=click.Path(path_type=Path),
    help="Archivo de salida unificado (.gift o .xml).",
)
@click.option(
    "-f", "--format", "formato",
    type=click.Choice(["gift", "xml"], case_sensitive=False),
    default=None,
    help="Formato de salida (por defecto se deduce de la extensión del archivo de salida).",
)
@click.option(
    "-r", "--recursive/--no-recursive",
    default=True,
    help="Procesar directorios recursivamente (por defecto True).",
)
@click.option(
    "--remove",
    is_flag=True,
    help="Borrar los archivos fuente después de unificarlos.",
)
def unify(paths, output_file, formato, recursive, remove):
    """Unifica árboles o grupos de archivos de preguntas (GIFT o XML) en un único archivo.

    Es la operación inversa a 'split' y 'tree export': recopila preguntas
    recorriendo los directorios especificados, infiere y preserva las categorías,
    y genera un único banco monolítico (.gift o .xml).
    """
    if not paths:
        paths = [Path(".")]

    try:
        total = unificar(
            rutas=paths,
            archivo_salida=output_file,
            formato=formato,
            recursivo=recursive,
            eliminar_origen=remove,
        )
    except Exception as e:
        raise click.ClickException(f"Error durante la unificación: {e}")

    if total == 0:
        click.echo("No se encontraron preguntas para unificar.", err=True)
        raise click.Exit(code=1)

    click.echo(f"✓ Unificación completada exitosamente: {total} preguntas escritas en {output_file}")
