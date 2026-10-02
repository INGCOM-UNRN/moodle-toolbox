"""Lector único y separación de GIFT consistente en todos los comandos."""


from questions.core.parser import parse_gift

# La línea en blanco está dentro de las llaves: no termina la pregunta.
CON_BLANCO = (
    "$CATEGORY: $course$/Funciones\n\n"
    "::Cuerpo:: ¿Qué devuelve f? {\n"
    "=int f(void) \\{\n\n    return 1;\\}\n"
    "~nada\n}\n\n"
    "::Otra:: ¿Sí? {T}\n"
)


def _preguntas(texto: str) -> list:
    return [q for q in parse_gift(texto)["questions"] if q["type"] != "Category"]


def test_una_pregunta_sin_cerrar_no_se_traga_el_resto():
    from questions.core.formatter import _bloques_gift

    texto = ("::Rota:: ¿Qué imprime `if (x) {`? {\n=algo\n~otra\n\n"
             "// [tag:java]\n// CAT: Clases\n::Sana:: ¿Sí? {T}\n\n"
             "$CATEGORY: $course$/Otra\n\n::Tercera:: ¿No? {F}\n")
    bloques = _bloques_gift(texto)
    assert len(bloques) == 4 and bloques[1].startswith("// [tag:java]") and bloques[2].startswith("$CATEGORY")
    titulos = [q["title"] for q in _preguntas(texto)]
    assert titulos[-2:] == ["Sana", "Tercera"]
    # Código con línea en blanco y llaves abiertas: sigue siendo una sola pregunta.
    assert len(_bloques_gift(CON_BLANCO)) == 3
