"""`questions ai` sobre GIFT y Moodle XML con un modelo simulado (sin red).

El modelo siempre recibe GIFT compacto; la respuesta vuelve a cada archivo con su
convención y, en XML, sobre el <question> original.
"""

import types
import xml.etree.ElementTree as ET

from click.testing import CliRunner

from questions.cli import cli
from questions.core import ai
from questions.core.moodle_xml import parse_xml
from questions.core.parser import parse_gift

runner = CliRunner()

GIFT = """$CATEGORY: $course$/Java

// [tag:java] [id:J-1]
::Igualdad::[markdown]¿Qué imprime?
```java
if (a == b) {
····System.out.println("si");↵
}
```
{
    =`si` #Bien
    ~nada
    ~error
}
"""

XML = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="category"><category><text>$course$/C</text></category></question>
  <question type="multichoice">
    <name><text>Punteros</text></name>
    <questiontext format="markdown"><text><![CDATA[¿Qué imprime?
```c
int x ＝ 5；↵
printf（＂%d＂, x）；
```]]></text></questiontext>
    <generalfeedback format="markdown"><text></text></generalfeedback>
    <defaultgrade>2.0000000</defaultgrade>
    <penalty>0.5</penalty>
    <idnumber>C-7</idnumber>
    <single>true</single>
    <answer fraction="100" format="markdown"><text>5</text><feedback format="markdown"><text>Sí</text></feedback></answer>
    <answer fraction="0" format="markdown"><text>0</text><feedback format="markdown"><text></text></feedback></answer>
    <answer fraction="0" format="markdown"><text>basura</text><feedback format="markdown"><text></text></feedback></answer>
    <tags><tag><text>punteros</text></tag></tags>
  </question>
