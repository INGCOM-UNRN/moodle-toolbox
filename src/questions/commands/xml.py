import click
import xml.etree.ElementTree as ET
from pathlib import Path
from questions.core.xml_tools import ensure_cdata_in_text_blocks, sanitize_filename, remove_tags_from_xml

from questions.commands.common import llm_option

@click.group()
@llm_option
def xml():
    """Herramientas para archivos XML de Moodle."""
    pass

@xml.command()
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('-r', '--recursive', is_flag=True, help='Procesar recursivamente')
def cdata(paths, recursive):
    """Asegura que los bloques <text> usen CDATA."""
    if not paths:
        paths = ['.']
    
    files = []
    for p in paths:
        path = Path(p)
        if path.is_file() and path.suffix == '.xml':
            files.append(path)
        elif path.is_dir():
            pattern = "**/*.xml" if recursive else "*.xml"
            files.extend(list(path.glob(pattern)))

    for f in files:
        content = f.read_text(encoding='utf-8')
        new_content, count = ensure_cdata_in_text_blocks(content)
        if count > 0:
            f.write_text(new_content, encoding='utf-8')
            click.echo(f"✓ {f}: {count} bloques actualizados")

@xml.command()
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('-r', '--recursive', is_flag=True, help='Procesar recursivamente')
def clean_tags(paths, recursive):
    """Elimina tags de las preguntas XML."""
    if not paths:
        paths = ['.']
    
    files = []
    for p in paths:
        path = Path(p)
        if path.is_file() and path.suffix == '.xml':
            files.append(path)
        elif path.is_dir():
            pattern = "**/*.xml" if recursive else "*.xml"
            files.extend(list(path.glob(pattern)))

    for f in files:
        try:
            tree = ET.parse(f)
            root = tree.getroot()
            count = remove_tags_from_xml(root)
            if count > 0:
                tree.write(f, encoding='utf-8', xml_declaration=True)
                click.echo(f"✓ {f}: {count} tags eliminados")
        except Exception as e:
            click.echo(f"Error en {f}: {e}", err=True)

@xml.command()
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
def rename(paths):
    """Renombra archivos XML según el nombre de la pregunta."""
    for p in paths:
        path = Path(p)
        if path.is_file() and path.suffix == '.xml':
            try:
                tree = ET.parse(path)
                root = tree.getroot()
                question = root.find('.//question')
                if question is not None:
                    name_elem = question.find('.//name/text')
                    if name_elem is not None and name_elem.text:
                        new_name = sanitize_filename(name_elem.text) + ".xml"
                        new_path = path.parent / new_name
                        if path != new_path:
                            path.rename(new_path)
                            click.echo(f"✓ {path} -> {new_path}")
            except Exception as e:
                click.echo(f"Error en {path}: {e}", err=True)
