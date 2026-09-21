from pathlib import Path
from typing import List, Optional

import click
import typer

from questions.core.formatter import format_gift_content, fix_code_indentation, convert_markdown_code_blocks, process_xml_cdata

from questions.commands.common import LLM_OPTION


def format_cmd(
    paths: Optional[List[Path]] = typer.Argument(None, exists=True),
    llm: bool = LLM_OPTION,
    recursive: bool = typer.Option(False, "-r", "--recursive", help="Procesar recursivamente"),
    dry_run: bool = typer.Option(False, "-n", "--dry-run", help="No aplicar cambios"),
    code: bool = typer.Option(False, "--code", help="Ajustar indentación en bloques de código (```)"),
    fullwidth: bool = typer.Option(False, "--fullwidth", help="Convertir caracteres de código a fullwidth"),
    normal: bool = typer.Option(False, "--normal", help="Convertir caracteres de código a normal (default)"),
    correct_first: bool = typer.Option(False, "--correct-first", help="Mueve la respuesta correcta al principio (solo MC)."),
):
    """Formatea archivos GIFT y ajusta bloques de código."""
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
            if code or fullwidth or normal:
                pattern_md = "**/*.md" if recursive else "*.md"
                files.extend(list(path.glob(pattern_md)))
                pattern_xml = "**/*.xml" if recursive else "*.xml"
                files.extend(list(path.glob(pattern_xml)))

    if not files:
        click.echo("No se encontraron archivos para procesar.")
        return

    to_normal = not fullwidth
    modified_count = 0
    
    for f in sorted(files):
        try:
            content = f.read_text(encoding='utf-8')
            modified = content
            
            # 1. Formateo GIFT (solo para archivos .gift)
            if f.suffix == '.gift':
                modified = format_gift_content(modified, correct_first=correct_first)
            
            # 2. Fix indentación código (opcional)
            if code:
                modified, _ = fix_code_indentation(modified)
            
            # 3. Conversión de caracteres (opcional)
            if fullwidth or normal:
                if f.suffix == '.xml':
                    modified, _ = process_xml_cdata(modified, to_normal)
                else:
                    modified, _ = convert_markdown_code_blocks(modified, to_normal)
            
            if content != modified:
                if not dry_run:
                    f.write_text(modified, encoding='utf-8')
                status = "[SIMULACIÓN]" if dry_run else "[MODIFICADO]"
                click.echo(f"{status} {f}")
                modified_count += 1
        except Exception as e:
            click.echo(f"Error procesando {f}: {e}", err=True)

    click.echo(f"\nResumen: {len(files)} archivos procesados, {modified_count} modificados.")