</quiz>
"""


class Modelo:
    """Cliente simulado: aplica `transformar` a cada pregunta del prompt."""

    def __init__(self, transformar=lambda n, texto: [texto]):
        self.transformar = transformar
        self.models = self
        self.prompts = []

    def generate_content(self, model, contents):
        self.prompts.append(contents)
        bloques = contents.split("\n\n--- PREGUNTA 1 ---\n", 1)[1]
        partes = ai._MARCADOR.split("--- PREGUNTA 1 ---\n" + bloques)
        salida = []
        for numero, texto in zip(partes[1::2], partes[2::2]):
            for resultado in self.transformar(int(numero), texto.strip()):
                salida.append(f"--- PREGUNTA {numero} ---\n{resultado}")
        return types.SimpleNamespace(text="\n\n".join(salida))


def _procesar(tmp_path, nombre, contenido, modelo, mode="improve"):
    origen = tmp_path / "banco"
    origen.mkdir(exist_ok=True)
    archivo = origen / nombre
    archivo.write_text(contenido, encoding="utf-8")
    salida = tmp_path / "salida"
    ai.run_global_ai_processing(modelo, "simulado", [archivo], salida, mode)
    return (salida / f"{archivo.stem}_{mode}{archivo.suffix}").read_text(encoding="utf-8")


def test_gift_se_envia_compacto_y_vuelve_con_su_convencion(tmp_path):
    modelo = Modelo(lambda n, t: [t.replace("nada", "no imprime nada")])
    salida = _procesar(tmp_path, "b.gift", GIFT, modelo)
    prompt = modelo.prompts[0]
    # Ni comentarios, ni categoría, ni marcas; el código va en ASCII sin escapar.
    assert "[tag:java]" not in prompt and "$CATEGORY" not in prompt
    assert "·" not in prompt and "↵" not in prompt
    assert 'if (a == b) {\n    System.out.println("si");\n}' in prompt
    # Al volver: metadatos, código protegido y marcas como en el original.
    assert salida.startswith("$CATEGORY: $course$/Java\n\n// [tag:java] [id:J-1]\n::Igualdad::")
    assert 'if （a ⩵ b） ｛↵\n····System.out.println（＂si＂）；↵\n｝' in salida
    pregunta = parse_gift(salida)["questions"][1]
    assert [c["text"]["text"] for c in pregunta["choices"]] == ["`si`", "no imprime nada", "error"]


def test_xml_conserva_metadatos_y_convencion_del_codigo(tmp_path):
    modelo = Modelo(lambda n, t: [t.replace("basura", "un valor indeterminado").replace("::Punteros::", "::Punteros en C::")])
    salida = _procesar(tmp_path, "b.xml", XML, modelo)
    prompt = modelo.prompts[0]
    assert "<question" not in prompt and "penalty" not in prompt
    assert "int x = 5;\nprintf(\"%d\", x);" in prompt
    pregunta = ET.fromstring(salida).findall("question")[1]
    assert pregunta.findtext("name/text") == "Punteros en C"
    assert pregunta.findtext("penalty") == "0.5" and pregunta.findtext("defaultgrade") == "2.0000000"
    assert pregunta.findtext("idnumber") == "C-7" and pregunta.findtext("tags/tag/text") == "punteros"
    assert "int x ＝ 5；↵\nprintf（＂%d＂, x）；\n```" in pregunta.findtext("questiontext/text")
    respuestas = pregunta.findall("answer")
    assert [a.findtext("text") for a in respuestas] == ["5", "0", "un valor indeterminado"]
    assert [a.get("fraction") for a in respuestas] == ["100", "0", "0"]
    assert respuestas[0].findtext("feedback/text") == "Sí" and respuestas[0].get("format") == "markdown"
    assert ET.fromstring(salida).find("question/category/text").text == "$course$/C"


def test_multiply_en_xml_crea_variaciones_sin_repetir_idnumber(tmp_path):
    modelo = Modelo(lambda n, t: [t.replace("Punteros", f"Punteros {i}") for i in range(1, 4)])
    salida = _procesar(tmp_path, "b.xml", XML, modelo, mode="multiply")
    preguntas = [q for q in ET.fromstring(salida).findall("question") if q.get("type") != "category"]
    assert [q.findtext("name/text") for q in preguntas] == ["Punteros 1", "Punteros 2", "Punteros 3"]
    assert [q.findtext("idnumber") for q in preguntas] == ["C-7", "", ""]


def test_respuestas_invalidas_o_que_cambian_la_forma_conservan_el_original(tmp_path, capsys):
    casos = {
        "sin GIFT": lambda n, t: ["Perdón, no puedo ayudar con eso."],
        "otro tipo": lambda n, t: ["::P:: ¿Sí? {T}"],
        "parte una opción": lambda n, t: [t.replace("~nada", "~int x = 5")],
    }
    for nombre, transformar in casos.items():
        salida = _procesar(tmp_path, "b.gift", GIFT, Modelo(transformar))
        assert salida == GIFT.strip() + "\n", nombre
    salida_xml = _procesar(tmp_path, "b.xml", XML, Modelo(lambda n, t: ["::X:: Q {T}"]))
    assert parse_xml(salida_xml)["questions"] == parse_xml(XML)["questions"]
    assert "se conserva el original" in capsys.readouterr().out


def test_separar_respuesta_con_cercos_y_sin_marcadores():
    texto = "```gift\n--- PREGUNTA 2 ---\n::B:: b {T}\n--- PREGUNTA 1 ---\n```\n::A:: a {T}\n```\n```"
    assert ai.separar_respuesta(texto, 2) == {2: ["::B:: b {T}"], 1: ["::A:: a {T}"]}
    assert ai.separar_respuesta("::A:: a {T}\n---\n::B:: b {F}", 2) == {1: ["::A:: a {T}"], 2: ["::B:: b {F}"]}


def test_la_salida_conserva_la_estructura_de_directorios(tmp_path):
    for carpeta in ("u1", "u2"):
        (tmp_path / "banco" / carpeta).mkdir(parents=True)
        (tmp_path / "banco" / carpeta / "q01.gift").write_text(f"::{carpeta}:: ¿Sí? {{T}}\n", encoding="utf-8")
    archivos = sorted((tmp_path / "banco").rglob("*.gift"))
    ai.run_global_ai_processing(Modelo(), "simulado", archivos, tmp_path / "salida", "improve")
    assert (tmp_path / "salida" / "u1" / "q01_improve.gift").read_text(encoding="utf-8").startswith("::u1::")
    assert (tmp_path / "salida" / "u2" / "q01_improve.gift").read_text(encoding="utf-8").startswith("::u2::")


def test_cli_dry_run_no_necesita_clave_y_muestra_el_ahorro(tmp_path, monkeypatch):
    monkeypatch.setattr(ai, "load_config", lambda: (_ for _ in ()).throw(AssertionError("no debe llamarse")))
    (tmp_path / "b.xml").write_text(XML, encoding="utf-8")
    (tmp_path / "b.gift").write_text(GIFT, encoding="utf-8")
    res = runner.invoke(cli, ["ai", str(tmp_path), "--dry-run"])
    assert res.exit_code == 0, res.output
    assert "2 preguntas" in res.output and "% menos" in res.output
    assert "--- PREGUNTA 2 ---" in res.output
    assert not list(tmp_path.glob("output_*"))


def test_titulos_gift_se_desescapan():
    assert parse_gift("::C\\: punteros:: ¿Sí? {T}")["questions"][0]["title"] == "C: punteros"


def test_xml_conserva_los_comentarios(tmp_path):
    con_comentario = XML.replace("<quiz>", "<quiz>\n  <!-- question: 1854266 -->", 1)
    salida = _procesar(tmp_path, "b.xml", con_comentario, Modelo())
    assert "<!-- question: 1854266 -->" in salida


def _con_feedback(n, texto):
    """Modelo que completa feedback y, además, intenta reescribir el enunciado y un feedback existente."""
    texto = texto.replace("¿Qué imprime?", "¿Qué muestra en pantalla?").replace("#Bien", "#Muy bien")
    lineas = []
    for linea in texto.splitlines():
        s = linea.strip()
        if s.startswith(("=", "~")) and "#" not in s:
            linea += " #Explicación de " + s[1:].strip()
        lineas.append(linea)
    lineas.insert(len(lineas) - 1, "\t####Repasá el concepto.")
    return ["\n".join(lineas)]


def test_feedback_completa_solo_lo_que_falta_en_gift(tmp_path):
    modelo = Modelo(_con_feedback)
    salida = _procesar(tmp_path, "b.gift", GIFT, modelo, mode="feedback")
    q = parse_gift(salida)["questions"][1]
    assert "¿Qué imprime?" in q["stem"]["text"]
    retros = [c["feedback"]["text"] for c in q["choices"]]
    assert retros == ["Bien", "Explicación de nada", "Explicación de error"]
    assert q["globalFeedback"]["text"] == "Repasá el concepto."
    assert salida.startswith("$CATEGORY: $course$/Java\n\n// [tag:java] [id:J-1]\n")
    assert "if （a ⩵ b） ｛↵" in salida


def test_feedback_en_xml_solo_toca_los_nodos_de_retroalimentacion(tmp_path):
    salida = _procesar(tmp_path, "b.xml", XML, Modelo(_con_feedback), mode="feedback")
    pregunta = ET.fromstring(salida).findall("question")[1]
    assert [a.findtext("feedback/text") for a in pregunta.findall("answer")] == [
        "Sí", "Explicación de 0", "Explicación de basura"]
    assert pregunta.findtext("generalfeedback/text") == "Repasá el concepto."
    assert pregunta.findtext("questiontext/text") == ET.fromstring(XML).findall("question")[1].findtext("questiontext/text")
    assert pregunta.findtext("penalty") == "0.5"


def test_feedback_saltea_las_preguntas_completas(tmp_path, capsys):
    archivo = tmp_path / "c.gift"
    archivo.write_text("::C:: ¿Sí? {=a #bien ~b #mal ####general}\n", encoding="utf-8")
    modelo = Modelo(_con_feedback)
    ai.run_global_ai_processing(modelo, "simulado", [archivo], tmp_path / "salida", "feedback")
    assert modelo.prompts == [] and "No se encontraron preguntas" in capsys.readouterr().out


def test_cache_evita_volver_a_consultar_al_modelo(tmp_path):
    modelo = Modelo(lambda n, t: [t.replace("nada", "no imprime nada")])
    primera = _procesar(tmp_path, "b.gift", GIFT, modelo)
    assert len(modelo.prompts) == 1
    segunda = _procesar(tmp_path, "b.gift", GIFT, modelo)
    assert len(modelo.prompts) == 1 and segunda == primera
    # Otro modo u otra instrucción no comparten la respuesta.
    _procesar(tmp_path, "b.gift", GIFT, modelo, mode="transform")
    assert len(modelo.prompts) == 2
    archivo = tmp_path / "banco" / "b.gift"
    ai.run_global_ai_processing(modelo, "simulado", [archivo], tmp_path / "salida", "improve", usar_cache=False)
    assert len(modelo.prompts) == 3
