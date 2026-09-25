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
uv tool install --editable /home/mrtin/dev/tools/moodle-toolbox
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
| [`questions health`](#health) | Audita la salud, porcentajes de opciones, feedback y enlaces en el banco de preguntas. |
| [`questions ai`](#ai) | Procesamiento de preguntas usando IA (Gemini). |
| [`questions validate`](#validate) | Valida archivos o directorios de preguntas GIFT. |
| [`questions format`](#format) | Formatea archivos GIFT y ajusta bloques de código. |
| [`questions split`](#split) | Divide archivos GIFT con múltiples preguntas en archivos individuales. |
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

Audita la salud, porcentajes de opciones, feedback y enlaces en el banco de preguntas.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `archivo` | `<class 'pathlib.Path'>` | Argumento obligatorio de entrada. |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--md` | `Optional[pathlib.Path]` | `None` | Exportar reporte en Markdown. |
| `--clean-html` | `<class 'bool'>` | `False` | Limpiar etiquetas HTML obsoletas y estilos inline. |
| `--json` | `<class 'bool'>` | `False` | Emite el diagnóstico como JSON versionado. |

#### Ejemplo de Invocación
```bash
questions health <archivo>
```

### `questions ai`

Procesamiento de preguntas usando IA (Gemini).

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--inputs` | `Optional[List[pathlib.Path]]` | `None` | - |
| `--llm` | `<class 'bool'>` | `False` | Muestra instrucciones para un LLM sobre este comando. |
| `--mode` | `<class 'str'>` | `improve` | Modo: improve (mejorar), multiply (variaciones) o transform (usar prompt personalizado). |
| `--prompt` | `Optional[str]` | `None` | Prompt personalizado o ruta a un archivo .txt con el prompt. |
| `--output` | `Optional[pathlib.Path]` | `None` | Directorio de salida (por defecto: output_<mode>). |
| `--model` | `Optional[str]` | `None` | Modelo de Gemini (default: configurado o gemini-2.0-flash). |
| `-r`, `--recursive` | `<class 'bool'>` | `False` | Procesar subdirectorios recursivamente. |
| `--batch-size` | `<class 'int'>` | `5` | Número de preguntas por petición a la API (default: 5). |
| `-i`, `--in-place` | `<class 'bool'>` | `False` | Escribir en la misma carpeta que el original. |
| `--suffix` | `Optional[str]` | `None` | Sufijo para los nuevos archivos (usado con --in-place, ej: -ia). |

#### Ejemplo de Invocación
```bash
questions ai
```

### `questions validate`

Valida archivos o directorios de preguntas GIFT.

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
questions validate
```

### `questions format`

Formatea archivos GIFT y ajusta bloques de código.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--paths` | `Optional[List[pathlib.Path]]` | `None` | - |
| `--llm` | `<class 'bool'>` | `False` | Muestra instrucciones para un LLM sobre este comando. |
| `-r`, `--recursive` | `<class 'bool'>` | `False` | Procesar recursivamente |
| `-n`, `--dry-run` | `<class 'bool'>` | `False` | No aplicar cambios |
| `--code` | `<class 'bool'>` | `False` | Ajustar indentación en bloques de código (```) |
| `--fullwidth` | `<class 'bool'>` | `False` | Convertir caracteres de código a fullwidth |
| `--normal` | `<class 'bool'>` | `False` | Convertir caracteres de código a normal (default) |
| `--correct-first` | `<class 'bool'>` | `False` | Mueve la respuesta correcta al principio (solo MC). |

#### Ejemplo de Invocación
```bash
questions format
```

### `questions split`

Divide archivos GIFT con múltiples preguntas en archivos individuales.

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--paths` | `Optional[List[pathlib.Path]]` | `None` | - |
| `--llm` | `<class 'bool'>` | `False` | Muestra instrucciones para un LLM sobre este comando. |
| `-r`, `--recursive` | `<class 'bool'>` | `False` | Procesar recursivamente. |
| `--remove` | `<class 'bool'>` | `False` | Borrar el archivo original después de dividirlo. |

#### Ejemplo de Invocación
```bash
questions split
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
    Requiere el extra 'ui': pip install questions[ui]

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