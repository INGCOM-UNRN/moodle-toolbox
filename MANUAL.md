# Manual de Uso y Referencia Técnica: moodle-toolbox

> **MOODLE-TOOLBOX** — Herramientas para gestionar preguntas de Moodle (GIFT, XML)
> **Versión:** `0.1.0` · **CLI principal:** `questions` · **Plugin Ripley:** `moodle-toolbox`

---

## 1. Arquitectura y Propósito Pedagógico

`moodle-toolbox` forma parte del ecosistema de herramientas de la cátedra de Programación 1 (UNRN). Su objetivo central es resolver de forma modular, determinista y automatizada las tareas asociadas a su dominio específico dentro del ciclo de desarrollo, evaluación y aprendizaje de software en C.

### Alcance Funcional (Qué cubre)
- Gestión integral, validación y mantenimiento de bancos de preguntas pedagógicas de Moodle.
- Conversión bidireccional fiel y sin pérdida entre formatos GIFT y Moodle XML.
- Normalización tipográfica de delimitadores de fórmulas matemáticas (LaTeX `\(...\)` y `\[...\]`) y bloques de código Markdown.
- Validación sintáctica y de completitud de metadatos de preguntas (retroalimentación, pesos porcentuales, categorías).
- Reorganización y sincronización de estructuras de directorios de categorías de preguntas.

### Límites de Responsabilidad y Delegación (Qué no cubre)
- Generación de preguntas de C con salida verificada por compilación: el comando `synth` **invoca** el motor de síntesis de `alucarD` (`generador_examenes.synthesizer`); la lógica de plantillas y su validación con GCC vive allí, no acá.
- Generación de exámenes en PDF con reconocimiento OMR (delegado a `alucard`).
- Creación de módulos de aprendizaje SCORM (delegado a `scorm-tools`).

### Principios de Diseño
- **Enfoque Pedagógico:** Diagnósticos y mensajes en español rioplatense orientados a facilitar la comprensión de errores conceptuales.
- **Salida Estructurada Dual:** Soporte nativo para visualización enriquecida en terminal (Rich) y salida parseable para orquestadores (`--json`).
- **Integración Contractual:** Capacidad de emitir secciones de reporte para `dredd` (`dredd-section`) y actuar como satélite orquestado por `ripley`.
- **Idempotencia y Robustez:** Validación de precondiciones y comandos de autodiagnóstico (`doctor`) para verificación del entorno.

---

## 2. Instalación y Requisitos

