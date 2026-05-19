import click
from pathlib import Path
from questions.core.validator import GiftAnalyzer
from questions.core.parser import parse_gift_file

@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('-o', '--output', help='Archivo de salida para el informe')
@click.option('-r', '--no-recursive', is_flag=True, help='No buscar recursivamente')
@click.option('-v', '--verbose', is_flag=True, help='Información detallada')
@click.option('-s', '--similarity', type=float, default=0.85, help='Threshold para duplicados')
@click.option('-j', '--json', 'output_json', is_flag=True, help='Salida en JSON')
def validate(path, output, no_recursive, verbose, similarity, output_json):
    """Valida archivos o directorios de preguntas GIFT."""
    path_obj = Path(path)
    
    if path_obj.is_file():
        # Validación de archivo único (simplificada para este comando)
        result = parse_gift_file(str(path_obj))
        if output_json:
            import json
            click.echo(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if result["success"]:
                click.echo(f"✅ Archivo válido: {path}")
                click.echo(f"   Preguntas encontradas: {result['questionCount']}")
            else:
                click.echo(f"❌ Archivo inválido: {path}")
                click.echo(f"   Error: {result['error']['message']}")
    else:
        # Validación de directorio
        analyzer = GiftAnalyzer(
            similarity_threshold=similarity,
            recursive=not no_recursive,
            verbose=verbose
        )
        analyzer.scan_directory(str(path_obj))
        
        if output_json:
            import json
            click.echo(json.dumps(analyzer.to_json(), indent=2, ensure_ascii=False))
        else:
            report = analyzer.generate_report(output)
            if not output:
                click.echo(report)
