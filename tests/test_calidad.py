"""Calidad del banco: metadatos de clasificación, blueprint y señales de redacción en health."""

from questions.core.moodle_xml import parse_xml
from questions.core.parser import parse_gift


def test_metadatos_de_clasificacion_en_gift_y_xml():
    gift = "// [tag:x] [bloom:B3-aplicar] [dificultad-enunciado:3.4/5] [clasificacion:jev-1.13.0 confianza=1]\n::A:: q {T}"
    assert parse_gift(gift)["questions"][0]["metadata"] == {
        "bloom": "aplicar", "dificultad_enunciado": 3.4, "clasificador": "jev-1.13.0"}
    xml = ('<quiz><!-- question: 1 --><!-- [bloom:B1-recordar] [dificultad-respuestas:2/5] -->'
           '<question type="truefalse"><name><text>x</text></name><questiontext><text>q</text></questiontext>'
           '<tags><tag><text>dificultad-enunciado:4</text></tag></tags></question>'
           '<question type="truefalse"><name><text>y</text></name><questiontext><text>q</text></questiontext></question></quiz>')
    primera, segunda = parse_xml(xml)["questions"]
    assert primera["metadata"] == {"bloom": "recordar", "dificultad_respuestas": 2.0, "dificultad_enunciado": 4.0}
    assert "metadata" not in segunda  # el comentario es de la pregunta que sigue, no de todas
