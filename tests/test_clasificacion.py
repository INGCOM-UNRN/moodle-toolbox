"""Clasificación con Jev (Bloom y dificultad) con un cliente simulado, sin red."""

import io
import json
import urllib.error
import xml.etree.ElementTree as ET

import pytest
from click.testing import CliRunner

from questions.cli import cli
from questions.core import clasificacion as cl
from questions.core.moodle_xml import parse_moodle_xml
from questions.core.parser import GiftParser, parse_gift

runner = CliRunner()

GIFT = """// [tag:java] [id:J-1]
::Igualdad::[markdown]¿Qué imprime?
```java
if (a ＝＝ b) ｛
····System.out.println（＂si＂）；↵
｝
```
{
    =`si` #Bien, compara referencias
    ~nada
    ~error
}

::VF:: ¿Java compila a bytecode? {T}
"""

XML = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <!-- question: 1854266 -->
  <question type="multichoice">
    <name><text>Punteros</text></name>
    <questiontext format="markdown"><text><![CDATA[¿Qué imprime `*p`?]]></text></questiontext>
    <answer fraction="100"><text>5</text><feedback><text>Porque p apunta a x</text></feedback></answer>
    <answer fraction="0"><text>0</text></answer>
    <tags><tag><text>punteros</text></tag><tag><text>bloom:recordar</text></tag></tags>
  </question>
