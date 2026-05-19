import click
from pathlib import Path
from questions.core.validator import GiftAnalyzer

from questions.commands.common import llm_option

@click.group()
@llm_option
def analyze():
    """Análisis y estadísticas de preguntas."""
    pass

@analyze.command(name="stats")
@click.argument('path', type=click.Path(exists=True))
@click.option('-r', '--no-recursive', is_flag=True, help='No buscar recursivamente')
@click.option('-o', '--output', help='Archivo de salida para el informe')
def stats(path, no_recursive, output):
    """Genera estadísticas de un directorio de preguntas."""
    path_obj = Path(path)
    if path_obj.is_dir():
        analyzer = GiftAnalyzer(recursive=not no_recursive)
        analyzer.scan_directory(str(path_obj))
        report = analyzer.generate_report(output)
        if not output:
            click.echo(report)
    else:
        click.echo("Por favor, especifica un directorio.", err=True)

@analyze.command(name="similar")
@click.argument('path', type=click.Path(exists=True))
@click.option('-s', '--similarity', type=float, default=0.85, help='Threshold de similitud')
def similar(path, similarity):
    """Encuentra preguntas similares en un directorio."""
    analyzer = GiftAnalyzer(similarity_threshold=similarity)
    analyzer.scan_directory(str(path))
    
    if analyzer.duplicates:
        click.echo(f"Se encontraron {len(analyzer.duplicates)} pares de preguntas similares:")
        for dup in analyzer.duplicates:
            q1 = analyzer.all_questions[dup["index1"]]
            q2 = analyzer.all_questions[dup["index2"]]
            click.echo(f"- Similitud {dup['similarity']:.3f}:")
            click.echo(f"  A: {q1['filepath']} - {q1['title']}")
            click.echo(f"  B: {q2['filepath']} - {q2['title']}")
    else:
        click.echo("No se encontraron duplicados significativos.")
