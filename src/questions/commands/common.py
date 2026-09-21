import json

import click
import typer

from questions.core.llm_instructions import get_instructions


def llm_callback(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(get_instructions(ctx.command.name))
    ctx.exit()


LLM_OPTION = typer.Option(
    False,
    "--llm",
    callback=llm_callback,
    is_eager=True,
    help="Muestra instrucciones para un LLM sobre este comando.",
)


def fail(message: str) -> "typer.Exit":
    """Reemplazo de `click.ClickException` compatible con el fork de click que
    typer usa internamente (`typer._click`): un `click.ClickException` de la
    librería `click` externa no es reconocido por el manejo de excepciones de
    typer y termina propagándose crudo en vez de imprimirse y salir con 1.
    """
    click.echo(f"Error: {message}", err=True)
    raise typer.Exit(code=1)


SCHEMA_VERSION = "1.0.0"


def emitir_json(comando: str, datos: dict) -> None:
    """Imprime `datos` como JSON con envoltorio versionado (`schema_version`, `comando`)."""
    payload = {"schema_version": SCHEMA_VERSION, "herramienta": "moodle-toolbox", "comando": comando}
    payload.update(datos)
    click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
