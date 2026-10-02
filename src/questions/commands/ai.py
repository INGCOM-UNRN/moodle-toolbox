from pathlib import Path
from typing import List, Optional

import click
import typer

from questions.core.ai import load_config, run_global_ai_processing, get_model
from questions.core.banco import expandir_rutas
from questions.commands.common import LLM_OPTION, fail


def ai(
    inputs: Optional[List[Path]] = typer.Argument(None, exists=True, help="Archivos .gift/.xml o directorios."),
    llm: bool = LLM_OPTION,
    mode: str = typer.Option(
        "improve", "--mode",
        click_type=click.Choice(["improve", "multiply", "transform", "feedback", "classify"]),
        help="Modo: improve (mejorar), multiply (variaciones), transform (usar prompt personalizado), "
             "feedback (completar sólo la retroalimentación que falta) o classify (Bloom y dificultad con Jev).",
    ),
    prompt: Optional[str] = typer.Option(None, "--prompt", help="Prompt personalizado o ruta a un archivo .txt con el prompt."),
    output: Optional[Path] = typer.Option(None, "--output", help="Directorio de salida (por defecto: output_<mode>)."),
    model: Optional[str] = typer.Option(None, "--model", help="Modelo de Gemini (default: configurado o gemini-2.0-flash)."),
    recursive: bool = typer.Option(False, "-r", "--recursive", help="Procesar subdirectorios recursivamente."),
    batch_size: int = typer.Option(5, "--batch-size", help="Número de preguntas por petición a la API (default: 5)."),
    in_place: bool = typer.Option(False, "-i", "--in-place", help="Escribir en la misma carpeta que el original."),
    suffix: Optional[str] = typer.Option(None, "--suffix", help="Sufijo para los nuevos archivos (usado con --in-place, ej: -ia)."),
    contexto: Optional[str] = typer.Option(
        None, "--contexto", help="classify: curso y nivel de los estudiantes (calibra Bloom y dificultad)."),
    concurrencia: int = typer.Option(4, "--concurrencia", help="classify: solicitudes simultáneas a Jev."),
    reclasificar: bool = typer.Option(False, "--reclasificar", help="classify: volver a clasificar las ya clasificadas."),
    tags: bool = typer.Option(False, "--tags", help="classify: escribir también tags de Moodle (bloom:…, dificultad-…)."),
    sin_cache: bool = typer.Option(
        False, "--sin-cache", help="No usar ni guardar respuestas en la caché (~/.cache/questions)."),
    dry_run: bool = typer.Option(
        False, "-n", "--dry-run",
        help="Mostrar lo que se enviaría (y cuánto se ahorra) sin llamar al modelo ni escribir archivos.",
    ),
):
    """Procesamiento de preguntas GIFT y Moodle XML usando IA (Gemini).

    El modelo recibe GIFT compacto (sin comentarios, categorías ni marcas · y ↵ en el
    código); las preguntas XML se convierten a GIFT y la respuesta se aplica sobre el
    XML original, que conserva sus metadatos.

    --mode classify usa Jev (TypeSafe) para agregar a cada pregunta un comentario con su
    nivel de Bloom y la dificultad (1–5) del enunciado y de las respuestas.
    """
    if not inputs:
        fail("Debes proporcionar al menos una ruta de entrada.")

    active_model = model or get_model()

    # Resolver prompt desde archivo si es necesario
    custom_prompt = prompt
    if custom_prompt and Path(custom_prompt).is_file():
        try:
            custom_prompt = Path(custom_prompt).read_text(encoding='utf-8').strip()
        except Exception as e:
            fail(f"Error al leer el archivo de prompt: {e}")

    # Si se provee prompt y no hay modo explícito de transform o multiply, usar transform
    if prompt and mode == 'improve':
        mode = 'transform'

    file_paths = expandir_rutas(inputs, recursive)
    if not file_paths:
        fail("No se encontraron archivos .gift o .xml para procesar.")

    if mode == "classify":
        from questions.core.clasificacion import CONTEXTO, ClienteJev, run_clasificacion

        cliente = None
        if not dry_run:
            try:
                from questions.core.cache import Cache

                cliente = ClienteJev(cache=Cache("jev", activa=not sin_cache))
            except ValueError as e:
                fail(str(e))
        output_dir = None
        if not in_place and not dry_run:
            output_dir = Path(output) if output else Path("output_classify")
            output_dir.mkdir(parents=True, exist_ok=True)
        run_clasificacion(
            file_paths, output_dir, in_place=in_place, suffix=suffix, contexto=contexto or CONTEXTO,
            concurrencia=concurrencia, reclasificar=reclasificar, tags=tags, dry_run=dry_run, cliente=cliente,
        )
        return

    client = None
    if not dry_run:
        try:
            client = load_config()
        except Exception as e:
            fail(str(e))

    output_dir = None
    if not in_place and not dry_run:
        output_dir = Path(output) if output else Path(f"output_{mode}")
        output_dir.mkdir(parents=True, exist_ok=True)

    run_global_ai_processing(
        client=client,
        model_id=active_model,
        file_paths=file_paths,
        output_dir=output_dir,
        mode=mode,
        custom_prompt=custom_prompt,
        batch_size=batch_size,
        in_place=in_place,
        suffix=suffix,
        dry_run=dry_run,
        usar_cache=not sin_cache,
    )
