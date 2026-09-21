from pathlib import Path
from typing import List, Optional

import click
import typer

from questions.core.splitter import split_file
from questions.commands.common import LLM_OPTION


def split(
    paths: Optional[List[Path]] = typer.Argument(None, exists=True),
    llm: bool = LLM_OPTION,
    recursive: bool = typer.Option(False, "-r", "--recursive", help="Procesar recursivamente."),
    remove: bool = typer.Option(False, "--remove", help="Borrar el archivo original después de dividirlo."),
):
    """Divide archivos GIFT con múltiples preguntas en archivos individuales."""
    if not paths:
        paths = ['.']
        
    files = []
    for p in paths:
        path = Path(p)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            pattern = "**/*.gift" if recursive else "*.gift"
            files.extend(list(path.glob(pattern)))

    if not files:
        click.echo("No se encontraron archivos GIFT.")
        return

    total_new_files = 0
    total_split_files = 0
    
    for f in sorted(files):
        try:
            count = split_file(f)
            if count > 0:
                click.echo(f"✓ {f}: dividido en {count} archivos")
                total_new_files += count
                total_split_files += 1
                if remove:
                    f.unlink()
        except Exception as e:
            click.echo(f"Error procesando {f}: {e}", err=True)

    click.echo(f"\nResumen: {total_split_files} archivos divididos, {total_new_files} nuevos archivos creados.")
