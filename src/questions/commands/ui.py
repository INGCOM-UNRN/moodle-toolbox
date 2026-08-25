import click
from pathlib import Path

from questions.commands.common import llm_option


@click.command()
@llm_option
@click.argument("directorio", type=click.Path(exists=True, file_okay=False), default=".")
@click.option("--host", default="127.0.0.1", show_default=True, help="Host del servidor web.")
@click.option("--port", type=int, default=5000, show_default=True, help="Puerto del servidor web.")
@click.option("--debug/--no-debug", default=False, help="Modo debug de Flask.")
def ui(directorio, host, port, debug):
    """Abre el editor web local (cerebro) sobre DIRECTORIO.

    Permite navegar y editar preguntas en Moodle XML y GIFT desde el navegador.
    Requiere el extra 'ui': pip install questions[ui]
    """
    try:
        from questions.ui.app import run
    except ImportError as e:
        raise click.ClickException(
            f"Faltan dependencias del editor web ({e}). "
            "Instalalas con: uv tool install questions --extra ui  |  pip install flask markdown"
        )
    run(str(Path(directorio).resolve()), host=host, port=port, debug=debug)
