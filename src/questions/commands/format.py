from pathlib import Path
from typing import List, Optional

import click
import typer

from questions.core.banco import expandir_rutas, formato_de
from questions.core.codigo import transformar_archivo
from questions.core.formatter import format_content

from questions.commands.common import LLM_OPTION, fail


def format_cmd(
    paths: Optional[List[Path]] = typer.Argument(None, exists=True),
    llm: bool = LLM_OPTION,
    recursive: bool = typer.Option(False, "-r", "--recursive", help="Procesar recursivamente"),
    dry_run: bool = typer.Option(False, "-n", "--dry-run", help="No aplicar cambios"),
    code: bool = typer.Option(False, "--code", help="Marcar la indentación del código con · (un punto por espacio)"),
    fullwidth: bool = typer.Option(
        False, "--fullwidth",
        help="Proteger el código: símbolos fullwidth y marcas · (indentación) y ↵ (fin de línea)",
    ),
    normal: bool = typer.Option(False, "--normal", help="Restaurar el código a caracteres normales (sin marcas)"),
    marcas: bool = typer.Option(
        True, "--marcas/--sin-marcas", help="Con --fullwidth, agregar las marcas · y ↵ (por defecto, sí)."
    ),
    correct_first: bool = typer.Option(
        False, "--correct-first", help="Ordena las opciones de opción múltiple por porcentaje (la correcta primero)."
    ),
):
    """Formatea archivos GIFT y Moodle XML y transforma el código (fullwidth, · y ↵)."""
    if fullwidth and normal:
        fail("--fullwidth y --normal son excluyentes.")
    if not paths:
        paths = [Path('.')]

    transforma_codigo = code or fullwidth or normal
    extensiones = (".gift", ".xml", ".md") if transforma_codigo else (".gift", ".xml")
    files = expandir_rutas(paths, recursive, extensiones)

    if not files:
        click.echo("No se encontraron archivos para procesar.")
        return

    modified_count = 0

    for f in sorted(files):
        try:
            content = f.read_text(encoding='utf-8')
            formato = formato_de(f) or "md"
            modified = content

            # 1. Código: fullwidth/normal y marcas (antes del formato: en GIFT, el código
            #    protegido ya no confunde la detección del bloque de respuestas).
            if fullwidth:
                modified, _ = transformar_archivo(modified, formato, fullwidth=True, espacios=marcas, saltos=marcas)
            elif normal:
                modified, _ = transformar_archivo(modified, formato, fullwidth=False)
            if code:
                modified, _ = transformar_archivo(modified, formato, fullwidth=None, espacios=True, saltos=False)

            # 2. Formato estándar (GIFT y XML)
            if formato in ("gift", "xml"):
                modified = format_content(modified, formato, correct_first=correct_first)

            if content != modified:
                if not dry_run:
                    f.write_text(modified, encoding='utf-8')
                status = "[SIMULACIÓN]" if dry_run else "[MODIFICADO]"
                click.echo(f"{status} {f}")
                modified_count += 1
        except Exception as e:
            click.echo(f"Error procesando {f}: {e}", err=True)

    click.echo(f"\nResumen: {len(files)} archivos procesados, {modified_count} modificados.")
