import os
import sys
from pathlib import Path
import click
from click.shell_completion import get_completion_class


class LazyGroup(click.Group):
    def list_commands(self, ctx):
        return ['ai', 'analyze', 'config', 'convert', 'fix', 'format', 'split', 'tree', 'validate', 'xml']

    def get_command(self, ctx, cmd_name):
        if cmd_name == 'config':
            from questions.commands.config import config
            return config
        if cmd_name == 'split':
            from questions.commands.split import split
            return split
        if cmd_name == 'ai':
            from questions.commands.ai import ai
            return ai
        if cmd_name == 'validate':
            from questions.commands.validate import validate
            return validate
        if cmd_name == 'format':
            from questions.commands.format import format_cmd
            return format_cmd
        if cmd_name == 'convert':
            from questions.commands.convert import convert
            return convert
        if cmd_name == 'xml':
            from questions.commands.xml import xml
            return xml
        if cmd_name == 'analyze':
            from questions.commands.analyze import analyze
            return analyze
        if cmd_name == 'fix':
            from questions.commands.fix import fix
            return fix
        if cmd_name == 'tree':
            from questions.commands.tree import tree
            return tree
        if cmd_name == 'synth':
            from questions.commands.synth import synth
            return synth
        return super().get_command(ctx, cmd_name)


from questions.core.llm_instructions import get_instructions


def _get_shell():
    shell_path = os.environ.get("SHELL", "bash")
    shell_name = os.path.basename(shell_path)
    if "zsh" in shell_name:
        return "zsh"
    elif "fish" in shell_name:
        return "fish"
    return "bash"


def show_completion_callback(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    shell = _get_shell()
    prog_name = ctx.info_name or "questions"
    complete_var = f"_{prog_name.upper().replace('-', '_')}_COMPLETE"
    comp_cls = get_completion_class(shell)
    if comp_cls:
        comp = comp_cls(ctx.command, {}, prog_name, complete_var)
        click.echo(comp.source())
    ctx.exit()


def install_completion_callback(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    shell = _get_shell()
    prog_name = ctx.info_name or "questions"
    complete_var = f"_{prog_name.upper().replace('-', '_')}_COMPLETE"
    comp_cls = get_completion_class(shell)
    if comp_cls:
        comp = comp_cls(ctx.command, {}, prog_name, complete_var)
        source_code = comp.source()
        home = Path.home()
        comp_dir = home / ".bash_completions"
        if comp_dir.is_dir() and shell == "bash":
            target_file = comp_dir / f"{prog_name}.bash"
            target_file.write_text(source_code, encoding="utf-8")
            click.echo(f"Completion installed in {target_file}")
        else:
            rc_file = home / f".{shell}rc"
            if rc_file.is_file():
                eval_line = f'eval "$({complete_var}={shell}_source {prog_name})"\n'
                content = rc_file.read_text(encoding="utf-8")
                if eval_line not in content:
                    with open(rc_file, "a", encoding="utf-8") as f:
                        f.write(f"\n# {prog_name} completion\n{eval_line}")
                click.echo(f"Completion installed in {rc_file}")
    ctx.exit()


def llm_callback(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(get_instructions(ctx.command.name))
    ctx.exit()


@click.group(cls=LazyGroup)
@click.option('--llm', is_flag=True, callback=llm_callback, 
              expose_value=False, is_eager=True,
              help='Muestra instrucciones generales para un LLM.')
@click.option('--show-completion', is_flag=True, callback=show_completion_callback,
              expose_value=False, is_eager=True,
              help='Show completion for the current shell, to copy it or customize the installation.')
@click.option('--install-completion', is_flag=True, callback=install_completion_callback,
              expose_value=False, is_eager=True,
              help='Install completion for the current shell.')
def cli():
    """Herramientas para la gestión de preguntas de Moodle."""
    pass


def main():
    try:
        cli()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
