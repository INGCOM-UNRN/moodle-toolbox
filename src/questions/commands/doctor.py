"""Comando doctor para diagnóstico del entorno de moodle-toolbox (questions)."""

import json
import shutil
import sys
import click


@click.command("doctor")
@click.option("--json", "json_output", is_flag=True, help="Emitir diagnóstico en formato JSON estructurado.")
def doctor_cmd(json_output: bool):
    """Verifica el estado del entorno de MOODLE-TOOLBOX (Python, TatSu, LanguageTool)."""
    diagnostico = []

    py_ok = sys.version_info >= (3, 10)
    diagnostico.append({
        "componente": "Python Runtime",
        "estado": "OK" if py_ok else "ERROR",
        "requerido": True,
        "detalle": f"Python {sys.version.split()[0]}",
    })

    try:
        import tatsu
        tatsu_ok = True
        tatsu_detail = f"TatSu {getattr(tatsu, '__version__', 'instalado')}"
    except ImportError:
        tatsu_ok = False
        tatsu_detail = "No instalado (requerido para el parser de preguntas GIFT)"

    diagnostico.append({
        "componente": "Parser TatSu (GIFT)",
        "estado": "OK" if tatsu_ok else "ERROR",
        "requerido": True,
        "detalle": tatsu_detail,
    })

    lt_path = shutil.which("languagetool") or shutil.which("languagetool-server")
    diagnostico.append({
        "componente": "LanguageTool Local",
        "estado": "OK" if lt_path else "ADVERTENCIA",
        "requerido": False,
        "detalle": lt_path or "No encontrado (se usará API remota si no hay servidor local)",
    })

    todo_ok = py_ok and tatsu_ok

    if json_output:
        payload = {
            "schema_version": "1.0.0",
            "herramienta": "moodle-toolbox",
            "ok": todo_ok,
            "componentes": diagnostico,
        }
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        sys.exit(0 if todo_ok else 1)

    try:
        from rich.console import Console
        from rich.table import Table
        console = Console()
        tabla = Table(title="🏥 Diagnóstico del Entorno MOODLE-TOOLBOX (doctor)", border_style="cyan")
        tabla.add_column("Componente", style="bold white")
        tabla.add_column("Estado", justify="center")
        tabla.add_column("Detalle")

        for c in diagnostico:
            color = "bold green" if c["estado"] == "OK" else ("bold yellow" if c["estado"] == "ADVERTENCIA" else "bold red")
            simbolo = "✓" if c["estado"] == "OK" else ("⚠️" if c["estado"] == "ADVERTENCIA" else "✗")
            tabla.add_row(c["componente"], f"[{color}]{simbolo} {c['estado']}[/{color}]", c["detalle"])

        console.print(tabla)
    except ImportError:
        click.echo("🏥 Diagnóstico del Entorno MOODLE-TOOLBOX (doctor)")
        for c in diagnostico:
            click.echo(f" - {c['componente']}: {c['estado']} ({c['detalle']})")

    if not todo_ok:
        sys.exit(1)
