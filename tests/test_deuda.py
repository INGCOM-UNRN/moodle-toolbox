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
