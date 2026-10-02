"""`questions dedup`: eliminar duplicados (GIFT y XML), log de eliminaciones y TUI de revisión."""

import contextlib
import io
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from click.testing import CliRunner

from questions.cli import cli
from questions.core.ai import leer_archivos, unidades_de
from questions.core.converter import gift_to_xml
from questions.core.deduplicar import Revision, agrupar, aplicar, registrar

runner = CliRunner()

PREGUNTA = "::Punteros{n}:: ¿Qué guarda un puntero en lenguaje C cuando se declara?\n{{=Una dirección de memoria ~Un entero ~Un carácter ~Nada}}\n"
COMPLETA = ("::Punteros:: ¿Qué guarda un puntero en lenguaje C cuando se declara?\n"
            "{=Una dirección de memoria #Bien ~Un entero #No ~Un carácter #No ~Nada #No}\n")


def _banco(tmp_path, archivos: dict) -> Path:
    raiz = tmp_path / "banco"
    for nombre, contenido in archivos.items():
        ruta = raiz / nombre
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(contenido, encoding="utf-8")
    return raiz


def _leer(raiz):
    with contextlib.redirect_stdout(io.StringIO()):
        archivos = leer_archivos(sorted(raiz.rglob("*.gift")) + sorted(raiz.rglob("*.xml")))
    return archivos, [u for u in unidades_de(archivos) if u.pregunta]


def test_conserva_la_mas_completa_y_detecta_entre_formatos(tmp_path):
    raiz = _banco(tmp_path, {
        "a/p1.gift": PREGUNTA.format(n=""),
        "b/p2.gift": COMPLETA,
        "c/p3.xml": gift_to_xml(PREGUNTA.format(n="")),
    })
    _, unidades = _leer(raiz)
    grupos = agrupar(unidades, 0.9)
    assert len(grupos) == 1
    assert grupos[0].conservada.archivo.name == "p2.gift"
    assert sorted(u.archivo.name for u, _ in grupos[0].duplicadas) == ["p1.gift", "p3.xml"]
    assert agrupar(unidades, 0.9, "primera")[0].conservada.archivo.name == "p1.gift"


def test_no_son_duplicados_con_otra_correcta_otro_tipo_u_otro_enunciado(tmp_path):
    otra_correcta = PREGUNTA.format(n="").replace("=Una dirección", "~Una dirección").replace("~Un entero", "=Un entero")
    otro_enunciado = PREGUNTA.format(n="").replace("cuando se declara", "cuando se libera")
    raiz = _banco(tmp_path, {
        "p1.gift": PREGUNTA.format(n=""),
        "p2.gift": otra_correcta,
        "p3.gift": otro_enunciado,
        "p4.gift": "::Punteros:: ¿Qué guarda un puntero en lenguaje C cuando se declara? {T}\n",
    })
    _, unidades = _leer(raiz)
    assert agrupar(unidades, 0.85) == []


def test_eliminar_en_gift_y_xml_conserva_categorias_y_comentarios_ajenos(tmp_path):
    xml = gift_to_xml(PREGUNTA.format(n="") + "\n::Otra:: ¿Cuánto es 2+2? {=4 ~3 ~5}\n")
    xml = xml.replace("<quiz>", '<quiz>\n<!-- question: 1 -->', 1)
    raiz = _banco(tmp_path, {
        "multi.gift": "$CATEGORY: $course$/C\n\n" + COMPLETA + "\n::Otra:: ¿Cuánto es 3+3? {=6 ~5 ~7}\n",
        "solo.gift": "$CATEGORY: $course$/C\n" + PREGUNTA.format(n=""),
        "banco.xml": xml,
    })
    archivos, unidades = _leer(raiz)
    grupos = agrupar(unidades, 0.9)
    cambios = aplicar(archivos, grupos)
    assert [p.name for p in cambios["borrados"]] == ["solo.gift"]
    assert [p.name for p in cambios["modificados"]] == ["banco.xml"]
    texto = (raiz / "banco.xml").read_text(encoding="utf-8")
    assert "question: 1" not in texto and "¿Cuánto es 2+2?" in texto
    assert [q.findtext("name/text") for q in ET.fromstring(texto).findall("question")] == ["Otra"]
    assert (raiz / "multi.gift").read_text(encoding="utf-8").startswith("$CATEGORY: $course$/C\n\n::Punteros::")


def test_log_con_rutas_completas(tmp_path):
    raiz = _banco(tmp_path, {"u1/a.gift": COMPLETA, "u2/b.gift": PREGUNTA.format(n="")})
    archivos, unidades = _leer(raiz)
    grupos = agrupar(unidades, 0.9)
    cambios = aplicar(archivos, grupos)
    log = tmp_path / "dedup.log"
    assert registrar(grupos, cambios, log, 0.9) == 1
    assert registrar(grupos, cambios, log, 0.9) == 1  # se agrega al final
    lineas = log.read_text(encoding="utf-8").splitlines()
    assert lineas[0].split("\t") == ["fecha", "accion", "eliminado", "conservado", "similitud", "umbral", "tipo", "titulo"]
    campos = lineas[1].split("\t")
    assert campos[1] == "archivo-borrado"
    assert campos[2] == str((raiz / "u2" / "b.gift").resolve()) and Path(campos[2]).is_absolute()
    assert campos[3] == str((raiz / "u1" / "a.gift").resolve())
    assert campos[6:] == ["MC", "Punteros"]
    assert len(lineas) == 3


def test_cli_simula_por_defecto_y_aplica_con_log(tmp_path):
    raiz = _banco(tmp_path, {"u1/a.gift": COMPLETA, "u2/b.gift": PREGUNTA.format(n="")})
    log = tmp_path / "registro.tsv"
    res = runner.invoke(cli, ["dedup", str(raiz), "-r", "-s", "0.9", "--log", str(log)])
    assert res.exit_code == 0, res.output
    assert "Se eliminarían 1" in res.output and (raiz / "u2" / "b.gift").exists() and not log.exists()
    res = runner.invoke(cli, ["dedup", str(raiz), "-r", "-s", "0.9", "--log", str(log), "--aplicar", "--json"])
    datos = json.loads(res.output)
    assert datos["eliminadas"] == 1 and datos["log"] == str(log.resolve())
    assert datos["grupos"][0]["elimina"][0]["archivo"].endswith("b.gift")
    assert not (raiz / "u2" / "b.gift").exists() and log.exists()
    res = runner.invoke(cli, ["dedup", str(raiz), "-r", "-s", "0.9"])
    assert "No hay duplicados" in res.output


def test_revision_manual(tmp_path):
    raiz = _banco(tmp_path, {"a.gift": COMPLETA, "b.gift": PREGUNTA.format(n=""), "c.gift": PREGUNTA.format(n="")})
    _, unidades = _leer(raiz)
    revision = Revision(agrupar(unidades, 0.9))
    principal, b, c = revision.miembros[0]
    assert revision.a_eliminar() == 2
    revision.alternar(0, b)
    revision.alternar(0, principal)  # la principal no se elimina nunca
    assert revision.a_eliminar() == 1 and not revision.se_elimina(principal)
    revision.hacer_principal(0, c)
    assert revision.principal[0] is c and revision.se_elimina(principal) and not revision.se_elimina(c)
    assert [(g.conservada, [u for u, _ in g.duplicadas]) for g in revision.grupos()] == [(c, [principal])]
    revision.conservar_todas(0)
    assert revision.grupos() == []
