VALIDATE_INSTRUCTIONS = """
# Instrucciones para LLM: Validación de Preguntas
Al generar o corregir preguntas GIFT:
1. **Evita líneas en blanco internas**: No insertes líneas vacías entre el título, el enunciado y el bloque de respuestas. En GIFT, una línea en blanco termina la pregunta.
2. **Escapa los dos puntos**: No uses `:` en enunciados o respuestas a menos que lo escapes como `\:`. Para separadores visuales usa `：` (fullwidth).
3. **Títulos obligatorios**: Usa siempre `::Título::` al inicio para facilitar la organización.
4. **Resuelve duplicados**: Si el validador indica alta similitud, asegúrate de que la nueva pregunta aporte un valor distinto.
"""

FORMAT_INSTRUCTIONS = """
# Instrucciones para LLM: Formato GIFT
Genera archivos GIFT siguiendo este estándar visual estricto:
1. **Título**: Primera línea, formato `::Título::`.
2. **Enunciado**: Siguiente línea inmediata, preferiblemente con prefijo `[markdown]`.
3. **Bloque de respuestas**: Abrir `{` en su propia línea, cerrar `}` en su propia línea.
4. **Indentación**: Usa exactamente 4 espacios para cada opción de respuesta (`=`, `~`, `#`).
5. **Sin espacios extra**: Evita líneas en blanco innecesarias dentro de la estructura.
"""

XML_INSTRUCTIONS = """
# Instrucciones para LLM: Mantenimiento XML
Al manipular archivos XML de Moodle:
1. **Secciones CDATA**: Envuelve SIEMPRE el contenido de los nodos `<text>` en `<![CDATA[ ... ]]>`.
2. **Atributo Format**: Asegúrate de que los bloques de texto tengan `format="markdown"` si el contenido lo requiere.
3. **Nombres de archivo**: Usa el subcomando `rename` para normalizar nombres basados en el título interno.
"""

CONVERT_INSTRUCTIONS = """
# Instrucciones para LLM: Conversión de Formatos
1. **HTML a Markdown**: Prefiere siempre el formato Markdown. Usa backticks (`) para código y negritas (**) para énfasis.
2. **Atributos de Formato**: Al convertir tags HTML, asegúrate de actualizar el atributo `format="html"` a `format="markdown"` en el XML resultante.
"""

AI_INSTRUCTIONS = """
# Instrucciones para LLM: Procesamiento con IA
1. **Modo Improve**: Mejora la gramática y precisión pedagógica sin alterar la estructura GIFT fundamental.
2. **Modo Multiply**: Crea variaciones que evalúen el mismo objetivo de aprendizaje pero con diferentes contextos o distractores.
3. **Salida Pura**: Devuelve únicamente el código GIFT, sin preámbulos ni explicaciones adicionales.
"""

FIX_INSTRUCTIONS = """
# Instrucciones para LLM: Correcciones de Código
1. **Indentación en Código**: En bloques de código (```), usa `····` (4 puntos medios) en lugar de espacios si el archivo se usará en contextos donde el espacio es un delimitador crítico.
2. **Caracteres Especiales**: Convierte caracteres como `{` `}` `=` `#` a sus versiones fullwidth dentro de bloques de código para evitar que el parser de Moodle los interprete como parte de la lógica GIFT.
"""

GENERAL_INSTRUCTIONS = """
# Instrucciones Generales para LLM (Questions CLI)
- Prioriza siempre el formato GIFT por su legibilidad sobre el XML.
- Usa el CLI para validar cada cambio antes de dar por finalizada una tarea.
- Mantén la consistencia en el etiquetado (`// [tag:nombre]`) e identificadores (`// [id:id]`).
"""

SPLIT_INSTRUCTIONS = """
# Instrucciones para LLM: Dividir Archivos GIFT
1. **Un solo archivo por pregunta**: El repositorio sigue la política de una pregunta por archivo. Usa `split` para desglosar bancos masivos.
2. **Nombres automáticos**: El comando usará el título `::Título::` para nombrar el nuevo archivo. Asegúrate de que los títulos sean descriptivos y únicos.
3. **Consistencia**: Al dividir, se mantiene el contenido exacto de cada bloque. Verifica que cada bloque resultante sea una pregunta GIFT válida e independiente.
"""

def get_instructions(command_name):
    mapping = {
        'validate': VALIDATE_INSTRUCTIONS,
        'analyze': VALIDATE_INSTRUCTIONS,
        'format': FORMAT_INSTRUCTIONS,
        'xml': XML_INSTRUCTIONS,
        'convert': CONVERT_INSTRUCTIONS,
        'ai': AI_INSTRUCTIONS,
        'fix': FIX_INSTRUCTIONS,
        'split': SPLIT_INSTRUCTIONS
    }
    return mapping.get(command_name, GENERAL_INSTRUCTIONS)
