import click
import sys

class LazyGroup(click.Group):
    def list_commands(self, ctx):
        return ['ai', 'analyze', 'convert', 'fix', 'format', 'validate', 'xml']

    def get_command(self, ctx, cmd_name):
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
        return super().get_command(ctx, cmd_name)

@click.group(cls=LazyGroup)
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
