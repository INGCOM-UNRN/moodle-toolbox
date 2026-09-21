import os
import sys

import click
import typer

from questions.core.llm_instructions import get_instructions

from questions.commands.ai import ai
from questions.commands.analyze import analyze_app
from questions.commands.config import config_app
from questions.commands.convert import convert_app
from questions.commands.doctor import doctor_cmd
from questions.commands.fix import fix_app
from questions.commands.format import format_cmd
from questions.commands.health import health_cmd
from questions.commands.spellcheck import spellcheck
from questions.commands.split import split
from questions.commands.synth import synth
from questions.commands.tree import tree_app
from questions.commands.ui import ui
from questions.commands.unify import unify
from questions.commands.validate import validate
from questions.commands.xml import xml_app


def llm_callback(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(get_instructions(ctx.info_name))
    ctx.exit()


app = typer.Typer(
    help="Herramientas para la gestión de preguntas de Moodle.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


@app.callback()
def main_callback(
    llm: bool = typer.Option(
        False,
        "--llm",
        callback=llm_callback,
        is_eager=True,
        help="Muestra instrucciones generales para un LLM.",
    ),
):
    """Herramientas para la gestión de preguntas de Moodle."""


app.command("doctor")(doctor_cmd)
app.command("health")(health_cmd)
app.command("ai")(ai)
app.command("validate")(validate)
app.command("format")(format_cmd)
app.command("split")(split)
app.command("unify")(unify)
app.command("synth")(synth)
app.command("ui")(ui)
app.command("spellcheck")(spellcheck)
# Alias históricos de `spellcheck` (LanguageTool).
app.command("languagetool")(spellcheck)
app.command("grammar")(spellcheck)

app.add_typer(config_app, name="config")
app.add_typer(convert_app, name="convert")
app.add_typer(fix_app, name="fix")
app.add_typer(analyze_app, name="analyze")
app.add_typer(tree_app, name="tree")
app.add_typer(xml_app, name="xml")

cli = typer.main.get_command(app)
cli.name = "questions"


def main():
    try:
        cli()
    except Exception as e:
        if os.environ.get("QUESTIONS_DEBUG"):
            raise
        click.echo(f"Error: {e} (QUESTIONS_DEBUG=1 muestra el traceback completo)", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
