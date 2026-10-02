"""Comando para eliminar preguntas duplicadas (GIFT y Moodle XML)."""

import contextlib
import io
from pathlib import Path
from typing import List, Optional

import click
import typer

from questions.commands.common import LLM_OPTION, con_configuracion, emitir_json, fail
from questions.core.ai import leer_archivos, unidades_de
from questions.core.banco import expandir_rutas
from questions.core.deduplicar import CRITERIOS, a_json, agrupar, aplicar, plan, registrar


def dedup(
    ctx: typer.Context,
    paths: Optional[List[Path]] = typer.Argument(None, exists=True, help="Archivos .gift/.xml o directorios."),
    llm: bool = LLM_OPTION,
    recursive: bool = typer.Option(False, "-r", "--recursive", help="Buscar recursivamente."),
    similarity: float = typer.Option(
        0.95, "-s", "--similarity", min=0.0, max=1.0,
        help="Similitud mínima (0–1) para considerar dos preguntas duplicadas.",
    ),
    conservar: str = typer.Option(
        "completa", "--conservar", click_type=click.Choice(CRITERIOS),
        help="Cuál se conserva de cada grupo: la más completa (feedback, título, opciones) o la primera.",
    ),
    aplicar_cambios: bool = typer.Option(
        False, "--aplicar", help="Eliminar de verdad (sin esta opción sólo se muestra lo que se eliminaría).",
    ),
    log: Path = typer.Option(
        Path("dedup.log"), "--log",
        help="Con --aplicar, log (TSV, se agrega al final) de cada pregunta eliminada con las rutas completas.",
    ),
    confirmar_jev: bool = typer.Option(
        False, "--confirmar-jev",
        help="Confirmar cada par con Jev (TypeSafe): sólo quedan los que evalúan exactamente lo mismo.",
    ),
    tui: bool = typer.Option(
        False, "--tui", help="Revisar los grupos en una interfaz de terminal y decidir cuáles eliminar (extra 'tui').",
    ),
    output_json: bool = typer.Option(False, "--json", help="Emite los grupos de duplicados como JSON versionado."),
):
    """Elimina preguntas duplicadas según un umbral de similitud (GIFT y Moodle XML).

    Sólo compara preguntas del mismo tipo y conserva, de cada grupo, la más completa;
    elimina las que son similares a ella por encima del umbral. Sin --aplicar sólo
    muestra lo que haría. Al aplicar, cada eliminación queda en --log con la ruta
    completa del archivo (de ella se infieren las categorías).
    """
    opciones = con_configuracion(ctx, paths, "dedup", {"similarity": (similarity, "umbral"), "conservar": conservar})
    similarity, conservar = float(opciones["similarity"]), opciones["conservar"]
    archivos_rutas = expandir_rutas(paths or [Path(".")], recursive)
    if not archivos_rutas:
        fail("No se encontraron archivos de preguntas (.gift / .xml).")

    with contextlib.redirect_stdout(io.StringIO()):
        archivos = leer_archivos(archivos_rutas)
    unidades = [u for u in unidades_de(archivos) if u.pregunta is not None]
    grupos = agrupar(unidades, similarity, conservar)
    descartados = []
    if confirmar_jev and grupos:
        from questions.core.clasificacion import ClienteJev
        from questions.core.deduplicar import confirmar_con_jev

        try:
            from questions.core.cache import Cache

            cliente = ClienteJev(cache=Cache("jev"))
        except ValueError as e:
            fail(str(e))
        grupos, descartados = confirmar_con_jev(grupos, cliente)
        if not output_json:
            for d in descartados:
                click.echo(f"≠ Jev: no son la misma pregunta ({d['probabilidad']:.2f}): {d['descartado']} "
                           f"↔ {d['conserva']}")

    if tui:
        if not grupos:
            click.echo(f"No hay duplicados con similitud ≥ {similarity:g} entre {len(unidades)} preguntas.")
            return
        try:
            from questions.tui.dedup import DedupApp
        except ImportError:
            fail('La interfaz de terminal requiere el extra opcional \'tui\': '
                 'uv tool install "questions[tui] @ git+https://github.com/INGCOM-UNRN/moodle-toolbox"')
        from questions.core.deduplicar import Revision

        resultado = DedupApp(archivos, Revision(grupos), similarity, log).run()
        if resultado:
            click.echo(f"Se eliminaron {resultado['eliminadas']} preguntas ({len(resultado['modificados'])} archivos "
                       f"modificados, {len(resultado['borrados'])} borrados). Registro: {log.resolve()}")
        else:
            click.echo("No se eliminó nada.")
        return

    cambios = aplicar(archivos, grupos) if aplicar_cambios else plan(archivos, grupos)
    eliminadas = sum(len(g.duplicadas) for g in grupos)
    registradas = registrar(grupos, cambios, log, similarity) if aplicar_cambios else 0

    if output_json:
        emitir_json("dedup", {
            "umbral": similarity,
            "aplicado": aplicar_cambios,
            "preguntas": len(unidades),
            "eliminadas": eliminadas,
            "grupos": a_json(grupos),
            "archivos_modificados": [str(r) for r in cambios["modificados"]],
            "archivos_borrados": [str(r) for r in cambios["borrados"]],
            **({"log": str(log.resolve())} if registradas else {}),
            **({"descartados_jev": descartados} if confirmar_jev else {}),
        })
        return

    if not grupos:
        click.echo(f"No hay duplicados con similitud ≥ {similarity:g} entre {len(unidades)} preguntas.")
        return

    for g in grupos:
        click.echo(f"✓ Se conserva: {g.conservada.archivo} — {g.conservada.pregunta.title or '<sin título>'}")
        for u, s in g.duplicadas:
            click.echo(f"    ✗ {s:.3f}  {u.archivo} — {u.pregunta.title or '<sin título>'}")
    verbo = "Se eliminaron" if aplicar_cambios else "Se eliminarían"
    click.echo(f"\n{verbo} {eliminadas} preguntas duplicadas en {len(grupos)} grupos "
               f"({len(cambios['modificados'])} archivos modificados, {len(cambios['borrados'])} borrados).")
    if not aplicar_cambios:
        click.echo("Simulación: no se modificó nada. Usá --aplicar para eliminarlas.")
    elif registradas:
        click.echo(f"Registro de las eliminaciones: {log.resolve()}")