</quiz>
"""


def respuesta(bloom="aplicar", enunciado=2.4, respuestas=1.5, modelo="jev-1.13.0"):
    datos = {
        "model": modelo,
        "answers": {
            "bloom": {"type": "choice", "choice": bloom, "confidence": 0.81},
            "enunciado": {"type": "score", "score": enunciado, "confidence": 0.7},
        },
        "usage": {"input_tokens": 100, "output_tokens": 10},
    }
    if respuestas is not None:
        datos["answers"]["respuestas"] = {"type": "score", "score": respuestas, "confidence": 0.6}
    return datos


class Cliente:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.pedidos = []

    def consultar(self, state, questions):
        self.pedidos.append((state, questions))
        return respuesta(respuestas=self.kwargs.get("respuestas", 1.5) if "respuestas" in questions else None,
                         bloom=self.kwargs.get("bloom", "aplicar"))


def test_estado_sin_feedback_con_codigo_en_ascii_y_correcta_marcada():
    q = GiftParser()._manual_parse(GIFT)[0]
    datos = cl.estado(q, "P2 (Java)")
    assert datos["contexto"] == "P2 (Java)" and datos["tipo"] == "opción múltiple"
    assert 'if (a == b) {\n    System.out.println("si");\n}' in datos["enunciado"]
    assert datos["opciones"][0] == {"texto": "`si`", "correcta": True}
    assert "compara referencias" not in json.dumps(datos, ensure_ascii=False)


def test_dificultad_de_respuestas_solo_con_opciones():
    mc, vf = GiftParser()._manual_parse(GIFT)
    assert set(cl.preguntas_jev(mc)) == {"bloom", "enunciado", "respuestas"}
    assert set(cl.preguntas_jev(vf)) == {"bloom", "enunciado"}
    assert cl.estado(vf)["respuesta_correcta"] == "verdadero"
    assert len(cl.preguntas_jev(mc)["enunciado"]["criteria"]) == 5


def test_clasificacion_y_comentario():
    c = cl.Clasificacion.desde_respuesta(respuesta())
    assert (c.bloom, c.enunciado, c.respuestas) == ("aplicar", 3.4, 2.5)
    assert c.comentario() == ("[bloom:B3-aplicar] [dificultad-enunciado:3.4/5] [dificultad-respuestas:2.5/5] "
                              "[clasificacion:jev-1.13.0 confianza=0.81,0.7,0.6]")
    assert c.tags() == ["bloom:aplicar", "dificultad-enunciado:3", "dificultad-respuestas:2"]


def test_gift_agrega_el_comentario_y_no_repite_al_volver_a_correr(tmp_path):
    banco = tmp_path / "b.gift"
    banco.write_text(GIFT, encoding="utf-8")
    cliente = Cliente()
    datos = cl.run_clasificacion([banco], None, in_place=True, cliente=cliente, tags=True)
    assert datos["clasificadas"] == 2 and datos["uso"] == {"input_tokens": 200, "output_tokens": 20}
    texto = banco.read_text(encoding="utf-8")
    assert texto.startswith("// [tag:java] [id:J-1]\n// [bloom:B3-aplicar] [dificultad-enunciado:3.4/5]")
    assert "::VF::" in texto and texto.count("[clasificacion:") == 2
    # El resto queda igual, y los tags llegan al modelo (Moodle los importa).
    preguntas = parse_gift(texto)["questions"]
    assert preguntas[0]["tags"] == ["java", "bloom:aplicar", "dificultad-enunciado:3", "dificultad-respuestas:2"]
    assert preguntas[0]["choices"] == parse_gift(GIFT)["questions"][0]["choices"]

    otro = Cliente()
    assert cl.run_clasificacion([banco], None, in_place=True, cliente=otro) is None
    assert otro.pedidos == []

    cl.run_clasificacion([banco], None, in_place=True, cliente=Cliente(bloom="analizar"), reclasificar=True)
    texto = banco.read_text(encoding="utf-8")
    assert texto.count("[clasificacion:") == 2 and "[bloom:B4-analizar]" in texto and "B3-aplicar" not in texto


def test_xml_comentario_antes_de_la_pregunta_y_tags_reemplazados(tmp_path):
    banco = tmp_path / "b.xml"
    banco.write_text(XML, encoding="utf-8")
    for _ in range(2):
        cl.run_clasificacion([banco], None, in_place=True, cliente=Cliente(), tags=True, reclasificar=True)
    texto = banco.read_text(encoding="utf-8")
    assert "<!-- question: 1854266 -->" in texto
    assert texto.count("[clasificacion:") == 1
    assert texto.index("[bloom:B3-aplicar]") < texto.index("<question")
    q = parse_moodle_xml(texto)[0]
    assert q.tags == ["punteros", "bloom:aplicar", "dificultad-enunciado:3", "dificultad-respuestas:2"]
    assert ET.fromstring(texto).find("question/answer/feedback/text").text == "Porque p apunta a x"


def test_salida_en_directorio_y_errores_no_detienen_el_resto(tmp_path, capsys):
    (tmp_path / "in").mkdir()
    (tmp_path / "in" / "b.gift").write_text(GIFT, encoding="utf-8")

    class Falla(Cliente):
        def consultar(self, state, questions):
            if state["tipo"] == "verdadero/falso":
                raise RuntimeError("TypeSafe respondió 422")
            return super().consultar(state, questions)

    datos = cl.run_clasificacion([tmp_path / "in" / "b.gift"], tmp_path / "out", cliente=Falla())
    assert datos["errores"] == 1 and datos["clasificadas"] == 1
    salida = (tmp_path / "out" / "b_classify.gift").read_text(encoding="utf-8")
    assert salida.count("[clasificacion:") == 1
    assert (tmp_path / "in" / "b.gift").read_text(encoding="utf-8") == GIFT
    assert "422" in capsys.readouterr().out


def test_cliente_reintenta_ante_429_y_no_ante_401(monkeypatch):
    llamadas = []

    def urlopen(pedido, timeout):
        llamadas.append(json.loads(pedido.data))
        if len(llamadas) == 1:
            raise urllib.error.HTTPError(pedido.full_url, 429, "lento", {}, io.BytesIO(b"rate"))
        return io.BytesIO(json.dumps(respuesta()).encode())

    monkeypatch.setattr(cl.urllib.request, "urlopen", urlopen)
    cliente = cl.ClienteJev(clave="k", espera=0)
    assert cliente.consultar({"a": 1}, {"q": {}})["answers"]["bloom"]["choice"] == "aplicar"
    assert len(llamadas) == 2 and llamadas[0]["model"] == "jev-latest"

    def no_autorizado(pedido, timeout):
        llamadas.append(1)
        raise urllib.error.HTTPError(pedido.full_url, 401, "no", {}, io.BytesIO(b"bad key"))

    llamadas.clear()
    monkeypatch.setattr(cl.urllib.request, "urlopen", no_autorizado)
    with pytest.raises(RuntimeError, match="401"):
        cliente.consultar({}, {})
    assert len(llamadas) == 1


def test_resolver_clave_desde_env(tmp_path, monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.setattr(cl.Path, "home", lambda: tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cl.resolver_clave() is None
    (tmp_path / ".env").write_text('OTRA=1\nTYPESAFE_API_KEY="apikey_x"\n', encoding="utf-8")
    assert cl.resolver_clave() == "apikey_x"
    monkeypatch.setenv("TYPESAFE_API_KEY", "apikey_env")
    assert cl.resolver_clave() == "apikey_env"


def test_cli_classify_dry_run_sin_clave(tmp_path, monkeypatch):
    monkeypatch.setattr(cl, "resolver_clave", lambda: None)
    (tmp_path / "b.xml").write_text(XML, encoding="utf-8")
    res = runner.invoke(cli, ["ai", str(tmp_path), "--mode", "classify", "--dry-run", "--contexto", "P1 (C)"])
    assert res.exit_code == 0, res.output
    assert '"contexto": "P1 (C)"' in res.output and '"respuestas"' in res.output
    res = runner.invoke(cli, ["ai", str(tmp_path), "--mode", "classify"])
    assert res.exit_code == 1 and "TYPESAFE_API_KEY" in res.output
