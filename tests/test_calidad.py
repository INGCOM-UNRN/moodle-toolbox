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


def test_health_clasificacion_y_blueprint(tmp_path):
    from questions.core.moodle_health import auditar_archivos, generar_reporte_markdown

    gift = "$CATEGORY: $course$/C/Punteros\n\n"
    for i in range(5):
        gift += f"// [bloom:B{1 + i % 2}-{'recordar' if i % 2 == 0 else 'comprender'}] [dificultad-enunciado:{1 + i}/5]\n::P{i}:: q{i}? {{=a ~b ~c}}\n\n"
    gift += "$CATEGORY: $course$/C/Arreglos\n\n// [bloom:B4-analizar]\n::A:: q? {=a ~b ~c}\n\n::S:: sin clasificar {=a ~b ~c}\n"
    (tmp_path / "banco.gift").write_text(gift, encoding="utf-8")
    sub = tmp_path / "Java" / "Excepciones"
    sub.mkdir(parents=True)
    (sub / "e.gift").write_text("// [bloom:B5-evaluar]\n::E:: q? {=a ~b ~c}\n", encoding="utf-8")

    res = auditar_archivos([tmp_path / "banco.gift", sub / "e.gift"])
    cla = res["clasificacion"]
    assert cla["evaluables"] == 8 and cla["clasificadas"] == 7
    assert cla["bloom"]["recordar"] == 3 and cla["bloom"]["analizar"] == 1 and cla["bloom"]["evaluar"] == 1
    assert cla["dificultad_enunciado_media"] == 3.0
    assert set(cla["blueprint"]) == {"C/Punteros", "C/Arreglos", "Java/Excepciones"}
    assert cla["categorias_sin_niveles_altos"] == [{"categoria": "C/Punteros", "clasificadas": 5}]
    assert any(a["clave"] == "sin_niveles_altos" for a in res["resumen"]["advertencias"])
    reporte = generar_reporte_markdown(res, "banco")
    assert "## Clasificación (Bloom y dificultad)" in reporte and "| C/Punteros | 3 | 2 | · | · | · | · | 5 |" in reporte
