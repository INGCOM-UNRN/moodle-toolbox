import click
from pathlib import Path
from questions.core.splitter import split_file
from questions.commands.common import llm_option

@click.command()
@llm_option
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('-r', '--recursive', is_flag=True, help='Procesar recursivamente.')
@click.option('--remove', is_flag=True, help='Borrar el archivo original después de dividirlo.')
def split(paths, recursive, remove):
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
