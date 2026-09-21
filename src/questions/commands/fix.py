import click
import typer
from pathlib import Path
from typing import List, Optional
from questions.core.formatter import fix_code_indentation, convert_markdown_code_blocks, process_xml_cdata
from questions.core.naming import rename_to_slug, rename_from_title, set_question_title

from questions.commands.common import LLM_OPTION

fix_app = typer.Typer(help="Comandos para corregir problemas comunes.")


@fix_app.callback()
def fix(llm: bool = LLM_OPTION):
    """Comandos para corregir problemas comunes."""


@fix_app.command(name="slugify")
def slugify_cmd(
    paths: Optional[List[str]] = typer.Argument(None, exists=True),
    recursive: bool = typer.Option(False, "-r", "--recursive", help="Procesar recursivamente"),
):
    """Slugifica los nombres de los archivos (minúsculas, sin espacios ni acentos)."""
    if not paths:
        paths = ['.']
    
    files = []
    for p in paths:
        path = Path(p)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            pattern = "**/*" if recursive else "*"
            files.extend([f for f in path.glob(pattern) if f.suffix in ('.gift', '.xml', '.md')])

    modified_count = 0
    for f in sorted(files):
        new_path = rename_to_slug(f)
        if new_path:
            click.echo(f"✓ {f} -> {new_path}")
            modified_count += 1
    
    click.echo(f"\nFinalizado: {modified_count} archivos renombrados.")

@fix_app.command(name="name-from-title")
def name_from_title_cmd(
    paths: Optional[List[str]] = typer.Argument(None, exists=True),
    recursive: bool = typer.Option(False, "-r", "--recursive", help="Procesar recursivamente"),
):
    """Renombra el archivo usando el título interno de la pregunta (slugificado)."""
    if not paths:
        paths = ['.']
    
    files = []
    for p in paths:
        path = Path(p)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            pattern = "**/*" if recursive else "*"
            files.extend([f for f in path.glob(pattern) if f.suffix in ('.gift', '.xml')])

    modified_count = 0
    for f in sorted(files):
        new_path = rename_from_title(f)
        if new_path:
            click.echo(f"✓ {f} -> {new_path}")
            modified_count += 1
    
    click.echo(f"\nFinalizado: {modified_count} archivos renombrados.")

@fix_app.command(name="title-from-name")
def title_from_name_cmd(
    paths: Optional[List[str]] = typer.Argument(None, exists=True),
    recursive: bool = typer.Option(False, "-r", "--recursive", help="Procesar recursivamente"),
):
    """Actualiza el título interno de la pregunta usando el nombre del archivo (sanitizado)."""
    if not paths:
        paths = ['.']
    
    files = []
    for p in paths:
        path = Path(p)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            pattern = "**/*" if recursive else "*"
            files.extend([f for f in path.glob(pattern) if f.suffix in ('.gift', '.xml')])

    modified_count = 0
    for f in sorted(files):
        # Usar el nombre del archivo sin extensión como título
        new_title = f.stem.replace('_', ' ').capitalize()
        if set_question_title(f, new_title):
            click.echo(f"✓ {f}: título actualizado a '{new_title}'")
            modified_count += 1
    
    click.echo(f"\nFinalizado: {modified_count} títulos actualizados.")

@fix_app.command(name="code-indent")
def code_indent(
    paths: Optional[List[str]] = typer.Argument(None, exists=True),
    recursive: bool = typer.Option(False, "-r", "--recursive", help="Procesar recursivamente"),
):
    """Corrige la indentación en bloques de código (```)."""
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

    modified_count = 0
    for f in files:
        content = f.read_text(encoding='utf-8')
        new_content, count = fix_code_indentation(content)
        if count > 0:
            f.write_text(new_content, encoding='utf-8')
            click.echo(f"✓ {f}: {count} líneas corregidas")
            modified_count += 1
    
    click.echo(f"\nFinalizado: {modified_count} archivos modificados.")

@fix_app.command(name="code-chars")
def code_chars(
    paths: Optional[List[str]] = typer.Argument(None, exists=True),
    recursive: bool = typer.Option(False, "-r", "--recursive", help="Procesar recursivamente"),
    to_normal: bool = typer.Option(True, "--to-normal", help="Convertir a normal (default)"),
    to_fullwidth: bool = typer.Option(False, "--to-fullwidth", help="Convertir a fullwidth"),
):
    """Corrige caracteres especiales en bloques de código."""
    if to_fullwidth:
        to_normal = False
        
    if not paths:
        paths = ['.']
    
    files = []
    for p in paths:
        path = Path(p)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            pattern = "**/*" if recursive else "*"
            files.extend([f for f in path.glob(pattern) if f.suffix in ('.gift', '.md', '.xml')])

    modified_count = 0
    for f in files:
        content = f.read_text(encoding='utf-8')
        if f.suffix == '.xml':
            new_content, count = process_xml_cdata(content, to_normal)
        else:
            new_content, count = convert_markdown_code_blocks(content, to_normal)
            
        if count > 0:
            f.write_text(new_content, encoding='utf-8')
            click.echo(f"✓ {f}: {count} bloques corregidos")
            modified_count += 1
    
    click.echo(f"\nFinalizado: {modified_count} archivos modificados.")
