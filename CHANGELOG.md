# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/);
versiones según [SemVer](https://semver.org/lang/es/).

## [Sin publicar]

### Agregado

- **paridad GIFT/XML**: `validate`, `analyze stats` y `analyze similar` recorren repositorios con archivos `.gift` y `.xml` (y mezclados) sobre un parser de Moodle XML al modelo unificado; los duplicados se detectan también entre formatos.
- **health**: acepta archivos y directorios (`-r`) de ambos formatos con el mismo diagnóstico; agrega fracciones que Moodle rechaza al importar, respuesta única/múltiple, feedback por opción, cantidad de opciones y opciones repetidas, longitud relativa de las respuestas (correcta vs. distractores y sesgo a nivel banco), código sin proteger, backticks sin cerrar; `--clean-html` también en XML; `--min-opciones`, `--umbral-longitud`, `--max-items`.
- **format**: formatea Moodle XML (sangría, CDATA, comentarios) y `--correct-first` ordena por porcentaje en ambos formatos; `--fullwidth` agrega las marcas `·` (indentación) y `↵` (fin de línea), con `--sin-marcas` para omitirlas.
- **split**: divide archivos Moodle XML (un archivo por pregunta, con su categoría).
- **código**: un único módulo (`questions.core.codigo`) para fullwidth y marcas en GIFT y XML, con la forma normal de GIFT escapada y las variantes históricas (U+2007, U+037E) llevadas a `·` y `；`.

### Corregido

- **formatter**: el formato GIFT ya no corta preguntas con líneas en blanco en el código, no mezcla el código del enunciado con el bloque de respuestas ni une las líneas del código de una opción; `--correct-first` mueve el feedback junto a su opción.
- **code-chars**: el mapa de caracteres había perdido el NBSP y el `;` griego (entradas `" " → " "`), cada pasada agregaba una línea en blanco antes del cierre del bloque y en XML sólo se procesaba el CDATA.
- **parser**: las opciones con `\=`, `\~` o `\#` escapados ya no se parten.
- **xml cdata**: un `<text/>` vacío hacía que el contenido se extendiera hasta el próximo `</text>` y el XML quedaba inválido.
- **tree/unify (XML)**: el código con `<` o `&` producía XML inválido al exportar.
- **validate --json**: el progreso del escaneo de directorios ya no ensucia la salida.
- **analyze similar**: filtrado por prefijos exacto; un repositorio de 10 mil preguntas pasa de más de una hora a segundos.

## [0.2.0] - 2026-09-28

Primera versión con registro de cambios; lo anterior está en el historial de git.

### Agregado

- **cli**: cumplir el contrato de línea de comandos de LINEAMIENTOS §3.2 (N-ECO-04) (`af62923`)

### Documentación

- agregar el texto de la licencia GPL-3.0-or-later que declara pyproject (N-ECO-06) (`703388b`)
- **archivo**: quitar enlaces a scripts y documentos que ya no existen (N-ECO-17) (`ac4779e`)
- **instalacion**: instalar desde el repositorio y no con pip install questions (N-MOODLE-03) (`430349a`)
- incorporar manual de uso integral y referencia tecnica (moodle-toolbox) (`7c4a32f`)

### Mantenimiento

- **calidad**: verificar errores de Python y dependencias vulnerables (N-ECO-08, N-ECO-13) (`e2d396b`)
- **deps**: mover google-genai al extra opcional ai y actualizar dependencias vulnerables (N-MOODLE-02) (`9bb92c4`)
