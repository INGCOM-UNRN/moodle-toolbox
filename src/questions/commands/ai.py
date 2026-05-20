import click
from pathlib import Path
from questions.core.ai import load_config, process_file_batched
from questions.commands.common import llm_option

@click.command()
@llm_option
@click.argument('inputs', nargs=-1, type=click.Path(exists=True))
@click.option('--mode', type=click.Choice(['improve', 'multiply', 'transform']), default='improve',
              help='Modo: improve (mejorar), multiply (variaciones) o transform (usar prompt personalizado).')
@click.option('--prompt', help='Prompt personalizado o ruta a un archivo .txt con el prompt.')
@click.option('--output', type=click.Path(), help='Directorio de salida (por defecto: output_<mode>).')
@click.option('--model', default='gemini-2.0-flash', help='Modelo de Gemini (default: gemini-2.0-flash).')
@click.option('-r', '--recursive', is_flag=True, help='Procesar subdirectorios recursivamente.')
@click.option('--batch-size', type=int, default=5, help='Número de preguntas por petición a la API (default: 5).')
def ai(inputs, mode, prompt, output, model, recursive, batch_size):
    """Procesamiento de preguntas usando IA (Gemini)."""
    if not inputs:
        click.echo("Error: Debes proporcionar al menos una ruta de entrada.", err=True)
        return

    # Resolver prompt desde archivo si es necesario
    custom_prompt = prompt
    if custom_prompt and Path(custom_prompt).exists() and Path(custom_prompt).is_file():
        try:
            custom_prompt = Path(custom_prompt).read_text(encoding='utf-8').strip()
        except Exception as e:
            click.echo(f"Error al leer el archivo de prompt: {e}", err=True)
            return
    
    # Si se provee prompt y no hay modo explícito de transform o multiply, usar transform
    if prompt and mode == 'improve':
        mode = 'transform'

    try:
        client = load_config()
    except Exception as e:
        click.echo(str(e), err=True)
        return
    
    output_dir = Path(output) if output else Path(f"output_{mode}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for input_str in inputs:
        input_path = Path(input_str)
        if input_path.is_file():
            process_file_batched(client, model, input_path, output_dir, mode, custom_prompt, batch_size)
        elif input_path.is_dir():
            pattern = "**/*.gift" if recursive else "*.gift"
            files = list(input_path.glob(pattern))
            if not files:
                click.echo(f"No se encontraron archivos .gift en {input_str}")
                continue
            for gift_file in files:
                process_file_batched(client, model, gift_file, output_dir, mode, custom_prompt, batch_size)
