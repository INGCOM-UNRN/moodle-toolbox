"""Motor de síntesis: compilación sandbox, distractores y exportación."""

from __future__ import annotations

import random
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

GCC = shutil.which("gcc")


@dataclass
class SnippetGenerado:
    """Un snippet C verificado listo para volverse pregunta."""

    plantilla: str
    titulo: str
    enunciado: str
    codigo: str
    salida_correcta: str
    distractores: list[str] = field(default_factory=list)
    explicacion: str = ""

    @property
    def opciones(self) -> list[str]:
        """Opciones mezcladas (correcta incluida) sin duplicados."""
        vistos: set[str] = {self.salida_correcta}
        opciones = [self.salida_correcta]
        for d in self.distractores:
            if d not in vistos:
                vistos.add(d)
                opciones.append(d)
        return opciones


def compilar_y_ejecutar(codigo: str, timeout_compilado: int = 20,
                        timeout_ejecucion: int = 5) -> tuple[bool, str]:
    """Compila y ejecuta un snippet C en un directorio temporal.

    Devuelve ``(True, stdout)`` si el programa termina con éxito; ``False`` y
    el diagnóstico en caso contrario. Requiere gcc en el PATH.
    """
    if GCC is None:
        raise RuntimeError("gcc no está disponible en el PATH")

    with tempfile.TemporaryDirectory(prefix="daedalus-") as tmp:
        fuente = Path(tmp) / "snippet.c"
        binario = Path(tmp) / "snippet.bin"
        fuente.write_text(codigo, encoding="utf-8")

        compilar = subprocess.run(
            [GCC, "-Wall", "-Wextra", "-Werror", "-std=c11", "-O0",
             "-o", str(binario), str(fuente)],
            capture_output=True, text=True, timeout=timeout_compilado,
        )
        if compilar.returncode != 0:
            return False, f"compilación falló:\n{compilar.stderr.strip()}"

        ejecutar = subprocess.run(
            [str(binario)],
            capture_output=True, text=True, timeout=timeout_ejecucion,
        )
        if ejecutar.returncode != 0:
            return False, f"ejecución falló (rc={ejecutar.returncode}):\n{ejecutar.stderr.strip()}"

        return True, ejecutar.stdout.rstrip("\n")


# ---------------------------------------------------------------------------
# Plantillas incorporadas
# ---------------------------------------------------------------------------

def _plantilla_precedencia(rng: random.Random) -> SnippetGenerado:
    a, b, c = rng.randint(2, 9), rng.randint(2, 9), rng.randint(2, 5)

    variantes = {
        "a + b * c": (a + b * c, f"({a} + {b}) * {c}", f"{a} + ({b} * {c}) invertido", f"{a*b + c*a}"),
        "(a + b) * c": ((a + b) * c, f"{a} + {b} * {c}", f"{a} * {b} + {c}", f"{a+b*c}"),
        "a - b - c": (a - b - c, f"{a} - ({b} - {c})", f"{b} - {a} - {c}", f"{a - (b+c)}"),
        "a * b % c": ((a * b) % c, f"{a} * ({b} % {c})", f"{a} % {b} * {c}", f"{(a*b) // c}"),
    }
    expr = rng.choice(list(variantes))
    correcto, d1, d2, d3 = variantes[expr]
    # Los distractores analíticos pueden colisionar o ser negativos raros: se validan al correr.
    codigo = (
        "#include <stdio.h>\n\n"
        "int main(void) {\n"
        f"    int a = {a}, b = {b}, c = {c};\n"
        f'    printf("%d\\n", {expr});\n'
        "    return 0;\n"
        "}\n"
    )
    ok, salida = compilar_y_ejecutar(codigo)
    if not ok:
        raise RuntimeError(salida)

    distractores = []
    for candidato in (d1, d2, d3):
        try:
            valor = eval(candidato, {"__builtins__": {}}, {"a": a, "b": b, "c": c})
            distractores.append(str(valor))
        except Exception:
            continue

    return SnippetGenerado(
        plantilla="precedencia",
        titulo=f"Precedencia de operadores ({a}, {b}, {c})",
        enunciado="¿Qué imprime por pantalla el siguiente programa?",
        codigo=codigo,
        salida_correcta=salida,
        distractores=[d for d in distractores],
        explicacion=f"`{expr}` aplica la precedencia estándar de C: `*`, `/` y `%` antes que `+` y `-`, "
                    "y asociatividad izquierda a derecha entre operadores de igual nivel.",
    )


def _plantilla_traza_punteros(rng: random.Random) -> SnippetGenerado:
    valores = [rng.randint(10, 99) for _ in range(4)]
    k = rng.randint(1, len(valores) - 1)
    codigo = (
        "#include <stdio.h>\n\n"
        "int main(void) {\n"
        f"    int v[] = {{{', '.join(map(str, valores))}}};\n"
        "    int *p = v;\n"
        f"    p += {k};\n"
        '    printf("%d\\n", *p);\n'
        "    return 0;\n"
        "}\n"
    )
    ok, salida = compilar_y_ejecutar(codigo)
    if not ok:
        raise RuntimeError(salida)

    distractores = [str(valores[0]), str(valores[k - 1] if k > 0 else valores[-1]),
                    str(valores[min(k + 1, len(valores) - 1)])]
    return SnippetGenerado(
        plantilla="traza-punteros",
        titulo=f"Aritmética de punteros (avanza {k})",
        enunciado="¿Qué imprime por pantalla el siguiente programa?",
        codigo=codigo,
        salida_correcta=salida,
        distractores=distractores,
        explicacion="`p += k` mueve el puntero `k` posiciones dentro del arreglo; "
                    "`*p` desreferencia esa posición (`v[" + str(k) + "]`).",
    )


