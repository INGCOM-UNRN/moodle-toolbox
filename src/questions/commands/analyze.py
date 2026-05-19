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
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('-r', '--recursive', is_flag=True, help='Buscar recursivamente')
@click.option('-o', '--output', help='Archivo de salida para el informe')
def stats(paths, recursive, output):
    """Genera estadísticas de un directorio de preguntas."""
    if not paths:
        paths = ['.']
        
    analyzer = GiftAnalyzer(recursive=recursive)
    for p in paths:
        path_obj = Path(p)
        if path_obj.is_dir():
            analyzer.scan_directory(str(path_obj))
        else:
            analyzer.analyze_file(path_obj)
            
    analyzer.find_duplicates()
    report = analyzer.generate_report(output)
    if not output:
        click.echo(report)

@analyze.command(name="similar")
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('-r', '--recursive', is_flag=True, help='Buscar recursivamente')
@click.option('-s', '--similarity', type=float, default=0.85, help='Threshold de similitud')
def similar(paths, recursive, similarity):
    """Encuentra preguntas similares en un directorio."""
    if not paths:
        paths = ['.']
        
    analyzer = GiftAnalyzer(similarity_threshold=similarity, recursive=recursive)
    for p in paths:
        path_obj = Path(p)
        if path_obj.is_dir():
            analyzer.scan_directory(str(path_obj))
        else:
            analyzer.analyze_file(path_obj)
            
    analyzer.find_duplicates()
    
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