### Requisitos del Sistema
- **Python:** `>= 3.10` (recomendado Python 3.11 o 3.12).
- **Gestor de paquetes:** [`uv`](https://github.com/astral-sh/uv) (entorno estándar de cátedra).
- **Toolchain C (si aplica):** GCC / Clang, Make, GDB y bibliotecas estándar de desarrollo.

### Instalación en el Entorno de Usuario
Para instalar la herramienta de forma global y aislada en el sistema mediante `uv tool`:
```bash
uv tool install "questions[ai,ui,languagetool] @ git+https://github.com/INGCOM-UNRN/moodle-toolbox"
```

### Verificación de Instalación
Ejecutá el comando `doctor` para constatar que todas las dependencias y binarios requeridos estén presentes y operativos:
```bash
questions doctor
```

---

## 3. Guía Integral de Comandos (CLI)

| Comando | Descripción Breve |
| :--- | :--- |
| [`questions doctor`](#doctor) | Verifica el estado del entorno de MOODLE-TOOLBOX (Python, LanguageTool, gcc y el motor de síntesis). |
| [`questions health`](#health) | Audita la salud del banco: claves de corrección, feedback, cantidad y longitud de opciones, código y enlaces. |
| [`questions ai`](#ai) | Procesamiento de preguntas GIFT y Moodle XML usando IA (Gemini). |
| [`questions validate`](#validate) | Valida archivos o directorios de preguntas GIFT y Moodle XML. |
| [`questions format`](#format) | Formatea archivos GIFT y Moodle XML y transforma el código (fullwidth, · y ↵). |
| [`questions split`](#split) | Divide archivos GIFT o Moodle XML con múltiples preguntas en archivos individuales. |
| [`questions unify`](#unify) | Unifica árboles o grupos de archivos de preguntas (GIFT o XML) en un único archivo. |
| [`questions synth`](#synth) | daedalus en belmont: sintetiza preguntas de C verificadas con GCC. |
| [`questions ui`](#ui) | Abre el editor web local (cerebro) sobre DIRECTORIO. |
| [`questions spellcheck`](#spellcheck) | Verifica y corrige ortografía y gramática en bancos GIFT y XML usando LanguageTool. |
| [`questions languagetool`](#languagetool) | Verifica y corrige ortografía y gramática en bancos GIFT y XML usando LanguageTool. |
| [`questions grammar`](#grammar) | Verifica y corrige ortografía y gramática en bancos GIFT y XML usando LanguageTool. |

### `questions doctor`

Verifica el estado del entorno de MOODLE-TOOLBOX (Python, LanguageTool, gcc y el motor de síntesis).

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `<class 'bool'>` | `False` | Emitir diagnóstico en formato JSON estructurado. |

#### Ejemplo de Invocación
```bash
questions doctor
```

### `questions health`

Audita la salud del banco sobre el modelo unificado de preguntas: **da el mismo diagnóstico para GIFT y Moodle XML** y acepta archivos sueltos, directorios o una mezcla de ambos formatos.

- **Claves de corrección:** respuesta única con una opción de 100 % (las demás pueden dar crédito parcial), respuesta múltiple cuyos porcentajes positivos suman 100, respuesta corta y numérica con alguna opción de 100 %, y porcentajes que Moodle acepta al importar (`%33.33%` se rechaza: hace falta `%33.33333%`).
- **Retroalimentación:** cobertura del feedback general y por opción; preguntas sin ningún feedback y preguntas con feedback en sólo algunas opciones.
- **Cantidad de opciones:** distribución en opción múltiple, preguntas con menos de `--min-opciones` (emparejamiento: menos de 3 pares) y opciones repetidas.
- **Longitud relativa de las respuestas:** preguntas donde la correcta es `--umbral-longitud` veces más larga (o más corta) que los distractores, y cuántas veces la correcta es la opción más larga frente a lo esperable por azar.
- **Código:** secciones sin proteger para GIFT, marcas no canónicas (U+2007, NBSP, `;` griego) y líneas en blanco sin `↵`; backticks sin cerrar.
- **Enlaces y HTML:** URLs `http://` o locales y etiquetas obsoletas (`<font>`, `<center>`, `style=`).

El informe empieza con un **resultado** que separa errores de advertencias. Son errores lo que Moodle no importaría o importaría mal: archivos ilegibles, porcentajes rechazados o que no suman 100, preguntas sin respuesta correcta o sin enunciado y, en GIFT, código que el formato interpreta o con líneas en blanco. El resto (feedback, opciones, longitud, enlaces, HTML) son advertencias. **Sale con código 1 si hay errores** (con `--estricto`, también ante advertencias); el JSON lleva `ok` y `resumen`.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `rutas` | `List[pathlib.Path]` | Archivos `.gift`/`.xml` o directorios. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `-r`, `--recursive` | `<class 'bool'>` | `False` | Buscar recursivamente en los directorios. |
| `--md` | `Optional[pathlib.Path]` | `None` | Exportar reporte en Markdown. |
| `--clean-html` | `<class 'bool'>` | `False` | Limpiar etiquetas HTML obsoletas y estilos inline (GIFT y XML). |
| `--min-opciones` | `<class 'int'>` | `3` | Mínimo de opciones esperado en opción múltiple. |
| `--umbral-longitud` | `<class 'float'>` | `1.5` | Razón de largo correcta/distractores a partir de la cual se advierte. |
| `--max-items` | `<class 'int'>` | `50` | Máximo de preguntas listadas por sección (0: todas). |
| `--estricto` | `<class 'bool'>` | `False` | Salir con código 1 también ante advertencias. |
| `--json` | `<class 'bool'>` | `False` | Emite el diagnóstico como JSON versionado. |

#### Ejemplo de Invocación
```bash
questions health banco.xml
questions health preguntas/ -r --md salud.md
```

### `questions ai`

Procesa preguntas GIFT y Moodle XML con Gemini (`improve`, `multiply` o `transform`). El modelo siempre recibe **GIFT compacto**, el formato más corto y el que los LLM conocen mejor:

- No se envían comentarios (`// [tag:…]`, `[id:…]`), `$CATEGORY` ni la estructura del XML; se conservan aparte.
- El código va en ASCII normal y sin las marcas `·`/`↵` (los símbolos fullwidth cuestan más tokens); la respuesta se vuelve a proteger y cada archivo recupera la convención de su original.
- En XML la respuesta se aplica sobre el `<question>` original: se conservan penalización, puntaje, numeración, tags, `idnumber` y formatos. Las variaciones de `multiply` no repiten el `idnumber`.
- Una respuesta que no es GIFT válido, que cambia el tipo o (en `improve`) la cantidad de opciones o de correctas deja la pregunta original.
- Con `--output`, la salida conserva la estructura de directorios.

En los bancos de la cátedra, lo enviado es un 47 % más corto que los archivos XML y un 7 % más corto que los GIFT.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--inputs` | `Optional[List[pathlib.Path]]` | `None` | Archivos .gift/.xml o directorios. |
| `--llm` | `<class 'bool'>` | `False` | Muestra instrucciones para un LLM sobre este comando. |
| `--mode` | `<class 'str'>` | `improve` | Modo: improve (mejorar), multiply (variaciones) o transform (usar prompt personalizado). |
| `--prompt` | `Optional[str]` | `None` | Prompt personalizado o ruta a un archivo .txt con el prompt. |
| `--output` | `Optional[pathlib.Path]` | `None` | Directorio de salida (por defecto: output_<mode>). |
| `--model` | `Optional[str]` | `None` | Modelo de Gemini (default: configurado o gemini-2.0-flash). |
| `-r`, `--recursive` | `<class 'bool'>` | `False` | Procesar subdirectorios recursivamente. |
| `--batch-size` | `<class 'int'>` | `5` | Número de preguntas por petición a la API (default: 5). |
| `-i`, `--in-place` | `<class 'bool'>` | `False` | Escribir en la misma carpeta que el original. |
| `--suffix` | `Optional[str]` | `None` | Sufijo para los nuevos archivos (usado con --in-place, ej: -ia). |
| `-n`, `--dry-run` | `<class 'bool'>` | `False` | Mostrar lo que se enviaría (y cuánto se ahorra) sin llamar al modelo ni escribir archivos. |

#### Ejemplo de Invocación
```bash
questions ai banco.xml --dry-run
questions ai preguntas/ -r --mode multiply --output variaciones/
```

### `questions validate`

Valida archivos o directorios de preguntas GIFT y Moodle XML: errores de parseo, estadísticas por formato y tipo, preguntas sin respuesta correcta y duplicados (también entre un `.gift` y un `.xml`). `questions analyze stats` y `questions analyze similar` recorren los mismos repositorios mixtos; la búsqueda de duplicados filtra por prefijos y escala a miles de preguntas.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--paths` | `Optional[List[pathlib.Path]]` | `None` | - |
| `--llm` | `<class 'bool'>` | `False` | Muestra instrucciones para un LLM sobre este comando. |
| `-o`, `--output` | `Optional[str]` | `None` | Archivo de salida para el informe |
| `-r`, `--recursive` | `<class 'bool'>` | `False` | Buscar recursivamente |
| `-v`, `--verbose` | `<class 'bool'>` | `False` | Información detallada |
| `-s`, `--similarity` | `<class 'float'>` | `0.85` | Threshold para duplicados |
| `-j`, `--json` | `<class 'bool'>` | `False` | Salida en JSON |

#### Ejemplo de Invocación
```bash
questions validate preguntas/ -r
```

### `questions format`

Formatea archivos GIFT y Moodle XML y transforma el código. GIFT: `::Título::`, enunciado, `{` y `}` en líneas propias y una opción por línea con 4 espacios. XML: sangría de 2 espacios y cada `<text>` con contenido en CDATA (conserva los comentarios). El código de enunciados y opciones conserva sus saltos de línea y sangría.

Las transformaciones de código son las mismas en ambos formatos (ver [caracteres especiales](docs/caracteres_especiales.md)): `--fullwidth` reemplaza los símbolos que chocan con GIFT (`{ } = ~ # : \ //`, y además `; < > [ ] ( ) * " &`) por sus formas fullwidth, marca la indentación con `·` (un punto por espacio) y cada fin de línea con `↵`; `--normal` lo deshace (en GIFT, escapando con `\` lo que GIFT interpretaría).

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--paths` | `Optional[List[pathlib.Path]]` | `None` | - |
| `--llm` | `<class 'bool'>` | `False` | Muestra instrucciones para un LLM sobre este comando. |
| `-r`, `--recursive` | `<class 'bool'>` | `False` | Procesar recursivamente |
| `-n`, `--dry-run` | `<class 'bool'>` | `False` | No aplicar cambios |
| `--code` | `<class 'bool'>` | `False` | Marcar la indentación del código con · (un punto por espacio) |
| `--fullwidth` | `<class 'bool'>` | `False` | Proteger el código: símbolos fullwidth y marcas · (indentación) y ↵ (fin de línea) |
| `--normal` | `<class 'bool'>` | `False` | Restaurar el código a caracteres normales (sin marcas) |
| `--marcas/--sin-marcas` | `<class 'bool'>` | `True` | Con --fullwidth, agregar las marcas · y ↵. |
| `--correct-first` | `<class 'bool'>` | `False` | Ordena las opciones de opción múltiple por porcentaje (la correcta primero). |

#### Ejemplo de Invocación
```bash
questions format preguntas/ -r --fullwidth
questions format banco.xml --correct-first
```

### `questions split`

Divide archivos GIFT o Moodle XML con múltiples preguntas en archivos individuales. En XML, cada archivo lleva la categoría vigente.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--paths` | `Optional[List[pathlib.Path]]` | `None` | - |
| `--llm` | `<class 'bool'>` | `False` | Muestra instrucciones para un LLM sobre este comando. |
| `-r`, `--recursive` | `<class 'bool'>` | `False` | Procesar recursivamente. |
| `--remove` | `<class 'bool'>` | `False` | Borrar el archivo original después de dividirlo. |

#### Ejemplo de Invocación
```bash
questions split banco.xml
```

### `questions unify`

Unifica árboles o grupos de archivos de preguntas (GIFT o XML) en un único archivo.

    Es la operación inversa a 'split' y 'tree export': recopila preguntas
    recorriendo los directorios especificados, infiere y preserva las categorías,
    y genera un único banco monolítico (.gift o .xml).

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `output_file` | `<class 'pathlib.Path'>` | Archivo de salida unificado (.gift o .xml). |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--paths` | `Optional[List[pathlib.Path]]` | `None` | - |
| `--llm` | `<class 'bool'>` | `False` | Muestra instrucciones para un LLM sobre este comando. |
| `-f`, `--format` | `Optional[str]` | `None` | Formato de salida (por defecto se deduce de la extensión del archivo de salida). |
| `-r`, `--recursive/--no-recursive` | `<class 'bool'>` | `True` | Procesar directorios recursivamente (por defecto True). |
| `--remove` | `<class 'bool'>` | `False` | Borrar los archivos fuente después de unificarlos. |

#### Ejemplo de Invocación
```bash
questions unify <output_file>
```

### `questions synth`

daedalus en belmont: sintetiza preguntas de C verificadas con GCC.

    PLANTILLA es una de las generadoras incorporadas (ver --listar). Cada
    pregunta se crea con parámetros aleatorios, se compila y ejecuta de verdad
    para fijar la salida correcta, y se acompaña de distractores verosímiles.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--plantilla` | `<class 'str'>` | `` | - |
| `--llm` | `<class 'bool'>` | `False` | Muestra instrucciones para un LLM sobre este comando. |
| `-n`, `--cantidad` | `<class 'int'>` | `5` | Cantidad de preguntas a sintetizar. |
| `-s`, `--semilla` | `<class 'int'>` | `42` | Semilla pseudo-aleatoria (salida reproducible). |
| `-o`, `--output` | `Optional[pathlib.Path]` | `None` | Archivo destino: .gift o .xml según la extensión. |
| `--listar` | `<class 'bool'>` | `False` | Lista las plantillas disponibles y sale. |
| `--json` | `<class 'bool'>` | `False` | Emite el resultado como JSON versionado. |

#### Ejemplo de Invocación
```bash
questions synth
```

### `questions ui`

Abre el editor web local (cerebro) sobre DIRECTORIO.

    Permite navegar y editar preguntas en Moodle XML y GIFT desde el navegador.
    Requiere el extra 'ui': uv tool install "questions[ui] @ git+https://github.com/INGCOM-UNRN/moodle-toolbox"

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--directorio` | `<class 'str'>` | `.` | - |
| `--llm` | `<class 'bool'>` | `False` | Muestra instrucciones para un LLM sobre este comando. |
| `--host` | `<class 'str'>` | `127.0.0.1` | Host del servidor web. |
| `--port` | `<class 'int'>` | `5000` | Puerto del servidor web. |
| `--debug/--no-debug` | `<class 'bool'>` | `False` | Modo debug de Flask. |

#### Ejemplo de Invocación
```bash
questions ui
```

### `questions spellcheck`

Verifica y corrige ortografía y gramática en bancos GIFT y XML usando LanguageTool.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--paths` | `Optional[List[pathlib.Path]]` | `None` | - |
| `--llm` | `<class 'bool'>` | `False` | Muestra instrucciones para un LLM sobre este comando. |
| `-s`, `--server` | `Optional[str]` | `None` | URL del servidor LanguageTool (por defecto http://localhost:8081 y API pública) |
| `-u`, `--username` | `Optional[str]` | `None` | Usuario / email de LanguageTool Premium |
| `-k`, `--api-key` | `Optional[str]` | `None` | API Key / Token de LanguageTool Premium |
| `--premium` | `<class 'bool'>` | `False` | Forzar uso de la API LanguageTool Premium |
| `-l`, `--lang` | `<class 'str'>` | `es-AR` | Código de idioma (default: es-AR) |
| `--ignore-rules` | `Optional[str]` | `None` | Reglas a ignorar separadas por comas |
| `--ignore-words` | `Optional[str]` | `None` | Palabras a ignorar separadas por comas |
| `-f`, `--fix` | `<class 'bool'>` | `False` | Aplica correcciones ortográficas automáticas |
| `--md`, `--output-md` | `Optional[pathlib.Path]` | `None` | Genera reporte Markdown |
| `--json` | `<class 'bool'>` | `False` | Emite salida estructurada en formato JSON |

#### Ejemplo de Invocación
```bash
questions spellcheck
```

### `questions languagetool`

Verifica y corrige ortografía y gramática en bancos GIFT y XML usando LanguageTool.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--paths` | `Optional[List[pathlib.Path]]` | `None` | - |
| `--llm` | `<class 'bool'>` | `False` | Muestra instrucciones para un LLM sobre este comando. |
| `-s`, `--server` | `Optional[str]` | `None` | URL del servidor LanguageTool (por defecto http://localhost:8081 y API pública) |
| `-u`, `--username` | `Optional[str]` | `None` | Usuario / email de LanguageTool Premium |
| `-k`, `--api-key` | `Optional[str]` | `None` | API Key / Token de LanguageTool Premium |
| `--premium` | `<class 'bool'>` | `False` | Forzar uso de la API LanguageTool Premium |
| `-l`, `--lang` | `<class 'str'>` | `es-AR` | Código de idioma (default: es-AR) |
| `--ignore-rules` | `Optional[str]` | `None` | Reglas a ignorar separadas por comas |
| `--ignore-words` | `Optional[str]` | `None` | Palabras a ignorar separadas por comas |
| `-f`, `--fix` | `<class 'bool'>` | `False` | Aplica correcciones ortográficas automáticas |
| `--md`, `--output-md` | `Optional[pathlib.Path]` | `None` | Genera reporte Markdown |
| `--json` | `<class 'bool'>` | `False` | Emite salida estructurada en formato JSON |

#### Ejemplo de Invocación
```bash
questions languagetool
```

### `questions grammar`

Verifica y corrige ortografía y gramática en bancos GIFT y XML usando LanguageTool.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--paths` | `Optional[List[pathlib.Path]]` | `None` | - |
| `--llm` | `<class 'bool'>` | `False` | Muestra instrucciones para un LLM sobre este comando. |
| `-s`, `--server` | `Optional[str]` | `None` | URL del servidor LanguageTool (por defecto http://localhost:8081 y API pública) |
| `-u`, `--username` | `Optional[str]` | `None` | Usuario / email de LanguageTool Premium |
| `-k`, `--api-key` | `Optional[str]` | `None` | API Key / Token de LanguageTool Premium |
| `--premium` | `<class 'bool'>` | `False` | Forzar uso de la API LanguageTool Premium |
| `-l`, `--lang` | `<class 'str'>` | `es-AR` | Código de idioma (default: es-AR) |
| `--ignore-rules` | `Optional[str]` | `None` | Reglas a ignorar separadas por comas |
| `--ignore-words` | `Optional[str]` | `None` | Palabras a ignorar separadas por comas |
| `-f`, `--fix` | `<class 'bool'>` | `False` | Aplica correcciones ortográficas automáticas |
| `--md`, `--output-md` | `Optional[pathlib.Path]` | `None` | Genera reporte Markdown |
| `--json` | `<class 'bool'>` | `False` | Emite salida estructurada en formato JSON |

#### Ejemplo de Invocación
```bash
questions grammar
```

---

## 4. Formatos de Salida e Integración con el Ecosistema

### Modo Interactivo / Terminal (Rich)
Por defecto, la herramienta renderiza paneles, árboles y tablas estilizadas para facilitar la lectura del estudiante y docente en terminales modernas con soporte ANSI.

### Modo Estructurado JSON (`--json`)
Para integración con pipelines de CI/CD, scripts de automatización u orquestadores externos, la opción `--json` emite un documento JSON estricto por la salida estándar (`stdout`), dirigiendo cualquier mensaje de logging a `stderr`:
```bash
questions doctor --json
```

### Integración con Dredd (`dredd-section`)
Cuando la herramienta genera reportes de evaluación para entregas de alumnos, produce una sección Markdown estandarizada conforme al contrato de integración de Dredd (v1.0.0):
```markdown
<!-- dredd-section: moodle-toolbox, tool=moodle-toolbox, version=0.1.0, status=ok -->
```
Este encabezado garantiza la agregación determinista de los hallazgos en la rúbrica docente.

### Integración con Ripley
`moodle-toolbox` está registrada en el catálogo de plugins satélites de Ripley (`SATELLITE_CATALOG`). Puede invocarse directamente a través del motor de evaluación de Ripley configurando el análisis en `ripley.toml`.

---

## 5. Diagnóstico y Códigos de Salida

### Códigos de Retorno (`exit code`)
| Código | Significado |
| :---: | :--- |
| `0` | Ejecución exitosa sin hallazgos críticos ni errores de sintaxis. |
| `1` | Hallazgos pedagógicos detectados, infracción de reglas o advertencias activas. |
| `2` | Error de sintaxis en argumentos CLI o archivo fuente no encontrado. |
| `>2` | Error no recuperable del sistema, fallo de memoria o excepción interna. |

### Diagnóstico del Entorno (`doctor`)
Ante comportamientos inesperados, verificá el estado operativo con:
```bash
questions doctor
```
Comprueba la presencia de las dependencias requeridas y la integridad de los componentes del paquete.