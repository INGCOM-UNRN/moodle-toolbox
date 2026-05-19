import click
from pathlib import Path
from questions.core.validator import GiftAnalyzer
from questions.core.parser import parse_gift_file

from questions.commands.common import llm_option

@click.command()
@llm_option
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('-o', '--output', help='Archivo de salida para el informe')
@click.option('-r', '--recursive', is_flag=True, help='Buscar recursivamente')
@click.option('-v', '--verbose', is_flag=True, help='Información detallada')
@click.option('-s', '--similarity', type=float, default=0.85, help='Threshold para duplicados')
@click.option('-j', '--json', 'output_json', is_flag=True, help='Salida en JSON')
def validate(paths, output, recursive, verbose, similarity, output_json):
    """Valida archivos o directorios de preguntas GIFT."""
    if not paths:
        paths = ['.']
        
    all_results = []
    analyzer = GiftAnalyzer(
        similarity_threshold=similarity,
        recursive=recursive,
        verbose=verbose
    )
    
    files_to_validate = []
    dirs_to_validate = []
    
    for p in paths:
        path_obj = Path(p)
        if path_obj.is_file():
            files_to_validate.append(path_obj)
        else:
            dirs_to_validate.append(path_obj)

    # Procesar archivos individuales
    for f in files_to_validate:
        analyzer.analyze_file(f)
        if output_json:
            result = parse_gift_file(str(f))
            all_results.append(result)
        else:
            # We already echo something? GiftAnalyzer.analyze_file doesn't echo.
            # But parse_gift_file does.
            result = parse_gift_file(str(f))
            if result["success"]:
                click.echo(f"✅ Archivo válido: {f}")
                click.echo(f"   Preguntas encontradas: {result['questionCount']}")
            else:
                click.echo(f"❌ Archivo inválido: {f}")
                click.echo(f"   Error: {result['error']['message']}")
                
    # Procesar directorios
    for d in dirs_to_validate:
        analyzer.scan_directory(str(d))
        
    if not output_json:
        if dirs_to_validate or files_to_validate:
            # find_duplicates is called by scan_directory, but if we only have files, 
            # we need to call it explicitly. scan_directory already calls it.
            # To be safe and avoid missing duplicates between files and dirs:
            analyzer.find_duplicates()
            report = analyzer.generate_report(output)
            if not output:
                click.echo(report)
    else:
        import json
        output_data = {
            "files": all_results,
            "directories": analyzer.to_json() if dirs_to_validate else None
        }
        click.echo(json.dumps(output_data, indent=2, ensure_ascii=False))
