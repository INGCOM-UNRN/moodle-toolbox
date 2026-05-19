from pathlib import Path
from questions.core.naming import slugify, get_question_title, set_question_title

def test_slugify():
    assert slugify("Hola Mundo") == "hola_mundo"
    assert slugify("Pregunta: ¿Qué es?") == "pregunta_que_es"
    assert slugify("Acción y Función") == "accion_y_funcion"

def test_get_set_gift_title(tmp_path):
    f = tmp_path / "test.gift"
    f.write_text("::Old Title::\nQuestion{=A}")
    
    assert get_question_title(f) == "Old Title"
    
    set_question_title(f, "New Title")
    assert get_question_title(f) == "New Title"
    assert "::New Title::" in f.read_text()

def test_get_set_xml_title(tmp_path):
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<quiz>
  <question type="multichoice">
    <name>
      <text>Old XML Title</text>
    </name>
  </question>
</quiz>"""
    f = tmp_path / "test.xml"
    f.write_text(xml_content)
    
    assert get_question_title(f) == "Old XML Title"
    
    set_question_title(f, "New XML Title")
    assert get_question_title(f) == "New XML Title"
    assert "<text>New XML Title</text>" in f.read_text()
