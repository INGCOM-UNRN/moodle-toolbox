import click
from questions.core.ai import main as ai_main

from questions.commands.common import llm_option

@click.command()
@llm_option
@click.argument('args', nargs=-1)
def ai(args):
    """Procesamiento de preguntas usando IA (Gemini)."""
    # Para mantener compatibilidad rápida, llamamos al main original
    # En una refactorización más profunda, moveríamos la lógica aquí
    import sys
    sys.argv = ['questions ai'] + list(args)
    ai_main()
