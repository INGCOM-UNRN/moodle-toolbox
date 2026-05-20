import click
from pathlib import Path
from questions.core.ai import load_config, run_global_ai_processing, get_model
from questions.commands.common import llm_option

@click.command()
@llm_option
@click.argument('inputs', nargs=-1, type=click.Path(exists=True))
@click.option('--mode', type=click.Choice(['improve', 'multiply', 'transform']), default='improve',
              help='Modo: improve (mejorar), multiply (variaciones) o transform (usar prompt personalizado).')
@click.option('--prompt', help='Prompt personalizado o ruta a un archivo .txt con el prompt.')
@click.option('--output', type=click.Path(), help='Directorio de salida (por defecto: output_<mode>).')
@click.option('--model', help='Modelo de Gemini (default: configurado o gemini-2.0-flash).')
@click.option('-r', '--recursive', is_flag=True, help='Procesar subdirectorios recursivamente.')
@click.option('--batch-size', type=int, default=5, help='Número de preguntas por petición a la API (default: 5).')
@click.option('-i', '--in-place', is_flag=True, help='Escribir en la misma carpeta que el original.')
@click.option('--suffix', help='Sufijo para los nuevos archivos (usado con --in-place, ej: -ia).')
def ai(inputs, mode, prompt, output, model, recursive, batch_size, in_place, suffix):
    """Procesamiento de preguntas usando IA (Gemini)."""
    if not inputs:
        click.echo("Error: Debes proporcionar al menos una ruta de entrada.", err=True)
        return

    # Resolver modelo
    active_model = model or get_model()

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
    
    output_dir = None
    if not in_place:
        output_dir = Path(output) if output else Path(f"output_{mode}")
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Collect all file paths
    file_paths = []
    for input_str in inputs:
        input_path = Path(input_str)
        if not input_path.exists():
            click.echo(f"❌ Error: La ruta {input_str} no existe.", err=True)
            continue
            
        if input_path.is_file():
            if input_path.suffix == '.gift':
                file_paths.append(input_path)
        elif input_path.is_dir():
            pattern = "**/*.gift" if recursive else "*.gift"
            file_paths.extend(sorted(list(input_path.glob(pattern))))

    if not file_paths:
        click.echo("❌ No se encontraron archivos .gift para procesar.", err=True)
        return

    run_global_ai_processing(
        client=client,
        model_id=active_model,
        file_paths=file_paths,
        output_dir=output_dir,
        mode=mode,
        custom_prompt=custom_prompt,
        batch_size=batch_size,
        in_place=in_place,
        suffix=suffix
    )
