import json
from pathlib import Path
import click

from questions.commands.common import llm_option
from questions.core.languagetool_checker import (
    analizar_archivo_banco,
    aplicar_autofix_archivo_banco,
    generar_reporte_markdown_languagetool,
)


@click.command('spellcheck')
@llm_option
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('--server', '-s', help='URL del servidor LanguageTool (por defecto http://localhost:8081 y API pública)')
@click.option('--username', '-u', help='Usuario / email de LanguageTool Premium')
@click.option('--api-key', '-k', help='API Key / Token de LanguageTool Premium')
@click.option('--premium', is_flag=True, help='Forzar uso de la API LanguageTool Premium')
@click.option('--lang', '-l', default='es-AR', help='Código de idioma (default: es-AR)')
@click.option('--ignore-rules', help='Reglas a ignorar separadas por comas')
@click.option('--ignore-words', help='Palabras a ignorar separadas por comas')
@click.option('--fix', '-f', is_flag=True, help='Aplica correcciones ortográficas automáticas')
@click.option('--md', '--output-md', 'output_md', type=click.Path(), help='Genera reporte Markdown')
@click.option('--json', 'output_json', is_flag=True, help='Emite salida estructurada en formato JSON')
def spellcheck(paths, server, username, api_key, premium, lang, ignore_rules, ignore_words, fix, output_md, output_json):
    """Verifica y corrige ortografía y gramática en bancos GIFT y XML usando LanguageTool."""
    if not paths:
        paths = ['.']

    archivos_a_revisar = []
    for p in paths:
        path_obj = Path(p)
        if path_obj.is_file() and path_obj.suffix.lower() in ('.gift', '.xml', '.txt'):
            archivos_a_revisar.append(path_obj)
        elif path_obj.is_dir():
            archivos_a_revisar.extend(sorted(path_obj.glob('**/*.gift')))
            archivos_a_revisar.extend(sorted(path_obj.glob('**/*.xml')))

    if not archivos_a_revisar:
        click.echo("No se encontraron archivos de preguntas (.gift / .xml) para analizar.")
        return

    reglas_ign = set(r.strip() for r in ignore_rules.split(",") if r.strip()) if ignore_rules else None
    palabras_ign = set(w.strip() for w in ignore_words.split(",") if w.strip()) if ignore_words else None

    todos_los_issues = []
    total_arreglos = 0

    for arch in archivos_a_revisar:
        issues = analizar_archivo_banco(
            arch,
            lang=lang,
            server_url=server,
            username=username,
            api_key=api_key,
            premium=premium,
            ignore_words=palabras_ign,
            ignore_rules=reglas_ign,
        )
        if fix and issues:
            total_arreglos += aplicar_autofix_archivo_banco(arch, issues)
        todos_los_issues.extend(issues)

    if output_md:
        md_text = generar_reporte_markdown_languagetool(todos_los_issues)
        out_p = Path(output_md)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(md_text, encoding='utf-8')
        click.echo(f"✓ Reporte Markdown generado en: {out_p}")
        if todos_los_issues:
            raise click.exceptions.Exit(1)
        return

    if output_json:
        res = {
            "total_archivos": len(archivos_a_revisar),
            "total_issues": len(todos_los_issues),
            "total_arreglos": total_arreglos,
            "issues": [i.to_dict() for i in todos_los_issues],
        }
        click.echo(json.dumps(res, indent=2, ensure_ascii=False))
        if todos_los_issues:
            raise click.exceptions.Exit(1)
        return

    if not todos_los_issues:
        click.echo(f"✅ LanguageTool Passed: {len(archivos_a_revisar)} archivos sin faltas ortográficas.")
        return

    click.echo(f"\n⚠️  Observaciones de LanguageTool ({len(todos_los_issues)} encontradas):")
    for iss in todos_los_issues:
        sug = ", ".join(iss.replacements[:2]) if iss.replacements else "—"
        click.echo(f"  - [{iss.file_path.name}] {iss.line}:{iss.column} | {iss.original_word} ({iss.context}) -> {sug}")

    if fix:
        click.echo(f"\n✓ Se aplicaron {total_arreglos} correcciones en los archivos.")

    raise click.exceptions.Exit(1)