def _plantilla_recursion(rng: random.Random) -> SnippetGenerado:
    n = rng.randint(3, 8)
    codigo = (
        "#include <stdio.h>\n\n"
        "int suma(int n) {\n"
        "    if (n <= 0) {\n"
        "        return 0;\n"
        "    }\n"
        "    return n + suma(n - 1);\n"
        "}\n\n"
        "int main(void) {\n"
        f'    printf("%d\\n", suma({n}));\n'
        "    return 0;\n"
        "}\n"
    )
    ok, salida = compilar_y_ejecutar(codigo)
    if not ok:
        raise RuntimeError(salida)

    real = sum(range(1, n + 1))
    distractores = [str(real - n), str(n * n), str(real + n)]
    return SnippetGenerado(
        plantilla="recursion",
        titulo=f"Recursión: suma de 1 a {n}",
        enunciado="¿Qué imprime por pantalla el siguiente programa?",
        codigo=codigo,
        salida_correcta=salida,
        distractores=distractores,
        explicacion="La recursión acumula `n + suma(n-1)` hasta el caso base `suma(0) = 0`.",
    )


def _plantilla_incrementos(rng: random.Random) -> SnippetGenerado:
    inicial = rng.randint(0, 5)
    codigo = (
        "#include <stdio.h>\n\n"
        "int main(void) {\n"
        f"    int i = {inicial};\n"
        '    printf("%d ", i++);\n'
        '    printf("%d ", i);\n'
        '    printf("%d\\n", ++i);\n'
        "    return 0;\n"
        "}\n"
    )
    ok, salida = compilar_y_ejecutar(codigo)
    if not ok:
        raise RuntimeError(salida)

    distractores = [f"{inicial+1} {inicial+1} {inicial+2}",
                    f"{inicial} {inicial+2} {inicial+2}",
                    f"{inicial+1} {inicial+1} {inicial+1}"]
    return SnippetGenerado(
        plantilla="incrementos",
        titulo="Post-incremento vs pre-incremento",
        enunciado="¿Qué imprime por pantalla el siguiente programa?",
        codigo=codigo,
        salida_correcta=salida,
        distractores=distractores,
        explicacion="`i++` entrega el valor viejo y luego incrementa; `++i` incrementa primero y entrega el valor nuevo.",
    )


PLANTILLAS = {
    "precedencia": ("Expresiones aritméticas con precedencia de operadores", _plantilla_precedencia),
    "traza-punteros": ("Traza de aritmética de punteros sobre un arreglo", _plantilla_traza_punteros),
    "recursion": ("Recursión simple (suma acumulada)", _plantilla_recursion),
    "incrementos": ("Post-incremento vs pre-incremento", _plantilla_incrementos),
}


def plantillas_disponibles() -> dict[str, str]:
    """Catálogo nombre -> descripción."""
    return {nombre: desc for nombre, (desc, _) in PLANTILLAS.items()}


def sintetizar(planta: str, cantidad: int = 5, semilla: int | None = None) -> list[SnippetGenerado]:
    """Genera `cantidad` snippets verificados con la plantilla indicada."""
    if GCC is None:
        raise RuntimeError("gcc no está disponible: daedalus lo necesita para verificar las respuestas")
    if planta not in PLANTILLAS:
        raise KeyError(f"Plantilla desconocida: '{planta}'. Disponibles: {', '.join(sorted(PLANTILLAS))}")

    generador = PLANTILLAS[planta][1]
    rng = random.Random(semilla)
    resultados: list[SnippetGenerado] = []
    intentos = 0
    while len(resultados) < cantidad and intentos < cantidad * 10:
        intentos += 1
        snippet = generador(rng)
        if any(s.salida_correcta == snippet.salida_correcta for s in resultados):
            continue  # variante repetida: no aporta como ítem de examen
        resultados.append(snippet)
    return resultados


# ---------------------------------------------------------------------------
# Exportación
# ---------------------------------------------------------------------------

def _bloque_codigo(codigo: str) -> str:
    # Sin líneas vacías internas: los parsers GIFT cortan bloques por líneas
    # en blanco y el código rompería la pregunta.
    limpio = "\n".join(l for l in codigo.rstrip("\n").splitlines() if l.strip())
    return "```c\n" + limpio + "\n```"


def exportar_gift(snippets: list[SnippetGenerado]) -> str:
    """Serializa los snippets como banco GIFT (selección múltiple)."""
    bloques = []
    for s in snippets:
        opciones = s.opciones
        cuerpo = [f"={_escape_gift(op)}" if op == s.salida_correcta else f"~{_escape_gift(op)}"
                  for op in opciones]
        bloque = (
            "// daedalus: sintetizado y verificado con gcc\n"
            f"::{s.titulo.replace('::', '')}:: {_escape_gift(s.enunciado)}\n"
            f"{_bloque_codigo(s.codigo)}\n"
            "{\n" + "\n".join(cuerpo) + "\n}"
        )
        bloques.append(bloque)
    return "\n\n".join(bloques) + "\n"


def exportar_xml(snippets: list[SnippetGenerado]) -> str:
    """Serializa los snippets como Moodle XML reutilizando gift_to_xml."""
    from questions.core.converter import gift_to_xml
    return gift_to_xml(exportar_gift(snippets))

def _escape_gift(texto: str) -> str:
    """Escapado GIFT consistente con questions.core.converter."""
    if not texto:
        return ""
    out = texto.replace("\\", "\\\\")
    for ch in ("=", "#", "{", "}", "~"):
        out = out.replace(ch, "\\" + ch)
    return out
