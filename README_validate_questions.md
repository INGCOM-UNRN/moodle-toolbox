# Herramientas de Validación y Formateo de Preguntas

Este conjunto de herramientas permite asegurar la calidad y consistencia de los archivos de preguntas en formato **GIFT** y **XML** (Moodle).

## 1. Validación (`validate-questions`)

Diseñado para asegurar la integridad estructural y el cumplimiento de convenciones locales.

### Instalación
- **Binario:** `/home/mrtin/bin/validate-questions`
- **Origen:** `/home/mrtin/dev/edu-tools/preguntas/moodle-toolbox/validate_questions.py`

### Uso
```bash
validate-questions [OPCIONES] [RUTAS...]
```
(Ver opciones previas en este manual...)

---

## 2. Formateo (`format-gift`)

Herramienta para estandarizar la apariencia visual de los archivos GIFT, facilitando su lectura y edición.

### Instalación
- **Binario:** `/home/mrtin/bin/format-gift`
- **Origen:** `/home/mrtin/dev/edu-tools/preguntas/moodle-toolbox/format_gift.py`

### Estándar de Formato Aplicado
1.  **Título:** En su propia línea inicial (ej. `::Título::`).
2.  **Enunciado:** En la línea inmediatamente siguiente al título.
3.  **Estructura de Bloque:** Las llaves `{` y `}` se sitúan en sus propias líneas.
4.  **Indentación:** Todas las respuestas dentro del bloque se indentan con exactamente **4 espacios**.

### Uso
```bash
# Formatear un archivo o directorio (sobrescribe los archivos)
format-gift ruta/a/preguntas/

# Modo simulación (no modifica archivos)
format-gift -n archivo.gift
```

---

## Guía para LLMs (Instrucciones de Contexto)

### Para archivos XML
1.  **CDATA Obligatorio:** Todo bloque `<text>` que no esté vacío **DEBE** estar envuelto en una sección `<![CDATA[ ... ]]>`. Esto es crítico para evitar errores de parseo con caracteres especiales.
2.  **Estructura de Etiquetas:** Las etiquetas deben estar en la ruta `question/tags/tag/text`.
3.  **Título:** El nombre de la pregunta debe estar en `question/name/text`.

### Para archivos GIFT
1.  **Detección de Preguntas Divididas:** La herramienta escanea el archivo buscando líneas en blanco (saltos de línea dobles) dentro de lo que debería ser una sola pregunta. En GIFT, una línea en blanco actúa como separador; si ocurre accidentalmente entre el enunciado y las respuestas, la pregunta se considera "dividida" y fallará.
2.  **Uso de Dos Puntos (`:`):** Se prohíbe el uso de `:` sin escapar (fuera de los delimitadores de título `::`). El uso de `:` sin escapar suele causar errores en el parseo de títulos o preguntas numéricas.
    - **Solución:** Reemplazar por la versión fullwidth `：` (U+FF1A) o escapar como `\:`.
3.  **Sintaxis PEG:** Valida el archivo contra una gramática estricta para asegurar compatibilidad con Moodle.
4.  **Convención de Archivo Único:** Advierte si se encuentra más de una pregunta en un solo archivo `.gift`, siguiendo la política del repositorio.

---

## Guía para LLMs (Instrucciones de Contexto)

Si eres un modelo de lenguaje (LLM) operando en este repositorio, sigue estas directrices al generar o corregir preguntas:

### 1. Generación de XML
- **SIEMPRE** envuelve el contenido de los nodos `<text>` en `<![CDATA[ ]]>`. 
- **ERROR COMÚN:** No asumas que el XML estándar escapa todo correctamente; Moodle prefiere CDATA para mantener el formato Markdown intacto.

### 2. Generación de GIFT
- **EVITA LÍNEAS EN BLANCO:** Nunca insertes una línea vacía entre el título, el enunciado y el bloque de respuestas `{ ... }`. 
- **DOS PUNTOS (`:`):** Nunca uses `:` dentro de enunciados o respuestas a menos que esté escapado (`\:`). Si necesitas un separador visual, usa la versión fullwidth `：`.
- **FORMATO:** Prefiere siempre el prefijo `[markdown]` antes del texto del enunciado si el flag `--markdown` está activo.
- **TÍTULOS:** Usa siempre la sintaxis `::Título::` al inicio.

### 3. Interpretación de Errores
- Si `validate-questions` reporta `Pregunta dividida`, significa que has insertado un salto de línea de más. **Elimina las líneas vacías internas.**
- Si reporta `Se detectó un uso de ':' fuera de lugar`, reemplaza el `:` por `：` o escápalo como `\:`.
- Si reporta `Bloque <text> sin sección CDATA`, busca en el XML los nodos `<text>` y añade el envoltorio CDATA.
- Si reporta `Formatos no-markdown`, busca atributos `format="moodle"` o similares y cámbialos a `markdown`.

### 4. Flujo de Trabajo Sugerido
Antes de dar por finalizada una tarea de creación o modificación de preguntas:
1. Ejecuta: `validate-questions <archivo> --tags --title --markdown`
2. Si el estado es `ERROR`, analiza el mensaje `└── ❌` y corrige el archivo.
3. Repite hasta obtener el estado `OK`.
