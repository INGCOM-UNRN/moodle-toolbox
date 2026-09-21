import click
import re
import typer
from pathlib import Path
from typing import List, Optional
from questions.core.converter import (
    convert_html_tags_to_markdown,
    xml_to_gift,
    gift_to_xml,
)

from questions.commands.common import LLM_OPTION, fail

convert_app = typer.Typer(help="Comandos para convertir entre formatos.")


@convert_app.callback()
def convert(llm: bool = LLM_OPTION):
    """Comandos para convertir entre formatos."""


@convert_app.command(name="html-to-md")
def html_to_md(
    paths: Optional[List[str]] = typer.Argument(None, exists=True),
    recursive: bool = typer.Option(False, "-r", "--recursive", help="Procesar recursivamente"),
):
    """Convierte tags HTML a Markdown en archivos XML o GIFT."""
    if not paths:
        paths = ['.']
    
    files = []
    for p in paths:
        path = Path(p)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            pattern = "**/*" if recursive else "*"
            files.extend([f for f in path.glob(pattern) if f.suffix in ('.xml', '.gift', '.md')])

    modified_count = 0
    for f in files:
        try:
            content = f.read_text(encoding='utf-8')
            # Si es XML, procesar dentro de CDATA
            if f.suffix == '.xml':
                def replace_cdata(match):
                    return f"<![CDATA[{convert_html_tags_to_markdown(match.group(1))}]]>"
                import re
                modified = re.sub(r'<!\[CDATA\[(.*?)\]\]>', replace_cdata, content, flags=re.DOTALL)
                # También cambiar format="html" a format="markdown"
                modified = modified.replace('format="html"', 'format="markdown"')
            else:
                modified = convert_html_tags_to_markdown(content)
            
            if content != modified:
                f.write_text(modified, encoding='utf-8')
                click.echo(f"✓ {f}")
                modified_count += 1
        except Exception as e:
            click.echo(f"Error en {f}: {e}", err=True)
    
    click.echo(f"\nFinalizado: {modified_count} archivos modificados.")


def _leer_entrada(path: Path | None) -> str:
    if path is None or str(path) == "-":
        import sys
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


@convert_app.command(name="xml-to-gift")
def xml_to_gift_cmd(
    path: Optional[str] = typer.Argument(None),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Archivo GIFT de salida (por defecto, stdout)."),
):
    """Convierte Moodle XML a GIFT (PATH o stdin; '-' para stdin)."""
    contenido = _leer_entrada(Path(path) if path else None)
    try:
        resultado = xml_to_gift(contenido)
    except Exception as e:
        fail(f"No se pudo convertir el XML: {e}")
    if output:
        Path(output).write_text(resultado, encoding="utf-8")
        click.echo(f"✓ GIFT generado: {output}")
    else:
        click.echo(resultado)


@convert_app.command(name="gift-to-xml")
def gift_to_xml_cmd(
    path: Optional[str] = typer.Argument(None),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Archivo XML de salida (por defecto, stdout)."),
):
    """Convierte GIFT a Moodle XML (PATH o stdin; '-' para stdin)."""
    contenido = _leer_entrada(Path(path) if path else None)
    try:
        resultado = gift_to_xml(contenido)
    except Exception as e:
        fail(f"No se pudo convertir el GIFT: {e}")
    if output:
        Path(output).write_text(resultado, encoding="utf-8")
        click.echo(f"✓ XML generado: {output}")
    else:
        click.echo(resultado)
