import click
from pathlib import Path
from questions.core.converter import convert_html_tags_to_markdown

from questions.commands.common import llm_option

@click.group()
@llm_option
def convert():
    """Comandos para convertir entre formatos."""
    pass

@convert.command(name="html-to-md")
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('-r', '--recursive', is_flag=True, help='Procesar recursivamente')
def html_to_md(paths, recursive):
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

# Por ahora dejo los otros como placeholders o los integro si son vitales
