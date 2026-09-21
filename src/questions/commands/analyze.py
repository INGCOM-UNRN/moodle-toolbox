from pathlib import Path
from typing import List, Optional

import click
import typer

from questions.core.validator import GiftAnalyzer

from questions.commands.common import LLM_OPTION

analyze_app = typer.Typer(help="Análisis y estadísticas de preguntas.")


@analyze_app.callback()
def analyze(llm: bool = LLM_OPTION):
    """Análisis y estadísticas de preguntas."""


@analyze_app.command(name="stats")
def stats(
    paths: Optional[List[str]] = typer.Argument(None, exists=True),
    recursive: bool = typer.Option(False, "-r", "--recursive", help="Buscar recursivamente"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Archivo de salida para el informe"),
):
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

@analyze_app.command(name="similar")
def similar(
    paths: Optional[List[str]] = typer.Argument(None, exists=True),
    recursive: bool = typer.Option(False, "-r", "--recursive", help="Buscar recursivamente"),
    similarity: float = typer.Option(0.85, "-s", "--similarity", help="Threshold de similitud"),
):
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
