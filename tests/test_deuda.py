"""Regresiones de la deuda listada en el documento de mejoras (parser, conversor, contrato)."""

from questions.core.parser import parse_gift


def test_emparejamiento_con_guiones_mayor_y_escapes():
    q = parse_gift("::M:: Uní {=1-1 -> 0 =a\\=b -> c\\~d =x > y -> z ####gen}")["questions"][0]
    assert [(p["subquestion"]["text"], p["subanswer"]) for p in q["matchPairs"]] == [
        ("1-1", "0"), ("a=b", "c~d"), ("x > y", "z")]
    assert q["globalFeedback"]["text"] == "gen"


def test_numerica_respeta_escapes_en_el_feedback():
    q = parse_gift("::N:: n {#=3.14:0.01 #pi es \\=3.14 ~%50%3 #casi}")["questions"][0]
    assert [(c["text"]["text"], c["feedback"]["text"], c.get("weight")) for c in q["choices"]] == [
        ("3.14:0.01", "pi es =3.14", None), ("3", "casi", 50.0)]


def test_respuesta_corta_conserva_el_credito_parcial():
    import xml.etree.ElementTree as ET

    from questions.core.converter import gift_to_xml

    xml = gift_to_xml("::C:: Capital de Francia {=París =%50%Paris}")
    fracciones = [a.get("fraction") for a in ET.fromstring(xml).find("question").findall("answer")]
    assert fracciones == ["100", "50"]


def test_gift_a_xml_conserva_lineas_en_blanco_del_codigo_y_es_valido():
    import xml.etree.ElementTree as ET

    from questions.core.converter import gift_to_xml

    # Con la llave abierta, el parser mantiene la línea en blanco dentro de la pregunta.
    xml = gift_to_xml("::C:: Ver\n```c\nint main() {\n    int a = 1 < 2 && 3;\n\n    return a;\n}\n```\n{=x ~y}")
    texto = ET.fromstring(xml).find("question/questiontext/text").text
    assert "int a = 1 < 2 && 3;\n\n    return a;" in texto
    assert "<![CDATA[" in xml


XML_PARRAFOS = """<?xml version="1.0" encoding="UTF-8"?>
<quiz><question type="multichoice">
<name><text>Linkage</text></name>
<questiontext format="markdown"><text><![CDATA[Considere `module.c`:

```c
int a = 1;
  
// comentario
```
#ifdef WINDOWS
// código A
#endif]]></text></questiontext>
<answer fraction="100"><text><![CDATA[`p->x`]]></text></answer>
<answer fraction="0"><text>otra</text></answer>
<idnumber>L-1</idnumber>
<tags><tag><text>enlace</text></tag></tags>
</question></quiz>"""


def test_xml_a_gift_sobre_el_modelo_es_gift_valido_y_sin_perdidas():
    from questions.core.codigo import transformar_codigo
    from questions.core.converter import xml_to_gift
    from questions.core.moodle_xml import parse_xml

    gift = xml_to_gift(XML_PARRAFOS)
    assert gift.startswith("// [id:L-1] [tag:enlace]\n::Linkage::[markdown]")
    pregunta = parse_gift(gift)["questions"][0]
    original = parse_xml(XML_PARRAFOS)["questions"][0]
    assert pregunta["type"] == "MC" and pregunta["id"] == "L-1" and pregunta["tags"] == ["enlace"]

    def normal(t):
        t = transformar_codigo(t, fullwidth=False)[0]
        return "\n".join(linea.rstrip() for linea in t.split("\n"))

    # Párrafos (\n), líneas de sólo espacios en el código (↵), // y -> (protegidos).
    assert normal(pregunta["stem"]["text"]) == normal(original["stem"]["text"]).replace("// código A", "／／ código A")
    assert normal(pregunta["choices"][0]["text"]["text"]) == "`p->x`"


def test_xml_a_gift_conserva_el_html_con_su_prefijo():
    from questions.core.converter import xml_to_gift

    xml = ('<quiz><question type="truefalse"><name><text>VF</text></name><questiontext format="html">'
           '<text><![CDATA[<p>¿<b>Cierto</b>?</p>]]></text></questiontext>'
           '<answer fraction="100"><text>true</text></answer><answer fraction="0"><text>false</text></answer>'
           '</question></quiz>')
    assert xml_to_gift(xml) == "::VF::[html]<p>¿<b>Cierto</b>?</p>\n{T}\n"
