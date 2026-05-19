import click
from questions.core.llm_instructions import get_instructions

def llm_callback(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(get_instructions(ctx.command.name))
    ctx.exit()

def llm_option(f):
    return click.option('--llm', is_flag=True, callback=llm_callback, 
                        expose_value=False, is_eager=True,
                        help='Muestra instrucciones para un LLM sobre este comando.')(f)
