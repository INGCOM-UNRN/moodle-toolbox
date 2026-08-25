import click
from pathlib import Path

from questions.commands.common import llm_option


@click.command()
@llm_option
@click.argument("plantilla", type=str, required=False, default="")
@click.option("-n", "--cantidad", type=int, default=5, show_default=True,
              help="Cantidad de preguntas a sintetizar.")
@click.option("-s", "--semilla", type=int, default=42, show_default=True,
              help="Semilla pseudo-aleatoria (salida reproducible).")
@click.option("-o", "--output", "archivo_salida", required=False,
              type=click.Path(path_type=Path),
              help="Archivo destino: .gift o .xml según la extensión.")
@click.option("--listar", is_flag=True, help="Lista las plantillas disponibles y sale.")
def synth(plantilla, cantidad, semilla, archivo_salida, listar):
    """daedalus en belmont: sintetiza preguntas de C verificadas con GCC.

    PLANTILLA es una de las generadoras incorporadas (ver --listar). Cada
    pregunta se crea con parámetros aleatorios, se compila y ejecuta de verdad
    para fijar la salida correcta, y se acompaña de distractores verosímiles.
    """
    from questions.core.synth import (
        exportar_gift,
        exportar_xml,
        plantillas_disponibles,
        sintetizar,
    )

    if listar or not plantilla:
        if not listar and not archivo_salida:
            raise click.ClickException("Indicá la plantilla. Ver opciones con --listar.")
        click.echo("Plantillas disponibles del sintetizador daedalus:")
        for nombre, descripcion in sorted(plantillas_disponibles().items()):
            click.echo(f"  - {nombre}: {descripcion}")
        return

    if not archivo_salida:
        raise click.ClickException("Falta -o/--output con la ruta del banco a generar.")

    try:
        snippets = sintetizar(plantilla, cantidad=cantidad, semilla=semilla)
    except KeyError as e:
        raise click.ClickException(str(e))
    except RuntimeError as e:
        raise click.ClickException(f"{e}")

    extension = archivo_salida.suffix.lower()
    if extension == ".gift":
        contenido = exportar_gift(snippets)
    elif extension == ".xml":
        contenido = exportar_xml(snippets)
    else:
        raise click.ClickException("La extensión de salida debe ser .gift o .xml")

    archivo_salida.parent.mkdir(parents=True, exist_ok=True)
    archivo_salida.write_text(contenido, encoding="utf-8")
    click.echo(f"✓ {len(snippets)} preguntas de C sintetizadas y verificadas con gcc "
               f"→ {archivo_salida}")
